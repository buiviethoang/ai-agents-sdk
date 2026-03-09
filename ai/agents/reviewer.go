package agents

import (
	"context"
	"strings"

	"github.com/yourorg/ai-agents-sdk/ai/llm"
)

const reviewerPrompt = `You are a strict Go reviewer.

Review the code and tests.

Check for:
- logical bugs
- race conditions
- missing edge cases
- incomplete tests

If problems exist:
Explain clearly and propose fixes.

If good:
Return APPROVED.

Respond with exactly APPROVED or REQUEST_CHANGES at the start of your response, followed by optional feedback.`

const Approved = "APPROVED"
const RequestChanges = "REQUEST_CHANGES"

type ReviewResult struct {
	Status  string
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
	prompt := reviewerPrompt + "\n\nCode to review:\n" + sb.String()

	resp, err := r.llm.Send(ctx, "", prompt)
	if err != nil {
		return ReviewResult{}, err
	}
	return parseReviewResponse(resp), nil
}

func parseReviewResponse(resp string) ReviewResult {
	upper := strings.ToUpper(strings.TrimSpace(resp))
	if strings.Contains(upper[:min(50, len(upper))], Approved) {
		return ReviewResult{Status: Approved}
	}
	if strings.Contains(upper[:min(100, len(upper))], RequestChanges) {
		return ReviewResult{Status: RequestChanges, Feedback: resp}
	}
	if strings.HasPrefix(upper, Approved) {
		return ReviewResult{Status: Approved}
	}
	return ReviewResult{Status: RequestChanges, Feedback: resp}
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
