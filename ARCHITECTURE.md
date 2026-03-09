# Project Architecture

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
