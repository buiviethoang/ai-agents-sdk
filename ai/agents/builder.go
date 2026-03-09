package agents

import (
	"context"
	"regexp"
	"strings"

	repoc "github.com/buiviethoang/ai-agents-sdk/ai/context"
	"github.com/buiviethoang/ai-agents-sdk/ai/llm"
)

const builderPrompt = `You are a senior Go engineer.

Task:
{{feature}}

Architecture:
{{architecture}}

Relevant files:
{{files}}

Requirements:
- idiomatic Go
- table-driven tests
- use context.Context
- avoid global state

Return updated files and tests.
Format each file as a markdown code block with the path as the first line: path: relative/path/to/file.go`

type Builder struct {
	llm *llm.Client
}

func NewBuilder(c *llm.Client) *Builder {
	return &Builder{llm: c}
}

func (b *Builder) Build(ctx context.Context, feature, architecture string, files []repoc.FileContent, feedback string) (map[string]string, error) {
	filesStr := formatFiles(files)
	prompt := strings.ReplaceAll(builderPrompt, "{{feature}}", feature)
	prompt = strings.ReplaceAll(prompt, "{{architecture}}", architecture)
	prompt = strings.ReplaceAll(prompt, "{{files}}", filesStr)
	if feedback != "" {
		prompt += "\n\nReviewer feedback to address:\n" + feedback
	}

	resp, err := b.llm.Send(ctx, "", prompt)
	if err != nil {
		return nil, err
	}
	return parseFileBlocks(resp), nil
}

func formatFiles(files []repoc.FileContent) string {
	var sb strings.Builder
	for _, f := range files {
		sb.WriteString("\n--- ")
		sb.WriteString(f.Path)
		sb.WriteString(" ---\n")
		sb.WriteString(f.Content)
		sb.WriteString("\n")
	}
	return sb.String()
}

var codeBlockRe = regexp.MustCompile(`(?s)path:\s*([^\s\n]+)\s*\n` + "```" + `\w*\s*\n(.*?)` + "```")

func parseFileBlocks(resp string) map[string]string {
	out := make(map[string]string)
	matches := codeBlockRe.FindAllStringSubmatch(resp, -1)
	for _, m := range matches {
		if len(m) >= 3 {
			path := strings.TrimSpace(m[1])
			content := strings.TrimSpace(m[2])
			if path != "" {
				out[path] = content
			}
		}
	}
	return out
}
