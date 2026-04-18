package server

import "testing"

func TestFormatOrderNumberPadsLeftZeros(t *testing.T) {
	cases := map[int]string{
		1:       "SK000001",
		42:      "SK000042",
		123456:  "SK123456",
		1234567: "SK1234567",
	}
	for id, want := range cases {
		if got := formatOrderNumber(id); got != want {
			t.Errorf("formatOrderNumber(%d)=%q want %q", id, got, want)
		}
	}
}

func TestIsValidOrderStatus(t *testing.T) {
	for _, s := range []string{"created", "paid", "shipped", "delivered", "cancelled"} {
		if !isValidOrderStatus(s) {
			t.Errorf("%q should be valid", s)
		}
	}
	for _, s := range []string{"", "done", "completed", "pending", "CREATED"} {
		if isValidOrderStatus(s) {
			t.Errorf("%q should be rejected", s)
		}
	}
}
