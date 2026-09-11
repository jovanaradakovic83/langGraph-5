"""
Single-pass node test — Phase 4

Runs Node 1 → Node 2 → Node 3 sequentially with a mock state.
No graph or loop — just confirms each node works in isolation
and that state is passed correctly between them.

Run from pipeline/:
    python3 test_nodes.py
"""

import sys
from pathlib import Path

# Allow running from inside pipeline/ — adds langGraph-5/ to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from pipeline.state import PipelineState
from pipeline.nodes.context_retrieval import context_retrieval_node
from pipeline.nodes.coding_agent import coding_agent_node
from pipeline.nodes.qa_reviewer import qa_reviewer_node

# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

ISSUE = (
    "Add a JWT-based session expiration middleware with auto-refresh functionality. "
    "The middleware should check if the access token is close to expiry (within 5 minutes) "
    "on every authenticated request, and silently refresh it using the refresh token "
    "before continuing. If the refresh token is also expired, redirect to /login."
)

state: PipelineState = {
    "issue": ISSUE,
    "search_queries": [],
    "rag_context": "",
    "code_draft": "",
    "files_touched": [],
    "review_status": "pending",
    "review_feedback": [],
    "iteration_count": 0,
    "max_iterations": 3,
    "pr_description": "",
}

DIVIDER = "\n" + "=" * 70 + "\n"

# ---------------------------------------------------------------------------
# Node 1 — Context Retrieval
# ---------------------------------------------------------------------------

print(DIVIDER)
print("RUNNING NODE 1 — Context Retrieval")
print(DIVIDER)

result_1 = context_retrieval_node(state)
state.update(result_1)

print(f"\nSearch queries generated: {state['search_queries']}")
print(f"\nRAG context preview (first 500 chars):\n{state['rag_context'][:500]}...")

# ---------------------------------------------------------------------------
# Node 2 — Coding Agent
# ---------------------------------------------------------------------------

print(DIVIDER)
print("RUNNING NODE 2 — Coding Agent")
print(DIVIDER)

result_2 = coding_agent_node(state)
state.update(result_2)

print(f"\nFiles touched: {state['files_touched']}")
print(f"\nCode draft preview (first 600 chars):\n{state['code_draft'][:600]}...")

# ---------------------------------------------------------------------------
# Node 3 — QA Reviewer
# ---------------------------------------------------------------------------

print(DIVIDER)
print("RUNNING NODE 3 — QA Reviewer")
print(DIVIDER)

result_3 = qa_reviewer_node(state)
state.update(result_3)

print(f"\nReview status : {state['review_status'].upper()}")
print(f"Feedback items: {len(state['review_feedback'])}")
for item in state["review_feedback"]:
    print(f"  • {item}")

# ---------------------------------------------------------------------------
# Final state summary
# ---------------------------------------------------------------------------

print(DIVIDER)
print("FINAL STATE SUMMARY")
print(DIVIDER)
print(f"  issue            : {state['issue'][:80]}...")
print(f"  search_queries   : {state['search_queries']}")
print(f"  rag_context      : {len(state['rag_context'])} chars")
print(f"  files_touched    : {state['files_touched']}")
print(f"  code_draft       : {len(state['code_draft'])} chars")
print(f"  review_status    : {state['review_status']}")
print(f"  review_feedback  : {len(state['review_feedback'])} item(s)")
print(f"  iteration_count  : {state['iteration_count']}")
print()
