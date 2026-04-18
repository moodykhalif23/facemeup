// Package auth owns password hashing, JWT issue/verify, and HTTP middleware.
//
// Token layout matches what the Python backend emits so tokens issued by
// either backend verify on the other (shared JWT_SECRET in .env):
//
//	{
//	  "sub":   <user_id>,       // string (users.id)
//	  "email": <email>,
//	  "role":  "customer"|"admin",
//	  "iat":   <unix ts>,
//	  "exp":   <unix ts>
//	}
//
// HS256. No refresh-token rotation logic yet — access tokens only.
package auth

import (
	"errors"
	"fmt"
	"time"

	"github.com/golang-jwt/jwt/v5"
)

// Claims is what we embed in every access token.
type Claims struct {
	Email string `json:"email"`
	Role  string `json:"role"`
	jwt.RegisteredClaims
}

// Issuer signs tokens with a shared secret.
type Issuer struct {
	secret []byte
	ttl    time.Duration
}

// NewIssuer creates an HS256 signer with the given access-token TTL.
// A zero TTL is interpreted as "use the 30-minute default"; negative TTLs
// are honoured verbatim (useful for tests that need expired tokens).
func NewIssuer(secret string, accessTTL time.Duration) *Issuer {
	if accessTTL == 0 {
		accessTTL = 30 * time.Minute
	}
	return &Issuer{secret: []byte(secret), ttl: accessTTL}
}

// Issue returns a signed access token.
func (i *Issuer) Issue(userID, email, role string) (string, time.Time, error) {
	now := time.Now().UTC()
	exp := now.Add(i.ttl)
	claims := &Claims{
		Email: email,
		Role:  role,
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   userID,
			IssuedAt:  jwt.NewNumericDate(now),
			ExpiresAt: jwt.NewNumericDate(exp),
		},
	}
	tok := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := tok.SignedString(i.secret)
	return signed, exp, err
}

// ErrInvalidToken covers every verification failure (expired, bad signature, wrong alg).
var ErrInvalidToken = errors.New("invalid token")

// Verify parses and validates a bearer token. Returns typed claims on success.
func (i *Issuer) Verify(tokenStr string) (*Claims, error) {
	parsed, err := jwt.ParseWithClaims(tokenStr, &Claims{}, func(t *jwt.Token) (any, error) {
		if _, ok := t.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected alg: %v", t.Header["alg"])
		}
		return i.secret, nil
	})
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrInvalidToken, err)
	}
	claims, ok := parsed.Claims.(*Claims)
	if !ok || !parsed.Valid {
		return nil, ErrInvalidToken
	}
	return claims, nil
}
