package config

import (
	"fmt"
	"os"
	"strings"
)

type Config struct {
	Env           string
	Port          string
	APIPrefix     string
	CORSOrigins   []string
	DatabaseURL   string
	RedisURL      string
	JWTSecret     string
	JWTAlgorithm  string
	AccessTTLMin  int
	RefreshTTLDay int
	MLServiceURL  string
	SkinTypes     []string
	Conditions    []string

	// WooCommerce — optional. If absent, the /sync/* endpoints 503 with
	// "not_configured" instead of crashing.
	WooCommerceURL    string
	WooCommerceKey    string
	WooCommerceSecret string
}

func Load() (*Config, error) {
	c := &Config{
		Env:          getenv("ENV", "development"),
		Port:         getenv("PORT", "8000"),
		APIPrefix:    getenv("API_V1_PREFIX", "/api/v1"),
		CORSOrigins:  splitCSV(getenv("CORS_ORIGINS", "*")),
		DatabaseURL:  os.Getenv("DATABASE_URL"),
		RedisURL:     getenv("REDIS_URL", "redis://localhost:6379/0"),
		JWTSecret:    os.Getenv("JWT_SECRET"),
		JWTAlgorithm: getenv("JWT_ALGORITHM", "HS256"),
		MLServiceURL: getenv("ML_SERVICE_URL", "http://ml-service:8000"),
		SkinTypes:    splitCSV(getenv("MODEL_SKIN_TYPES", "Oily,Dry,Combination,Normal,Sensitive")),
		Conditions:   splitCSV(getenv("MODEL_CONDITIONS", "Acne,Hyperpigmentation,Uneven tone,Dehydration,Wrinkles,Redness,None detected")),

		WooCommerceURL:    os.Getenv("WOOCOMMERCE_URL"),
		WooCommerceKey:    os.Getenv("WOOCOMMERCE_CONSUMER_KEY"),
		WooCommerceSecret: os.Getenv("WOOCOMMERCE_CONSUMER_SECRET"),
	}

	if c.DatabaseURL == "" {
		return nil, fmt.Errorf("DATABASE_URL is required")
	}
	if c.JWTSecret == "" {
		return nil, fmt.Errorf("JWT_SECRET is required")
	}
	return c, nil
}

func getenv(k, fallback string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return fallback
}

func splitCSV(s string) []string {
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
