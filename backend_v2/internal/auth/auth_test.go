package auth

import (
	"testing"
	"time"
)

func TestHashAndVerifyPassword(t *testing.T) {
	hash, err := HashPassword("hunter2!")
	if err != nil {
		t.Fatalf("hash: %v", err)
	}
	if hash == "hunter2!" {
		t.Fatalf("bcrypt returned plaintext")
	}
	if err := VerifyPassword(hash, "hunter2!"); err != nil {
		t.Fatalf("verify right password: %v", err)
	}
	if err := VerifyPassword(hash, "wrong"); err != ErrWrongPassword {
		t.Fatalf("want ErrWrongPassword, got %v", err)
	}
}

func TestJWTIssueAndVerify(t *testing.T) {
	iss := NewIssuer("test-secret", 5*time.Minute)
	tok, exp, err := iss.Issue("user-123", "alice@example.com", "customer")
	if err != nil {
		t.Fatalf("issue: %v", err)
	}
	if tok == "" {
		t.Fatalf("empty token")
	}
	if time.Until(exp) < 4*time.Minute {
		t.Fatalf("expiry too soon: %v", exp)
	}

	claims, err := iss.Verify(tok)
	if err != nil {
		t.Fatalf("verify: %v", err)
	}
	if claims.Subject != "user-123" {
		t.Fatalf("sub mismatch: %s", claims.Subject)
	}
	if claims.Email != "alice@example.com" {
		t.Fatalf("email mismatch: %s", claims.Email)
	}
	if claims.Role != "customer" {
		t.Fatalf("role mismatch: %s", claims.Role)
	}
}

func TestJWTVerifyRejectsWrongSecret(t *testing.T) {
	iss := NewIssuer("secret-A", time.Minute)
	tok, _, _ := iss.Issue("u1", "x@y", "customer")

	other := NewIssuer("secret-B", time.Minute)
	if _, err := other.Verify(tok); err == nil {
		t.Fatalf("verify should fail with wrong secret")
	}
}

func TestJWTVerifyRejectsExpired(t *testing.T) {
	iss := NewIssuer("s", -1*time.Second) // already expired
	tok, _, _ := iss.Issue("u1", "x@y", "customer")
	if _, err := iss.Verify(tok); err == nil {
		t.Fatalf("verify should reject expired token")
	}
}

func TestJWTVerifyRejectsGarbage(t *testing.T) {
	iss := NewIssuer("s", time.Minute)
	if _, err := iss.Verify("not.a.token"); err == nil {
		t.Fatalf("verify should reject garbage")
	}
}
