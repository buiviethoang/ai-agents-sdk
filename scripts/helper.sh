#!/bin/bash
# Terminal helper for ai-agents-sdk
# Usage: source scripts/helper.sh   OR   bash scripts/helper.sh <cmd>

set -e

SDK_MODULE="github.com/buiviethoang/ai-agents-sdk"
INSTALL_CMD="GOPROXY=direct go install ${SDK_MODULE}/cmd/ai-engineer@main"

install_cli() {
  echo "Installing ai-engineer..."
  $INSTALL_CMD
  echo "Done. Run: ai-engineer \"your task\""
}

run() {
  if [ -z "$1" ]; then
    echo "Usage: run \"Add Redis cache\""
    exit 1
  fi
  ai-engineer "$@"
}

validate() {
  local root="${1:-.}"
  local script="${root}/scripts/validate.sh"
  if [ ! -f "$script" ]; then
    echo "No scripts/validate.sh in $root"
    exit 1
  fi
  echo "Running validate from $root"
  (cd "$root" && bash "$script")
}

validate_standalone() {
  local root="${1:-.}"
  echo "=== Validate (standalone, from $root) ==="
  (cd "$root" && {
    echo "[1/5] Formatting"
    go fmt ./...
    echo "[2/5] Vet"
    go vet ./...
    echo "[3/5] Lint"
    golangci-lint run
    echo "[4/5] Test"
    go test ./...
    echo "[5/5] Coverage"
    go test -cover ./...
    echo "=== All passed ==="
  })
}

show_validate_flow() {
  cat <<'EOF'
Validate flow (scripts/validate.sh):
  1. go fmt ./...      - format code
  2. go vet ./...      - static analysis
  3. golangci-lint run - linter
  4. go test ./...     - run tests
  5. go test -cover    - coverage

Runner invokes: bash scripts/validate.sh (cwd = project root)
On any failure, ai-engineer exits with error.
EOF
}

case "${1:-}" in
  install) install_cli ;;
  run)     shift; run "$@" ;;
  validate) validate "$2" ;;
  validate-standalone) validate_standalone "$2" ;;
  show-validate) show_validate_flow ;;
  *)
    echo "Helper commands: install | run | validate [dir] | validate-standalone [dir] | show-validate"
    echo "  install             - go install ai-engineer"
    echo "  run \"task\"          - ai-engineer \"task\""
    echo "  validate [dir]      - run scripts/validate.sh in dir"
    echo "  validate-standalone - run validate steps without script file"
    echo "  show-validate      - print validate flow"
    ;;
esac
