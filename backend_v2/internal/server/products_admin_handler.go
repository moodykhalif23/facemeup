package server

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/go-chi/chi/v5"

	"skincare/backend-v2/internal/db"
)

type productAdminRequest struct {
	SKU         string   `json:"sku"`
	Name        string   `json:"name"`
	Price       *float64 `json:"price,omitempty"`
	WCID        *int     `json:"wc_id,omitempty"`
	Stock       int      `json:"stock"`
	Description string   `json:"description,omitempty"`
	Category    string   `json:"category,omitempty"`
	ImageURL    string   `json:"image_url,omitempty"`
	Ingredients []string `json:"ingredients"`
	SuitableFor string   `json:"suitable_for"`
	Effects     []string `json:"effects"`
	Benefits    []string `json:"benefits"`
	Usage       string   `json:"usage,omitempty"`
}

func (req *productAdminRequest) toUpsertInput() *db.UpsertInput {
	in := &db.UpsertInput{
		SKU: req.SKU, Name: req.Name, Price: req.Price, WCID: req.WCID, Stock: req.Stock,
		Ingredients: req.Ingredients, SuitableFor: req.SuitableFor,
		Effects: req.Effects, Benefits: req.Benefits,
	}
	if s := strings.TrimSpace(req.Description); s != "" {
		in.Description = &s
	}
	if s := strings.TrimSpace(req.Category); s != "" {
		in.Category = &s
	}
	if s := strings.TrimSpace(req.ImageURL); s != "" {
		in.ImageURL = &s
	}
	if s := strings.TrimSpace(req.Usage); s != "" {
		in.Usage = &s
	}
	return in
}

// POST /products/admin/create
func (s *Server) handleAdminCreateProduct(w http.ResponseWriter, r *http.Request) {
	var req productAdminRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	if err := s.deps.Products.Upsert(r.Context(), req.toUpsertInput()); err != nil {
		s.log.Error("create product", "err", err)
		writeError(w, http.StatusBadRequest, "bad_request", err.Error())
		return
	}
	s.invalidateProductCache(r)
	writeJSON(w, http.StatusOK, map[string]any{"status": "ok", "id": req.SKU})
}

// PUT /products/admin/{sku}
func (s *Server) handleAdminUpdateProduct(w http.ResponseWriter, r *http.Request) {
	sku := chi.URLParam(r, "sku")
	if sku == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "sku required")
		return
	}
	var req productAdminRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	req.SKU = sku
	if err := s.deps.Products.Upsert(r.Context(), req.toUpsertInput()); err != nil {
		s.log.Error("update product", "err", err, "sku", sku)
		writeError(w, http.StatusBadRequest, "bad_request", err.Error())
		return
	}
	s.invalidateProductCache(r)
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// DELETE /products/admin/{sku}
func (s *Server) handleAdminDeleteProduct(w http.ResponseWriter, r *http.Request) {
	sku := chi.URLParam(r, "sku")
	if err := s.deps.Products.Delete(r.Context(), sku); err != nil {
		if errors.Is(err, db.ErrProductNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "product not found")
			return
		}
		s.log.Error("delete product", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not delete")
		return
	}
	s.invalidateProductCache(r)
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// DELETE /products/admin/bulk
func (s *Server) handleAdminBulkDeleteProducts(w http.ResponseWriter, r *http.Request) {
	n, err := s.deps.Products.BulkDelete(r.Context())
	if err != nil {
		s.log.Error("bulk delete products", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "bulk delete failed")
		return
	}
	s.invalidateProductCache(r)
	writeJSON(w, http.StatusOK, map[string]any{"deleted": n})
}

// POST /products/admin/seed — idempotent minimal catalog seeder.
// Inserts a handful of canonical Dr Rashel-style SKUs if the catalog is empty
// so the UI has something to render during dev. Real catalog comes from WC sync.
func (s *Server) handleAdminSeedProducts(w http.ResponseWriter, r *http.Request) {
	seeds := seedCatalog()
	skus := make([]string, 0, len(seeds))
	for _, s := range seeds {
		skus = append(skus, s.SKU)
	}
	existing, err := s.deps.Products.CountBySKUs(r.Context(), skus)
	if err != nil {
		s.log.Error("count seed skus", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "seed check failed")
		return
	}
	if existing == len(seeds) {
		writeJSON(w, http.StatusOK, map[string]int{"products": 0}) // already seeded
		return
	}
	inserted := 0
	for _, seed := range seeds {
		if err := s.deps.Products.Upsert(r.Context(), seed); err != nil {
			s.log.Error("seed insert", "err", err, "sku", seed.SKU)
			continue
		}
		inserted++
	}
	s.invalidateProductCache(r)
	writeJSON(w, http.StatusOK, map[string]int{"products": inserted})
}

func seedCatalog() []*db.UpsertInput {
	price := func(p float64) *float64 { return &p }
	desc := func(s string) *string { return &s }
	return []*db.UpsertInput{
		{
			SKU: "DR-CLEANSER-01", Name: "Salicylic Acid Gentle Cleanser", Price: price(1200),
			Stock: 20, Description: desc("Daily cleanser for blemish-prone skin."),
			Category: desc("Cleanser"), ImageURL: desc(""),
			SuitableFor: "all", Effects: []string{"acne", "oiliness"},
			Benefits: []string{"clarifying", "gentle"},
			Ingredients: []string{"Salicylic Acid 2%", "Niacinamide"},
		},
		{
			SKU: "DR-HA-SERUM-01", Name: "Hyaluronic Acid Hydrating Serum", Price: price(1800),
			Stock: 15, Description: desc("Deep hydration for dry, dehydrated skin."),
			Category: desc("Serum"),
			SuitableFor: "all", Effects: []string{"dryness"},
			Benefits: []string{"hydration", "plumping"},
			Ingredients: []string{"Hyaluronic Acid", "Glycerin"},
		},
		{
			SKU: "DR-NIA-SERUM-01", Name: "Niacinamide 10% Pore Serum", Price: price(1600),
			Stock: 12, Description: desc("Minimizes pores and controls excess sebum."),
			Category: desc("Serum"),
			SuitableFor: "all", Effects: []string{"oiliness", "acne"},
			Benefits: []string{"pore-refining", "brightening"},
			Ingredients: []string{"Niacinamide 10%", "Zinc PCA"},
		},
		{
			SKU: "DR-VITC-01", Name: "Vitamin C Brightening Treatment", Price: price(2200),
			Stock: 10, Description: desc("Targets dark spots and uneven tone."),
			Category: desc("Treatment"),
			SuitableFor: "all", Effects: []string{"hyperpigmentation"},
			Benefits: []string{"brightening", "antioxidant"},
			Ingredients: []string{"Ascorbic Acid 15%", "Vitamin E"},
		},
		{
			SKU: "DR-RET-01", Name: "Retinol 0.3% Renewal Cream", Price: price(2600),
			Stock: 8, Description: desc("Smooths fine lines and improves texture."),
			Category: desc("Moisturizer"),
			SuitableFor: "all", Effects: []string{"wrinkles"},
			Benefits: []string{"anti-aging", "resurfacing"},
			Ingredients: []string{"Retinol 0.3%", "Squalane"},
		},
		{
			SKU: "DR-CENT-01", Name: "Centella Calming Gel", Price: price(1400),
			Stock: 18, Description: desc("Soothes redness and irritation."),
			Category: desc("Moisturizer"),
			SuitableFor: "all", Effects: []string{"redness"},
			Benefits: []string{"calming", "repairing"},
			Ingredients: []string{"Centella Asiatica", "Madecassoside"},
		},
	}
}

func (s *Server) invalidateProductCache(r *http.Request) {
	if s.deps.Cache == nil {
		return
	}
	keys, _ := s.deps.Cache.Keys(r.Context(), "products:*")
	keys2, _ := s.deps.Cache.Keys(r.Context(), "recommend:*")
	keys = append(keys, keys2...)
	if len(keys) > 0 {
		_, _ = s.deps.Cache.Delete(r.Context(), keys...)
	}
}
