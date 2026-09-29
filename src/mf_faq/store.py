"""Embed chunks and persist them in Chroma. The model loads only when store_chunks runs."""

from __future__ import annotations

from datetime import date

from mf_faq.config import CHROMA_PATH, EMBEDDING_MODEL, EMBEDDINGS_PREVIEW_PATH, INGESTED_AT_PATH

COLLECTION_NAME = "scheme_chunks"
VECTOR_DIMENSION = 384


def store_chunks(chunks: list[dict]) -> int:
    """Replace the on-disk collection with embeddings of these chunks."""
    if not chunks:
        raise RuntimeError("No chunks to store. Load and chunk documents before embedding.")

    from sentence_transformers import SentenceTransformer
    import chromadb

    model = SentenceTransformer(EMBEDDING_MODEL)
    vectors = model.encode([chunk["text"] for chunk in chunks], show_progress_bar=False)
    if len(vectors) == 0 or len(vectors[0]) != VECTOR_DIMENSION:
        raise RuntimeError(
            f"{EMBEDDING_MODEL} must produce {VECTOR_DIMENSION}-dimension vectors."
        )

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    names = [collection.name for collection in client.list_collections()]
    if COLLECTION_NAME in names:
        client.delete_collection(COLLECTION_NAME)
    collection = client.create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=[f"chunk-{index:04d}" for index in range(len(chunks))],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[_metadata(chunk) for chunk in chunks],
        embeddings=[vector.tolist() for vector in vectors],
    )

    stored = collection.count()
    if stored != len(chunks):
        raise RuntimeError(f"Expected {len(chunks)} chunks in Chroma, found {stored}.")

    INGESTED_AT_PATH.write_text(date.today().isoformat() + "\n", encoding="utf-8")
    _write_preview(vectors)
    print(f"stored {stored} chunks in {CHROMA_PATH}")
    return stored


def _write_preview(vectors) -> None:
    """Save the first 10 dimensions of the first 5 stored vectors."""
    lines = [
        f"model: {EMBEDDING_MODEL}",
        f"dimensions: {VECTOR_DIMENSION}",
        "preview: first 5 vectors, first 10 dimensions",
        "",
    ]
    for index, vector in enumerate(vectors[:5]):
        head = " ".join(f"{float(value):.6f}" for value in vector[:10])
        lines.append(f"chunk-{index:04d}: {head}")
    EMBEDDINGS_PREVIEW_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {EMBEDDINGS_PREVIEW_PATH}")


def _metadata(chunk: dict) -> dict:
    return {
        "source_url": str(chunk["source_url"]),
        "scheme": str(chunk["scheme"]),
        "plan": str(chunk["plan"]),
        "doc_title": str(chunk["doc_title"]),
        "chunk_index": int(chunk["chunk_index"]),
    }
