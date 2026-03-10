# How Validate Works

## Flow

```
ai-engineer run "task"
       │
       ▼
  Builder + Reviewer
  (max 2 iterations)
       │
       ▼
  Write files to disk
       │
       ▼
  exec: bash scripts/validate.sh
  (cwd = project root)
       │
       ▼
  ┌─────────────────────────────────┐
  │ 1. go fmt ./...                  │  ← Format all Go files
  │ 2. go vet ./...                  │  ← Static analysis, suspicious constructs
  │ 3. golangci-lint run              │  ← Linter (requires golangci-lint installed)
  │ 4. go test ./...                 │  ← Run all tests
  │ 5. go test -cover ./...          │  ← Run tests with coverage
  └─────────────────────────────────┘
       │
       ├── success → Done
       │
       └── failure → Error; files remain on disk (you can fix or revert)
```

## What Each Step Does

| Step | Command | Purpose |
|------|---------|---------|
| 1 | `go fmt ./...` | Rewrites Go files to standard format |
| 2 | `go vet ./...` | Reports suspicious code (e.g. printf format issues, unreachable code) |
| 3 | `golangci-lint run` | Runs linters; fails on style/vet issues |
| 4 | `go test ./...` | Runs all `*_test.go` tests |
| 5 | `go test -cover ./...` | Same + coverage (any failure fails the whole script) |

## Invocation

The runner calls:

```go
cmd := exec.Command("bash", script)
cmd.Dir = rootDir          // your project root
cmd.Stdout = os.Stdout
cmd.Stderr = os.Stderr
cmd.Run()
```

So output goes directly to your terminal. If any step exits non-zero (`set -e`), the script stops and ai-engineer returns an error.

## Run Validate Manually

```bash
# From project root
bash scripts/validate.sh

# Or use helper
bash scripts/helper.sh validate /path/to/project

# Without validate.sh file (steps only)
bash scripts/helper.sh validate-standalone /path/to/project
```

## Script Path

Default: `{rootDir}/scripts/validate.sh`. Override via `sdk.Config.ValidateScript`.
