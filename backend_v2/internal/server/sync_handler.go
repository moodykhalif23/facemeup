package server

import (
	"context"
	"errors"
	"net/http"
	"strconv"
	"strings"
	"time"

	"skincare/backend-v2/internal/db"
	"skincare/backend-v2/internal/woocommerce"
)

const wcSyncTimeout = 90 * time.Second

// POST /sync/woocommerce          — admin: full product sync from the WC store
func (s *Server) handleSyncWoocommerceProducts(w http.ResponseWriter, r *http.Request) {
	if s.deps.WCClient == nil {
		writeError(w, http.StatusServiceUnavailable, "not_configured",
			"WooCommerce credentials not set")
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), wcSyncTimeout)
	defer cancel()

	products, err := s.deps.WCClient.FetchAllProducts(ctx)
	if err != nil {
		if errors.Is(err, woocommerce.ErrNotConfigured) {
			writeError(w, http.StatusServiceUnavailable, "not_configured", err.Error())
			return
		}
		s.log.Error("wc fetch products", "err", err)
		writeError(w, http.StatusBadGateway, "wc_error", err.Error())
		return
	}

	var added, updated, failed int
	for _, wp := range products {
		existing, _ := s.deps.Products.GetBySKU(ctx, fallbackSKU(wp))
		input := wcToUpsertInput(wp)
		if err := s.deps.Products.Upsert(ctx, input); err != nil {
			s.log.Warn("wc upsert", "err", err, "sku", input.SKU)
			failed++
			continue
		}
		if existing == nil {
			added++
		} else {
			updated++
		}
	}
	s.invalidateProductCache(r)

	writeJSON(w, http.StatusOK, map[string]any{
		"products_synced":  added + updated,
		"products_added":   added,
		"products_updated": updated,
		"products_failed":  failed,
	})
}

// POST /sync/woocommerce/wc-id  — populate wc_id on local products by matching SKU.
// Returns how many SKUs got linked. Authenticated users can run it (cart uses it).
func (s *Server) handleSyncWoocommerceIDs(w http.ResponseWriter, r *http.Request) {
	if s.deps.WCClient == nil {
		writeJSON(w, http.StatusOK, map[string]int{"synced": 0})
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), wcSyncTimeout)
	defer cancel()

	wc, err := s.deps.WCClient.FetchAllProducts(ctx)
	if err != nil {
		s.log.Error("wc fetch for id sync", "err", err)
		writeError(w, http.StatusBadGateway, "wc_error", err.Error())
		return
	}
	local, err := s.deps.Products.List(ctx)
	if err != nil {
		s.log.Error("list local products", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", err.Error())
		return
	}

	bySKU := make(map[string]int, len(wc))
	for _, p := range wc {
		if p.SKU != "" {
			bySKU[strings.ToLower(p.SKU)] = p.ID
		}
	}

	var synced int
	for _, l := range local {
		if l.WCID != nil {
			continue
		}
		if wcID, ok := bySKU[strings.ToLower(l.SKU)]; ok {
			if err := s.deps.Products.SetWCID(ctx, l.SKU, wcID); err == nil {
				synced++
			}
		}
	}
	s.invalidateProductCache(r)
	writeJSON(w, http.StatusOK, map[string]int{"synced": synced})
}

// POST /sync/woocommerce/orders  — admin: pull recent WC orders, try to
// match them to a local user by email. Matches are added; misses counted.
func (s *Server) handleSyncWoocommerceOrders(w http.ResponseWriter, r *http.Request) {
	if s.deps.WCClient == nil {
		writeError(w, http.StatusServiceUnavailable, "not_configured",
			"WooCommerce credentials not set")
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), wcSyncTimeout)
	defer cancel()

	orders, err := s.deps.WCClient.FetchRecentOrders(ctx, 100)
	if err != nil {
		s.log.Error("wc fetch orders", "err", err)
		writeError(w, http.StatusBadGateway, "wc_error", err.Error())
		return
	}

	var added, updated, skipped int
	for _, wo := range orders {
		if wo.CustomerEmail == "" {
			skipped++
			continue
		}
		user, err := s.deps.Users.GetByEmail(ctx, wo.CustomerEmail)
		if err != nil {
			skipped++
			continue
		}
		items := make([]db.OrderItem, 0, len(wo.LineItems))
		for _, li := range wo.LineItems {
			price, _ := strconv.ParseFloat(li.Total, 64)
			items = append(items, db.OrderItem{
				SKU: li.SKU, ProductName: li.Name, Quantity: li.Quantity, Price: price,
			})
		}
		total, _ := strconv.ParseFloat(wo.Total, 64)
		if _, _, err := s.deps.Orders.Insert(ctx, &db.InsertOrderInput{
			UserID: user.ID, Channel: "woocommerce", Items: items, Total: &total,
		}); err != nil {
			s.log.Warn("insert wc order", "err", err)
			skipped++
			continue
		}
		added++
		_ = updated
	}

	writeJSON(w, http.StatusOK, map[string]int{
		"orders_synced":    added,
		"added":            added,
		"updated":          updated,
		"skipped_no_user":  skipped,
	})
}

// --- helpers ----------------------------------------------------------------

func fallbackSKU(p woocommerce.Product) string {
	if strings.TrimSpace(p.SKU) != "" {
		return p.SKU
	}
	return "wc-" + strconv.Itoa(p.ID)
}

func wcToUpsertInput(p woocommerce.Product) *db.UpsertInput {
	sku := fallbackSKU(p)
	price := woocommerce.ParsePrice(p.Price)
	if price == 0 {
		price = woocommerce.ParsePrice(p.RegularPrice)
	}
	var priceP *float64
	if price > 0 {
		priceP = &price
	}
	wcID := p.ID
	in := &db.UpsertInput{
		SKU:         sku,
		Name:        p.Name,
		Price:       priceP,
		WCID:        &wcID,
		SuitableFor: "all",
	}
	if p.StockQuantity != nil {
		in.Stock = *p.StockQuantity
	}
	if desc := strings.TrimSpace(stripHTML(p.Description)); desc != "" {
		in.Description = &desc
	}
	if len(p.Categories) > 0 {
		c := p.Categories[0].Name
		in.Category = &c
	}
	if len(p.Images) > 0 {
		img := p.Images[0].Src
		in.ImageURL = &img
	}
	return in
}

func stripHTML(s string) string {
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
