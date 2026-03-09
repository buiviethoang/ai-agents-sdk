package context

import (
	stdctx "context"
	"os"
	"path/filepath"
	"testing"
)

func TestExtractKeywords(t *testing.T) {
	tests := []struct {
		name     string
		feature  string
		wantMin  int
		hasRedis bool
	}{
		{"single", "Add Redis cache", 1, true},
		{"multi", "Add Redis cache to user API", 2, true},
		{"filter stopwords", "the and for", 0, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			k := extractKeywords(tt.feature)
			if len(k) < tt.wantMin {
				t.Errorf("got %d keywords, want at least %d", len(k), tt.wantMin)
			}
			if tt.hasRedis {
				found := false
				for _, w := range k {
					if w == "redis" {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("expected 'redis' in keywords, got %v", k)
				}
			}
		})
	}
}

func TestMatchScore(t *testing.T) {
	tests := []struct {
		content  string
		path     string
		keywords []string
		want     int
	}{
		{"redis cache", "foo.go", []string{"redis"}, 1},
		{"no match", "foo.go", []string{"bar"}, 0},
		{"redis cache", "redis/foo.go", []string{"redis", "cache"}, 2},
	}
	for _, tt := range tests {
		t.Run(tt.path, func(t *testing.T) {
			got := matchScore(tt.content, tt.path, tt.keywords)
			if got != tt.want {
				t.Errorf("matchScore() = %d, want %d", got, tt.want)
			}
		})
	}
}

func TestSelectTopFiles(t *testing.T) {
	tests := []struct {
		name       string
		candidates []scoredFile
		max        int
		wantLen    int
	}{
		{"under cap", []scoredFile{{"a", "", 1}, {"b", "", 2}}, 5, 2},
		{"over cap", []scoredFile{{"a", "", 1}, {"b", "", 2}, {"c", "", 3}}, 2, 2},
		{"empty", []scoredFile{}, 5, 0},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := selectTopFiles(tt.candidates, tt.max)
			if len(got) != tt.wantLen {
				t.Errorf("selectTopFiles() len = %d, want %d", len(got), tt.wantLen)
			}
		})
	}
}

func TestExtractor_Extract(t *testing.T) {
	dir := t.TempDir()
	archPath := filepath.Join(dir, "ARCHITECTURE.md")
	if err := os.WriteFile(archPath, []byte("# Arch\n"), 0644); err != nil {
		t.Fatal(err)
	}
	goPath := filepath.Join(dir, "pkg", "foo.go")
	if err := os.MkdirAll(filepath.Dir(goPath), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(goPath, []byte("package pkg\n"), 0644); err != nil {
		t.Fatal(err)
	}

	e := NewExtractor(5)
	rc, err := e.Extract(stdctx.Background(), dir, "foo bar")
	if err != nil {
		t.Fatal(err)
	}
	if rc.Architecture != "# Arch\n" {
		t.Errorf("Architecture = %q", rc.Architecture)
	}
	if len(rc.Files) == 0 {
		t.Error("expected at least one file")
	}
}
