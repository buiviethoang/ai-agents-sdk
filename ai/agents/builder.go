package agents

import (
	"context"
	"regexp"
	"strings"

	repoc "github.com/buiviethoang/ai-agents-sdk/ai/context"
	"github.com/buiviethoang/ai-agents-sdk/ai/llm"
)

const builderSystemPrompt = `You are a senior Go engineer.

Requirements:
- idiomatic Go
- table-driven tests
- use context.Context
- avoid global state
- change only what the task requires

Output format for each file:
<<FILE path/to/file.go>>
...content...
<<END>>

Example:
<<FILE pkg/foo.go>>
package pkg
func Bar() int { return 1 }
<<END>>`

const builderUserTemplate = `Task:
{{feature}}

Relevant files:
{{files}}{{feedback}}

Return updated files using <<FILE path>>...<<END>> format.`

type Builder struct {
	llm *llm.Client
}

func NewBuilder(c *llm.Client) *Builder {
	return &Builder{llm: c}
}

func (b *Builder) Build(ctx context.Context, feature, architecture string, files []repoc.FileContent, feedback string) (map[string]string, error) {
	filesStr := formatFiles(files)
	feedbackPart := ""
	if feedback != "" {
		feedbackPart = "\n\nReviewer feedback to address:\n" + feedback
	}
	system := builderSystemPrompt + "\n\nArchitecture:\n" + architecture
	user := strings.ReplaceAll(builderUserTemplate, "{{feature}}", feature)
	user = strings.ReplaceAll(user, "{{files}}", filesStr)
	user = strings.ReplaceAll(user, "{{feedback}}", feedbackPart)

	resp, err := b.llm.Send(ctx, system, user)
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

var fileBlockRe = regexp.MustCompile(`(?s)<<FILE\s+([^\s>]+)>>\s*\n(.*?)<<END>>`)
var codeBlockRe = regexp.MustCompile(`(?s)path:\s*([^\s\n]+)\s*\n` + "```" + `\w*\s*\n(.*?)` + "```")

func parseFileBlocks(resp string) map[string]string {
	out := make(map[string]string)
	matches := fileBlockRe.FindAllStringSubmatch(resp, -1)
	if len(matches) == 0 {
		matches = codeBlockRe.FindAllStringSubmatch(resp, -1)
	}
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
