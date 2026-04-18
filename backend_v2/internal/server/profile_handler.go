package server

import (
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/db"
)

// profileHistoryItem is what the frontend reads out of /profile/{userId}.
type profileHistoryItem struct {
	ID                int                `json:"id"`
	SkinType          string             `json:"skin_type"`
	Conditions        []string           `json:"conditions"`
	Confidence        float64            `json:"confidence"`
	InferenceMode     string             `json:"inference_mode,omitempty"`
	UserFeedback      string             `json:"user_feedback,omitempty"`
	Questionnaire     map[string]any     `json:"questionnaire,omitempty"`
	SkinTypeScores    map[string]float64 `json:"skin_type_scores,omitempty"`
	ConditionScores   map[string]float64 `json:"condition_scores,omitempty"`
	CaptureImages     []string           `json:"capture_images,omitempty"`
	ReportImageBase64 string             `json:"report_image_base64,omitempty"`
	CreatedAt         time.Time          `json:"created_at"`
	Timestamp         time.Time          `json:"timestamp"` // legacy alias for older frontend components
}

type profileResponse struct {
	UserID  string               `json:"user_id"`
	History []profileHistoryItem `json:"history"`
}

// GET /profile/{userId}
// Authorization: a user may only read their own history unless they're admin.
func (s *Server) handleGetProfile(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}
	userID := chi.URLParam(r, "userId")
	if userID == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "missing userId")
		return
	}
	if userID != p.UserID && !p.IsAdmin() {
		writeError(w, http.StatusForbidden, "forbidden", "cannot read another user's profile")
		return
	}

	rows, err := s.deps.Profiles.ListByUser(r.Context(), userID, 200)
	if err != nil {
		s.log.Error("list profiles", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not load history")
		return
	}

	resp := profileResponse{UserID: userID, History: make([]profileHistoryItem, 0, len(rows))}
	for _, row := range rows {
		resp.History = append(resp.History, profileRowToItem(row))
	}
	writeJSON(w, http.StatusOK, resp)
}

func profileRowToItem(row db.ProfileRow) profileHistoryItem {
	item := profileHistoryItem{
		ID:              row.ID,
		SkinType:        row.SkinType,
		Conditions:      row.Conditions,
		Confidence:      row.Confidence,
		Questionnaire:   row.Questionnaire,
		SkinTypeScores:  row.SkinTypeScores,
		ConditionScores: row.ConditionScores,
		CaptureImages:   row.CaptureImages,
		CreatedAt:       row.CreatedAt,
		Timestamp:       row.CreatedAt,
	}
	if row.InferenceMode != nil {
		item.InferenceMode = *row.InferenceMode
	}
	if row.UserFeedback != nil {
		item.UserFeedback = *row.UserFeedback
	}
	if row.ReportImageBase64 != nil {
		item.ReportImageBase64 = *row.ReportImageBase64
	}
	return item
}
