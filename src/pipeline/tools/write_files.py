"""Write files to disk."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_files(root_dir: str, files: dict[str, str], dry_run: bool = False) -> None:
    if dry_run:
        logger.info("[WRITE] dry-run: would write %d files", len(files))
        return
    for path, content in files.items():
        full = Path(root_dir) / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        logger.info("[WRITE] %s", path)
