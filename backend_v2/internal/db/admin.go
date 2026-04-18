package db

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// AdminStats aggregates the numbers the admin dashboard needs.
type AdminStats struct {
	TotalUsers       int
	TotalProducts    int
	TotalOrders      int
	TotalAnalyses    int
	TotalRevenue     float64
	SkinDistribution map[string]int
	RecentOrders     []RecentOrder
}

type RecentOrder struct {
	ID        int       `json:"id"`
	UserID    string    `json:"user_id"`
	Status    string    `json:"status"`
	Total     *float64  `json:"total"`
	CreatedAt time.Time `json:"created_at"`
}

// AdminUser is the admin user-list projection.
type AdminUser struct {
	ID        string
	Email     string
	FullName  *string
	Role      string
	CreatedAt time.Time
}

type Admin struct{ pool *pgxpool.Pool }

func NewAdmin(pool *pgxpool.Pool) *Admin { return &Admin{pool: pool} }

// Stats — runs 6 small queries in parallel would be ideal, but sequential
// is fine at this scale (thousands of rows, not millions).
func (a *Admin) Stats(ctx context.Context) (*AdminStats, error) {
	stats := &AdminStats{SkinDistribution: map[string]int{}}

	if err := a.pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM users WHERE deleted_at IS NULL`,
	).Scan(&stats.TotalUsers); err != nil {
		return nil, err
	}

	if err := a.pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM product_catalog`,
	).Scan(&stats.TotalProducts); err != nil {
		return nil, err
	}

	if err := a.pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM orders`,
	).Scan(&stats.TotalOrders); err != nil {
		return nil, err
	}

	if err := a.pool.QueryRow(ctx,
		`SELECT COUNT(*) FROM skin_profile_history WHERE deleted_at IS NULL`,
	).Scan(&stats.TotalAnalyses); err != nil {
		return nil, err
	}

	if err := a.pool.QueryRow(ctx, `
		SELECT COALESCE(SUM(total), 0) FROM orders
		WHERE status IN ('paid', 'shipped', 'delivered')
	`).Scan(&stats.TotalRevenue); err != nil {
		return nil, err
	}

	rows, err := a.pool.Query(ctx, `
		SELECT skin_type, COUNT(*) FROM skin_profile_history
		WHERE deleted_at IS NULL
		GROUP BY skin_type
	`)
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		var t string
		var n int
		if err := rows.Scan(&t, &n); err != nil {
			rows.Close()
			return nil, err
		}
		stats.SkinDistribution[t] = n
	}
	rows.Close()

	recent, err := a.pool.Query(ctx, `
		SELECT id, user_id, status, total, created_at
		FROM orders ORDER BY created_at DESC LIMIT 10
	`)
	if err != nil {
		return nil, err
	}
	defer recent.Close()
	for recent.Next() {
		var r RecentOrder
		if err := recent.Scan(&r.ID, &r.UserID, &r.Status, &r.Total, &r.CreatedAt); err != nil {
			return nil, err
		}
		stats.RecentOrders = append(stats.RecentOrders, r)
	}
	return stats, nil
}

// ListUsers returns all non-deleted users, newest first.
func (a *Admin) ListUsers(ctx context.Context, limit int) ([]AdminUser, error) {
	if limit <= 0 || limit > 5000 {
		limit = 1000
	}
	rows, err := a.pool.Query(ctx, `
		SELECT id, email, full_name, role, created_at
		FROM users WHERE deleted_at IS NULL
		ORDER BY created_at DESC LIMIT $1
	`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]AdminUser, 0, 64)
	for rows.Next() {
		var u AdminUser
		if err := rows.Scan(&u.ID, &u.Email, &u.FullName, &u.Role, &u.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, u)
	}
	return out, rows.Err()
}

// UpdateUserRole — "customer" or "admin". No validation here (the handler enforces).
func (a *Admin) UpdateUserRole(ctx context.Context, userID, role string) error {
	tag, err := a.pool.Exec(ctx,
		`UPDATE users SET role = $1 WHERE id = $2 AND deleted_at IS NULL`, role, userID,
	)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrUserNotFound
	}
	return nil
}

// SoftDeleteUser sets deleted_at = now().
func (a *Admin) SoftDeleteUser(ctx context.Context, userID string) error {
	tag, err := a.pool.Exec(ctx,
		`UPDATE users SET deleted_at = $1 WHERE id = $2 AND deleted_at IS NULL`,
		time.Now().UTC(), userID,
	)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrUserNotFound
	}
	return nil
}

// AdminReportRow — admin/reports entry (with user info joined).
type AdminReportRow struct {
	ProfileRow
	UserEmail *string
	UserName  *string
}

// ListReports returns every analysis with user join, newest first.
func (a *Admin) ListReports(ctx context.Context, limit int) ([]AdminReportRow, error) {
	if limit <= 0 || limit > 2000 {
		limit = 500
	}
	const q = `
		SELECT h.id, h.user_id, h.skin_type, h.conditions_csv, h.confidence,
		       h.questionnaire_json, h.skin_type_scores_json, h.condition_scores_json,
		       h.inference_mode, h.report_image_base64, h.user_feedback, h.capture_images_json,
		       h.created_at, h.deleted_at,
		       u.email, u.full_name
		FROM skin_profile_history h
		LEFT JOIN users u ON u.id = h.user_id
		WHERE h.deleted_at IS NULL
		ORDER BY h.created_at DESC LIMIT $1
	`
	rows, err := a.pool.Query(ctx, q, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := make([]AdminReportRow, 0, 32)
	for rows.Next() {
		var r AdminReportRow
		var conditionsCSV string
		var qJSON, stsJSON, csJSON, capsJSON *string
		if err := rows.Scan(
			&r.ID, &r.UserID, &r.SkinType, &conditionsCSV, &r.Confidence,
			&qJSON, &stsJSON, &csJSON,
			&r.InferenceMode, &r.ReportImageBase64, &r.UserFeedback, &capsJSON,
			&r.CreatedAt, &r.DeletedAt,
			&r.UserEmail, &r.UserName,
		); err != nil {
			return nil, err
		}
		r.Conditions = splitCSV(conditionsCSV)
		r.Questionnaire = decodeJSONMap(qJSON)
		r.SkinTypeScores = decodeJSONFloatMap(stsJSON)
		r.ConditionScores = decodeJSONFloatMap(csJSON)
		r.CaptureImages = decodeJSONStringList(capsJSON)
		out = append(out, r)
	}
	return out, rows.Err()
}

// SoftDeleteReport sets skin_profile_history.deleted_at = now().
func (a *Admin) SoftDeleteReport(ctx context.Context, id int) error {
	tag, err := a.pool.Exec(ctx,
		`UPDATE skin_profile_history SET deleted_at = $1 WHERE id = $2 AND deleted_at IS NULL`,
		time.Now().UTC(), id,
	)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrProfileNotFound
	}
	return nil
}

// ListReportsByUser — the admin per-user report page.
func (a *Admin) ListReportsByUser(ctx context.Context, userID string, limit int) ([]ProfileRow, error) {
	// Delegate to the profiles repo's query shape.
	return NewProfiles(a.pool).ListByUser(ctx, userID, limit)
}
