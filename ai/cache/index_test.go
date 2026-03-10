package cache

import (
	"os"
	"path/filepath"
	"testing"
)

func TestIndex_GetPut(t *testing.T) {
	dir := t.TempDir()
	idx := New(dir)

	content := "package pkg\n"
	rel := "pkg/foo.go"
	mtime := int64(12345)

	_, ok := idx.Get(rel, mtime)
	if ok {
		t.Error("Get before Put should miss")
	}

	err := idx.Put(rel, mtime, content)
	if err != nil {
		t.Fatal(err)
	}

	got, ok := idx.Get(rel, mtime)
	if !ok {
		t.Error("Get after Put should hit")
	}
	if got != content {
		t.Errorf("got %q, want %q", got, content)
	}

	_, ok = idx.Get(rel, mtime+1)
	if ok {
		t.Error("Get with different mtime should miss")
	}
}

func TestIndex_Persist(t *testing.T) {
	dir := t.TempDir()
	idx := New(dir)
	_ = idx.Put("a.go", 1, "content a")
	_ = idx.save()

	idx2 := New(dir)
	got, ok := idx2.Get("a.go", 1)
	if !ok {
		t.Error("loaded index should have entry")
	}
	if got != "content a" {
		t.Errorf("got %q, want %q", got, "content a")
	}
}

func TestIndex_EmptyDir(t *testing.T) {
	idx := New("")
	_ = idx.Put("x.go", 1, "x")
	err := idx.save()
	if err != nil {
		t.Fatal(err)
	}
	_, ok := idx.Get("x.go", 1)
	if !ok {
		t.Error("in-memory index should hit")
	}
}

func TestIndex_FileCreated(t *testing.T) {
	dir := t.TempDir()
	idx := New(dir)
	_ = idx.Put("b.go", 2, "content b")
	_ = idx.save()

	path := filepath.Join(dir, ".ai-agents-cache", "index.json")
	if _, err := os.Stat(path); os.IsNotExist(err) {
		t.Error("index.json should exist")
	}
}
