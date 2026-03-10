package agents

import (
	"context"
	"strings"

	"github.com/buiviethoang/ai-agents-sdk/ai/llm"
)

const reviewerSystemPrompt = `You are a strict Go reviewer.

Checklist:
- logical bugs
- race conditions
- missing edge cases
- incomplete tests

If problems: explain clearly and propose fixes.
If good: return APPROVED.
If unsure: prefer REQUEST_CHANGES.

First line must be: VERDICT: APPROVED or VERDICT: REQUEST_CHANGES
Then list each finding (or "None"), then your verdict.`

const Approved = "APPROVED"
const RequestChanges = "REQUEST_CHANGES"

type ReviewResult struct {
	Status   string
	Feedback string
}

type Reviewer struct {
	llm *llm.Client
}

func NewReviewer(c *llm.Client) *Reviewer {
	return &Reviewer{llm: c}
}

func (r *Reviewer) Review(ctx context.Context, files map[string]string) (ReviewResult, error) {
	var sb strings.Builder
	for path, content := range files {
		sb.WriteString("\n--- ")
		sb.WriteString(path)
		sb.WriteString(" ---\n")
		sb.WriteString(content)
		sb.WriteString("\n")
	}
	user := "Code to review:\n" + sb.String()

	resp, err := r.llm.Send(ctx, reviewerSystemPrompt, user)
	if err != nil {
		return ReviewResult{}, err
	}
	return parseReviewResponse(resp), nil
}

func parseReviewResponse(resp string) ReviewResult {
	upper := strings.ToUpper(strings.TrimSpace(resp))
	if strings.Contains(upper, "VERDICT: APPROVED") {
		return ReviewResult{Status: Approved}
	}
	if strings.Contains(upper, "VERDICT: REQUEST_CHANGES") {
		return ReviewResult{Status: RequestChanges, Feedback: resp}
	}
	if strings.Contains(upper[:min(50, len(upper))], Approved) {
		return ReviewResult{Status: Approved}
	}
	if strings.Contains(upper[:min(100, len(upper))], RequestChanges) {
		return ReviewResult{Status: RequestChanges, Feedback: resp}
	}
	return ReviewResult{Status: RequestChanges, Feedback: resp}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
