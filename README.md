# ai-agents-sdk

Go SDK and CLI for an AI agent workflow: Builder writes Go code, Reviewer validates, max 2 debate iterations, local Go validation.

## Install

```bash
go get github.com/buiviethoang/ai-agents-sdk
```

## Library Usage

```go
import (
    "context"
    "github.com/buiviethoang/ai-agents-sdk/sdk"
)

func main() {
    result, err := sdk.Run(context.Background(), "Add Redis cache to user profile API", sdk.Config{
        RootDir:   "/path/to/project",
        MaxFiles:  15,
        MaxTokens: 4096,
    })
    if err != nil {
        // handle
    }
    // result.Approved, result.Files, result.Iterations
}
```

## CLI Usage

```bash
go install github.com/buiviethoang/ai-agents-sdk/cmd/ai-engineer@latest
export ANTHROPIC_API_KEY=your-key
ai-engineer run "Add Redis cache to user profile API"
```

Flags: `--dry-run`, `--max-files=15`, `--max-tokens=4096`

**See [docs/HOWTO.md](docs/HOWTO.md)** for setup and usage with a real project (e.g. notification-service).

## Layout

- `sdk` - Public API (`sdk.Run`)
- `ai/llm` - Claude client
- `ai/context` - Repo context extractor
- `ai/agents` - Builder and Reviewer agents
- `ai/runner` - Orchestration and debate loop

