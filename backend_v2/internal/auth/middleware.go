package auth

import (
	"context"
	"encoding/json"
	"net/http"
	"strings"
)

// ctxKey is unexported so callers must use Principal()/WithPrincipal().
type ctxKey struct{ name string }

var principalKey = ctxKey{name: "principal"}

// Principal is what handlers read out of the request context after the middleware ran.
type Principal struct {
	UserID string
	Email  string
	Role   string
}

// IsAdmin — sugar used by admin-only handlers.
func (p *Principal) IsAdmin() bool { return p != nil && p.Role == "admin" }

// Middleware returns a chi-compatible middleware that:
//   - rejects requests without a valid `Authorization: Bearer <token>` header (401)
//   - attaches a Principal to the request context on success
func Middleware(issuer *Issuer) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			tok := bearerToken(r)
			if tok == "" {
				writeErr(w, http.StatusUnauthorized, "missing_token", "Authorization header required")
				return
			}
			claims, err := issuer.Verify(tok)
			if err != nil {
				writeErr(w, http.StatusUnauthorized, "invalid_token", err.Error())
				return
			}
			p := &Principal{UserID: claims.Subject, Email: claims.Email, Role: claims.Role}
			next.ServeHTTP(w, r.WithContext(context.WithValue(r.Context(), principalKey, p)))
		})
	}
}

// RequireAdmin rejects 403 if the principal's role isn't "admin". Chain after Middleware.
func RequireAdmin() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			p := PrincipalFrom(r.Context())
			if p == nil || !p.IsAdmin() {
				writeErr(w, http.StatusForbidden, "forbidden", "admin role required")
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

// PrincipalFrom extracts the authenticated principal from context; nil if unauthenticated.
func PrincipalFrom(ctx context.Context) *Principal {
	p, _ := ctx.Value(principalKey).(*Principal)
	return p
}

func bearerToken(r *http.Request) string {
	h := r.Header.Get("Authorization")
	const prefix = "Bearer "
	if !strings.HasPrefix(h, prefix) {
		return ""
	}
	return strings.TrimSpace(h[len(prefix):])
}

func writeErr(w http.ResponseWriter, status int, code, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(map[string]any{
		"error": map[string]string{"code": code, "message": msg},
	})
}
