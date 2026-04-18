package server

import (
	"encoding/json"
	"log/slog"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	chimw "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/config"
)

type Server struct {
	cfg    *config.Config
	deps   *Deps
	log    *slog.Logger
	router *chi.Mux
	start  time.Time
}

func New(cfg *config.Config, deps *Deps, log *slog.Logger) *Server {
	s := &Server{cfg: cfg, deps: deps, log: log, start: time.Now()}
	s.router = s.buildRouter()
	return s
}

func (s *Server) Router() http.Handler { return s.router }

func (s *Server) buildRouter() *chi.Mux {
	r := chi.NewRouter()

	r.Use(chimw.RequestID)
	r.Use(chimw.RealIP)
	r.Use(chimw.Recoverer)
	r.Use(requestLogger(s.log))
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   s.cfg.CORSOrigins,
		AllowedMethods:   []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	r.Get("/health", s.health)

	r.Route(s.cfg.APIPrefix, func(api chi.Router) {
		api.Get("/health", s.health)

		// Public auth routes
		api.Post("/auth/signup", s.handleSignup)
		api.Post("/auth/login", s.handleLogin)

		// Image proxy — public on purpose (frontend needs to embed without auth).
		// SSRF-hardened via safeDialContext.
		api.Get("/proxy/image", s.handleImageProxy)

		// Authenticated routes
		api.Group(func(protected chi.Router) {
			if s.deps != nil && s.deps.Issuer != nil {
				protected.Use(auth.Middleware(s.deps.Issuer))
			}
			protected.Get("/auth/me", s.handleMe)

			// Analyze + profile (Phase 5c)
			protected.Post("/analyze", s.handleAnalyze)
			protected.Post("/analyze/feedback", s.handleAnalyzeFeedback)
			protected.Post("/training/submit", s.handleTrainingSubmit)
			protected.Get("/profile/{userId}", s.handleGetProfile)

			// Products (Phase 5d)
			protected.Get("/products", s.handleListProducts)
			protected.Get("/products/{id}", s.handleGetProduct)

			// Recommend (Phase 5d)
			protected.Post("/recommend", s.handleRecommend)

			// Orders (Phase 5e)
			protected.Post("/orders", s.handleCreateOrder)
			protected.Get("/orders", s.handleListOrders)
			protected.Get("/orders/{id}", s.handleGetOrder)

			// Loyalty (Phase 5e)
			protected.Get("/loyalty", s.handleGetLoyalty)
			protected.Get("/loyalty/{userId}", s.handleGetLoyalty)
			protected.Post("/loyalty/earn", s.handleLoyaltyEarn)

			// WooCommerce sync — wc-id resolution is used by the cart,
			// so non-admin users can call it.
			protected.Post("/sync/woocommerce/wc-id", s.handleSyncWoocommerceIDs)

			// Admin-only routes (Phase 5f)
			protected.Group(func(admin chi.Router) {
				admin.Use(auth.RequireAdmin())
				admin.Get("/admin/stats", s.handleAdminStats)
				admin.Get("/admin/users", s.handleAdminListUsers)
				admin.Put("/admin/users/{userId}/role", s.handleAdminUpdateUserRole)
				admin.Delete("/admin/users/{userId}", s.handleAdminDeleteUser)
				admin.Get("/admin/orders", s.handleAdminListOrders)
				admin.Put("/admin/orders/{orderId}/status", s.handleAdminUpdateOrderStatus)
				admin.Get("/admin/reports", s.handleAdminListReports)
				admin.Delete("/admin/reports/{reportId}", s.handleAdminDeleteReport)
				admin.Get("/admin/reports/{userId}", s.handleAdminUserReports)
				admin.Post("/admin/cache/clear", s.handleAdminCacheClear)
				admin.Post("/admin/training/sync", s.handleAdminTrainingSync)

				// Product admin CRUD
				admin.Post("/products/admin/create", s.handleAdminCreateProduct)
				admin.Put("/products/admin/{sku}", s.handleAdminUpdateProduct)
				admin.Delete("/products/admin/{sku}", s.handleAdminDeleteProduct)
				admin.Delete("/products/admin/bulk", s.handleAdminBulkDeleteProducts)
				admin.Post("/products/admin/seed", s.handleAdminSeedProducts)

				// WC sync (admin)
				admin.Post("/sync/woocommerce", s.handleSyncWoocommerceProducts)
				admin.Post("/sync/woocommerce/orders", s.handleSyncWoocommerceOrders)
			})
		})
	})

	return r
}

func (s *Server) health(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"status": "ok",
		"uptime": time.Since(s.start).String(),
		"env":    s.cfg.Env,
	})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func requestLogger(log *slog.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()
			ww := chimw.NewWrapResponseWriter(w, r.ProtoMajor)
			next.ServeHTTP(ww, r)
			log.Info("http",
				"method", r.Method,
				"path", r.URL.Path,
				"status", ww.Status(),
				"bytes", ww.BytesWritten(),
				"dur_ms", time.Since(start).Milliseconds(),
			)
		})
	}
}
