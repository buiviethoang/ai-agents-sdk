# How Validate Works

## Flow

```
pipeline "task"
       │
       ▼
  Architect → Coder → Reviewer → DevOps
  (conditional: Reviewer can loop back to Coder max 2 times)
       │
       ▼
  DevOps: Write files, go fmt, validate.sh, git push
       │
       ▼
  exec: bash scripts/validate.sh
  (cwd = project root)
       │
       ▼
  ┌─────────────────────────────────┐
  │ 1. go fmt ./...                  │
  │ 2. go vet ./...                  │
  │ 3. golangci-lint run              │
  │ 4. go test ./...                 │
  │ 5. go test -cover ./...          │
  └─────────────────────────────────┘
       │
       ├── success → Done
       │
       └── failure → RuntimeError
```

## Run Validate Manually

```bash
bash scripts/validate.sh
bash scripts/helper.sh validate /path/to/project
bash scripts/helper.sh validate-standalone /path/to/project
```
