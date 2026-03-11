"""Run golangci-lint."""
import logging
import subprocess

logger = logging.getLogger(__name__)


def run_golangci_lint(root_dir: str, timeout: int = 120) -> str:
    try:
        result = subprocess.run(
            ["golangci-lint", "run"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return "golangci-lint: passed"
        return result.stdout or result.stderr or "golangci-lint failed"
    except FileNotFoundError:
        logger.warning("golangci-lint not found")
        return "golangci-lint not installed"
    except subprocess.TimeoutExpired:
        return "golangci-lint timeout"
    except Exception as e:
        return f"golangci-lint error: {e}"
