"""Git add, commit, push."""
import logging
import subprocess

logger = logging.getLogger(__name__)


def git_push(root_dir: str, message: str = "ai-agent: apply changes", dry_run: bool = False) -> tuple[bool, str]:
    if dry_run:
        return True, "dry-run: git push skipped"
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=root_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=root_dir,
            capture_output=True,
            check=True,
        )
        result = subprocess.run(
            ["git", "push"],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return True, "git push succeeded"
        return False, result.stderr or result.stdout or "git push failed"
    except subprocess.CalledProcessError as e:
        return False, str(e.stderr) if e.stderr else str(e)
    except Exception as e:
        return False, str(e)
