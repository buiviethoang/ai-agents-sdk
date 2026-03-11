"""Node B: Reviewer - gosec + LLM review."""
import logging

from langchain_core.language_models.chat_models import BaseChatModel

from pipeline.llm.claude import send
from pipeline.state import PipelineState
from pipeline.tools.gosec import run_gosec
from pipeline.tools.write_files import write_files

logger = logging.getLogger(__name__)

SYSTEM = """You are a strict Go reviewer.

Checklist:
- logical bugs
- race conditions
- missing edge cases
- incomplete tests

Use gosec output below. If problems: explain clearly and propose fixes.
If good: return APPROVED. If unsure: prefer REQUEST_CHANGES.

First line must be: VERDICT: APPROVED or VERDICT: REQUEST_CHANGES
Then list each finding (or "None"), then your verdict."""


def parse_verdict(resp: str) -> tuple[bool, str]:
    upper = resp.upper().strip()
    if "VERDICT: APPROVED" in upper:
        return True, ""
    if "VERDICT: REQUEST_CHANGES" in upper:
        return False, resp
    if "APPROVED" in upper[:50]:
        return True, ""
    if "REQUEST_CHANGES" in upper[:100]:
        return False, resp
    return False, resp


def make_reviewer_node(model: BaseChatModel, root_dir: str = "."):
    def reviewer(state: PipelineState) -> dict:
        files = state.get("files", {})
        root = state.get("root_dir", root_dir)
        dry_run = state.get("dry_run", False)

        logger.info("[REVIEWER] gosec + LLM review")

        write_files(root, files, dry_run=dry_run)
        gosec_out = run_gosec(root)
        files_str = "\n".join(
            f"\n--- {p} ---\n{c}" for p, c in files.items()
        )
        user = f"gosec output:\n{gosec_out}\n\nCode to review:\n{files_str}"

        resp = send(model, SYSTEM, user)
        passed, feedback = parse_verdict(resp)

        if passed:
            logger.info("[REVIEWER] APPROVED")
            return {"review_issues": [], "review_feedback": ""}
        logger.info("[REVIEWER] REQUEST_CHANGES")
        iteration = state.get("iteration", 0) + 1
        return {
            "review_issues": [feedback] if feedback else [],
            "review_feedback": feedback,
            "iteration": iteration,
        }

    return reviewer
