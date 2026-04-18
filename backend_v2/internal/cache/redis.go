// Package cache wraps the Redis client the rest of the app uses.
//
// Key schema is shared with the old Python backend:
//
//	products:catalog
//	products:detail:{sku}
//	recommend:{userID}:{skinType}:{conditions}:{gender}:{age}
//
// TTL defaults to 5 minutes (matches REDIS_CACHE_TTL_SECONDS).
package cache

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// DefaultTTL is the fallback TTL used when callers don't pass one.
const DefaultTTL = 5 * time.Minute

// Client holds a go-redis client and a default TTL.
type Client struct {
	rdb *redis.Client
	ttl time.Duration
}

// New parses a redis:// URL and connects.
func New(ctx context.Context, url string, defaultTTL time.Duration) (*Client, error) {
	opt, err := redis.ParseURL(url)
	if err != nil {
		return nil, fmt.Errorf("parse REDIS_URL: %w", err)
	}
	rdb := redis.NewClient(opt)
	pingCtx, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()
	if err := rdb.Ping(pingCtx).Err(); err != nil {
		_ = rdb.Close()
		return nil, fmt.Errorf("redis ping: %w", err)
	}
	if defaultTTL <= 0 {
		defaultTTL = DefaultTTL
	}
	return &Client{rdb: rdb, ttl: defaultTTL}, nil
}

// Close releases the connection pool.
func (c *Client) Close() error { return c.rdb.Close() }

// GetJSON loads and JSON-unmarshals a value. Returns (false, nil) on miss.
func (c *Client) GetJSON(ctx context.Context, key string, dst any) (bool, error) {
	raw, err := c.rdb.Get(ctx, key).Bytes()
	if errors.Is(err, redis.Nil) {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	if err := json.Unmarshal(raw, dst); err != nil {
		return false, fmt.Errorf("cache decode %q: %w", key, err)
	}
	return true, nil
}

// SetJSON marshals and stores with the client's default TTL (or the overridden one).
func (c *Client) SetJSON(ctx context.Context, key string, val any, ttl time.Duration) error {
	raw, err := json.Marshal(val)
	if err != nil {
		return err
	}
	if ttl <= 0 {
		ttl = c.ttl
	}
	return c.rdb.Set(ctx, key, raw, ttl).Err()
}

// Delete removes one or more keys (used by admin cache-clear).
func (c *Client) Delete(ctx context.Context, keys ...string) (int64, error) {
	if len(keys) == 0 {
		return 0, nil
	}
	return c.rdb.Del(ctx, keys...).Result()
}

// Keys returns keys matching a glob pattern (use sparingly — O(N)).
func (c *Client) Keys(ctx context.Context, pattern string) ([]string, error) {
	return c.rdb.Keys(ctx, pattern).Result()
}
