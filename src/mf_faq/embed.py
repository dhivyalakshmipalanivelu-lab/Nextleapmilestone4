"""Embed text with the ONNX MiniLM model. This avoids loading PyTorch."""

from __future__ import annotations

_function = None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one 384-dimension vector per text. The model downloads once."""
    global _function
    if _function is None:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        _function = ONNXMiniLM_L6_V2()
    vectors = _function(texts)
    return [[float(value) for value in vector] for vector in vectors]
