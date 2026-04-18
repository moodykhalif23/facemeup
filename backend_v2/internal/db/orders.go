package db

import (
	"context"
	"encoding/json"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// OrderItem is one line inside orders.items_json.
type OrderItem struct {
	SKU         string  `json:"sku"`
	ProductName string  `json:"product_name"`
	Quantity    int     `json:"quantity"`
	Price       float64 `json:"price"`
}

// Order mirrors the orders table with items_json decoded.
type Order struct {
	ID         int
	UserID     string
	WCOrderID  *int
	Channel    string
	Status     string
	Total      *float64
	Items      []OrderItem
	CreatedAt  time.Time
	UserEmail  *string // populated by admin list queries (JOIN users)
	UserName   *string
}

// ErrOrderNotFound is returned on 0-row GETs.
var ErrOrderNotFound = errors.New("order not found")

type Orders struct{ pool *pgxpool.Pool }

func NewOrders(pool *pgxpool.Pool) *Orders { return &Orders{pool: pool} }

// InsertInput is the create-order payload.
type InsertOrderInput struct {
	UserID  string
	Channel string
	Items   []OrderItem
	Total   *float64
}

// Insert creates a new order and returns its generated id.
func (o *Orders) Insert(ctx context.Context, in *InsertOrderInput) (int, time.Time, error) {
	itemsJSON, err := json.Marshal(in.Items)
	if err != nil {
		return 0, time.Time{}, err
	}
	now := time.Now().UTC()
	const q = `
		INSERT INTO orders (user_id, channel, items_json, status, total, created_at)
		VALUES ($1, $2, $3, 'created', $4, $5)
		RETURNING id, created_at
	`
	var id int
	var createdAt time.Time
	if err := o.pool.QueryRow(ctx, q, in.UserID, in.Channel, string(itemsJSON), in.Total, now).
		Scan(&id, &createdAt); err != nil {
		return 0, time.Time{}, err
	}
	return id, createdAt, nil
}

// ListByUser returns a user's orders newest-first.
func (o *Orders) ListByUser(ctx context.Context, userID string) ([]Order, error) {
	const q = `
		SELECT id, user_id, wc_order_id, channel, status, total, items_json, created_at
		FROM orders
		WHERE user_id = $1
		ORDER BY created_at DESC
	`
	rows, err := o.pool.Query(ctx, q, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]Order, 0, 16)
	for rows.Next() {
		ord, err := scanOrder(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, ord)
	}
	return out, rows.Err()
}

// GetByID returns a single order; callers must enforce ownership.
func (o *Orders) GetByID(ctx context.Context, id int) (*Order, error) {
	const q = `
		SELECT id, user_id, wc_order_id, channel, status, total, items_json, created_at
		FROM orders WHERE id = $1
	`
	ord, err := scanOrder(o.pool.QueryRow(ctx, q, id))
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrOrderNotFound
	}
	if err != nil {
		return nil, err
	}
	return &ord, nil
}

// ListAllWithUser is the admin list — joins users for email + full_name.
func (o *Orders) ListAllWithUser(ctx context.Context, limit int) ([]Order, error) {
	if limit <= 0 || limit > 2000 {
		limit = 500
	}
	const q = `
		SELECT o.id, o.user_id, o.wc_order_id, o.channel, o.status, o.total,
		       o.items_json, o.created_at, u.email, u.full_name
		FROM orders o
		LEFT JOIN users u ON u.id = o.user_id
		ORDER BY o.created_at DESC
		LIMIT $1
	`
	rows, err := o.pool.Query(ctx, q, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]Order, 0, 32)
	for rows.Next() {
		var ord Order
		var itemsJSON string
		err := rows.Scan(&ord.ID, &ord.UserID, &ord.WCOrderID, &ord.Channel, &ord.Status,
			&ord.Total, &itemsJSON, &ord.CreatedAt, &ord.UserEmail, &ord.UserName)
		if err != nil {
			return nil, err
		}
		_ = json.Unmarshal([]byte(itemsJSON), &ord.Items)
		out = append(out, ord)
	}
	return out, rows.Err()
}

// UpdateStatus — admin only. Status strings match the old Python backend:
// "created" | "paid" | "shipped" | "delivered" | "cancelled".
func (o *Orders) UpdateStatus(ctx context.Context, id int, status string) error {
	tag, err := o.pool.Exec(ctx, `UPDATE orders SET status = $1 WHERE id = $2`, status, id)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrOrderNotFound
	}
	return nil
}

func scanOrder(r rowScanner) (Order, error) {
	var ord Order
	var itemsJSON string
	err := r.Scan(&ord.ID, &ord.UserID, &ord.WCOrderID, &ord.Channel, &ord.Status,
		&ord.Total, &itemsJSON, &ord.CreatedAt)
	if err != nil {
		return ord, err
	}
	_ = json.Unmarshal([]byte(itemsJSON), &ord.Items)
	return ord, nil
}
