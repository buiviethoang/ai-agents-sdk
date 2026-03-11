"""Node D: DevOps - format, lint, test, git push."""
import logging
import subprocess

from pipeline.state import PipelineState
from pipeline.tools.write_files import write_files
from pipeline.tools.validate import run_validate
from pipeline.tools.git_push import git_push

logger = logging.getLogger(__name__)


def run_fmt(root_dir: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["go", "fmt", "./..."],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return r.returncode == 0, r.stderr or r.stdout or ""
    except Exception as e:
        return False, str(e)


def make_devops_node(root_dir: str, dry_run: bool = False):
    def devops(state: PipelineState) -> dict:
        files = state.get("files", {})
        root = state.get("root_dir", root_dir)
        is_dry = state.get("dry_run", dry_run)

        logger.info("[DEVOPS] format, lint, test, push")

        write_files(root, files, dry_run=is_dry)
        if not files:
            return {}

        if not is_dry and files:
            ok, msg = run_fmt(root)
            if not ok:
                raise RuntimeError(f"go fmt failed: {msg}")

            ok, msg = run_validate(root)
            if not ok:
                raise RuntimeError(f"validation failed: {msg}")

            ok, msg = git_push(root, dry_run=False)
            if not ok:
                logger.warning("[DEVOPS] git push failed: %s", msg)

        idx = state.get("current_task_idx", 0)
        return {"current_task_idx": idx + 1}

    return devops
