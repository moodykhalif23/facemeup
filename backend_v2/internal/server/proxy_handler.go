package server

import (
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// GET /proxy/image?url=...
//
// Fetches a remote image and streams it back. Use case: the frontend needs to
// display product images from Dr Rashel's WC store under a same-origin URL to
// avoid CORS / mixed-content issues.
//
// Safety:
//   - only http / https
//   - no private-network targets (blocks SSRF against 127.0.0.1, 10.x, 169.254.*, etc.)
//   - content-type must start with "image/"
//   - response size capped at 10 MB
func (s *Server) handleImageProxy(w http.ResponseWriter, r *http.Request) {
	raw := r.URL.Query().Get("url")
	if raw == "" {
		writeError(w, http.StatusBadRequest, "bad_request", "url query param required")
		return
	}
	target, err := validateProxyURL(raw)
	if err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", err.Error())
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 15*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target.String(), nil)
	if err != nil {
		writeError(w, http.StatusBadRequest, "bad_request", "invalid request")
		return
	}
	req.Header.Set("User-Agent", "skincare-proxy/1.0")

	client := &http.Client{
		Timeout: 15 * time.Second,
		Transport: &http.Transport{
			DialContext:         safeDialContext,
			TLSHandshakeTimeout: 5 * time.Second,
		},
	}
	resp, err := client.Do(req)
	if err != nil {
		s.log.Warn("image proxy fetch", "err", err, "url", target.String())
		writeError(w, http.StatusBadGateway, "fetch_failed", "upstream fetch failed")
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		writeError(w, resp.StatusCode, "upstream_error", "upstream returned non-200")
		return
	}
	ct := resp.Header.Get("Content-Type")
	if !strings.HasPrefix(ct, "image/") {
		writeError(w, http.StatusBadRequest, "bad_content_type", "target is not an image")
		return
	}

	const maxBytes = 10 * 1024 * 1024
	w.Header().Set("Content-Type", ct)
	w.Header().Set("Cache-Control", "public, max-age=3600")
	w.WriteHeader(http.StatusOK)
	_, _ = io.Copy(w, io.LimitReader(resp.Body, maxBytes))
}

// validateProxyURL rejects anything that isn't a plain http(s) URL targeting
// a host. Does not resolve DNS — SSRF on private networks is stopped at dial
// time by `safeDialContext` below.
func validateProxyURL(raw string) (*url.URL, error) {
	u, err := url.Parse(raw)
	if err != nil {
		return nil, errors.New("invalid url")
	}
	if u.Scheme != "http" && u.Scheme != "https" {
		return nil, errors.New("scheme must be http or https")
	}
	if u.Host == "" {
		return nil, errors.New("host required")
	}
	return u, nil
}

// safeDialContext blocks connections to private-network addresses to stop
// trivial SSRF (`url=http://127.0.0.1:6379/...` etc). Wraps the default dialer.
func safeDialContext(ctx context.Context, network, addr string) (net.Conn, error) {
	host, port, err := net.SplitHostPort(addr)
	if err != nil {
		return nil, err
	}
	ips, err := net.DefaultResolver.LookupIPAddr(ctx, host)
	if err != nil {
		return nil, err
	}
	for _, ip := range ips {
		if isPrivateIP(ip.IP) {
			return nil, errors.New("refusing to connect to private address")
		}
	}
	d := net.Dialer{Timeout: 5 * time.Second}
	return d.DialContext(ctx, network, net.JoinHostPort(host, port))
}

// isPrivateIP returns true for loopback, link-local, private, and RFC6598 space.
func isPrivateIP(ip net.IP) bool {
	if ip.IsLoopback() || ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() {
		return true
	}
	if ip.IsPrivate() {
		return true
	}
	// CGNAT / RFC6598: 100.64.0.0/10
	_, cgnat, _ := net.ParseCIDR("100.64.0.0/10")
	return cgnat.Contains(ip)
}
