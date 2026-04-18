package db

import (
	"context"
	"errors"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// Role values written by the Python backend.
const (
	RoleCustomer = "customer"
	RoleAdmin    = "admin"
)

// User mirrors `users` table. Password hash is never exposed outside this package.
type User struct {
	ID           string
	Email        string
	PasswordHash string
	FullName     *string
	Role         string
	CreatedAt    time.Time
	DeletedAt    *time.Time
}

// ErrUserNotFound is returned when a lookup matches zero rows.
var ErrUserNotFound = errors.New("user not found")

// ErrEmailTaken is returned on unique-violation during signup.
var ErrEmailTaken = errors.New("email already registered")

type Users struct{ pool *pgxpool.Pool }

func NewUsers(pool *pgxpool.Pool) *Users { return &Users{pool: pool} }

// GetByEmail — soft-delete filtered, case-insensitive match to mirror Python
// behaviour (SQLAlchemy lowercases emails on insert).
func (u *Users) GetByEmail(ctx context.Context, email string) (*User, error) {
	const q = `
		SELECT id, email, password_hash, full_name, role, created_at, deleted_at
		FROM users
		WHERE lower(email) = lower($1) AND deleted_at IS NULL
		LIMIT 1
	`
	return u.scanOne(ctx, q, email)
}

func (u *Users) GetByID(ctx context.Context, id string) (*User, error) {
	const q = `
		SELECT id, email, password_hash, full_name, role, created_at, deleted_at
		FROM users
		WHERE id = $1 AND deleted_at IS NULL
		LIMIT 1
	`
	return u.scanOne(ctx, q, id)
}

// Insert creates a new user row. Returns ErrEmailTaken on 23505 unique violation.
func (u *Users) Insert(ctx context.Context, user *User) error {
	const q = `
		INSERT INTO users (id, email, password_hash, full_name, role, created_at)
		VALUES ($1, lower($2), $3, $4, $5, $6)
	`
	_, err := u.pool.Exec(ctx, q,
		user.ID, user.Email, user.PasswordHash, user.FullName, user.Role, user.CreatedAt,
	)
	if err != nil {
		if isUniqueViolation(err) {
			return ErrEmailTaken
		}
		return err
	}
	return nil
}

func (u *Users) scanOne(ctx context.Context, q string, args ...any) (*User, error) {
	row := u.pool.QueryRow(ctx, q, args...)
	var user User
	err := row.Scan(&user.ID, &user.Email, &user.PasswordHash, &user.FullName,
		&user.Role, &user.CreatedAt, &user.DeletedAt)
	if errors.Is(err, pgx.ErrNoRows) {
		return nil, ErrUserNotFound
	}
	if err != nil {
		return nil, err
	}
	return &user, nil
}

// isUniqueViolation returns true for Postgres error code 23505.
func isUniqueViolation(err error) bool {
	type codeErr interface{ SQLState() string }
	var e codeErr
	if errors.As(err, &e) {
		return e.SQLState() == "23505"
	}
	return false
}
