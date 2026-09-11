"""
Node 2 — Coding Agent (Senior Developer)

Reads the feature request, RAG-retrieved codebase context, and any
prior review feedback, then writes the implementation.
"""

import re
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from pipeline.state import PipelineState

# ---------------------------------------------------------------------------
# LLM + prompt setup
# ---------------------------------------------------------------------------

llm = ChatOllama(model="llama3.1", temperature=0.2)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "coding_agent.md"


def _load_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def _parse_files_touched(response_text: str) -> list[str]:
    """Extract the list of file paths from the FILES TOUCHED section."""
    match = re.search(r"FILES TOUCHED:\s*(.*?)\s*CODE:", response_text, re.DOTALL)
    if not match:
        return []
    lines = match.group(1).strip().splitlines()
    return [line.strip("- \t") for line in lines if line.strip("- \t")]


def _parse_code_draft(response_text: str) -> str:
    """Return the full CODE section as-is for the reviewer to evaluate."""
    match = re.search(r"(CODE:.*)", response_text, re.DOTALL)
    return match.group(1).strip() if match else response_text.strip()


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

def coding_agent_node(state: PipelineState) -> dict:
    """
    Node 2 — writes or revises the implementation based on the issue,
    RAG context, and any accumulated review feedback.
    """
    iteration = state.get("iteration_count", 0) + 1
    print(f"\n[Node 2] Coding Agent — writing implementation (iteration {iteration})...")

    # Build the user message
    parts = [
        f"## Feature Request\n{state['issue']}",
        f"## Existing Codebase Context (retrieved via RAG)\n{state['rag_context']}",
    ]

    feedback = state.get("review_feedback", [])
    if feedback:
        feedback_block = "\n".join(f"- {item}" for item in feedback)
        parts.append(
            f"## Previous Review Feedback (you must address all of these)\n{feedback_block}"
        )

    user_message = "\n\n---\n\n".join(parts)

    messages = [
        SystemMessage(content=_load_system_prompt()),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    response_text = response.content

    files_touched = _parse_files_touched(response_text)
    code_draft = _parse_code_draft(response_text)

    print(f"[Node 2] Files touched: {files_touched}")

    return {
        "code_draft": code_draft,
        "files_touched": files_touched,
        "iteration_count": iteration,
    }
