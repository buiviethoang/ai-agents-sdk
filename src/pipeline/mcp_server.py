"""MCP server for Claude Code and Cursor."""
import json
import os

from mcp.server.fastmcp import FastMCP

from pipeline.api import (
    run_architect,
    run_coder,
    run_reviewer,
    apply_files,
    run_devops,
)
from pipeline.config import ANTHROPIC_API_KEY, ROOT_DIR

mcp = FastMCP(
    "ai-agents-pipeline",
    json_response=True,
)


@mcp.tool()
def pipeline_architect(requirement: str, root_dir: str = "") -> str:
    """Create architecture plan and task list from a requirement.

    Call this first for any coding task. Returns plan (markdown) and tasks (JSON array).
    """
    root = root_dir or os.environ.get("ROOT_DIR", os.getcwd())
    result = run_architect(requirement, api_key=ANTHROPIC_API_KEY)
    return json.dumps({
        "plan_md": result["plan_md"],
        "tasks": result["tasks"],
    }, indent=2)


@mcp.tool()
def pipeline_coder(
    root_dir: str,
    task_description: str,
    plan_md: str,
    existing_files: str = "{}",
    review_feedback: str = "",
) -> str:
    """Implement one task. Returns generated files as JSON {path: content}.

    existing_files: JSON object of path->content for context.
    review_feedback: Paste reviewer feedback to address (if retrying).
    """
    try:
        existing = json.loads(existing_files) if existing_files else {}
    except json.JSONDecodeError:
        existing = {}
    files = run_coder(
        root_dir=root_dir,
        task_desc=task_description,
        plan_md=plan_md,
        existing_files=existing if existing else None,
        review_feedback=review_feedback,
        api_key=ANTHROPIC_API_KEY,
    )
    return json.dumps(files, indent=2)


@mcp.tool()
def pipeline_review(root_dir: str, files_json: str, dry_run: bool = True) -> str:
    """Review Go code. Writes files before review (unless dry_run).

    Returns JSON: {approved: bool, feedback: str}.
    """
    try:
        files = json.loads(files_json)
    except json.JSONDecodeError:
        return json.dumps({"approved": False, "feedback": "Invalid files_json"})
    result = run_reviewer(root_dir, files, dry_run=dry_run, api_key=ANTHROPIC_API_KEY)
    return json.dumps(result)


@mcp.tool()
def pipeline_apply_files(root_dir: str, files_json: str, dry_run: bool = False) -> str:
    """Write generated files to disk.

    files_json: {path: content}. Returns list of paths written.
    """
    try:
        files = json.loads(files_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid files_json", "paths": []})
    paths = apply_files(root_dir, files, dry_run=dry_run)
    return json.dumps({"paths": paths, "dry_run": dry_run})


@mcp.tool()
def pipeline_devops(root_dir: str, files_json: str, dry_run: bool = False) -> str:
    """Format, lint, test, and git push. Writes files first.

    files_json: {path: content}. Returns {ok: bool, message: str}.
    """
    try:
        files = json.loads(files_json)
    except json.JSONDecodeError:
        return json.dumps({"ok": False, "message": "Invalid files_json"})
    result = run_devops(root_dir, files, dry_run=dry_run)
    return json.dumps(result)


def main() -> None:
    mcp.run(transport="stdio")
