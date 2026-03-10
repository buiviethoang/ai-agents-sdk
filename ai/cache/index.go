package cache

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
)

type entry struct {
	Mtime   int64  `json:"mtime"`
	Hash    string `json:"hash"`
	Content string `json:"content"`
}

type Index struct {
	path string
	data map[string]entry
}

func New(dir string) *Index {
	idx := &Index{data: make(map[string]entry)}
	if dir != "" {
		idx.path = filepath.Join(dir, ".ai-agents-cache", "index.json")
		_ = idx.load()
	}
	return idx
}

func hashContent(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

func (idx *Index) load() error {
	if idx.path == "" {
		return nil
	}
	b, err := os.ReadFile(idx.path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	return json.Unmarshal(b, &idx.data)
}

func (idx *Index) save() error {
	if idx.path == "" || len(idx.data) == 0 {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(idx.path), 0755); err != nil {
		return err
	}
	b, err := json.Marshal(idx.data)
	if err != nil {
		return err
	}
	return os.WriteFile(idx.path, b, 0644)
}

func (idx *Index) Get(relPath string, mtime int64) (string, bool) {
	if idx.data == nil {
		idx.data = make(map[string]entry)
		_ = idx.load()
	}
	e, ok := idx.data[relPath]
	if !ok || e.Mtime != mtime {
		return "", false
	}
	return e.Content, true
}

func (idx *Index) Put(relPath string, mtime int64, content string) error {
	h := hashContent([]byte(content))
	if idx.data == nil {
		idx.data = make(map[string]entry)
		_ = idx.load()
	}
	idx.data[relPath] = entry{Mtime: mtime, Hash: h, Content: content}
	return idx.save()
}
