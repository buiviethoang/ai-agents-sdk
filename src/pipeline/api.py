"""Standalone pipeline operations for MCP and interactive mode."""
import logging

from pipeline.config import MAX_FILES
from pipeline.extractor import extract
from pipeline.llm.client import get_model
from pipeline.llm.claude import send
from pipeline.nodes.architect import parse_plan_tasks
from pipeline.nodes.coder import (
    format_files,
    parse_file_blocks,
    SYSTEM_TEMPLATE,
    USER_TEMPLATE,
)
from pipeline.nodes.reviewer import parse_verdict, SYSTEM as REVIEWER_SYSTEM
from pipeline.tools.gosec import run_gosec
from pipeline.tools.write_files import write_files
from pipeline.tools.validate import run_validate
from pipeline.tools.git_push import git_push

logger = logging.getLogger(__name__)


def run_architect(requirement: str, api_key: str = "") -> dict:
    """Return plan_md and tasks."""
    model = get_model(api_key=api_key)
    user = f"Requirement:\n{requirement}"
    resp = send(model, _architect_system(), user)
    plan_md, tasks = parse_plan_tasks(resp)
    return {"plan_md": plan_md, "tasks": tasks}


def _architect_system() -> str:
    return """You are a senior Go engineer acting as architect.

Given a requirement, produce:
1. A plan (markdown) with architecture notes and approach.
2. A JSON array of tasks. Each task: {"id": "T1", "description": "...", "target_files": ["path/to/file.go"]}

Output format:
<<PLAN>>
...markdown plan...
<<END_PLAN>>
<<TASKS>>
[{"id": "T1", "description": "...", "target_files": ["..."]}, ...]
<<END_TASKS>>"""


def run_coder(
    root_dir: str,
    task_desc: str,
    plan_md: str,
    existing_files: dict[str, str] | None = None,
    review_feedback: str = "",
    api_key: str = "",
    max_files: int = MAX_FILES,
) -> dict[str, str]:
    """Implement one task, return files dict."""
    model = get_model(api_key=api_key)
    if existing_files:
        files_list = [(p, c) for p, c in existing_files.items()]
    else:
        _, files_list = extract(root_dir, task_desc, max_files)
    if not plan_md:
        plan_md, _ = extract(root_dir, task_desc, 1)

    feedback = ""
    if review_feedback:
        feedback = f"\n\nReviewer feedback to address:\n{review_feedback}"

    files_str = format_files(files_list)
    system = SYSTEM_TEMPLATE.format(plan_md=plan_md)
    user = USER_TEMPLATE.format(
        task_desc=task_desc,
        files_str=files_str,
        feedback=feedback,
    )
    resp = send(model, system, user)
    return parse_file_blocks(resp)


def run_reviewer(
    root_dir: str,
    files: dict[str, str],
    dry_run: bool = False,
    api_key: str = "",
) -> dict:
    """Review files. Returns approved, feedback."""
    model = get_model(api_key=api_key)
    write_files(root_dir, files, dry_run=dry_run)
    gosec_out = run_gosec(root_dir)
    files_str = "\n".join(f"\n--- {p} ---\n{c}" for p, c in files.items())
    user = f"gosec output:\n{gosec_out}\n\nCode to review:\n{files_str}"
    resp = send(model, REVIEWER_SYSTEM, user)
    passed, feedback = parse_verdict(resp)
    return {"approved": passed, "feedback": feedback}


def apply_files(root_dir: str, files: dict[str, str], dry_run: bool = False) -> list[str]:
    """Write files to disk. Returns list of paths written."""
    write_files(root_dir, files, dry_run=dry_run)
    return list(files.keys())


def run_devops(root_dir: str, files: dict[str, str], dry_run: bool = False) -> dict:
    """Format, lint, test, git push."""
    write_files(root_dir, files, dry_run=dry_run)
    if not files:
        return {"ok": True, "message": "No files to process"}

    if dry_run:
        return {"ok": True, "message": "dry-run"}

    import subprocess
    try:
        r = subprocess.run(
            ["go", "fmt", "./..."],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if r.returncode != 0:
            return {"ok": False, "message": f"go fmt: {r.stderr or r.stdout}"}
    except Exception as e:
        return {"ok": False, "message": str(e)}

    ok, msg = run_validate(root_dir)
    if not ok:
        return {"ok": False, "message": msg}

    ok, msg = git_push(root_dir, dry_run=False)
    return {"ok": ok, "message": msg}
