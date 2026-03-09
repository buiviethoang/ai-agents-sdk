package sdk

import (
	"context"

	"github.com/yourorg/ai-agents-sdk/ai/llm"
	"github.com/yourorg/ai-agents-sdk/ai/runner"
)

// Config configures an AI agent run.
type Config struct {
	RootDir        string // project root; default: cwd
	ValidateScript string // path to validate.sh; default: scripts/validate.sh
	DryRun         bool   // skip writing files and validation
	MaxFiles       int    // max files in context; default: 15
	MaxTokens      int64  // max output tokens; default: 4096
	APIKey         string // Anthropic API key; default: ANTHROPIC_API_KEY env
}

func (c *Config) defaults() {
	if c.MaxFiles <= 0 {
		c.MaxFiles = 15
	}
	if c.MaxTokens <= 0 {
		c.MaxTokens = 4096
	}
}

// Result is the outcome of a Run.
type Result = runner.Result

// Run executes the Builder → Reviewer loop (max 2 iterations), then validates.
func Run(ctx context.Context, feature string, cfg Config) (Result, error) {
	cfg.defaults()

	llmClient := llm.NewClient(cfg.APIKey)
	llmClient.SetMaxTokens(cfg.MaxTokens)
	r := runner.NewRunner(llmClient, cfg.MaxFiles)

	return r.Execute(ctx, feature, runner.Config{
		RootDir:        cfg.RootDir,
		ValidateScript: cfg.ValidateScript,
		DryRun:         cfg.DryRun,
	})
}
