"""Interactive questions against the stored chunks. Does not ingest."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mf_faq.answer import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
