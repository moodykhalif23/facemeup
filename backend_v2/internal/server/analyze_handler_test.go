package server

import (
	"testing"
	"time"

	"skincare/backend-v2/internal/db"
)

func TestCoerceIntID(t *testing.T) {
	tt := []struct {
		name string
		in   any
		want int
		ok   bool
	}{
		{"float", float64(42), 42, true},
		{"int", 7, 7, true},
		{"numeric string", "101", 101, true},
		{"padded string", "  9 ", 9, true},
		{"empty string", "", 0, false},
		{"non-numeric string", "abc", 0, false},
		{"nil", nil, 0, false},
		{"bool", true, 0, false},
	}
	for _, tc := range tt {
		t.Run(tc.name, func(t *testing.T) {
			got, ok := coerceIntID(tc.in)
			if ok != tc.ok || got != tc.want {
				t.Fatalf("got (%d, %v), want (%d, %v)", got, ok, tc.want, tc.ok)
			}
		})
	}
}

func TestProfileRowToItemMapsAllFields(t *testing.T) {
	mode := "onnx_mobilenet"
	feedback := "confirmed"
	report := "iVBORw0K..."
	row := db.ProfileRow{
		ID:                42,
		UserID:            "user-1",
		SkinType:          "Oily",
		Conditions:        []string{"Acne", "Redness"},
		Confidence:        0.83,
		Questionnaire:     map[string]any{"oil_levels": "very_oily"},
		SkinTypeScores:    map[string]float64{"Oily": 0.7, "Dry": 0.1},
		ConditionScores:   map[string]float64{"Acne": 0.9, "Redness": 0.6},
		InferenceMode:     &mode,
		UserFeedback:      &feedback,
		ReportImageBase64: &report,
		CaptureImages:     []string{"capture1", "capture2"},
		CreatedAt:         time.Date(2026, 4, 18, 10, 0, 0, 0, time.UTC),
	}

	item := profileRowToItem(row)

	if item.ID != 42 || item.SkinType != "Oily" {
		t.Fatalf("basic fields wrong: %+v", item)
	}
	if len(item.Conditions) != 2 {
		t.Fatalf("conditions lost: %+v", item.Conditions)
	}
	if item.InferenceMode != "onnx_mobilenet" {
		t.Fatalf("inference_mode not copied: %q", item.InferenceMode)
	}
	if item.UserFeedback != "confirmed" {
		t.Fatalf("user_feedback not copied: %q", item.UserFeedback)
	}
	if item.ReportImageBase64 != report {
		t.Fatalf("report_image_base64 not copied")
	}
	if !item.CreatedAt.Equal(item.Timestamp) {
		t.Fatalf("timestamp alias should equal created_at")
	}
	if item.SkinTypeScores["Oily"] != 0.7 {
		t.Fatalf("skin_type_scores lost: %+v", item.SkinTypeScores)
	}
}

func TestProfileRowToItemHandlesNilOptionals(t *testing.T) {
	row := db.ProfileRow{ID: 1, UserID: "u", SkinType: "Normal", CreatedAt: time.Now()}
	item := profileRowToItem(row)

	if item.InferenceMode != "" || item.UserFeedback != "" || item.ReportImageBase64 != "" {
		t.Fatalf("nil pointers should produce empty strings, got: %+v", item)
	}
}
