package runner

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"

	"github.com/buiviethoang/ai-agents-sdk/ai/agents"
	repoc "github.com/buiviethoang/ai-agents-sdk/ai/context"
	"github.com/buiviethoang/ai-agents-sdk/ai/llm"
)

const maxIterations = 2

type Config struct {
	RootDir         string
	ValidateScript  string
	DryRun          bool
	CacheDir        string // enable file index; default: rootDir
	MaxCharsPerFile int    // truncate files over this; default: 8000
}

type Result struct {
	Approved      bool
	Files         map[string]string
	Iterations    int
	FinalFeedback string
}

type Runner struct {
	llmClient *llm.Client
	extractor *repoc.Extractor
	builder   *agents.Builder
	reviewer  *agents.Reviewer
}

func NewRunner(llmClient *llm.Client, maxFiles int) *Runner {
	return &Runner{
		llmClient: llmClient,
		extractor: repoc.NewExtractor(maxFiles),
		builder:   agents.NewBuilder(llmClient),
		reviewer:  agents.NewReviewer(llmClient),
	}
}

func (r *Runner) Execute(ctx context.Context, feature string, cfg Config) (Result, error) {
	rootDir := cfg.RootDir
	if rootDir == "" {
		rootDir, _ = os.Getwd()
	}
	validateScript := cfg.ValidateScript
	if validateScript == "" {
		validateScript = filepath.Join(rootDir, "scripts", "validate.sh")
	}
	cacheDir := cfg.CacheDir
	if cacheDir == "" {
		cacheDir = rootDir
	}
	r.extractor.CacheDir = cacheDir
	if cfg.MaxCharsPerFile > 0 {
		r.extractor.MaxCharsPerFile = cfg.MaxCharsPerFile
	}

	rc, err := r.extractor.Extract(ctx, rootDir, feature)
	if err != nil {
		return Result{}, err
	}

	filesForBuilder := rc.Files
	feedback := ""
	var files map[string]string

	for iter := 0; iter < maxIterations; iter++ {
		built, err := r.builder.Build(ctx, feature, rc.Architecture, filesForBuilder, feedback)
		if err != nil {
			return Result{}, fmt.Errorf("builder: %w", err)
		}
		files = built

		review, err := r.reviewer.Review(ctx, files)
		if err != nil {
			return Result{}, fmt.Errorf("reviewer: %w", err)
		}

		if review.Status == agents.Approved {
			if !cfg.DryRun {
				if err := r.writeFiles(rootDir, files); err != nil {
					return Result{}, err
				}
				if err := r.runValidate(rootDir, validateScript); err != nil {
					return Result{}, fmt.Errorf("validation failed: %w", err)
				}
			}
			return Result{
				Approved:   true,
				Files:      files,
				Iterations: iter + 1,
			}, nil
		}
		feedback = review.Feedback
		filesForBuilder = mapToFileContent(files)
	}

	return Result{
		Approved:      false,
		Files:         files,
		Iterations:    maxIterations,
		FinalFeedback: feedback,
	}, fmt.Errorf("review did not approve after %d iterations", maxIterations)
}

func (r *Runner) writeFiles(rootDir string, files map[string]string) error {
	for path, content := range files {
		fullPath := filepath.Join(rootDir, path)
		if err := os.MkdirAll(filepath.Dir(fullPath), 0755); err != nil {
			return err
		}
		if err := os.WriteFile(fullPath, []byte(content), 0644); err != nil {
			return err
		}
	}
	return nil
}

func mapToFileContent(files map[string]string) []repoc.FileContent {
	var out []repoc.FileContent
	for path, content := range files {
		out = append(out, repoc.FileContent{Path: path, Content: content})
	}
	return out
}

func (r *Runner) runValidate(rootDir, script string) error {
	cmd := exec.Command("bash", script)
	cmd.Dir = rootDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
