"""Load official pages into data/raw. Does not chunk or embed."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mf_faq.load import load_all


if __name__ == "__main__":
    load_all()
