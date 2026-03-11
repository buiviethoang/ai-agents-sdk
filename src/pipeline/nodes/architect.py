"""Node C: Architect - plans and tasks from requirement."""
import json
import logging
import re

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.config import get_stream_writer

from pipeline.llm.claude import send
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)

SYSTEM = """You are a senior Go engineer acting as architect.

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


def parse_plan_tasks(response: str) -> tuple[str, list[dict]]:
    plan = ""
    tasks: list[dict] = []
    plan_match = re.search(r"<<PLAN>>\s*\n(.*?)<<END_PLAN>>", response, re.DOTALL)
    if plan_match:
        plan = plan_match.group(1).strip()
    tasks_match = re.search(r"<<TASKS>>\s*\n(.*?)<<END_TASKS>>", response, re.DOTALL)
    if tasks_match:
        try:
            tasks = json.loads(tasks_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    if not tasks:
        tasks = [{"id": "T1", "description": "Implement requirement", "target_files": []}]
    return plan, tasks


def make_architect_node(model: BaseChatModel):
    def architect(state: PipelineState) -> dict:
        req = state.get("requirement", "")
        writer = get_stream_writer()
        if writer:
            writer({"step": "architect", "msg": f"Planning for: {req[:60]}..."})
        logger.info("[ARCHITECT] planning for: %s...", req[:80] if req else "")
        user = f"Requirement:\n{req}"
        resp = send(model, SYSTEM, user)
        plan_md, tasks = parse_plan_tasks(resp)
        if writer:
            writer({"step": "architect", "msg": f"Plan ready: {len(tasks)} tasks"})
        logger.info("[ARCHITECT] plan %d chars, %d tasks", len(plan_md), len(tasks))
        return {
            "plan_md": plan_md,
            "tasks": tasks,
            "current_task_idx": 0,
            "iteration": 0,
        }

    return architect
