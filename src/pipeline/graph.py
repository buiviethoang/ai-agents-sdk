"""LangGraph pipeline: Architect -> Coder -> Reviewer -> DevOps."""
import logging
from pathlib import Path


from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from pipeline.config import MAX_FILES, MAX_ITERATIONS, ROOT_DIR
from pipeline.llm.client import get_model
from pipeline.nodes.architect import make_architect_node
from pipeline.nodes.coder import make_coder_node
from pipeline.nodes.devops import make_devops_node
from pipeline.nodes.reviewer import make_reviewer_node
from pipeline.state import PipelineState

logger = logging.getLogger(__name__)


def has_go_files(files: dict[str, str]) -> bool:
    return any(Path(p).suffix == ".go" for p in files)


def route_after_coder(state: PipelineState) -> str:
    files = state.get("files", {})
    if not files:
        return "devops"
    if has_go_files(files):
        return "reviewer"
    return "devops"


def route_after_reviewer(state: PipelineState) -> str:
    issues = state.get("review_issues", [])
    iteration = state.get("iteration", 0)
    if issues and iteration < MAX_ITERATIONS:
        return "coder"
    if issues:
        return "__end__"
    return "devops"


def route_after_devops(state: PipelineState) -> str:
    tasks = state.get("tasks", [])
    idx = state.get("current_task_idx", 0)
    if idx < len(tasks):
        return "coder"
    return "__end__"


def build_graph(
    root_dir: str = ROOT_DIR,
    dry_run: bool = False,
    api_key: str = "",
):
    model = get_model(api_key=api_key)

    graph_builder = StateGraph(PipelineState)

    graph_builder.add_node("architect", make_architect_node(model))
    graph_builder.add_node(
        "coder",
        make_coder_node(model, root_dir, MAX_FILES),
    )
    graph_builder.add_node("reviewer", make_reviewer_node(model, root_dir))
    graph_builder.add_node("devops", make_devops_node(root_dir, dry_run))

    graph_builder.add_edge(START, "architect")
    graph_builder.add_edge("architect", "coder")
    graph_builder.add_conditional_edges(
        "coder",
        route_after_coder,
        path_map={"reviewer": "reviewer", "devops": "devops"},
    )
    graph_builder.add_conditional_edges(
        "reviewer",
        route_after_reviewer,
        path_map={"coder": "coder", "devops": "devops", "__end__": END},
    )
    graph_builder.add_conditional_edges(
        "devops",
        route_after_devops,
        path_map={"coder": "coder", "__end__": END},
    )

    checkpointer = MemorySaver()
    return graph_builder.compile(checkpointer=checkpointer)


def run_graph(
    requirement: str,
    root_dir: str = ROOT_DIR,
    dry_run: bool = False,
    thread_id: str = "default",
    api_key: str = "",
) -> PipelineState:
    graph = build_graph(root_dir, dry_run, api_key)
    config = {"configurable": {"thread_id": thread_id}}
    initial: PipelineState = {
        "requirement": requirement,
        "root_dir": root_dir,
        "dry_run": dry_run,
    }
    return graph.invoke(initial, config)


def _format_step(node: str, data: dict) -> str:
    name = node.upper().replace("_", " ")
    if node == "architect" and data.get("plan_md"):
        tasks = data.get("tasks", [])
        return f"\n═══ {name} ═══\n  Plan: {len(data['plan_md'])} chars, {len(tasks)} tasks\n"
    if node == "coder" and data.get("files"):
        return f"\n═══ {name} ═══\n  Produced {len(data['files'])} files\n"
    if node == "reviewer":
        issues = data.get("review_issues", [])
        status = "APPROVED" if not issues else "REQUEST_CHANGES"
        return f"\n═══ {name} ═══\n  {status}\n"
    if node == "devops":
        return f"\n═══ {name} ═══\n  Format, lint, test, push\n"
    return f"\n═══ {name} ═══\n"


def run_graph_stream(
    requirement: str,
    root_dir: str = ROOT_DIR,
    dry_run: bool = False,
    thread_id: str = "default",
    api_key: str = "",
    stream_tokens: bool = True,
):
    graph = build_graph(root_dir, dry_run, api_key)
    config = {"configurable": {"thread_id": thread_id}}
    initial: PipelineState = {
        "requirement": requirement,
        "root_dir": root_dir,
        "dry_run": dry_run,
    }
    modes = ["updates", "custom"]
    if stream_tokens:
        modes.append("messages")

    final = None
    try:
        for chunk in graph.stream(
            initial,
            config,
            stream_mode=modes,
            version="v2",
        ):
            t = chunk.get("type")
            data = chunk.get("data")
            if t == "updates":
                for node, node_data in data.items():
                    yield ("step", node, node_data)
            elif t == "custom" and isinstance(data, dict):
                yield ("progress", data.get("step", ""), data)
            elif t == "messages":
                msg, meta = data
                if msg.content:
                    yield ("token", meta.get("langgraph_node", ""), msg.content)
        snapshot = graph.get_state(config)
        final = snapshot.values if snapshot and getattr(snapshot, "values", None) else None
    except Exception:
        raise
    yield ("done", None, final)
