package agents

import (
	"testing"
)

func TestParseFileBlocks(t *testing.T) {
	tests := []struct {
		name   string
		resp   string
		want   map[string]string
	}{
		{
			name: "single block",
			resp: "path: foo/bar.go\n```go\npackage foo\n```",
			want: map[string]string{"foo/bar.go": "package foo"},
		},
		{
			name: "multiple blocks",
			resp: "path: a.go\n```\ncontent a\n```\npath: b.go\n```go\ncontent b\n```",
			want: map[string]string{"a.go": "content a", "b.go": "content b"},
		},
		{
			name: "no blocks",
			resp: "just text",
			want: map[string]string{},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := parseFileBlocks(tt.resp)
			if len(got) != len(tt.want) {
				t.Errorf("len = %d, want %d", len(got), len(tt.want))
			}
			for k, v := range tt.want {
				if got[k] != v {
					t.Errorf("got[%q] = %q, want %q", k, got[k], v)
				}
			}
		})
	}
}
