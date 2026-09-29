"""Split loaded documents into readable chunks. Does not embed or store vectors."""

from __future__ import annotations

import re

from mf_faq.config import CHUNK_OVERLAP, CHUNK_SIZE, CHUNKS_PATH, RAW_DIR

_FACT_HEADING = re.compile(
    r"^(?:\d+\.\s*|[IVX]+\.\s*)?(?:Minimum Application|Minimum Additional|Minimum Redemption|Exit Load|Benchmark\b|Lock[- ]?in|Recurring Expenses|Actual expenses|Maximum Total Expense Ratio)",
    re.IGNORECASE,
)


def chunk_all() -> list[dict]:
    """Read data/raw, write data/chunks.txt, and print a length summary."""
    if CHUNK_SIZE is None or CHUNK_OVERLAP is None:
        raise RuntimeError("Set CHUNK_SIZE and CHUNK_OVERLAP in config before chunking.")
    if CHUNK_OVERLAP >= CHUNK_SIZE:
        raise RuntimeError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")

    documents = [_read_raw(path) for path in sorted(RAW_DIR.glob("*.txt"))]
    chunks: list[dict] = []
    for document in documents:
        parts = pack_units(_units(document["text"]), CHUNK_SIZE, CHUNK_OVERLAP)
        for index, text in enumerate(parts):
            labeled = f"{document['scheme']}\n{text}" if document["scheme"] else text
            chunks.append(
                {
                    "source_url": document["source_url"],
                    "scheme": document["scheme"],
                    "plan": document["plan"],
                    "doc_title": document["doc_title"],
                    "chunk_index": index,
                    "text": labeled,
                }
            )

    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHUNKS_PATH.write_text(_render(chunks), encoding="utf-8")
    _print_summary(documents, chunks)
    return chunks


def pack_units(units: list[str], size: int, overlap: int) -> list[str]:
    """Pack lines into chunks. A line shorter than size is never cut."""
    chunks: list[str] = []
    current: list[str] = []

    def length(lines: list[str]) -> int:
        return len("\n".join(lines)) if lines else 0

    for unit in _pieces(units, size):
        heading = bool(_FACT_HEADING.match(unit))
        if current and (heading or length(current) + 1 + len(unit) > size):
            chunks.append("\n".join(current))
            # A fact heading starts clean so the previous section does not dominate its embedding.
            current = [] if heading else _overlap_tail(current, overlap)
            while current and length(current) + 1 + len(unit) > size:
                current = current[1:]
        current.append(unit)

    if current:
        chunks.append("\n".join(current))
    return chunks


def _units(text: str) -> list[str]:
    units: list[str] = []
    for paragraph in text.split("\n\n"):
        for line in paragraph.splitlines():
            cleaned = line.strip()
            if cleaned:
                units.append(cleaned)
    return units


def _pieces(units: list[str], size: int) -> list[str]:
    pieces: list[str] = []
    for unit in units:
        if len(unit) <= size:
            pieces.append(unit)
            continue
        start = 0
        while start < len(unit):
            pieces.append(unit[start : start + size])
            start += size
    return pieces


def _overlap_tail(lines: list[str], overlap: int) -> list[str]:
    """Keep the trailing lines whose text is within the overlap budget."""
    kept: list[str] = []
    used = 0
    for line in reversed(lines):
        extra = len(line) if not kept else len(line) + 1
        if used + extra > overlap:
            break
        kept.append(line)
        used += extra
    kept.reverse()
    return kept


def _read_raw(path) -> dict:
    """Raw files start with url, scheme, plan, and title lines, then the body."""
    lines = path.read_text(encoding="utf-8").splitlines()
    fields = {}
    body_start = 0
    for index, line in enumerate(lines):
        if index > 3 or ":" not in line:
            body_start = index
            break
        key, value = line.split(":", 1)
        if key.strip() not in {"url", "scheme", "plan", "title"}:
            body_start = index
            break
        fields[key.strip()] = value.strip()
        body_start = index + 1
    body = "\n".join(lines[body_start:]).strip()
    return {
        "source_url": fields.get("url", ""),
        "scheme": fields.get("scheme", ""),
        "plan": fields.get("plan", "unknown"),
        "doc_title": fields.get("title", path.stem),
        "text": body,
    }


def _render(chunks: list[dict]) -> str:
    blocks = []
    for chunk in chunks:
        header = "\n".join(
            [
                f"source_url: {chunk['source_url']}",
                f"scheme: {chunk['scheme']}",
                f"plan: {chunk['plan']}",
                f"doc_title: {chunk['doc_title']}",
                f"chunk_index: {chunk['chunk_index']}",
                "",
                chunk["text"],
            ]
        )
        blocks.append(header)
    return "\n---\n".join(blocks) + ("\n" if blocks else "")


def _print_summary(documents: list[dict], chunks: list[dict]) -> None:
    lengths = [len(chunk["text"]) for chunk in chunks]
    print(f"documents: {len(documents)}")
    print(f"chunks: {len(chunks)}")
    if lengths:
        print(f"min chunk length: {min(lengths)}")
        print(f"max chunk length: {max(lengths)}")
    print(f"wrote {CHUNKS_PATH}")


if __name__ == "__main__":
    chunk_all()
