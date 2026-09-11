# Implementation Plan

Brief per-phase breakdown of what was built and on which branch.

---

## Phase 1 — Scaffold
**Branch:** `feature/1-setup`

Create the project skeleton: directory structure for both `nextjs-app/` and `pipeline/`, `requirements.txt` with all Python dependencies (LangGraph, LangChain, Ollama, ChromaDB, sentence-transformers), and `state.py` defining the `PipelineState` TypedDict — the single shared object passed between all graph nodes.

---

## Phase 2 — Next.js Sample Codebase
**Branch:** `feature/2-Next.js-sample-codebase`

Write ~6 realistic TypeScript source files that simulate an existing production Next.js app. This is the codebase the RAG engine indexes. Files are intentionally incomplete in the JWT/session area (no expiry checks, no auto-refresh) to create a genuine gap for the feature request to fill. Includes: shared types, JWT utilities, session management, middleware, NextAuth route, and a users API route that establishes the project's error-handling convention.

---

## Phase 3 — RAG Layer
**Branch:** `feature/3-rag-implementation`

Implement `rag/indexer.py` — walks the `nextjs-app/src` tree, splits TypeScript files by export boundaries, embeds each chunk with `sentence-transformers/all-MiniLM-L6-v2`, and persists to a local ChromaDB collection. Implement `rag/retriever.py` — a clean query interface that accepts a search string and returns the top-k most relevant code snippets with file path metadata. Verify with a manual query before moving on.

---

## Phase 4 — Nodes
**Branch:** TBD

Implement all four LangGraph node functions:
- **Node 1** (`context_retrieval.py`) — calls the LLM to generate search queries from the issue, runs them through the retriever, assembles a formatted context block.
- **Node 2** (`coding_agent.py`) — Senior Developer persona; reads issue + RAG context + prior feedback; writes structured code output.
- **Node 3** (`qa_reviewer.py`) — Tech Lead persona; evaluates code against a fixed checklist (security, architecture consistency, error handling, TypeScript strictness); returns Pass/Fail + change list.
- **Node 5** (`pr_publisher.py`) — assembles the final markdown PR description from the full state and writes it to `output/`.

Also writes the two prompt files in `prompts/`.

---

## Phase 5 — Graph Assembly
**Branch:** TBD

Wire all nodes into a `StateGraph` in `graph.py`. Add the conditional edge (Node 4 — PR Gatekeeper): routes back to the Coding Agent on `fail` while `iteration_count < max_iterations`, otherwise forwards to the PR Publisher. Compile the graph.

---

## Phase 6 — End-to-End Test
**Branch:** TBD

Implement `main.py` CLI entry point. Run the full pipeline with the JWT middleware feature request. Observe the coding → review loop, verify the conditional router fires correctly, and inspect the generated PR description in `output/`.
