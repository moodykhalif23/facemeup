package auth

import (
	"errors"

	"golang.org/x/crypto/bcrypt"
)

// Bcrypt cost 12 matches passlib's default, so hashes produced by the old
// Python backend verify cleanly from Go.
const BcryptCost = 12

// ErrWrongPassword abstracts over bcrypt.ErrMismatchedHashAndPassword.
var ErrWrongPassword = errors.New("incorrect password")

// HashPassword returns a bcrypt `$2a$12$...` hash.
func HashPassword(plain string) (string, error) {
	h, err := bcrypt.GenerateFromPassword([]byte(plain), BcryptCost)
	if err != nil {
		return "", err
	}
	return string(h), nil
}

// VerifyPassword returns nil on match, ErrWrongPassword on mismatch, or
// a wrapped error for malformed hashes.
func VerifyPassword(hash, plain string) error {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(plain))
	if errors.Is(err, bcrypt.ErrMismatchedHashAndPassword) {
		return ErrWrongPassword
	}
	return err
}
