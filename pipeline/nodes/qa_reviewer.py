"""
Node 3 — QA Reviewer (Tech Lead / Security Reviewer)

Evaluates the code draft against a fixed checklist and returns
a Pass/Fail status with a list of requested changes.
"""

import json
import re
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from pipeline.state import PipelineState

# ---------------------------------------------------------------------------
# LLM + prompt setup
# ---------------------------------------------------------------------------

llm = ChatOllama(model="llama3.1", temperature=0.1)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "qa_reviewer.md"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_review_response(text: str) -> tuple[str, list[str]]:
    """
    Extract status and feedback list from the LLM response.
    Expects a JSON object; falls back gracefully if the LLM adds extra text.
    Returns (status, feedback_list).
    """
    # Try to find a JSON object anywhere in the response
    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            status = str(data.get("status", "fail")).lower().strip()
            feedback = data.get("feedback", [])
            if not isinstance(feedback, list):
                feedback = [str(feedback)]
            return status, [str(f) for f in feedback]
        except json.JSONDecodeError:
            pass

    # Fallback: if the LLM didn't return valid JSON, treat as fail
    print("[Node 3] Warning: could not parse JSON response — defaulting to fail")
    return "fail", ["Reviewer response could not be parsed — please retry"]


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

def qa_reviewer_node(state: PipelineState) -> dict:
    """
    Node 3 — evaluates the code draft and updates review_status
    and review_feedback in the state.
    Note: iteration_count is incremented by the coding_agent_node,
    not here, to avoid double-counting.
    """
    iteration = state.get("iteration_count", 1)
    print(f"\n[Node 3] QA Reviewer — evaluating code (iteration {iteration})...")

    user_message = "\n\n---\n\n".join([
        f"## Feature Request\n{state['issue']}",
        f"## Existing Codebase Patterns (for architecture consistency check)\n{state['rag_context']}",
        f"## Proposed Code\n{state['code_draft']}",
    ])

    messages = [
        SystemMessage(content=_load_system_prompt()),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    status, new_feedback = _parse_review_response(response.content)

    # Accumulate feedback across iterations so the coding agent has full history
    existing_feedback = state.get("review_feedback", [])
    accumulated_feedback = existing_feedback + new_feedback

    print(f"[Node 3] Status: {status.upper()}")
    if new_feedback:
        for item in new_feedback:
            print(f"  • {item}")

    return {
        "review_status": status,
        "review_feedback": accumulated_feedback,
    }
