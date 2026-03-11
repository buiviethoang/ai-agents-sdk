"""CLI entry point for the pipeline."""
import argparse
import logging
import sys

from pipeline.config import ANTHROPIC_API_KEY, DRY_RUN, ROOT_DIR
from pipeline.graph import run_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="LangGraph coding pipeline")
    parser.add_argument(
        "requirement",
        nargs="?",
        default="",
        help="Task or requirement to implement",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=DRY_RUN,
        help="Skip writing files and validation",
    )
    parser.add_argument(
        "--root-dir",
        default=ROOT_DIR,
        help="Project root (default: cwd)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )
    args = parser.parse_args()

    req = args.requirement
    if not req and len(sys.argv) > 1 and sys.argv[1] == "run":
        req = " ".join(sys.argv[2:])
    if not req:
        parser.error("Requirement is required")
        return

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set")
        sys.exit(1)

    try:
        result = run_graph(
            requirement=req,
            root_dir=args.root_dir,
            dry_run=args.dry_run,
            api_key=ANTHROPIC_API_KEY,
        )
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        sys.exit(1)

    issues = result.get("review_issues", [])
    if issues:
        logger.error("Review did not approve:\n%s", issues[0] if issues else "")
        sys.exit(1)

    logger.info("Pipeline completed successfully")
