"""Load official pages, chunk them, and store embeddings. Does not answer questions."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mf_faq.chunk import chunk_all
from mf_faq.load import load_all
from mf_faq.store import store_chunks


def main() -> None:
    load_all()
    chunks = chunk_all()
    stored = store_chunks(chunks)
    print(f"chunk count: {stored}")


if __name__ == "__main__":
    main()
