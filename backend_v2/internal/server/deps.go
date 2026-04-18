package server

import (
	"time"

	"github.com/jackc/pgx/v5/pgxpool"

	"skincare/backend-v2/internal/auth"
	"skincare/backend-v2/internal/cache"
	"skincare/backend-v2/internal/db"
	"skincare/backend-v2/internal/mlclient"
)

// Deps bundles the external dependencies each handler group needs.
// Constructed once in main() and passed into server.New; handlers read from it.
type Deps struct {
	Pool      *pgxpool.Pool
	Users     *db.Users
	Cache     *cache.Client
	MLClient  *mlclient.Client
	Issuer    *auth.Issuer
	AccessTTL time.Duration
}
