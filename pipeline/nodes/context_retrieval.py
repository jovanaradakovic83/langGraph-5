"""
Node 1 — Context Retrieval (RAG Engine)

Takes the feature request from state, asks the LLM to generate targeted
search queries, runs them through the codebase retriever, and appends the
relevant code context to the state.
"""

import json
import re

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from pipeline.state import PipelineState
from pipeline.rag.retriever import CodebaseRetriever

# ---------------------------------------------------------------------------
# LLM setup
# ---------------------------------------------------------------------------

llm = ChatOllama(model="llama3.1", temperature=0.1)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_json_list(text: str) -> list[str]:
    """
    Extract a JSON array from LLM output that may contain surrounding text.
    Falls back to splitting on newlines if no valid JSON array is found.
    """
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return [str(q).strip() for q in result if str(q).strip()]
        except json.JSONDecodeError:
            pass

    # Fallback: treat each non-empty line as a query
    lines = [line.strip("- •*\t ") for line in text.splitlines() if line.strip()]
    return lines[:4]  # cap at 4 queries


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

def context_retrieval_node(state: PipelineState) -> dict:
    """
    Node 1 — generates search queries from the issue and retrieves
    relevant code snippets from the indexed Next.js codebase.
    """
    print("\n[Node 1] Context Retrieval — generating search queries...")

    issue = state["issue"]

    # Step 1: Ask the LLM to decompose the issue into codebase search queries
    messages = [
        SystemMessage(content=(
            "You are a code search assistant. Given a feature request, "
            "generate 3 to 4 short, targeted search queries to find relevant "
            "code in an existing TypeScript / Next.js codebase. "
            "Return only a JSON array of strings, no explanation."
        )),
        HumanMessage(content=f"Feature request:\n{issue}"),
    ]

    response = llm.invoke(messages)
    queries = _extract_json_list(response.content)

    print(f"[Node 1] Generated {len(queries)} search queries:")
    for q in queries:
        print(f"  • {q}")

    # Step 2: Run each query through the retriever and collect results
    retriever = CodebaseRetriever()
    all_results: list[dict] = []
    seen_ids: set[str] = set()

    for query in queries:
        results = retriever.query(query, n_results=3)
        for r in results:
            chunk_id = f"{r['file_path']}::chunk_{r['chunk_index']}"
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                all_results.append(r)

    # Sort by distance (most relevant first) and cap at 6 chunks total
    all_results.sort(key=lambda r: r["distance"])
    all_results = all_results[:6]

    files_found = list({r["file_path"] for r in all_results})
    print(f"[Node 1] Retrieved {len(all_results)} unique chunks from: {', '.join(files_found)}")

    # Step 3: Format into a context block for the coding agent
    rag_context = retriever.format_context(all_results)

    return {
        "search_queries": queries,
        "rag_context": rag_context,
    }
