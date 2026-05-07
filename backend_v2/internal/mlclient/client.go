// Package mlclient calls the Python ML sidecar (`ml-service`) over HTTP/JSON.
//
// Contract matches ml_service/app/schemas.py. If the sidecar is unreachable
// we surface a typed error so the Go handler can decide whether to 503 or
// fall back.
package mlclient

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Landmark matches ml_service Landmark schema.
type Landmark struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// AnalyzeRequest mirrors ml_service/app/schemas.py.
type AnalyzeRequest struct {
	ImageBase64   string         `json:"image_base64"`
	Landmarks     []Landmark     `json:"landmarks,omitempty"`
	Questionnaire map[string]any `json:"questionnaire"`
}

// Heatmap matches HeatmapPayload.
type Heatmap struct {
	Label       string `json:"label"`
	ImageBase64 string `json:"image_base64"`
}

// QualityWarning mirrors ml_service QualityWarning. Severity is "warn" or
// "block"; "block" responses come back as 422 with the warnings on the error
// detail and are surfaced to the user as a retake prompt.
type QualityWarning struct {
	Code     string `json:"code"`
	Severity string `json:"severity"`
	Message  string `json:"message"`
}

// AnalyzeResponse mirrors AnalyzeResponse.
type AnalyzeResponse struct {
	SkinType        string             `json:"skin_type"`
	SkinTypeScores  map[string]float64 `json:"skin_type_scores"`
	Conditions      []string           `json:"conditions"`
	ConditionScores map[string]float64 `json:"condition_scores"`
	Confidence      float64            `json:"confidence"`
	InferenceMode   string             `json:"inference_mode"`
	Heatmaps        []Heatmap          `json:"heatmaps"`
	QualityWarnings []QualityWarning   `json:"quality_warnings"`
	Disclaimer      string             `json:"disclaimer"`
}

// Client is safe for concurrent use.
type Client struct {
	baseURL string
	http    *http.Client
}

// ErrSidecarUnavailable means the ML service didn't respond / 5xx'd.
var ErrSidecarUnavailable = errors.New("ml-service unavailable")

// ErrBadRequest = 4xx client-side problem (the sidecar tells us the image is
// bad, no face, etc). When `Code == "image_quality_too_low"`, `Warnings`
// carries the structured retake guidance the frontend should display.
type ErrBadRequest struct {
	Code     string
	Msg      string
	Warnings []QualityWarning
}

func (e *ErrBadRequest) Error() string { return "ml-service 4xx: " + e.Msg }

// New returns a client with sane defaults. `timeout` applies to the whole
// /v1/analyze call (decode + detect + classify + heatmap) — 30s is generous
// for CPU inference without a trained classifier; retune after Phase 3.
func New(baseURL string, timeout time.Duration) *Client {
	if timeout == 0 {
		timeout = 30 * time.Second
	}
	return &Client{
		baseURL: baseURL,
		http: &http.Client{
			Timeout: timeout,
		},
	}
}

// Analyze calls POST {baseURL}/v1/analyze.
func (c *Client) Analyze(ctx context.Context, req *AnalyzeRequest) (*AnalyzeResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("encode analyze request: %w", err)
	}
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/v1/analyze", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Accept", "application/json")

	resp, err := c.http.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("%w: %v", ErrSidecarUnavailable, err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)

	if resp.StatusCode >= 500 {
		return nil, fmt.Errorf("%w: status=%d body=%s", ErrSidecarUnavailable, resp.StatusCode, string(raw))
	}
	if resp.StatusCode >= 400 {
		// FastAPI's `HTTPException(detail=...)` puts whatever was passed in
		// under `detail`. We expect either a plain string or a structured
		// object `{code, message, warnings: [...]}` for quality blocks.
		var asString struct {
			Detail string `json:"detail"`
		}
		var asObject struct {
			Detail struct {
				Code     string           `json:"code"`
				Message  string           `json:"message"`
				Warnings []QualityWarning `json:"warnings"`
			} `json:"detail"`
		}
		if jErr := json.Unmarshal(raw, &asObject); jErr == nil && asObject.Detail.Code != "" {
			return nil, &ErrBadRequest{
				Code:     asObject.Detail.Code,
				Msg:      asObject.Detail.Message,
				Warnings: asObject.Detail.Warnings,
			}
		}
		msg := string(raw)
		if jErr := json.Unmarshal(raw, &asString); jErr == nil && asString.Detail != "" {
			msg = asString.Detail
		}
		return nil, &ErrBadRequest{Msg: msg}
	}

	var out AnalyzeResponse
	if err := json.Unmarshal(raw, &out); err != nil {
		return nil, fmt.Errorf("decode analyze response: %w", err)
	}
	return &out, nil
}

// Healthz returns nil if ml-service responds 200 on /healthz.
func (c *Client) Healthz(ctx context.Context) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/healthz", nil)
	if err != nil {
		return err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return fmt.Errorf("%w: %v", ErrSidecarUnavailable, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("%w: status=%d", ErrSidecarUnavailable, resp.StatusCode)
	}
	return nil
}
