"""Embed a question and return the top chunks from the persisted Chroma collection."""

from __future__ import annotations

import sys

from mf_faq.config import CHROMA_PATH, DISTANCE_THRESHOLD, EMBEDDING_MODEL, TOP_K
from mf_faq.store import COLLECTION_NAME

MISSING_COLLECTION = "Chroma collection is missing. Run python scripts/ingest.py"

_model = None
_client = None
_client_path: str | None = None


def _embedder():
    """Load MiniLM once per process. Later questions reuse it."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _chroma():
    """Open the persisted store once. A second client in this process breaks Chroma."""
    global _client, _client_path
    path = str(CHROMA_PATH)
    if _client is None or _client_path != path:
        import chromadb

        _client = chromadb.PersistentClient(path=path)
        _client_path = path
    return _client


def retrieve(question: str) -> dict:
    """Return top-k chunks. Does not ingest and does not call a language model."""
    if not CHROMA_PATH.exists():
        raise RuntimeError(MISSING_COLLECTION)

    client = _chroma()
    names = [collection.name for collection in client.list_collections()]
    if COLLECTION_NAME not in names:
        raise RuntimeError(MISSING_COLLECTION)

    vector = _embedder().encode(question, show_progress_bar=False)
    result = client.get_collection(COLLECTION_NAME).query(
        query_embeddings=[vector.tolist()],
        n_results=TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]
    for rank, (text, metadata, distance) in enumerate(
        zip(documents[0], metadatas[0], distances[0]),
        start=1,
    ):
        chunks.append(
            {
                "rank": rank,
                "text": text or "",
                "metadata": metadata or {},
                "distance": float(distance),
            }
        )

    best = chunks[0]["distance"] if chunks else None
    low_confidence = best is None or best > DISTANCE_THRESHOLD
    return {"chunks": chunks, "low_confidence": low_confidence, "best_distance": best}


def main(argv: list[str] | None = None) -> int:
    from mf_faq.guard import decide

    args = list(sys.argv[1:] if argv is None else argv)
    question = " ".join(args).strip()
    if not question:
        print('Usage: python -m mf_faq.retrieve "your question"')
        return 1

    verdict = decide(question)
    if verdict is not None and verdict.skip_retrieval:
        print(verdict.message)
        return 0

    try:
        found = retrieve(question)
    except RuntimeError as exc:
        print(exc)
        return 1

    if verdict is None:
        verdict = decide(question, found)
    print(verdict.message)
    if verdict.show_chunks:
        _print_chunks(found["chunks"])
    return 0


def _print_chunks(chunks: list[dict]) -> None:
    for chunk in chunks:
        metadata = chunk["metadata"]
        first_line = next((line for line in chunk["text"].splitlines() if line.strip()), "")
        print(
            f"{chunk['rank']}. {metadata.get('scheme', '')} | {metadata.get('source_url', '')} "
            f"| {chunk['distance']:.4f}"
        )
        print(f"   {first_line}")


if __name__ == "__main__":
    raise SystemExit(main())
