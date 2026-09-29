"""Streamlit chat for the facts-only FAQ. Does not load or ingest documents."""

from __future__ import annotations

import html
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import streamlit as st

from mf_faq.answer import answer_question
from mf_faq.memory import Memory

DISCLAIMER = "Facts-only. No investment advice."
EXAMPLES = (
    "What is the expense ratio of HDFC Large Cap Fund Direct?",
    "What is the lock-in period for HDFC ELSS Tax Saver?",
    "What is the minimum SIP for HDFC Flexi Cap Fund?",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"], .stMarkdown, button, input, textarea {
    font-family: 'Inter', sans-serif !important;
}
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }
.block-container { max-width: 760px; padding-top: 1.5rem; padding-bottom: 6rem; }

.app-header { display: flex; align-items: center; gap: 12px; }
.logo-mark {
    width: 38px; height: 38px; border-radius: 12px; background: #00D09C;
    color: #fff; font-weight: 700; font-size: 18px;
    display: flex; align-items: center; justify-content: center;
}
.app-title { font-size: 20px; font-weight: 700; color: #1F2937; line-height: 1.2; }
.app-tag {
    display:
