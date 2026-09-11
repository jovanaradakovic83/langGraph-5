"""
Graph routing test — Phase 5

Tests the conditional router (Node 4 — PR Gatekeeper) with mock states.
No LLM calls — just verifies the routing logic is correct.

Run from pipeline/:
    python3 test_graph.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.graph import route_after_review, graph

DIVIDER = "\n" + "=" * 60 + "\n"

# ---------------------------------------------------------------------------
# Test 1: Review FAILED, iterations below cap → should loop back
# ---------------------------------------------------------------------------

print(DIVIDER)
print("TEST 1 — FAIL + below cap → expect: coding_agent")
print(DIVIDER)

state_fail = {
    "issue": "test",
    "search_queries": [],
    "rag_context": "",
    "code_draft": "",
    "files_touched": [],
    "review_status": "fail",
    "review_feedback": ["Missing error handling"],
    "iteration_count": 1,
    "max_iterations": 3,
    "pr_description": "",
}

result = route_after_review(state_fail)
assert result == "coding_agent", f"Expected 'coding_agent', got '{result}'"
print(f"  ✅  Routed to: {result}")

# ---------------------------------------------------------------------------
# Test 2: Review PASSED → should exit to pr_publisher
# ---------------------------------------------------------------------------

print(DIVIDER)
print("TEST 2 — PASS → expect: pr_publisher")
print(DIVIDER)

state_pass = {**state_fail, "review_status": "pass", "review_feedback": []}
result = route_after_review(state_pass)
assert result == "pr_publisher", f"Expected 'pr_publisher', got '{result}'"
print(f"  ✅  Routed to: {result}")

# ---------------------------------------------------------------------------
# Test 3: FAILED but iteration cap reached → force to pr_publisher
# ---------------------------------------------------------------------------

print(DIVIDER)
print("TEST 3 — FAIL + cap reached → expect: pr_publisher (forced)")
print(DIVIDER)

state_cap = {**state_fail, "review_status": "fail", "iteration_count": 3}
result = route_after_review(state_cap)
assert result == "pr_publisher", f"Expected 'pr_publisher', got '{result}'"
print(f"  ✅  Routed to: {result}")

# ---------------------------------------------------------------------------
# Test 4: FAILED on final allowed iteration (iteration == max) → force through
# ---------------------------------------------------------------------------

print(DIVIDER)
print("TEST 4 — FAIL + iteration equals max → expect: pr_publisher (forced)")
print(DIVIDER)

state_at_cap = {**state_fail, "review_status": "fail", "iteration_count": 3, "max_iterations": 3}
result = route_after_review(state_at_cap)
assert result == "pr_publisher", f"Expected 'pr_publisher', got '{result}'"
print(f"  ✅  Routed to: {result}")

# ---------------------------------------------------------------------------
# Test 5: Verify graph structure
# ---------------------------------------------------------------------------

print(DIVIDER)
print("TEST 5 — Graph structure check")
print(DIVIDER)

expected_nodes = {"__start__", "context_retrieval", "coding_agent", "qa_reviewer", "pr_publisher"}
actual_nodes = set(graph.nodes.keys())
assert actual_nodes == expected_nodes, f"Node mismatch: {actual_nodes}"
print(f"  ✅  All nodes present: {sorted(actual_nodes)}")

print(DIVIDER)
print("ALL TESTS PASSED ✅")
print(DIVIDER)
