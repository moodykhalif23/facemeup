package db

import (
	"context"
	"errors"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Product mirrors one row of product_catalog. CSV columns are pre-split.
type Product struct {
	SKU         string
	Name        string
	Price       *float64
	WCID        *int
	Stock       int
	Description *string
	Category    *string
	ImageURL    *string
	Ingredients []string
	SuitableFor string   // "male" | "female" | "all"
	Effects     []string // e.g. "acne", "hyperpigmentation"
	Benefits    []string
	Usage       *string
}

// ErrProductNotFound is returned on 0-row SELECTs by SKU.
var ErrProductNotFound = errors.New("product not found")

type Products struct{ pool *pgxpool.Pool }

func NewProducts(pool *pgxpool.Pool) *Products { return &Products{pool: pool} }

const productSelectCols = `
	sku, name, price, wc_id, stock, description, category, image_url,
	ingredients_csv, suitable_for, effects_csv, benefits_csv, usage
`

// List returns every product row (no pagination for now — matches old backend).
func (p *Products) List(ctx context.Context) ([]Product, error) {
	rows, err := p.pool.Query(ctx, `SELECT `+productSelectCols+` FROM product_catalog ORDER BY name`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]Product, 0, 64)
	for rows.Next() {
		pr, err := scanProduct(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, pr)
	}
	return out, rows.Err()
}

func (p *Products) GetBySKU(ctx context.Context, sku string) (*Product, error) {
	row := p.pool.QueryRow(ctx, `SELECT `+productSelectCols+` FROM product_catalog WHERE sku = $1`, sku)
	pr, err := scanProduct(row)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrProductNotFound
	}
	if err != nil {
		return nil, err
	}
	return &pr, nil
}

// UpsertInput is what the admin create/update handlers pass in.
type UpsertInput struct {
	SKU         string
	Name        string
	Price       *float64
	WCID        *int
	Stock       int
	Description *string
	Category    *string
	ImageURL    *string
	Ingredients []string
	SuitableFor string
	Effects     []string
	Benefits    []string
	Usage       *string
}

// Upsert does an INSERT ... ON CONFLICT (sku) DO UPDATE.
func (p *Products) Upsert(ctx context.Context, in *UpsertInput) error {
	if strings.TrimSpace(in.SKU) == "" {
		return errors.New("sku required")
	}
	if strings.TrimSpace(in.Name) == "" {
		return errors.New("name required")
	}
	if in.SuitableFor == "" {
		in.SuitableFor = "all"
	}

	const q = `
		INSERT INTO product_catalog (
			sku, name, price, wc_id, stock, description, category, image_url,
			ingredients_csv, suitable_for, effects_csv, benefits_csv, usage
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
		ON CONFLICT (sku) DO UPDATE SET
			name = EXCLUDED.name,
			price = EXCLUDED.price,
			wc_id = COALESCE(EXCLUDED.wc_id, product_catalog.wc_id),
			stock = EXCLUDED.stock,
			description = EXCLUDED.description,
			category = EXCLUDED.category,
			image_url = EXCLUDED.image_url,
			ingredients_csv = EXCLUDED.ingredients_csv,
			suitable_for = EXCLUDED.suitable_for,
			effects_csv = EXCLUDED.effects_csv,
			benefits_csv = EXCLUDED.benefits_csv,
			usage = EXCLUDED.usage
	`
	_, err := p.pool.Exec(ctx, q,
		in.SKU, in.Name, in.Price, in.WCID, in.Stock, in.Description, in.Category,
		in.ImageURL, strings.Join(in.Ingredients, ","), in.SuitableFor,
		strings.Join(in.Effects, ","), strings.Join(in.Benefits, ","), in.Usage,
	)
	return err
}

// SetWCID lets the sync job fill in wc_id for a SKU after matching.
func (p *Products) SetWCID(ctx context.Context, sku string, wcID int) error {
	tag, err := p.pool.Exec(ctx, `UPDATE product_catalog SET wc_id = $1 WHERE sku = $2`, wcID, sku)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrProductNotFound
	}
	return nil
}

func (p *Products) Delete(ctx context.Context, sku string) error {
	tag, err := p.pool.Exec(ctx, `DELETE FROM product_catalog WHERE sku = $1`, sku)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrProductNotFound
	}
	return nil
}

// BulkDelete removes all rows and returns the deleted count.
func (p *Products) BulkDelete(ctx context.Context) (int64, error) {
	tag, err := p.pool.Exec(ctx, `DELETE FROM product_catalog`)
	if err != nil {
		return 0, err
	}
	return tag.RowsAffected(), nil
}

// CountBySKUs returns how many of the given SKUs exist (used for seed idempotency).
func (p *Products) CountBySKUs(ctx context.Context, skus []string) (int, error) {
	if len(skus) == 0 {
		return 0, nil
	}
	var n int
	err := p.pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM product_catalog WHERE sku = ANY($1)`, skus,
	).Scan(&n)
	return n, err
}

func scanProduct(r rowScanner) (Product, error) {
	var p Product
	var ingCSV, effCSV string
	var benCSV *string
	err := r.Scan(
		&p.SKU, &p.Name, &p.Price, &p.WCID, &p.Stock,
		&p.Description, &p.Category, &p.ImageURL,
		&ingCSV, &p.SuitableFor, &effCSV, &benCSV, &p.Usage,
	)
	if err != nil {
		return p, err
	}
	p.Ingredients = splitCSV(ingCSV)
	p.Effects = splitCSV(effCSV)
	if benCSV != nil {
		p.Benefits = splitCSV(*benCSV)
	}
	return p, nil
}
