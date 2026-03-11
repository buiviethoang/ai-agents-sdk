"""CLI entry point for the pipeline."""
import argparse
import logging
import os
import sys
from pathlib import Path

from pipeline.api import run_architect, run_coder, run_reviewer, apply_files, run_devops
from pipeline.config import ANTHROPIC_API_KEY, DRY_RUN, ROOT_DIR
from pipeline.config import MAX_ITERATIONS
from pipeline.graph import run_graph, run_graph_stream, _format_step

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)

ARCHITECTURE_TEMPLATE = """# Project Architecture

## Overview

This document describes the structure and conventions for the Go project. AI agents use this to understand context and produce idiomatic code.

## Directory Layout

```
project-root/
├── cmd/           # Executables
├── internal/      # Private application code
├── pkg/           # Public reusable packages
└── scripts/       # Build and validation scripts
```

## Conventions

- Use `context.Context` for cancellation and timeouts
- Avoid global state; prefer dependency injection
- Table-driven tests for all non-trivial logic
- Interfaces for external dependencies (testing, mocking)
"""

VALIDATE_TEMPLATE = """#!/bin/bash
set -e
echo "Formatting"
go fmt ./...
echo "Vet"
go vet ./...
echo "Lint"
golangci-lint run
echo "Test"
go test ./...
echo "Coverage"
go test -cover ./...
"""


def _run_streaming(args, req: str) -> dict | None:
    final = None
    for event_type, key, data in run_graph_stream(
        requirement=req,
        root_dir=args.root_dir,
        dry_run=args.dry_run,
        api_key=ANTHROPIC_API_KEY,
        stream_tokens=args.verbose,
    ):
        if event_type == "step":
            print(_format_step(key, data or {}), end="", flush=True)
        elif event_type == "progress" and data:
            msg = data.get("msg", "")
            if msg:
                print(f"  → {msg}", flush=True)
        elif event_type == "token" and args.verbose and data:
            print(data, end="", flush=True)
        elif event_type == "done":
            final = data
    return final


def _prompt(msg: str, choices: str = "ynq") -> str:
    while True:
        try:
            r = input(f"\n{msg} [{choices}]> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "q"
        if not r:
            continue
        if r[0] in choices:
            return r[0]
        print(f"  Choose one of: {choices}")


def _run_interactive(args, req: str) -> int:
    root = args.root_dir
    dry_run = args.dry_run

    print("\n═══ ARCHITECT ═══")
    arch_result = run_architect(req, api_key=ANTHROPIC_API_KEY)
    plan_md = arch_result["plan_md"]
    tasks = arch_result["tasks"]
    print(f"Plan: {len(plan_md)} chars, {len(tasks)} tasks")
    for i, t in enumerate(tasks, 1):
        print(f"  {i}. {t.get('description', '')[:70]}...")
    print("\n--- Plan (first 500 chars) ---")
    print(plan_md[:500] + ("..." if len(plan_md) > 500 else ""))
    choice = _prompt("Proceed? [y]es / [n]o quit", "ynq")
    if choice != "y":
        return 0 if choice == "n" else 1

    all_files: dict[str, str] = {}

    for task_idx in range(len(tasks)):
        task = tasks[task_idx]
        desc = task.get("description", "implement")
        review_feedback = ""
        iteration = 0

        while True:
            print(f"\n═══ CODER Task {task_idx + 1}/{len(tasks)} ═══")
            print(f"  {desc[:60]}...")
            files = run_coder(
                root_dir=root,
                task_desc=desc,
                plan_md=plan_md,
                existing_files=all_files if all_files else None,
                review_feedback=review_feedback,
                api_key=ANTHROPIC_API_KEY,
            )
            if not files:
                print("  No files produced")
                break
            print(f"  Produced {len(files)} files: {', '.join(files.keys())}")
            for path, content in list(files.items())[:2]:
                print(f"\n--- {path} (first 150 chars) ---")
                print(content[:150] + ("..." if len(content) > 150 else ""))
            if len(files) > 2:
                print(f"\n... and {len(files) - 2} more")
            choice = _prompt("[y] apply / [n] skip / [e]dit / [q]uit", "ynqe")
            if choice == "q":
                return 1
            if choice == "n":
                break
            if choice == "e":
                editor = os.environ.get("EDITOR", "nano")
                for path, content in files.items():
                    full = Path(root) / path
                    full.parent.mkdir(parents=True, exist_ok=True)
                    full.write_text(content, encoding="utf-8")
                os.system(f'{editor} "{Path(root) / list(files.keys())[0]}"')
                all_files.update({p: (Path(root) / p).read_text() for p in files})
                apply_files(root, {p: (Path(root) / p).read_text() for p in files}, dry_run=dry_run)
                break

            if not any(p.endswith(".go") for p in files):
                all_files.update(files)
                apply_files(root, files, dry_run=dry_run)
                break

            print("\n═══ REVIEWER ═══")
            review = run_reviewer(root, files, dry_run=dry_run, api_key=ANTHROPIC_API_KEY)
            if review["approved"]:
                print("  APPROVED")
                all_files.update(files)
                apply_files(root, files, dry_run=dry_run)
                break
            print("  REQUEST_CHANGES")
            print("\n--- Feedback ---")
            fb = review["feedback"]
            print(fb[:600] + ("..." if len(fb) > 600 else ""))
            iteration += 1
            if iteration >= MAX_ITERATIONS:
                choice = _prompt("Max retries. [a]pprove anyway / [q]uit", "aq")
                if choice == "a":
                    all_files.update(files)
                    apply_files(root, files, dry_run=dry_run)
                break
            choice = _prompt("[c]ontinue (retry coder) / [e]dit files / [a]pprove anyway", "cea")
            if choice == "a":
                all_files.update(files)
                apply_files(root, files, dry_run=dry_run)
                break
            if choice == "e":
                editor = os.environ.get("EDITOR", "nano")
                for path, content in files.items():
                    full = Path(root) / path
                    full.parent.mkdir(parents=True, exist_ok=True)
                    full.write_text(content, encoding="utf-8")
                os.system(f'{editor} "{Path(root) / list(files.keys())[0]}"')
                all_files.update({p: (Path(root) / p).read_text() for p in files})
                files = {p: (Path(root) / p).read_text() for p in files}
            review_feedback = review["feedback"]

    if not all_files:
        print("No files written")
        return 0

    print("\n═══ DEVOPS ═══")
    result = run_devops(root, all_files, dry_run=dry_run)
    if result.get("ok"):
        print("  Done:", result.get("message", ""))
    else:
        print("  Error:", result.get("message", ""))
        return 1
    print("\n✓ Pipeline completed successfully")
    return 0


def cmd_init(path: Path) -> int:
    path = path.resolve()
    arch = path / "ARCHITECTURE.md"
    validate = path / "scripts" / "validate.sh"
    created = []
    if not arch.exists():
        arch.parent.mkdir(parents=True, exist_ok=True)
        arch.write_text(ARCHITECTURE_TEMPLATE, encoding="utf-8")
        created.append(str(arch))
    validate.parent.mkdir(parents=True, exist_ok=True)
    if not validate.exists():
        validate.write_text(VALIDATE_TEMPLATE, encoding="utf-8")
        validate.chmod(0o755)
        created.append(str(validate))
    if created:
        logger.info("Created: %s", ", ".join(created))
    else:
        logger.info("Files already exist in %s", path)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph coding pipeline")
    parser.add_argument(
        "requirement",
        nargs="?",
        default="",
        help="Task or requirement; use 'init [path]' to scaffold",
    )
    parser.add_argument(
        "extra",
        nargs="?",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--dry-run", action="store_true", default=DRY_RUN)
    parser.add_argument("--root-dir", default=ROOT_DIR)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--no-stream", action="store_true")
    parser.add_argument("--interactive", "-i", action="store_true", help="Step-by-step with prompts")
    args = parser.parse_args()

    if args.requirement == "init":
        target = Path(args.extra or args.root_dir or ".").resolve()
        sys.exit(cmd_init(target))

    req = args.requirement
    if not req and len(sys.argv) > 1 and sys.argv[1] == "run":
        req = " ".join(sys.argv[2:])
    if not req:
        parser.error("Requirement is required. Usage: pipeline \"Your task\" or pipeline run \"Your task\"")
        return

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    try:
        if args.interactive:
            sys.exit(_run_interactive(args, req))
        if args.no_stream:
            result = run_graph(
                requirement=req,
                root_dir=args.root_dir,
                dry_run=args.dry_run,
                api_key=ANTHROPIC_API_KEY,
            )
        else:
            result = _run_streaming(args, req)
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        sys.exit(1)

    if not result:
        sys.exit(1)

    issues = result.get("review_issues", [])
    if issues:
        logger.error("Review did not approve:\n%s", issues[0] if issues else "")
        sys.exit(1)

    print("\n✓ Pipeline completed successfully")
