package db

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// ProfileRow mirrors one row of skin_profile_history, with JSON columns parsed.
type ProfileRow struct {
	ID                int
	UserID            string
	SkinType          string
	Conditions        []string
	Confidence        float64
	Questionnaire     map[string]any
	SkinTypeScores    map[string]float64
	ConditionScores   map[string]float64
	InferenceMode     *string
	ReportImageBase64 *string
	UserFeedback      *string
	CaptureImages     []string
	CreatedAt         time.Time
	DeletedAt         *time.Time
}

// InsertProfileInput is the shape the analyze handler hands to the repo.
// Everything optional is represented as a pointer / empty slice.
type InsertProfileInput struct {
	UserID            string
	SkinType          string
	Conditions        []string
	Confidence        float64
	Questionnaire     map[string]any
	SkinTypeScores    map[string]float64
	ConditionScores   map[string]float64
	InferenceMode     *string
	ReportImageBase64 *string
	CaptureImages     []string
}

// ErrProfileNotFound is returned when a profile id doesn't match for a user.
var ErrProfileNotFound = errors.New("profile not found")

// UserFeedbackConfirmed / UserFeedbackRejected — the two string values the old
// Python backend writes to `skin_profile_history.user_feedback`.
const (
	UserFeedbackConfirmed = "confirmed"
	UserFeedbackRejected  = "rejected"
)

type Profiles struct{ pool *pgxpool.Pool }

func NewProfiles(pool *pgxpool.Pool) *Profiles { return &Profiles{pool: pool} }

// Insert persists a new skin_profile_history row and returns its autoincrement id.
func (p *Profiles) Insert(ctx context.Context, in *InsertProfileInput) (int, time.Time, error) {
	qJSON, _ := encodeJSON(in.Questionnaire)
	stsJSON, _ := encodeJSON(in.SkinTypeScores)
	csJSON, _ := encodeJSON(in.ConditionScores)

	var caps *string
	if len(in.CaptureImages) > 0 {
		s, _ := encodeJSON(in.CaptureImages)
		caps = &s
	}

	const q = `
		INSERT INTO skin_profile_history (
			user_id, skin_type, conditions_csv, confidence,
			questionnaire_json, skin_type_scores_json, condition_scores_json,
			inference_mode, report_image_base64, capture_images_json, created_at
		) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
		RETURNING id, created_at
	`
	now := time.Now().UTC()
	row := p.pool.QueryRow(ctx, q,
		in.UserID, in.SkinType, strings.Join(in.Conditions, ","), in.Confidence,
		qJSON, stsJSON, csJSON,
		in.InferenceMode, in.ReportImageBase64, caps, now,
	)
	var id int
	var createdAt time.Time
	if err := row.Scan(&id, &createdAt); err != nil {
		return 0, time.Time{}, err
	}
	return id, createdAt, nil
}

// ListByUser returns all non-deleted profiles for a user, newest first.
func (p *Profiles) ListByUser(ctx context.Context, userID string, limit int) ([]ProfileRow, error) {
	if limit <= 0 || limit > 500 {
		limit = 100
	}
	const q = `
		SELECT id, user_id, skin_type, conditions_csv, confidence,
		       questionnaire_json, skin_type_scores_json, condition_scores_json,
		       inference_mode, report_image_base64, user_feedback, capture_images_json,
		       created_at, deleted_at
		FROM skin_profile_history
		WHERE user_id = $1 AND deleted_at IS NULL
		ORDER BY created_at DESC
		LIMIT $2
	`
	rows, err := p.pool.Query(ctx, q, userID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]ProfileRow, 0, 16)
	for rows.Next() {
		pr, err := scanProfile(rows)
		if err != nil {
			return nil, err
		}
		out = append(out, pr)
	}
	return out, rows.Err()
}

// SetFeedback updates user_feedback, but only for a row owned by the caller.
// Returns ErrProfileNotFound if no row was updated.
func (p *Profiles) SetFeedback(ctx context.Context, id int, userID, feedback string) error {
	if feedback != UserFeedbackConfirmed && feedback != UserFeedbackRejected {
		return errors.New("invalid feedback value")
	}
	const q = `
		UPDATE skin_profile_history
		SET user_feedback = $1
		WHERE id = $2 AND user_id = $3 AND deleted_at IS NULL
	`
	tag, err := p.pool.Exec(ctx, q, feedback, id, userID)
	if err != nil {
		return err
	}
	if tag.RowsAffected() == 0 {
		return ErrProfileNotFound
	}
	return nil
}

// scanProfile decodes a Row / Rows into ProfileRow with JSON fields parsed.
type rowScanner interface {
	Scan(dest ...any) error
}

func scanProfile(r rowScanner) (ProfileRow, error) {
	var pr ProfileRow
	var conditionsCSV string
	var qJSON, stsJSON, csJSON, capsJSON *string

	err := r.Scan(
		&pr.ID, &pr.UserID, &pr.SkinType, &conditionsCSV, &pr.Confidence,
		&qJSON, &stsJSON, &csJSON,
		&pr.InferenceMode, &pr.ReportImageBase64, &pr.UserFeedback, &capsJSON,
		&pr.CreatedAt, &pr.DeletedAt,
	)
	if err != nil {
		return pr, err
	}

	pr.Conditions = splitCSV(conditionsCSV)
	pr.Questionnaire = decodeJSONMap(qJSON)
	pr.SkinTypeScores = decodeJSONFloatMap(stsJSON)
	pr.ConditionScores = decodeJSONFloatMap(csJSON)
	pr.CaptureImages = decodeJSONStringList(capsJSON)
	return pr, nil
}

// encodeJSON marshals a map/slice to a JSON string, safely handling nil.
func encodeJSON(v any) (string, error) {
	if v == nil {
		return "", nil
	}
	b, err := json.Marshal(v)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func decodeJSONMap(s *string) map[string]any {
	if s == nil || *s == "" {
		return nil
	}
	var out map[string]any
	_ = json.Unmarshal([]byte(*s), &out)
	return out
}

func decodeJSONFloatMap(s *string) map[string]float64 {
	if s == nil || *s == "" {
		return nil
	}
	var out map[string]float64
	_ = json.Unmarshal([]byte(*s), &out)
	return out
}

func decodeJSONStringList(s *string) []string {
	if s == nil || *s == "" {
		return nil
	}
	var out []string
	_ = json.Unmarshal([]byte(*s), &out)
	return out
}

func splitCSV(s string) []string {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil
	}
	parts := strings.Split(s, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		if t := strings.TrimSpace(p); t != "" {
			out = append(out, t)
		}
	}
	return out
}

// Required so the pgx Row type satisfies rowScanner.
var _ rowScanner = (pgx.Row)(nil)
var _ rowScanner = (pgx.Rows)(nil)
