"""Extract relevant Go files and architecture from repo."""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

STOP_WORDS = frozenset({"the", "and", "for", "with"})


def extract_keywords(feature: str) -> list[str]:
    words = feature.lower().split()
    return [w for w in words if len(w) > 2 and w not in STOP_WORDS]


def match_score(content: str, path: str, keywords: list[str]) -> int:
    lower = f"{content} {path}".lower()
    return sum(1 for kw in keywords if kw in lower)


def find_relevant_files(
    root_dir: str,
    feature: str,
    max_files: int = 15,
    max_chars_per_file: int = 8000,
) -> list[tuple[str, str]]:
    keywords = extract_keywords(feature)
    root = Path(root_dir)
    candidates: list[tuple[str, str, int]] = []

    for path in root.rglob("*.go"):
        parts = path.relative_to(root).parts
        if "vendor" in parts or ".git" in parts or any(
            p.startswith(".") for p in parts
        ):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file] + "\n// ... truncated"
        rel = str(path.relative_to(root))
        score = match_score(content, rel, keywords)
        candidates.append((rel, content, score))

    candidates.sort(key=lambda x: -x[2])
    return [(p, c) for p, c, _ in candidates[:max_files]]


def extract(root_dir: str, feature: str, max_files: int = 15, max_chars: int = 8000) -> tuple[str, list[tuple[str, str]]]:
    arch_path = Path(root_dir) / "ARCHITECTURE.md"
    arch = ""
    if arch_path.exists():
        arch = arch_path.read_text(encoding="utf-8", errors="ignore")

    files = find_relevant_files(root_dir, feature, max_files, max_chars)
    logger.info("[EXTRACTOR] arch=%d chars, %d files", len(arch), len(files))
    return arch, files
