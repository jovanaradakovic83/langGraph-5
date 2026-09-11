# langGraph-5 — Autonomous Feature Architect & PR Generator

A cyclic multi-agent LangGraph pipeline that takes a raw GitHub issue, cross-references an existing codebase via RAG, writes an implementation, autonomously peer-reviews it, and generates a production-ready PR description.

---

## Architecture

```
Issue
  │
  ▼
[Node 1] Context Retrieval (RAG Engine)
  │  Converts the issue into search queries, retrieves relevant
  │  code snippets from the indexed Next.js codebase via ChromaDB.
  ▼
[Node 2] Coding Agent (Senior Developer)
  │  Reads issue + RAG context (+ reviewer feedback on retries),
  │  writes or modifies the necessary files.
  ▼
[Node 3] QA Reviewer (Tech Lead / Security Reviewer)
  │  Evaluates code against security, architecture, error-handling,
  │  and TypeScript standards. Returns Pass/Fail + change requests.
  ▼
[Node 4] PR Gatekeeper (Conditional Router)
  │  FAIL + iterations < 3  ──► back to Node 2
  │  PASS or iterations ≥ 3 ──► Node 5
  ▼
[Node 5] PR Publisher
     Generates a clean markdown PR description with summary,
     files touched, implementation reasoning, and QA sign-off.
```

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph (cyclic graph, conditional edges) |
| LLM | Ollama — `llama3.1` (local, no API key) |
| Vector DB | ChromaDB (local, file-persisted) |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` |
| Sample codebase | Next.js 14 (TypeScript) |
| Language | Python 3.11+ |

---

## Project Structure

```
langGraph-5/
├── nextjs-app/              # Sample Next.js codebase indexed by RAG
│   └── src/
│       ├── middleware.ts
│       ├── types/index.ts
│       ├── lib/auth.ts
│       ├── lib/session.ts
│       ├── lib/db.ts
│       └── app/api/
│           ├── auth/[...nextauth]/route.ts
│           └── users/route.ts
│
└── pipeline/
    ├── state.py             # PipelineState TypedDict (shared graph state)
    ├── graph.py             # Graph assembly + conditional router
    ├── main.py              # CLI entry point
    ├── requirements.txt
    ├── nodes/
    │   ├── context_retrieval.py   # Node 1
    │   ├── coding_agent.py        # Node 2
    │   ├── qa_reviewer.py         # Node 3
    │   └── pr_publisher.py        # Node 5
    ├── rag/
    │   ├── indexer.py       # Index nextjs-app into ChromaDB
    │   └── retriever.py     # Query interface
    ├── prompts/
    │   ├── coding_agent.md
    │   └── qa_reviewer.md
    └── output/              # Generated PR descriptions (.md)
```

---

## Setup

```bash
cd pipeline

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Index the Next.js codebase (run once)
python3 -m rag.indexer

# Run the pipeline
python3 main.py
```

> **Note:** Always activate the virtual environment (`source venv/bin/activate`) before running any commands in a new terminal session.

> **Important:** The ChromaDB index (`rag/chroma_db/`) is gitignored and not committed. You must run `python3 -m rag.indexer` to build it before running the pipeline or `test_nodes.py`. Re-run the indexer any time you switch to a fresh branch or clone the repo.

---

## Testing Nodes in Isolation

Before running the full pipeline, you can verify each node works correctly with a single-pass test (Node 1 → Node 2 → Node 3, no loop):

```bash
cd pipeline
source venv/bin/activate
python3 test_nodes.py
```

This runs one coding → review iteration with the JWT middleware feature request and prints the output of each node. The ChromaDB index must exist first — run `python3 -m rag.indexer` if you haven't already.

> The `rag/chroma_db/` directory and `__pycache__/` folders are regenerated automatically and are gitignored — no need to commit them.

---

## Testing the Graph Router

To verify the conditional routing logic (Node 4 — PR Gatekeeper) without making any LLM calls:

```bash
cd pipeline
source venv/bin/activate
python3 test_graph.py
```

Tests 5 scenarios: fail below cap (loops back), pass (exits), fail at cap (forced through), and graph node structure check.

---

## Implementation Plan

For a per-phase breakdown of what was built and on which branch, see [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md).

---

## Build Progress

| Phase | Description | Status |
|---|---|---|
| 1 | Scaffold: folders, requirements.txt, state.py | ✅ Done |
| 2 | Next.js sample codebase (~6 files) | ✅ Done |
| 3 | RAG layer: indexer.py + retriever.py | ✅ Done |
| 4 | Nodes: context_retrieval, coding_agent, qa_reviewer, pr_publisher | ✅ Done |
| 5 | Graph assembly: graph.py with conditional router | ✅ Done |
| 6 | main.py + end-to-end test run | ✅ Done |
