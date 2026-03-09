package main

import (
	"context"
	"flag"
	"fmt"
	"os"
	"strings"

	"github.com/buiviethoang/ai-agents-sdk/sdk"
)

func main() {
	dryRun := flag.Bool("dry-run", false, "skip writing files and validation")
	maxFiles := flag.Int("max-files", 15, "max files to include in context")
	maxTokens := flag.Int64("max-tokens", 4096, "max output tokens")
	flag.Parse()

	args := flag.Args()
	var feature string
	switch {
	case len(args) == 1:
		feature = args[0]
	case len(args) >= 2 && args[0] == "run":
		feature = strings.Join(args[1:], " ")
	default:
		fmt.Fprintf(os.Stderr, "Usage: ai-engineer \"<task>\"\n       ai-engineer run \"<task>\"\n")
		os.Exit(1)
	}

	ctx := context.Background()
	cfg := sdk.Config{
		DryRun:    *dryRun,
		MaxFiles:  *maxFiles,
		MaxTokens: *maxTokens,
	}
	result, err := sdk.Run(ctx, feature, cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		if !result.Approved && result.FinalFeedback != "" {
			fmt.Fprintf(os.Stderr, "Reviewer feedback: %s\n", result.FinalFeedback)
		}
		os.Exit(1)
	}

	fmt.Printf("Approved in %d iteration(s)\n", result.Iterations)
}
