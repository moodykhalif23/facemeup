package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/cache"
	"skincare/backend-v2/internal/config"
	"skincare/backend-v2/internal/db"
	"skincare/backend-v2/internal/mlclient"
	"skincare/backend-v2/internal/server"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	slog.SetDefault(logger)

	cfg, err := config.Load()
	if err != nil {
		slog.Error("config load failed", "err", err)
		os.Exit(1)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	// --- dependencies ---
	pool, err := db.NewPool(ctx, cfg.DatabaseURL)
	if err != nil {
		slog.Error("pg pool", "err", err)
		os.Exit(1)
	}
	defer pool.Close()
	slog.Info("pg pool ready")

	redisCli, err := cache.New(ctx, cfg.RedisURL, 5*time.Minute)
	if err != nil {
		slog.Error("redis", "err", err)
		os.Exit(1)
	}
	defer redisCli.Close()
	slog.Info("redis ready")

	ml := mlclient.New(cfg.MLServiceURL, 30*time.Second)
	if err := ml.Healthz(ctx); err != nil {
		slog.Warn("ml-service health check failed (continuing, will retry per-request)", "err", err)
	} else {
		slog.Info("ml-service ready", "url", cfg.MLServiceURL)
	}

	deps := &server.Deps{
		Pool:      pool,
		Users:     db.NewUsers(pool),
		Cache:     redisCli,
		MLClient:  ml,
		Issuer:    auth.NewIssuer(cfg.JWTSecret, 30*time.Minute),
		AccessTTL: 30 * time.Minute,
	}

	srv := server.New(cfg, deps, logger)

	httpServer := &http.Server{
		Addr:              ":" + cfg.Port,
		Handler:           srv.Router(),
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       60 * time.Second,
		WriteTimeout:      185 * time.Second,
		IdleTimeout:       120 * time.Second,
	}

	go func() {
		slog.Info("api listening", "addr", httpServer.Addr, "env", cfg.Env)
		if err := httpServer.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			slog.Error("http server failed", "err", err)
			os.Exit(1)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)
	<-stop

	slog.Info("shutting down")
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer shutdownCancel()
	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		slog.Error("shutdown error", "err", err)
	}
}
