"""
CLI Entry Point — Phase 6

Runs the full autonomous feature architect pipeline:
    Issue → RAG Context → Code → Review loop → PR Description

Run from pipeline/:
    python3 main.py
"""

import sys
from pathlib import Path

# Allow running from inside pipeline/ — adds langGraph-5/ to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.graph import graph
from pipeline.state import PipelineState

DIVIDER = "=" * 70

DEFAULT_ISSUE = (
    "Add a JWT-based session expiration middleware with auto-refresh functionality. "
    "The middleware should check if the access token is close to expiry (within 5 minutes) "
    "on every authenticated request, and silently refresh it using the refresh token "
    "before continuing. If the refresh token is also expired, redirect to /login."
)


def main() -> None:
    print(f"\n{DIVIDER}")
    print("  Autonomous Feature Architect & PR Generator")
    print(f"{DIVIDER}\n")

    # Accept issue from CLI arg or prompt interactively
    if len(sys.argv) > 1:
        issue = " ".join(sys.argv[1:])
        print(f"Feature request (from args):\n  {issue}\n")
    else:
        print("Enter your GitHub issue / feature request.")
        print(f"(Press Enter to use the default JWT middleware example)\n")
        user_input = input("> ").strip()
        issue = user_input if user_input else DEFAULT_ISSUE
        print()

    # Build initial state
    initial_state: PipelineState = {
        "issue": issue,
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

    print(f"{DIVIDER}")
    print("  Starting pipeline...")
    print(f"{DIVIDER}")

    # Run the full graph
    final_state: PipelineState = graph.invoke(initial_state)

    # Summary
    print(f"\n{DIVIDER}")
    print("  Pipeline Complete")
    print(f"{DIVIDER}")
    print(f"  Iterations      : {final_state['iteration_count']}")
    print(f"  Review status   : {final_state['review_status'].upper()}")
    print(f"  Files touched   : {final_state['files_touched']}")

    if final_state["review_feedback"]:
        print(f"  Review feedback : {len(final_state['review_feedback'])} item(s) accumulated")

    # Locate the saved PR file
    output_dir = Path(__file__).parent / "output"
    pr_files = sorted(output_dir.glob("*_pr.md"), reverse=True)
    if pr_files:
        print(f"\n  PR description  : output/{pr_files[0].name}")
        print(f"\n{DIVIDER}")
        print("  PR Description Preview (first 800 chars)")
        print(DIVIDER)
        print(final_state["pr_description"][:800])
        if len(final_state["pr_description"]) > 800:
            print(f"\n  ... (see output/{pr_files[0].name} for full description)")
    else:
        print("\n  No PR file found in output/")

    print(f"\n{DIVIDER}\n")


if __name__ == "__main__":
    main()
