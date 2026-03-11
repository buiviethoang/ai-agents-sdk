"""Run validate.sh (go fmt, vet, lint, test)."""
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def run_validate(root_dir: str, script_path: str | None = None, timeout: int = 300) -> tuple[bool, str]:
    root = Path(root_dir)
    script = Path(script_path) if script_path else root / "scripts" / "validate.sh"
    if not script.exists():
        return False, f"validate script not found: {script}"
    try:
        result = subprocess.run(
            ["bash", str(script)],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout or "passed"
        return False, result.stderr or result.stdout or "validation failed"
    except subprocess.TimeoutExpired:
        return False, "validation timeout"
    except Exception as e:
        return False, str(e)
