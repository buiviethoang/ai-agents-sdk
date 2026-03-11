# MCP Server Setup (Claude Code + Cursor)

## Install

```bash
pip install ai-agents-pipeline
```

## Configure

### Cursor

Add to `~/.cursor/mcp.json` (user) or project `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ai-agents-pipeline": {
      "command": "pipeline-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "ROOT_DIR": "/path/to/your-go-project"
      }
    }
  }
}
```

Or with `uvx`:

```json
{
  "mcpServers": {
    "ai-agents-pipeline": {
      "command": "uvx",
      "args": ["--from", "ai-agents-pipeline", "pipeline-mcp"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "ROOT_DIR": "/path/to/your-go-project"
      }
    }
  }
}
```

### Claude Code

Add to Claude code config (e.g. `~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ai-agents-pipeline": {
      "command": "pipeline-mcp",
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

Set `ROOT_DIR` in env to your Go project root, or pass it to each tool.

### Claudible

```json
{
  "mcpServers": {
    "ai-agents-pipeline": {
      "command": "pipeline-mcp",
      "env": {
        "LLM_CLIENT": "openai",
        "LLM_BASE_URL": "https://claudible.io/v1",
        "ANTHROPIC_API_KEY": "your-claudible-token"
      }
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `pipeline_architect` | Create plan and tasks from requirement |
| `pipeline_coder` | Implement one task, returns files JSON |
| `pipeline_review` | Review code (gosec + LLM) |
| `pipeline_apply_files` | Write files to disk |
| `pipeline_devops` | Format, lint, test, git push |

## Usage Flow

1. User: "Add retry logic to my Go project"
2. Claude calls `pipeline_architect` → gets plan + tasks
3. Claude calls `pipeline_coder` for task 1 → gets files
4. User approves (or Claude applies)
5. Claude calls `pipeline_apply_files` then `pipeline_devops`
6. Or: `pipeline_review` first, then fix with `pipeline_coder` if needed
