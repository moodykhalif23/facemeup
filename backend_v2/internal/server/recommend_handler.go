package server

import (
	"encoding/json"
	"fmt"
	"net/http"
	"sort"
	"strings"
	"time"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/db"
)

type recommendRequest struct {
	SkinType   string   `json:"skin_type"`
	Conditions []string `json:"conditions"`
	Gender     string   `json:"gender,omitempty"`
	Age        *int     `json:"age,omitempty"`
}

type recommendResponse struct {
	Products   []productView `json:"products"`
	Disclaimer string        `json:"disclaimer"`
}

const (
	recommendCacheTTL = 5 * time.Minute
	recommendMaxHits  = 15

	recommendDisclaimer = "This analysis is informational and does not replace professional dermatology advice."
)

// POST /recommend — rule-based product ranking.
//
// Scoring:
//   +3 per user-condition that appears in product.effects (case-insensitive substring)
//   +2 if product.suitable_for matches the user's gender exactly
//   +1 if product.suitable_for == "all"
//   +2 if the user's skin_type appears in product.effects or benefits
//
// Returns top `recommendMaxHits` with a score > 0, sorted by score desc.
func (s *Server) handleRecommend(w http.ResponseWriter, r *http.Request) {
	p := auth.PrincipalFrom(r.Context())
	if p == nil {
		writeError(w, http.StatusUnauthorized, "unauthenticated", "missing auth")
		return
	}

	var req recommendRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid JSON body")
		return
	}
	if req.SkinType == "" && len(req.Conditions) == 0 {
		writeError(w, http.StatusBadRequest, "bad_request",
			"skin_type or at least one condition is required")
		return
	}

	key := recommendCacheKey(p.UserID, &req)
	if s.deps.Cache != nil {
		var cached recommendResponse
		if hit, _ := s.deps.Cache.GetJSON(r.Context(), key, &cached); hit {
			writeJSON(w, http.StatusOK, cached)
			return
		}
	}

	products, err := s.deps.Products.List(r.Context())
	if err != nil {
		s.log.Error("list products (recommend)", "err", err)
		writeError(w, http.StatusInternalServerError, "internal", "could not load catalog")
		return
	}

	ranked := rankProducts(products, &req)
	resp := recommendResponse{
		Products:   ranked,
		Disclaimer: recommendDisclaimer,
	}
	if s.deps.Cache != nil {
		_ = s.deps.Cache.SetJSON(r.Context(), key, resp, recommendCacheTTL)
	}
	writeJSON(w, http.StatusOK, resp)
}

// rankProducts runs the scoring rubric described on handleRecommend and
// returns the top matches. Pure function — unit-tested.
func rankProducts(products []db.Product, req *recommendRequest) []productView {
	type scored struct {
		p     db.Product
		score int
	}
	userConds := lowerAll(req.Conditions)
	userType := strings.ToLower(req.SkinType)
	gender := strings.ToLower(req.Gender)

	hits := make([]scored, 0, len(products))
	for _, p := range products {
		score := 0
		effects := lowerAll(p.Effects)
		benefits := lowerAll(p.Benefits)

		for _, c := range userConds {
			if c == "" {
				continue
			}
			if containsFuzzy(effects, c) {
				score += 3
			} else if containsFuzzy(benefits, c) {
				score += 1
			}
		}

		switch strings.ToLower(p.SuitableFor) {
		case "all", "":
			score += 1
		case gender:
			if gender != "" {
				score += 2
			}
		}

		if userType != "" {
			if containsFuzzy(effects, userType) || containsFuzzy(benefits, userType) {
				score += 2
			}
		}

		if score > 0 {
			hits = append(hits, scored{p: p, score: score})
		}
	}

	sort.SliceStable(hits, func(i, j int) bool {
		if hits[i].score != hits[j].score {
			return hits[i].score > hits[j].score
		}
		return hits[i].p.Name < hits[j].p.Name
	})

	if len(hits) > recommendMaxHits {
		hits = hits[:recommendMaxHits]
	}
	out := make([]productView, 0, len(hits))
	for _, h := range hits {
		out = append(out, productToView(h.p))
	}
	return out
}

func lowerAll(xs []string) []string {
	out := make([]string, len(xs))
	for i, x := range xs {
		out[i] = strings.ToLower(strings.TrimSpace(x))
	}
	return out
}

// containsFuzzy: true if any element of xs contains `needle` as a substring,
// OR vice versa. Handles plural/spelling variance loosely.
func containsFuzzy(xs []string, needle string) bool {
	for _, x := range xs {
		if x == "" {
			continue
		}
		if strings.Contains(x, needle) || strings.Contains(needle, x) {
			return true
		}
	}
	return false
}

func recommendCacheKey(userID string, req *recommendRequest) string {
	conds := append([]string(nil), req.Conditions...)
	sort.Strings(conds)
	age := ""
	if req.Age != nil {
		age = fmt.Sprintf("%d", *req.Age)
	}
	return fmt.Sprintf("recommend:%s:%s:%s:%s:%s",
		userID,
		strings.ToLower(req.SkinType),
		strings.Join(conds, "|"),
		strings.ToLower(req.Gender),
		age,
	)
}
