package server

import (
	"encoding/json"
	"net/http"
)

// errorBody is the shape the frontend's axios interceptor already handles
// (error.response.data.error.message). `Warnings` is optional — populated
// only on quality-block errors so the FE can render a retake card.
type errorBody struct {
	Error struct {
		Code     string           `json:"code"`
		Message  string           `json:"message"`
		Warnings []map[string]any `json:"warnings,omitempty"`
	} `json:"error"`
}

func writeError(w http.ResponseWriter, status int, code, message string) {
	writeErrorWithWarnings(w, status, code, message, nil)
}

func writeErrorWithWarnings(w http.ResponseWriter, status int, code, message string,
	warnings []map[string]any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	var body errorBody
	body.Error.Code = code
	body.Error.Message = message
	body.Error.Warnings = warnings
	_ = json.NewEncoder(w).Encode(body)
}
