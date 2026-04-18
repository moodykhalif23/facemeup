package cache

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/redis/go-redis/v9"
)

// ErrRateLimited is returned when a caller has exceeded the limit for the window.
var ErrRateLimited = errors.New("rate limit exceeded")

func (c *Client) CheckRate(
	ctx context.Context, bucket, id string, max int, window time.Duration,
) (int, error) {
	key := fmt.Sprintf("ratelimit:%s:%s", bucket, id)
	count, err := c.rdb.Incr(ctx, key).Result()
	if err != nil {
		return 0, err
	}
	if count == 1 {
		if err := c.rdb.Expire(ctx, key, window).Err(); err != nil && !errors.Is(err, redis.Nil) {
			return int(count), err
		}
	}
	if int(count) > max {
		return int(count), ErrRateLimited
	}
	return int(count), nil
}
