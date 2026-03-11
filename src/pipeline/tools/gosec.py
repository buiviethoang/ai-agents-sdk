"""Run gosec security linter."""
import logging
import subprocess

logger = logging.getLogger(__name__)


def run_gosec(root_dir: str, timeout: int = 60) -> str:
    try:
        result = subprocess.run(
            ["gosec", "./...", "-fmt", "plain"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return "gosec: no issues"
        return result.stdout or result.stderr or "gosec failed"
    except FileNotFoundError:
        logger.warning("gosec not found, skipping")
        return "gosec not installed"
    except subprocess.TimeoutExpired:
        return "gosec timeout"
    except Exception as e:
        return f"gosec error: {e}"
