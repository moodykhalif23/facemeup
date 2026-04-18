package auth

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestMiddlewareRejectsMissingHeader(t *testing.T) {
	iss := NewIssuer("s", time.Minute)
	handler := Middleware(iss)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Fatalf("next handler should not run on missing auth")
	}))
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/x", nil))
	if w.Code != http.StatusUnauthorized {
		t.Fatalf("want 401, got %d", w.Code)
	}
}

func TestMiddlewareAttachesPrincipal(t *testing.T) {
	iss := NewIssuer("s", time.Minute)
	tok, _, _ := iss.Issue("u1", "a@b", "admin")

	var gotPrincipal *Principal
	handler := Middleware(iss)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPrincipal = PrincipalFrom(r.Context())
		w.WriteHeader(http.StatusOK)
	}))

	req := httptest.NewRequest(http.MethodGet, "/x", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("want 200, got %d", w.Code)
	}
	if gotPrincipal == nil || gotPrincipal.UserID != "u1" || !gotPrincipal.IsAdmin() {
		t.Fatalf("principal not attached correctly: %+v", gotPrincipal)
	}
}

func TestRequireAdminRejectsCustomer(t *testing.T) {
	iss := NewIssuer("s", time.Minute)
	tok, _, _ := iss.Issue("u1", "c@x", "customer")

	handler := Middleware(iss)(RequireAdmin()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Fatalf("should not reach handler")
	})))

	req := httptest.NewRequest(http.MethodGet, "/admin", nil)
	req.Header.Set("Authorization", "Bearer "+tok)
	w := httptest.NewRecorder()
	handler.ServeHTTP(w, req)
	if w.Code != http.StatusForbidden {
		t.Fatalf("want 403, got %d", w.Code)
	}
}
