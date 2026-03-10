package agents

import (
	"testing"
)

func TestParseReviewResponse(t *testing.T) {
	tests := []struct {
		name   string
		resp   string
		status string
	}{
		{"verdict approved", "VERDICT: APPROVED\nLooks good.", Approved},
		{"verdict changes", "VERDICT: REQUEST_CHANGES\nFix the bug.", RequestChanges},
		{"approved start", "APPROVED\nLooks good.", Approved},
		{"approved lowercase", "approved. The code is fine.", Approved},
		{"request changes", "REQUEST_CHANGES\nFix the bug.", RequestChanges},
		{"implicit changes", "There are issues: ...", RequestChanges},
		{"approved in body", "I approve. APPROVED", Approved},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := parseReviewResponse(tt.resp)
			if got.Status != tt.status {
				t.Errorf("parseReviewResponse() Status = %q, want %q", got.Status, tt.status)
			}
		})
	}
}
