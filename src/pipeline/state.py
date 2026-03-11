"""Pipeline state schema."""
from typing import TypedDict


class PipelineState(TypedDict, total=False):
    requirement: str
    plan_md: str
    tasks: list[dict]
    current_task_idx: int
    files: dict[str, str]
    review_issues: list[str]
    review_feedback: str
    iteration: int
    root_dir: str
    dry_run: bool
