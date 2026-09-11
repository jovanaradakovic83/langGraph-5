"""
Node 5 — PR Publisher

Reads the final pipeline state and generates a clean markdown PR description.
Saves it to pipeline/output/<timestamp>_pr.md.
"""

from datetime import datetime
from pathlib import Path

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from pipeline.state import PipelineState

# ---------------------------------------------------------------------------
# LLM + output directory setup
# ---------------------------------------------------------------------------

llm = ChatOllama(model="llama3.1", temperature=0.3)

OUTPUT_DIR = Path(__file__).parent.parent / "output"


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

def pr_publisher_node(state: PipelineState) -> dict:
    """
    Node 5 — generates a markdown PR description from the final state
    and writes it to the output/ directory.
    """
    print("\n[Node 5] PR Publisher — generating PR description...")

    iteration_count = state.get("iteration_count", 1)
    review_status = state.get("review_status", "unknown")
    files_touched = state.get("files_touched", [])
    forced = iteration_count >= state.get("max_iterations", 3) and review_status != "pass"

    files_list = "\n".join(f"- `{f}`" for f in files_touched) if files_touched else "- (no files recorded)"

    cap_note = (
        "\n> ⚠️ **Note:** This PR reached the maximum review iteration limit "
        f"({state.get('max_iterations', 3)}) without a clean pass. "
        "Manual review is strongly recommended before merging.\n"
        if forced else ""
    )

    user_message = f"""Generate a clean GitHub Pull Request description in markdown for the following implementation.

## Feature Request
{state["issue"]}

## Files Modified
{files_list}

## Implementation (code produced by the coding agent)
{state["code_draft"]}

## Codebase Context Used (from RAG)
{state["rag_context"]}

---

The PR description must include these sections:
1. **Summary** — one paragraph describing what was implemented and why
2. **Motivation** — the problem this solves
3. **Changes Made** — one bullet per file touched, with a brief description of what changed
4. **Implementation Reasoning** — explain key design decisions, referencing the existing codebase patterns found via RAG
5. **Testing Notes** — what should be tested manually or with automated tests
6. **QA Sign-off** — state that the code passed automated peer review in {iteration_count} iteration(s){" (forced through at iteration cap)" if forced else ""}

{cap_note}Write only the markdown PR description, no other commentary."""

    messages = [
        SystemMessage(content=(
            "You are a senior engineer writing a clear, professional GitHub Pull Request description. "
            "Use markdown. Be concise but thorough. Reference specific files and functions by name."
        )),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    pr_description = response.content.strip()

    # Save to output/
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_path = OUTPUT_DIR / f"{timestamp}_pr.md"
    output_path.write_text(pr_description, encoding="utf-8")

    print(f"[Node 5] PR description saved to: {output_path.name}")

    return {"pr_description": pr_description}
