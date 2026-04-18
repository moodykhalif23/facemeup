package server

import (
	"errors"
	"net/http"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"

	"skincare/backend-v2/internal/db"
)

// productView is what the frontend consumes from /products + /products/{sku}.
// Keeps exact field names the old backend produced.
type productView struct {
	ID          string   `json:"id"`
	SKU         string   `json:"sku"`
	Name        string   `json:"name"`
	Price       *float64 `json:"price"`
	WCID        *int     `json:"wc_id,omitempty"`
	Stock       int      `json:"stock"`
	Description string   `json:"description,omitempty"`
	Category    string   `json:"category,omitempty"`
	ImageURL    string   `json:"image_url,omitempty"`
	Ingredients []string `json:"ingredients,omitempty"`
	SuitableFor string   `json:"suitable_for"`
	Effects     []string `json:"effects,omitempty"`
	Benefits    []string `json:"benefits,omitempty"`
	Usage       string   `json:"usage,omitempty"`
}

func productToView(p db.Product) productView {
	v := productView{
		ID:          p.SKU,   // frontend uses sku as id
		SKU:         p.SKU,
		Name:        p.Name,
		Price:       p.Price,
		WCID:        p.WCID,
		Stock:       p.Stock,
		Ingredients: p.Ingredients,
		SuitableFor: p.SuitableFor,
		Effects:     p.Effects,
		Benefits:    p.Benefits,
	}
	if p.Description != nil {
		v.Description = *p.Description
	}
	if p.Category != nil {
		v.Category = *p.Category
	}
	if p.ImageURL != nil {
		v.ImageURL = *p.ImageURL
	}
	if p.Usage != nil {
		v.Usage = *p.Usage
	}
	return v
}

const (
	productCatalogKey    = "products:catalog"
	productDetailKey     = "products:detail:"
	productCacheTTL      = 5 * time.Minute
)

// GET /products
func (s *Server) handleListProducts(w http.ResponseWriter, r *http.Request) {
	if s.deps.Cache != nil {
		var cached []productView
		if hit, _ := s.deps.Cache.GetJSON(r.Context(), productCatalogKey, &cached); hit {
			writeJSON(w, http.StatusOK, cached)
			return
		}
	}

	products, err := s.deps.Products.List(r.Context())
	if err != nil {
		s.log.Error("list products", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not list products")
		return
	}
	out := make([]productView, 0, len(products))
	for _, p := range products {
		out = append(out, productToView(p))
	}
	if s.deps.Cache != nil {
		_ = s.deps.Cache.SetJSON(r.Context(), productCatalogKey, out, productCacheTTL)
	}
	writeJSON(w, http.StatusOK, out)
}

// GET /products/{id}  — id is actually the SKU.
func (s *Server) handleGetProduct(w http.ResponseWriter, r *http.Request) {
	sku := strings.TrimSpace(chi.URLParam(r, "id"))
	if sku == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "product id required")
		return
	}
	cacheKey := productDetailKey + sku
	if s.deps.Cache != nil {
		var cached productView
		if hit, _ := s.deps.Cache.GetJSON(r.Context(), cacheKey, &cached); hit {
			writeJSON(w, http.StatusOK, cached)
			return
		}
	}

	p, err := s.deps.Products.GetBySKU(r.Context(), sku)
	if err != nil {
		if errors.Is(err, db.ErrProductNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "product not found")
			return
		}
		s.log.Error("get product", "err", err, "sku", sku)
		writeError(w, http.StatusInternalServerError, "internal", "lookup failed")
		return
	}
	view := productToView(*p)
	if s.deps.Cache != nil {
		_ = s.deps.Cache.SetJSON(r.Context(), cacheKey, view, productCacheTTL)
	}
	writeJSON(w, http.StatusOK, view)
}
