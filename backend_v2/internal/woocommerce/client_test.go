package woocommerce

import "testing"

func TestStripTagsRemovesSimpleHTML(t *testing.T) {
	cases := map[string]string{
		"":                                 "",
		"plain":                            "plain",
		"<p>hello</p>":                     "hello",
		"<b>bold</b> and <i>italic</i>":    "bold and italic",
		"<div class='x'>nested<br/></div>": "nested",
		"  <p>trim me</p>  ":               "trim me",
	}
	for in, want := range cases {
		if got := stripTags(in); got != want {
			t.Errorf("stripTags(%q)=%q want %q", in, got, want)
		}
	}
}

func TestMapToUpsertFallsBackToWCIDWhenSkuMissing(t *testing.T) {
	out := MapToUpsert(Product{ID: 42})
	if out["sku"].(string) != "wc-42" {
		t.Fatalf("expected fallback SKU 'wc-42', got %v", out["sku"])
	}
}

func TestMapToUpsertPullsRegularPriceIfPriceZero(t *testing.T) {
	out := MapToUpsert(Product{ID: 1, SKU: "X", Price: "0", RegularPrice: "9.95"})
	if out["price"].(float64) != 9.95 {
		t.Fatalf("expected regular_price fallback, got %v", out["price"])
	}
}
