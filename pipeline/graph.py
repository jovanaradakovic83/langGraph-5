"""
Graph Assembly — Phase 5

Wires all nodes into a LangGraph StateGraph and defines the
conditional router (Node 4 — PR Gatekeeper).

Graph flow:
    START
      │
      ▼
    context_retrieval   (Node 1 — RAG Engine)
      │
      ▼
    coding_agent        (Node 2 — Senior Developer)
      │
      ▼
    qa_reviewer         (Node 3 — QA Reviewer)
      │
      ▼
    [PR Gatekeeper]     (Node 4 — conditional router)
      │
      ├── FAIL + iterations < max  ──► coding_agent  (loop back)
      │
      └── PASS  or  iterations >= max  ──► pr_publisher
                                                │
                                               END
"""

from langgraph.graph import StateGraph, END

from pipeline.state import PipelineState
from pipeline.nodes.context_retrieval import context_retrieval_node
from pipeline.nodes.coding_agent import coding_agent_node
from pipeline.nodes.qa_reviewer import qa_reviewer_node
from pipeline.nodes.pr_publisher import pr_publisher_node

# ---------------------------------------------------------------------------
# Node 4 — PR Gatekeeper (conditional router)
# ---------------------------------------------------------------------------

def route_after_review(state: PipelineState) -> str:
    """
    Decides where to route after the QA Reviewer runs.

    - Routes back to coding_agent if the review failed and we haven't
      hit the iteration cap yet.
    - Routes to pr_publisher if the review passed OR the cap is reached
      (forced through with a warning note in the PR description).
    """
    status = state.get("review_status", "fail")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 3)

    if status == "pass" or iteration_count >= max_iterations:
        if iteration_count >= max_iterations and status != "pass":
            print(
                f"\n[Node 4] ⚠️  Iteration cap reached ({max_iterations}). "
                "Routing to PR Publisher without a clean pass."
            )
        else:
            print(f"\n[Node 4] ✅ Review passed — routing to PR Publisher.")
        return "pr_publisher"

    print(
        f"\n[Node 4] 🔄 Review failed (iteration {iteration_count}/{max_iterations}) "
        "— routing back to Coding Agent."
    )
    return "coding_agent"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """Construct and compile the pipeline StateGraph."""

    builder = StateGraph(PipelineState)

    # Register nodes
    builder.add_node("context_retrieval", context_retrieval_node)
    builder.add_node("coding_agent", coding_agent_node)
    builder.add_node("qa_reviewer", qa_reviewer_node)
    builder.add_node("pr_publisher", pr_publisher_node)

    # Entry point
    builder.set_entry_point("context_retrieval")

    # Fixed edges
    builder.add_edge("context_retrieval", "coding_agent")
    builder.add_edge("coding_agent", "qa_reviewer")

    # Conditional edge — Node 4 PR Gatekeeper
    builder.add_conditional_edges(
        "qa_reviewer",
        route_after_review,
        {
            "coding_agent": "coding_agent",   # loop back
            "pr_publisher": "pr_publisher",   # exit loop
        },
    )

    # Terminal edge
    builder.add_edge("pr_publisher", END)

    return builder.compile()


# Compiled graph — imported by main.py
graph = build_graph()
