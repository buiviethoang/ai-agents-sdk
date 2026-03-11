"""Node A: Coder - implements task, outputs files."""
import logging
import re

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.config import get_stream_writer

from pipeline.extractor import extract
from pipeline.llm.claude import send
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)

SYSTEM_TEMPLATE = """You are a senior Go engineer.

Requirements:
- idiomatic Go
- table-driven tests
- use context.Context
- avoid global state
- change only what the task requires

Architecture:
{plan_md}

Output format for each file:
<<FILE path/to/file.go>>
...content...
<<END>>"""

USER_TEMPLATE = """Task {task_desc}

Relevant files:
{files_str}
{feedback}

Return updated/new files using <<FILE path>>...<<END>> format."""

FILE_BLOCK_RE = re.compile(r"<<FILE\s+([^\s>]+)>>\s*\n(.*?)<<END>>", re.DOTALL)
CODE_BLOCK_RE = re.compile(
    r"path:\s*([^\s\n]+)\s*\n```\w*\s*\n(.*?)```", re.DOTALL
)


def parse_file_blocks(resp: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in FILE_BLOCK_RE.finditer(resp):
        path, content = m.group(1).strip(), m.group(2).strip()
        if path:
            out[path] = content
    if not out:
        for m in CODE_BLOCK_RE.finditer(resp):
            path, content = m.group(1).strip(), m.group(2).strip()
            if path:
                out[path] = content
    return out


def format_files(files: list[tuple[str, str]]) -> str:
    return "\n".join(f"\n--- {p} ---\n{c}" for p, c in files)


def make_coder_node(
    model: BaseChatModel,
    root_dir: str,
    max_files: int = 15,
):
    def coder(state: PipelineState) -> dict:
        plan_md = state.get("plan_md", "")
        tasks = state.get("tasks", [])
        idx = state.get("current_task_idx", 0)
        review_feedback = state.get("review_feedback", "")
        root = state.get("root_dir", root_dir)

        if idx >= len(tasks):
            return {"files": {}}

        task = tasks[idx]
        desc = task.get("description", "implement")
        writer = get_stream_writer()
        if writer:
            writer({"step": "coder", "msg": f"Task {idx + 1}/{len(tasks)}: {desc[:50]}..."})
        logger.info("[CODER] task %d: %s...", idx, desc[:50] if desc else "")

        existing = state.get("files", {})
        if review_feedback and existing:
            files_list = [(p, c) for p, c in existing.items()]
        else:
            arch, files_list = extract(root, desc, max_files)
        if not plan_md:
            plan_md, _ = extract(root, desc, 1)

        feedback = ""
        if review_feedback:
            feedback = f"\n\nReviewer feedback to address:\n{review_feedback}"

        files_str = format_files(files_list)
        system = SYSTEM_TEMPLATE.format(plan_md=plan_md)
        user = USER_TEMPLATE.format(
            task_desc=desc,
            files_str=files_str,
            feedback=feedback,
        )

        resp = send(model, system, user)
        files = parse_file_blocks(resp)
        if writer:
            writer({"step": "coder", "msg": f"Produced {len(files)} files"})
        logger.info("[CODER] produced %d files", len(files))
        return {
            "files": files,
            "review_issues": [],
            "review_feedback": "",
        }

    return coder
