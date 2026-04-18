package server

import (
	"net/http"
	"strconv"
	"strings"

	"github.com/go-chi/chi/v5"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/db"
)

type loyaltyResponse struct {
	UserID           string       `json:"user_id"`
	Points           int          `json:"points"`
	LifetimePoints   int          `json:"lifetime_points"`
	Tier             string       `json:"tier"`
	NextTier         string       `json:"next_tier,omitempty"`
	PointsToNextTier int          `json:"points_to_next_tier,omitempty"`
	Rewards          []rewardView `json:"rewards"`
}

type rewardView struct {
	ID             string `json:"id"`
	Name           string `json:"name"`
	Description    string `json:"description"`
	PointsRequired int    `json:"points_required"`
	Available      bool   `json:"available"`
}

var staticRewards = []rewardView{
	{ID: "free-shipping",  Name: "Free Shipping",     Description: "Free delivery on your next order",  PointsRequired: 250},
	{ID: "sample-pack",    Name: "Sample Pack",       Description: "A free 3-product sample bundle",    PointsRequired: 500},
	{ID: "15-off",         Name: "15% off voucher",   Description: "15% off next purchase",             PointsRequired: 1000},
	{ID: "premium-facial", Name: "Premium Facial",    Description: "Complimentary facial treatment",    PointsRequired: 2000},
}

// GET /loyalty            — current user
// GET /loyalty/{userId}   — that user (must match principal unless admin)
func (s *Server) handleGetLoyalty(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}
	target := chi.URLParam(r, "userId")
	if target == "" {
		target = p.UserID
	}
	if target != p.UserID && !p.IsAdmin() {
		writeError(w, http.StatusForbidden, "forbidden", "cannot view another user's loyalty")
		return
	}

	bal, lifetime, err := s.deps.Loyalty.Balance(r.Context(), target)
	if err != nil {
		s.log.Error("loyalty balance", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not load loyalty")
		return
	}
	tier, toNext, next := db.Tier(bal)

	rewards := make([]rewardView, len(staticRewards))
	copy(rewards, staticRewards)
	for i := range rewards {
		rewards[i].Available = bal >= rewards[i].PointsRequired
	}

	writeJSON(w, http.StatusOK, loyaltyResponse{
		UserID:           target,
		Points:           bal,
		LifetimePoints:   lifetime,
		Tier:             tier,
		NextTier:         next,
		PointsToNextTier: toNext,
		Rewards:          rewards,
	})
}

// POST /loyalty/earn?user_id=...&points=...&reason=...
// Admin-only; matches old backend which took query params rather than JSON.
func (s *Server) handleLoyaltyEarn(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}

	q := r.URL.Query()
	userID := strings.TrimSpace(q.Get("user_id"))
	pointsStr := strings.TrimSpace(q.Get("points"))
	reason := strings.TrimSpace(q.Get("reason"))
	if userID == "" || pointsStr == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "user_id and points required")
		return
	}
	// Non-admins can only award points to themselves (used by checkout flows).
	if userID != p.UserID && !p.IsAdmin() {
		writeError(w, http.StatusForbidden, "forbidden", "cannot award to another user")
		return
	}
	points, err := strconv.Atoi(pointsStr)
	if err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "points must be an integer")
		return
	}
	if reason == "" {
		reason = "manual_award"
	}

	if err := s.deps.Loyalty.Earn(r.Context(), userID, points, reason); err != nil {
		s.log.Error("loyalty earn", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not record award")
		return
	}
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}
