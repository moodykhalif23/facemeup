// Package woocommerce is a minimal REST-API client for a WooCommerce store.
//
// Scope: enough to sync products and (optionally) orders into the local DB.
// Auth via consumer_key/consumer_secret query params (documented WC pattern).
package woocommerce

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// Product is a minimal subset of WC's product schema — just what we map
// into product_catalog.
type Product struct {
	ID               int    `json:"id"`
	Name             string `json:"name"`
	Slug             string `json:"slug"`
	SKU              string `json:"sku"`
	Price            string `json:"price"`             // WC serialises as string
	RegularPrice     string `json:"regular_price"`
	StockQuantity    *int   `json:"stock_quantity"`
	StockStatus      string `json:"stock_status"`
	Description      string `json:"description"`
	ShortDescription string `json:"short_description"`
	Categories       []struct {
		Name string `json:"name"`
	} `json:"categories"`
	Images []struct {
		Src string `json:"src"`
	} `json:"images"`
}

// Order is a minimal subset of WC's order schema.
type Order struct {
	ID        int    `json:"id"`
	Status    string `json:"status"`
	Total     string `json:"total"`
	Currency  string `json:"currency"`
	DateCreated string `json:"date_created"`
	LineItems []struct {
		ProductID int    `json:"product_id"`
		Name      string `json:"name"`
		Quantity  int    `json:"quantity"`
		Total     string `json:"total"`
		SKU       string `json:"sku"`
	} `json:"line_items"`
	CustomerEmail string `json:"billing.email"` // not always populated
}

// Client is safe for concurrent use.
type Client struct {
	baseURL  string
	consumer string
	secret   string
	http     *http.Client
}

// New returns a client pointed at a WC store root (e.g. "https://drrashel.co.ke").
func New(baseURL, consumerKey, consumerSecret string, timeout time.Duration) *Client {
	if timeout == 0 {
		timeout = 30 * time.Second
	}
	return &Client{
		baseURL:  strings.TrimSuffix(baseURL, "/"),
		consumer: consumerKey,
		secret:   consumerSecret,
		http:     &http.Client{Timeout: timeout},
	}
}

// ErrNotConfigured is returned when the client was created without credentials.
var ErrNotConfigured = errors.New("woocommerce credentials not configured")

// FetchAllProducts paginates through /wc/v3/products until exhausted.
func (c *Client) FetchAllProducts(ctx context.Context) ([]Product, error) {
	if c.consumer == "" || c.secret == "" {
		return nil, ErrNotConfigured
	}
	var all []Product
	for page := 1; page <= 50; page++ { // 50×100 = 5k cap
		batch, err := c.fetchProductsPage(ctx, page, 100)
		if err != nil {
			return nil, err
		}
		if len(batch) == 0 {
			break
		}
		all = append(all, batch...)
		if len(batch) < 100 {
			break
		}
	}
	return all, nil
}

func (c *Client) fetchProductsPage(ctx context.Context, page, perPage int) ([]Product, error) {
	q := url.Values{}
	q.Set("consumer_key", c.consumer)
	q.Set("consumer_secret", c.secret)
	q.Set("page", strconv.Itoa(page))
	q.Set("per_page", strconv.Itoa(perPage))

	u := c.baseURL + "/wp-json/wc/v3/products?" + q.Encode()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return nil, err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("woocommerce fetch: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("woocommerce status %d: %s", resp.StatusCode, string(body))
	}
	var out []Product
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, fmt.Errorf("decode products: %w", err)
	}
	return out, nil
}

// FetchRecentOrders returns recent orders (paginated, capped at 500).
func (c *Client) FetchRecentOrders(ctx context.Context, perPage int) ([]Order, error) {
	if c.consumer == "" || c.secret == "" {
		return nil, ErrNotConfigured
	}
	if perPage <= 0 || perPage > 100 {
		perPage = 50
	}
	q := url.Values{}
	q.Set("consumer_key", c.consumer)
	q.Set("consumer_secret", c.secret)
	q.Set("per_page", strconv.Itoa(perPage))
	q.Set("orderby", "date")
	q.Set("order", "desc")

	u := c.baseURL + "/wp-json/wc/v3/orders?" + q.Encode()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return nil, err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("woocommerce orders: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("woocommerce status %d: %s", resp.StatusCode, string(body))
	}
	var out []Order
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, fmt.Errorf("decode orders: %w", err)
	}
	return out, nil
}

// MapToUpsert converts a WC Product into the shape our db.Products.Upsert expects.
// Callers still need to pass that through the Products repo.
func MapToUpsert(p Product) map[string]any {
	sku := strings.TrimSpace(p.SKU)
	if sku == "" {
		sku = fmt.Sprintf("wc-%d", p.ID)
	}
	price, _ := strconv.ParseFloat(p.Price, 64)
	if price == 0 {
		price, _ = strconv.ParseFloat(p.RegularPrice, 64)
	}
	img := ""
	if len(p.Images) > 0 {
		img = p.Images[0].Src
	}
	cat := ""
	if len(p.Categories) > 0 {
		cat = p.Categories[0].Name
	}
	stock := 0
	if p.StockQuantity != nil {
		stock = *p.StockQuantity
	}
	return map[string]any{
		"sku":          sku,
		"name":         p.Name,
		"price":        price,
		"wc_id":        p.ID,
		"stock":        stock,
		"description":  stripTags(p.Description),
		"short":        stripTags(p.ShortDescription),
		"image_url":    img,
		"category":     cat,
	}
}

// stripTags is a no-regex HTML stripper good enough for WC-provided HTML.
func stripTags(s string) string {
	var sb strings.Builder
	inTag := false
	for _, r := range s {
		switch {
		case r == '<':
			inTag = true
		case r == '>':
			inTag = false
		case !inTag:
			sb.WriteRune(r)
		}
	}
	return strings.TrimSpace(sb.String())
}
