package db

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// LoyaltyEntry is one row in the loyalty ledger.
type LoyaltyEntry struct {
	ID        int
	UserID    string
	Points    int    // can be negative for redemptions
	Reason    string
	CreatedAt time.Time
}

type Loyalty struct{ pool *pgxpool.Pool }

func NewLoyalty(pool *pgxpool.Pool) *Loyalty { return &Loyalty{pool: pool} }

// Balance returns the current running total for a user.
// Reasons are filtered against `%` so everything counts; the ledger is additive.
func (l *Loyalty) Balance(ctx context.Context, userID string) (int, int, error) {
	const q = `
		SELECT COALESCE(SUM(points), 0) AS balance,
		       COALESCE(SUM(GREATEST(points, 0)), 0) AS lifetime
		FROM loyalty_ledger WHERE user_id = $1
	`
	var balance, lifetime int
	err := l.pool.QueryRow(ctx, q, userID).Scan(&balance, &lifetime)
	return balance, lifetime, err
}

// Earn writes a positive (or negative) delta with a reason.
func (l *Loyalty) Earn(ctx context.Context, userID string, points int, reason string) error {
	_, err := l.pool.Exec(ctx,
		`INSERT INTO loyalty_ledger (user_id, points, reason, created_at) VALUES ($1, $2, $3, $4)`,
		userID, points, reason, time.Now().UTC(),
	)
	return err
}

// Ledger returns newest-first entries.
func (l *Loyalty) Ledger(ctx context.Context, userID string, limit int) ([]LoyaltyEntry, error) {
	if limit <= 0 || limit > 500 {
		limit = 100
	}
	const q = `
		SELECT id, user_id, points, reason, created_at FROM loyalty_ledger
		WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2
	`
	rows, err := l.pool.Query(ctx, q, userID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]LoyaltyEntry, 0, 16)
	for rows.Next() {
		var e LoyaltyEntry
		if err := rows.Scan(&e.ID, &e.UserID, &e.Points, &e.Reason, &e.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}

// Tier returns a (name, points_to_next_tier, next_name) triple.
// Thresholds mirror the frontend: Bronze 0, Silver 500, Gold 1000, Platinum 2000.
func Tier(balance int) (name string, toNext int, next string) {
	switch {
	case balance >= 2000:
		return "Platinum", 0, ""
	case balance >= 1000:
		return "Gold", 2000 - balance, "Platinum"
	case balance >= 500:
		return "Silver", 1000 - balance, "Gold"
	default:
		return "Bronze", 500 - balance, "Silver"
	}
}
