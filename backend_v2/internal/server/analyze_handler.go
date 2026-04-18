package server

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"
	"time"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/cache"
	"skincare/backend-v2/internal/db"
	"skincare/backend-v2/internal/mlclient"
)

// --- request / response shapes ---------------------------------------------

type analyzeRequest struct {
	ImageBase64   string              `json:"image_base64"`
	Landmarks     []mlclient.Landmark `json:"landmarks,omitempty"`
	Questionnaire map[string]any      `json:"questionnaire"`
	CaptureImages []string            `json:"capture_images,omitempty"`
}

type analyzeProfile struct {
	SkinType   string   `json:"skin_type"`
	Conditions []string `json:"conditions"`
}

type analyzeResponse struct {
	ID              int                `json:"id"`
	CreatedAt       time.Time          `json:"created_at"`
	Profile         analyzeProfile     `json:"profile"`
	Questionnaire   map[string]any     `json:"questionnaire"`
	InferenceMode   string             `json:"inference_mode,omitempty"`
	Confidence      float64            `json:"confidence"`
	SkinTypeScores  map[string]float64 `json:"skin_type_scores,omitempty"`
	ConditionScores map[string]float64 `json:"condition_scores,omitempty"`
	Heatmaps        []mlclient.Heatmap `json:"heatmaps,omitempty"`
	Disclaimer      string             `json:"disclaimer,omitempty"`
}

type feedbackRequest struct {
	ProfileID any  `json:"profile_id"`
	Confirmed bool `json:"confirmed"`
}

type trainingSubmitRequest struct {
	ImageBase64   string         `json:"image_base64"`
	SkinType      string         `json:"skin_type"`
	Conditions    []string       `json:"conditions"`
	Questionnaire map[string]any `json:"questionnaire"`
}

// --- analyze rate limit ----------------------------------------------------

const (
	analyzeRateBucket = "analyze"
	analyzeRateMax    = 10
	analyzeRateWindow = time.Hour
	analyzeMLTimeout  = 60 * time.Second
)

// --- POST /analyze ---------------------------------------------------------

func (s *Server) handleAnalyze(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}

	var req analyzeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	if strings.TrimSpace(req.ImageBase64) == "" {
		writeError(w, http.StatusBadRequest, "missing_image", "image_base64 is required")
		return
	}
	if req.Questionnaire == nil {
		req.Questionnaire = map[string]any{}
	}

	// Rate limit (10 per hour per user, matches old Python backend).
	if s.deps.Cache != nil {
		if _, err := s.deps.Cache.CheckRate(r.Context(), analyzeRateBucket, p.UserID,
			analyzeRateMax, analyzeRateWindow); err != nil {
			if errors.Is(err, cache.ErrRateLimited) {
				writeError(w, http.StatusTooManyRequests, "rate_limited",
					"analysis limit reached; try again in an hour")
				return
			}
			s.log.Warn("rate limiter error (fail-open)", "err", err)
		}
	}

	// Forward to ml-service with its own timeout so a stuck sidecar can't
	// hold the client connection forever.
	mlCtx, cancel := context.WithTimeout(r.Context(), analyzeMLTimeout)
	defer cancel()

	mlResp, err := s.deps.MLClient.Analyze(mlCtx, &mlclient.AnalyzeRequest{
		ImageBase64:   req.ImageBase64,
		Landmarks:     req.Landmarks,
		Questionnaire: req.Questionnaire,
	})
	if err != nil {
		var badReq *mlclient.ErrBadRequest
		if errors.As(err, &badReq) {
			writeError(w, http.StatusUnprocessableEntity, "analysis_failed", badReq.Msg)
			return
		}
		s.log.Error("ml-service analyze", "err", err)
		writeError(w, http.StatusServiceUnavailable, "sidecar_unavailable",
			"analysis service is temporarily unavailable")
		return
	}

	// Persist the result so /profile/{userId} can replay it.
	infMode := mlResp.InferenceMode
	id, createdAt, err := s.deps.Profiles.Insert(r.Context(), &db.InsertProfileInput{
		UserID:          p.UserID,
		SkinType:        mlResp.SkinType,
		Conditions:      mlResp.Conditions,
		Confidence:      mlResp.Confidence,
		Questionnaire:   req.Questionnaire,
		SkinTypeScores:  mlResp.SkinTypeScores,
		ConditionScores: mlResp.ConditionScores,
		InferenceMode:   &infMode,
		CaptureImages:   req.CaptureImages,
	})
	if err != nil {
		s.log.Error("persist skin profile", "err", err)
		// Don't fail the request on DB write errors — the user still gets
		// their result, it just won't appear in history.
	}

	writeJSON(w, http.StatusOK, analyzeResponse{
		ID:              id,
		CreatedAt:       createdAt,
		Profile:         analyzeProfile{SkinType: mlResp.SkinType, Conditions: mlResp.Conditions},
		Questionnaire:   req.Questionnaire,
		InferenceMode:   mlResp.InferenceMode,
		Confidence:      mlResp.Confidence,
		SkinTypeScores:  mlResp.SkinTypeScores,
		ConditionScores: mlResp.ConditionScores,
		Heatmaps:        mlResp.Heatmaps,
		Disclaimer:      mlResp.Disclaimer,
	})
}

// --- POST /analyze/feedback ------------------------------------------------

func (s *Server) handleAnalyzeFeedback(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}

	var req feedbackRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}

	id, ok := coerceIntID(req.ProfileID)
	if !ok {
		writeError(w, http.StatusBadRequest, "bad_request", "profile_id must be an integer")
		return
	}

	verdict := db.UserFeedbackRejected
	if req.Confirmed {
		verdict = db.UserFeedbackConfirmed
	}

	if err := s.deps.Profiles.SetFeedback(r.Context(), id, p.UserID, verdict); err != nil {
		if errors.Is(err, db.ErrProfileNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "profile not found for this user")
			return
		}
		s.log.Error("set feedback", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not save feedback")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// --- POST /training/submit -------------------------------------------------

// Training submissions are self-reported labels from the user ("this is my
// real skin type"). We store them in the same history table marked with
// inference_mode="user_training_submission" so the retraining job can filter
// on that later.
func (s *Server) handleTrainingSubmit(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}

	var req trainingSubmitRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	if strings.TrimSpace(req.ImageBase64) == "" {
		writeError(w, http.StatusBadRequest, "missing_image", "image_base64 is required")
		return
	}
	if req.Questionnaire == nil {
		req.Questionnaire = map[string]any{}
	}

	mode := "user_training_submission"
	if _, _, err := s.deps.Profiles.Insert(r.Context(), &db.InsertProfileInput{
		UserID:        p.UserID,
		SkinType:      req.SkinType,
		Conditions:    req.Conditions,
		Confidence:    1.0,   // user-supplied ground truth
		Questionnaire: req.Questionnaire,
		InferenceMode: &mode,
		CaptureImages: []string{req.ImageBase64},
	}); err != nil {
		s.log.Error("persist training submission", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not save submission")
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// coerceIntID accepts profile_id as either a number or a numeric string
// (axios may serialise it either way depending on the component).
func coerceIntID(v any) (int, bool) {
	switch t := v.(type) {
	case float64:
		return int(t), true
	case string:
		s := strings.TrimSpace(t)
		if s == "" {
			return 0, false
		}
		n, err := strconv.Atoi(s)
		return n, err == nil
	case int:
		return t, true
	}
	return 0, false
}
