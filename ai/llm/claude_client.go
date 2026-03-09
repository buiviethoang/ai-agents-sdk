package llm

import (
	"context"
	"os"
	"strings"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"
)

const (
	DefaultMaxOutputTokens = 4096
	DefaultInputTokenLimit = 180000
	charsPerToken          = 4
)

type Client struct {
	anthropic anthropic.Client
	maxTokens int64
}

func NewClient(apiKey string) *Client {
	key := apiKey
	if key == "" {
		key, _ = os.LookupEnv("ANTHROPIC_API_KEY")
	}
	return &Client{
		anthropic: anthropic.NewClient(option.WithAPIKey(key)),
		maxTokens: DefaultMaxOutputTokens,
	}
}

func (c *Client) SetMaxTokens(n int64) {
	c.maxTokens = n
}

func truncateToTokenLimit(s string, limit int) string {
	maxChars := limit * charsPerToken
	if len(s) <= maxChars {
		return s
	}
	return s[:maxChars] + "\n...(truncated)"
}

func (c *Client) Send(ctx context.Context, system, user string) (string, error) {
	system = truncateToTokenLimit(system, DefaultInputTokenLimit/2)
	user = truncateToTokenLimit(user, DefaultInputTokenLimit/2)

	msg, err := c.anthropic.Messages.New(ctx, anthropic.MessageNewParams{
		Model:     anthropic.ModelClaudeSonnet4_5_20250929,
		MaxTokens: c.maxTokens,
		System:    []anthropic.TextBlockParam{{Text: system}},
		Messages: []anthropic.MessageParam{
			anthropic.NewUserMessage(anthropic.NewTextBlock(user)),
		},
	})
	if err != nil {
		return "", err
	}

	var sb strings.Builder
	for _, block := range msg.Content {
		if tb, ok := block.AsAny().(anthropic.TextBlock); ok {
			sb.WriteString(tb.Text)
		}
	}
	return sb.String(), nil
}
