"""Project settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CHUNKS_PATH = DATA_DIR / "chunks.txt"
SOURCES_MD_PATH = DATA_DIR / "sources.md"
INGESTED_AT_PATH = DATA_DIR / "ingested_at.txt"
EMBEDDINGS_PREVIEW_PATH = DATA_DIR / "embeddings_preview.txt"
CHROMA_PATH = DATA_DIR / "chroma"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
TOP_K = 8
MEMORY_TURNS = 10
# Chroma L2 distance. Lower is closer. In-scope fact questions scored 0.40–0.71;
# unrelated questions scored 1.03 and above. 0.90 sits in that gap.
DISTANCE_THRESHOLD = 0.90
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

REQUEST_TIMEOUT_SECONDS = 90
MIN_TEXT_CHARS = 400
