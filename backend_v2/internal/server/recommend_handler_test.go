package server

import (
	"testing"

	"skincare/backend-v2/internal/db"
)

func TestRankProductsOrdersByConditionMatch(t *testing.T) {
	cleanser := db.Product{
		SKU: "A", Name: "Salicylic Cleanser", SuitableFor: "all",
		Effects: []string{"acne", "oiliness"},
	}
	vitC := db.Product{
		SKU: "B", Name: "Vitamin C Serum", SuitableFor: "all",
		Effects: []string{"hyperpigmentation"},
	}
	moisturizer := db.Product{
		SKU: "C", Name: "Basic Moisturizer", SuitableFor: "all",
	}

	req := &recommendRequest{
		SkinType:   "oily",
		Conditions: []string{"acne"},
	}
	out := rankProducts([]db.Product{moisturizer, vitC, cleanser}, req)

	if len(out) == 0 {
		t.Fatal("expected at least one match")
	}
	if out[0].SKU != "A" {
		t.Fatalf("cleanser should rank first, got %s (full list: %+v)", out[0].SKU, skus(out))
	}
}

func TestRankProductsRespectsGenderMatch(t *testing.T) {
	unisex := db.Product{SKU: "U", Name: "U", SuitableFor: "all", Effects: []string{"wrinkles"}}
	female := db.Product{SKU: "F", Name: "F", SuitableFor: "female", Effects: []string{"wrinkles"}}
	male := db.Product{SKU: "M", Name: "M", SuitableFor: "male", Effects: []string{"wrinkles"}}

	req := &recommendRequest{Conditions: []string{"wrinkles"}, Gender: "female"}
	out := rankProducts([]db.Product{male, unisex, female}, req)
	if len(out) < 2 {
		t.Fatalf("expected >=2 matches, got %d", len(out))
	}
	if out[0].SKU != "F" {
		t.Fatalf("female-matched product should rank first, got %s", out[0].SKU)
	}
}

func TestRankProductsDropsZeroScore(t *testing.T) {
	noMatch := db.Product{SKU: "X", SuitableFor: "nonexistent-gender"}
	req := &recommendRequest{Conditions: []string{"acne"}}
	out := rankProducts([]db.Product{noMatch}, req)
	if len(out) != 0 {
		t.Fatalf("expected 0 matches for zero-score product, got %d", len(out))
	}
}

func TestRecommendCacheKeyIsStableUnderConditionOrder(t *testing.T) {
	a := &recommendRequest{SkinType: "oily", Conditions: []string{"acne", "redness"}, Gender: "female"}
	b := &recommendRequest{SkinType: "oily", Conditions: []string{"redness", "acne"}, Gender: "female"}
	if recommendCacheKey("u1", a) != recommendCacheKey("u1", b) {
		t.Fatal("cache key must be order-independent")
	}
}

func TestContainsFuzzyHandlesSubstrings(t *testing.T) {
	if !containsFuzzy([]string{"acne-clearing"}, "acne") {
		t.Fatal("should match substring")
	}
	if !containsFuzzy([]string{"acne"}, "anti-acne-formula") {
		t.Fatal("should match reverse substring")
	}
	if containsFuzzy([]string{"wrinkles"}, "redness") {
		t.Fatal("no-op match")
	}
}

func skus(vs []productView) []string {
	out := make([]string, len(vs))
	for i, v := range vs {
		out[i] = v.SKU
	}
	return out
}
