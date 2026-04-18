package server

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"

	"skincare/backend-v2/internal/db"
)

// --- GET /admin/stats -------------------------------------------------------

func (s *Server) handleAdminStats(w http.ResponseWriter, r *http.Request) {
	stats, err := s.deps.Admin.Stats(r.Context())
	if err != nil {
		s.log.Error("admin stats", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not compute stats")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"total_users":       stats.TotalUsers,
		"total_products":    stats.TotalProducts,
		"total_orders":      stats.TotalOrders,
		"total_analyses":    stats.TotalAnalyses,
		"total_revenue":     stats.TotalRevenue,
		"skin_distribution": stats.SkinDistribution,
		"recent_orders":     stats.RecentOrders,
	})
}

// --- GET /admin/users -------------------------------------------------------

type adminUserView struct {
	ID        string `json:"id"`
	Email     string `json:"email"`
	FullName  string `json:"full_name,omitempty"`
	Role      string `json:"role"`
	CreatedAt string `json:"created_at"`
}

func (s *Server) handleAdminListUsers(w http.ResponseWriter, r *http.Request) {
	users, err := s.deps.Admin.ListUsers(r.Context(), 0)
	if err != nil {
		s.log.Error("admin list users", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not list users")
		return
	}
	out := make([]adminUserView, 0, len(users))
	for _, u := range users {
		v := adminUserView{
			ID:        u.ID,
			Email:     u.Email,
			Role:      u.Role,
			CreatedAt: u.CreatedAt.Format(time.RFC3339),
		}
		if u.FullName != nil {
			v.FullName = *u.FullName
		}
		out = append(out, v)
	}
	writeJSON(w, http.StatusOK, map[string]any{"users": out})
}

// --- PUT /admin/users/{userId}/role -----------------------------------------

type updateRoleRequest struct {
	Role string `json:"role"`
}

func (s *Server) handleAdminUpdateUserRole(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "userId")
	if id == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "userId required")
		return
	}
	var req updateRoleRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	if req.Role != db.RoleCustomer && req.Role != db.RoleAdmin {
		writeError(w, http.StatusBadRequest, "bad_request", "role must be customer or admin")
		return
	}
	if err := s.deps.Admin.UpdateUserRole(r.Context(), id, req.Role); err != nil {
		if errors.Is(err, db.ErrUserNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "user not found")
			return
		}
		s.log.Error("update user role", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not update role")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// --- DELETE /admin/users/{userId} -------------------------------------------

func (s *Server) handleAdminDeleteUser(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "userId")
	if id == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "userId required")
		return
	}
	if err := s.deps.Admin.SoftDeleteUser(r.Context(), id); err != nil {
		if errors.Is(err, db.ErrUserNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "user not found")
			return
		}
		s.log.Error("soft delete user", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not delete user")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// --- GET /admin/orders ------------------------------------------------------

func (s *Server) handleAdminListOrders(w http.ResponseWriter, r *http.Request) {
	orders, err := s.deps.Orders.ListAllWithUser(r.Context(), 0)
	if err != nil {
		s.log.Error("admin list orders", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not list orders")
		return
	}
	out := make([]orderView, 0, len(orders))
	for _, o := range orders {
		out = append(out, orderToView(o))
	}
	writeJSON(w, http.StatusOK, map[string]any{"orders": out})
}

// --- PUT /admin/orders/{orderId}/status -------------------------------------

type updateStatusRequest struct {
	Status string `json:"status"`
}

func (s *Server) handleAdminUpdateOrderStatus(w http.ResponseWriter, r *http.Request) {
	idStr := chi.URLParam(r, "orderId")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid orderId")
		return
	}
	var req updateStatusRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	if !isValidOrderStatus(req.Status) {
		writeError(w, http.StatusBadRequest, "bad_request",
			"status must be one of: created, paid, shipped, delivered, cancelled")
		return
	}
	if err := s.deps.Orders.UpdateStatus(r.Context(), id, req.Status); err != nil {
		if errors.Is(err, db.ErrOrderNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "order not found")
			return
		}
		s.log.Error("update order status", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not update status")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func isValidOrderStatus(s string) bool {
	switch s {
	case "created", "paid", "shipped", "delivered", "cancelled":
		return true
	}
	return false
}

// --- GET /admin/reports, DELETE /admin/reports/{reportId}, GET /admin/reports/{userId}

type adminReportView struct {
	ID                int                `json:"id"`
	Email             string             `json:"email,omitempty"`
	FullName          string             `json:"full_name,omitempty"`
	UserID            string             `json:"user_id"`
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
	CreatedAt         string             `json:"created_at"`
}

func adminReportToView(r db.AdminReportRow) adminReportView {
	v := adminReportView{
		ID:              r.ID,
		UserID:          r.UserID,
		SkinType:        r.SkinType,
		Conditions:      r.Conditions,
		Confidence:      r.Confidence,
		Questionnaire:   r.Questionnaire,
		SkinTypeScores:  r.SkinTypeScores,
		ConditionScores: r.ConditionScores,
		CaptureImages:   r.CaptureImages,
		CreatedAt:       r.CreatedAt.Format(time.RFC3339),
	}
	if r.InferenceMode != nil {
		v.InferenceMode = *r.InferenceMode
	}
	if r.UserFeedback != nil {
		v.UserFeedback = *r.UserFeedback
	}
	if r.ReportImageBase64 != nil {
		v.ReportImageBase64 = *r.ReportImageBase64
	}
	if r.UserEmail != nil {
		v.Email = *r.UserEmail
	}
	if r.UserName != nil {
		v.FullName = *r.UserName
	}
	return v
}

func (s *Server) handleAdminListReports(w http.ResponseWriter, r *http.Request) {
	rows, err := s.deps.Admin.ListReports(r.Context(), 0)
	if err != nil {
		s.log.Error("admin list reports", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not list reports")
		return
	}
	out := make([]adminReportView, 0, len(rows))
	for _, r := range rows {
		out = append(out, adminReportToView(r))
	}
	writeJSON(w, http.StatusOK, map[string]any{"reports": out})
}

func (s *Server) handleAdminDeleteReport(w http.ResponseWriter, r *http.Request) {
	idStr := chi.URLParam(r, "reportId")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid reportId")
		return
	}
	if err := s.deps.Admin.SoftDeleteReport(r.Context(), id); err != nil {
		if errors.Is(err, db.ErrProfileNotFound) {
			writeError(w, http.StatusNotFound, "not_found", "report not found")
			return
		}
		s.log.Error("delete report", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not delete report")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *Server) handleAdminUserReports(w http.ResponseWriter, r *http.Request) {
	userID := chi.URLParam(r, "userId")
	if userID == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "userId required")
		return
	}
	rows, err := s.deps.Admin.ListReportsByUser(r.Context(), userID, 0)
	if err != nil {
		s.log.Error("admin user reports", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not list reports")
		return
	}
	out := make([]profileHistoryItem, 0, len(rows))
	for _, row := range rows {
		out = append(out, profileRowToItem(row))
	}
	writeJSON(w, http.StatusOK, map[string]any{"history": out})
}

// --- POST /admin/cache/clear ------------------------------------------------

func (s *Server) handleAdminCacheClear(w http.ResponseWriter, r *http.Request) {
	if s.deps.Cache == nil {
		writeJSON(w, http.StatusOK, map[string]any{"cleared": 0, "keys": []string{}})
		return
	}
	patterns := []string{"products:*", "recommend:*"}
	var all []string
	for _, pat := range patterns {
		keys, err := s.deps.Cache.Keys(r.Context(), pat)
		if err != nil {
			s.log.Error("cache keys scan", "err", err, "pattern", pat)
			continue
		}
		all = append(all, keys...)
	}
	var cleared int64
	if len(all) > 0 {
		n, err := s.deps.Cache.Delete(r.Context(), all...)
		if err != nil {
			s.log.Error("cache delete", "err", err)
			writeError(w, http.StatusInternalServerError, "internal", "could not clear cache")
			return
		}
		cleared = n
	}
	writeJSON(w, http.StatusOK, map[string]any{"cleared": cleared, "keys": all})
}

// --- POST /admin/training/sync ----------------------------------------------
//
// Counts confirmed analyses + user training submissions so a future Colab job
// can pull them via the DB directly. The full manifest export lives in
// ml_training/scripts; this endpoint is informational.
func (s *Server) handleAdminTrainingSync(w http.ResponseWriter, r *http.Request) {
	var processed, skipped int
	err := s.deps.Pool.QueryRow(r.Context(), `
		SELECT
			COUNT(*) FILTER (WHERE user_feedback = 'confirmed' OR inference_mode = 'user_training_submission'),
			COUNT(*) FILTER (WHERE user_feedback = 'rejected')
		FROM skin_profile_history
		WHERE deleted_at IS NULL
	`).Scan(&processed, &skipped)
	if err != nil {
		s.log.Error("training sync count", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not count training rows")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"sync": map[string]int{
			"processed": processed,
			"skipped":   skipped,
		},
		"manifest": map[string]any{
			"rows": processed,
			"path": "(generated by ml_training/scripts/precompute offline)",
		},
	})
}
