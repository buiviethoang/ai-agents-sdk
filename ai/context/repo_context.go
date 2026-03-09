package context

import (
	stdctx "context"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type FileContent struct {
	Path    string
	Content string
}

type RepoContext struct {
	Architecture string
	Files       []FileContent
}

type Extractor struct {
	MaxFiles int
}

func NewExtractor(maxFiles int) *Extractor {
	if maxFiles <= 0 {
		maxFiles = 15
	}
	return &Extractor{MaxFiles: maxFiles}
}

func (e *Extractor) Extract(ctx stdctx.Context, rootDir, feature string) (*RepoContext, error) {
	arch, _ := os.ReadFile(filepath.Join(rootDir, "ARCHITECTURE.md"))
	rc := &RepoContext{
		Architecture: string(arch),
		Files:       e.findRelevantFiles(ctx, rootDir, feature),
	}
	return rc, nil
}

type scoredFile struct {
	path    string
	content string
	score   int
}

func (e *Extractor) findRelevantFiles(ctx stdctx.Context, rootDir, feature string) []FileContent {
	keywords := extractKeywords(feature)
	var candidates []scoredFile

	_ = filepath.Walk(rootDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		select {
		case <-ctx.Done():
			return stdctx.Canceled
		default:
		}
		if info.IsDir() {
			if info.Name() == "vendor" || info.Name() == ".git" || strings.HasPrefix(info.Name(), ".") {
				return filepath.SkipDir
			}
			return nil
		}
		if filepath.Ext(path) != ".go" {
			return nil
		}
		rel, _ := filepath.Rel(rootDir, path)
		content, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		score := matchScore(string(content), rel, keywords)
		candidates = append(candidates, scoredFile{path: rel, content: string(content), score: score})
		return nil
	})

	return selectTopFiles(candidates, e.MaxFiles)
}

func extractKeywords(feature string) []string {
	f := strings.ToLower(feature)
	var k []string
	for _, w := range strings.Fields(f) {
		if len(w) > 2 && w != "the" && w != "and" && w != "for" && w != "with" {
			k = append(k, w)
		}
	}
	return k
}

func matchScore(content, path string, keywords []string) int {
	lower := strings.ToLower(content + " " + path)
	score := 0
	for _, kw := range keywords {
		if strings.Contains(lower, kw) {
			score++
		}
	}
	return score
}

func selectTopFiles(candidates []scoredFile, max int) []FileContent {
	sort.Slice(candidates, func(i, j int) bool {
		return candidates[i].score > candidates[j].score
	})
	var out []FileContent
	for i, c := range candidates {
		if i >= max {
			break
		}
		out = append(out, FileContent{Path: c.path, Content: c.content})
	}
	return out
}
