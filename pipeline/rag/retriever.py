"""
RAG Retriever — Phase 3

Query interface over the ChromaDB collection built by indexer.py.
Used by Node 1 (context_retrieval.py) to fetch relevant codebase snippets.
"""

from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ---------------------------------------------------------------------------
# Paths — must match indexer.py
# ---------------------------------------------------------------------------

CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"
COLLECTION_NAME = "nextjs_codebase"

# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------

class CodebaseRetriever:
    """
    Wraps the ChromaDB collection for semantic code search.

    Usage:
        retriever = CodebaseRetriever()
        results = retriever.query("JWT token expiry handling", n_results=3)
        for r in results:
            print(r["file_path"])
            print(r["text"])
    """

    def __init__(self) -> None:
        if not CHROMA_DIR.exists():
            raise FileNotFoundError(
                f"ChromaDB not found at {CHROMA_DIR}.\n"
                "Run the indexer first:  python3 -m rag.indexer"
            )

        embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embedding_fn,
        )

    def query(self, search_text: str, n_results: int = 4) -> list[dict]:
        """
        Semantic search over the indexed codebase.

        Args:
            search_text: Natural language or code-style query string.
            n_results:   Number of top chunks to return (default 4).

        Returns:
            List of dicts with keys: file_path, chunk_index, text, distance.
            Sorted by relevance (lowest distance first).
        """
        results = self.collection.query(
            query_texts=[search_text],
            n_results=min(n_results, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        output = []
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            output.append({
                "file_path": meta["file_path"],
                "chunk_index": meta["chunk_index"],
                "text": doc,
                "distance": round(dist, 4),
            })

        return output

    def format_context(self, results: list[dict]) -> str:
        """
        Format query results into a single readable context block
        suitable for injection into an LLM prompt.
        """
        if not results:
            return "No relevant codebase context found."

        lines = []
        seen_files: set[str] = set()

        for r in results:
            file_path = r["file_path"]
            # Show each file path header only once
            if file_path not in seen_files:
                lines.append(f"\n### {file_path}\n")
                seen_files.add(file_path)
            lines.append("```typescript")
            lines.append(r["text"])
            lines.append("```\n")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Manual test — run directly to verify the index is working
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    retriever = CodebaseRetriever()

    test_queries = [
        "JWT token expiry and refresh",
        "middleware authentication check",
        "session cookie handling",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)
        results = retriever.query(query, n_results=2)
        print(retriever.format_context(results))
