package llm

import (
	"context"
	"os"
	"strings"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"
)

const ModelSonnet = "sonnet"
const ModelHaiku = "haiku"

const (
	DefaultMaxOutputTokens = 4096
	DefaultInputTokenLimit = 180000
	charsPerToken          = 4
)

type Client struct {
	anthropic anthropic.Client
	maxTokens int64
	model     anthropic.Model
}

func NewClient(apiKey string) *Client {
	key := apiKey
	if key == "" {
		key, _ = os.LookupEnv("ANTHROPIC_API_KEY")
	}
	return &Client{
		anthropic: anthropic.NewClient(option.WithAPIKey(key)),
		maxTokens: DefaultMaxOutputTokens,
		model:     anthropic.ModelClaudeSonnet4_5_20250929,
	}
}

func (c *Client) SetMaxTokens(n int64) {
	c.maxTokens = n
}

func (c *Client) SetModel(m anthropic.Model) {
	c.model = m
}

func ModelFromName(name string) anthropic.Model {
	switch strings.ToLower(name) {
	case ModelHaiku:
		return anthropic.ModelClaudeHaiku4_5_20251001
	case ModelSonnet:
		return anthropic.ModelClaudeSonnet4_5_20250929
	default:
		return anthropic.ModelClaudeSonnet4_5_20250929
	}
}

func truncateToTokenLimit(s string, limit int) string {
	maxChars := limit * charsPerToken
	if len(s) <= maxChars {
		return s
	}
	return s[:maxChars] + "\n...(truncated)"
}

func cacheCtrl5m() anthropic.CacheControlEphemeralParam {
	cc := anthropic.NewCacheControlEphemeralParam()
	cc.TTL = anthropic.CacheControlEphemeralTTLTTL5m
	return cc
}

func (c *Client) Send(ctx context.Context, system, user string) (string, error) {
	system = truncateToTokenLimit(system, DefaultInputTokenLimit/2)
	user = truncateToTokenLimit(user, DefaultInputTokenLimit/2)

	systemBlocks := []anthropic.TextBlockParam{}
	if system != "" {
		systemBlocks = []anthropic.TextBlockParam{{Text: system, CacheControl: cacheCtrl5m()}}
	}

	model := c.model
	if model == "" {
		model = anthropic.ModelClaudeSonnet4_5_20250929
	}
	msg, err := c.anthropic.Messages.New(ctx, anthropic.MessageNewParams{
		Model:     model,
		MaxTokens: c.maxTokens,
		System:    systemBlocks,
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
