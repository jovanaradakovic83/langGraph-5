"""
RAG Indexer — Phase 3

Walks nextjs-app/src, splits TypeScript files by export boundaries,
embeds each chunk with sentence-transformers, and persists to ChromaDB.

Run once (or re-run to rebuild the index):
    cd pipeline
    python3 -m rag.indexer
"""

import re
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# pipeline/rag/indexer.py  →  up 3 levels  →  langGraph-5/
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CODEBASE_DIR = ROOT_DIR / "nextjs-app" / "src"
CHROMA_DIR = Path(__file__).resolve().parent / "chroma_db"

COLLECTION_NAME = "nextjs_codebase"

# Only index TypeScript source files
ALLOWED_EXTENSIONS = {".ts", ".tsx"}

# Minimum number of lines a chunk must have to be worth indexing
MIN_CHUNK_LINES = 3

# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

# Split a file at each top-level export declaration so each exported
# symbol becomes its own chunk. This keeps logical units together and
# produces more precise RAG results than fixed-line splitting.
EXPORT_PATTERN = re.compile(
    r"(?=^export\s+(default\s+|async\s+)?(function|const|class|interface|type|enum|abstract)\b)",
    re.MULTILINE,
)


def chunk_file(content: str, file_path: str) -> list[dict]:
    """
    Split file content by export boundaries.
    Returns a list of chunk dicts: {text, file_path, chunk_index}.
    Falls back to treating the whole file as one chunk if no exports found.
    """
    parts = EXPORT_PATTERN.split(content)
    # Filter out empty strings and whitespace-only fragments
    parts = [p.strip() for p in parts if p is not None and p.strip()]

    # If splitting produced nothing useful, treat the whole file as one chunk
    if not parts:
        parts = [content.strip()]

    chunks = []
    for idx, part in enumerate(parts):
        if len(part.splitlines()) < MIN_CHUNK_LINES:
            continue
        chunks.append({
            "text": part,
            "file_path": file_path,
            "chunk_index": idx,
        })

    return chunks


# ---------------------------------------------------------------------------
# Indexer
# ---------------------------------------------------------------------------

def build_index() -> None:
    """Walk the Next.js codebase, chunk every .ts/.tsx file, embed and store."""

    print(f"[Indexer] Codebase path : {CODEBASE_DIR}")
    print(f"[Indexer] ChromaDB path : {CHROMA_DIR}")

    if not CODEBASE_DIR.exists():
        raise FileNotFoundError(
            f"Codebase directory not found: {CODEBASE_DIR}\n"
            "Make sure nextjs-app/src exists relative to langGraph-5/"
        )

    # Collect all .ts / .tsx files (skip node_modules just in case)
    source_files = [
        f for f in CODEBASE_DIR.rglob("*")
        if f.suffix in ALLOWED_EXTENSIONS and "node_modules" not in f.parts
    ]

    if not source_files:
        print("[Indexer] No TypeScript files found — nothing to index.")
        return

    print(f"[Indexer] Found {len(source_files)} source file(s)")

    # Build all chunks
    all_chunks: list[dict] = []
    for file in sorted(source_files):
        relative_path = str(file.relative_to(ROOT_DIR))
        content = file.read_text(encoding="utf-8")
        chunks = chunk_file(content, relative_path)
        print(f"  {relative_path}  →  {len(chunks)} chunk(s)")
        all_chunks.extend(chunks)

    print(f"[Indexer] Total chunks to embed: {len(all_chunks)}")

    # Set up ChromaDB with sentence-transformers embedding function
    embedding_fn = SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Drop and recreate the collection for a clean rebuild
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"[Indexer] Existing collection '{COLLECTION_NAME}' cleared")
    except Exception:
        pass  # Collection didn't exist yet

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        # distance metric is cosine similarity
        metadata={"hnsw:space": "cosine"},
        # "hnsw:M": 32,                 # Max links per node (default is 16);how many neighbours each vector connects to in the graph. Higher = more accurate search, more memory.
        # "hnsw:construction_ef": 200   # Build-time accuracy trade-off;how many candidates are explored while building the index. Higher = better quality graph, slower build time. Default is 100.
        # ef_search — how many candidates are explored at query time. Higher = more accurate results, slower queries.
    )

    # Upsert all chunks
    collection.add(
        ids=[f"{c['file_path']}::chunk_{c['chunk_index']}" for c in all_chunks],
        documents=[c["text"] for c in all_chunks],
        metadatas=[{"file_path": c["file_path"], "chunk_index": c["chunk_index"]} for c in all_chunks],
    )

    print(f"[Indexer] Done — {len(all_chunks)} chunks stored in '{COLLECTION_NAME}'")


if __name__ == "__main__":
    build_index()
