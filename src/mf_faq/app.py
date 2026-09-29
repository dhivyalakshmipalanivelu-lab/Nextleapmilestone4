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


def _load_css() -> None:
    try:
        css = Path(__file__).with_name("style.css").read_text(encoding="utf-8")
    except OSError:
        return
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def _ensure_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "memory" not in st.session_state:
        st.session_state.memory = Memory()


def _ask(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    try:
        result = answer_question(question, st.session_state.memory)
    except RuntimeError as exc:
        result = {"text": str(exc), "chunks": [], "question": question}
    except Exception as exc:
        result = {
            "text": f"The answer service failed: {type(exc).__name__}: {exc}",
            "chunks": [],
            "question": question,
        }
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["text"],
            "chunks": result.get("chunks") or [],
            "resolved": result.get("question", question),
        }
    )


def _source_chip(text: str, chunks: list[dict]) -> None:
    if "http" in (text or "") or not chunks:
        return
    meta = chunks[0].get("metadata") or {}
    url = meta.get("source_url", "")
    if not url:
        return
    label = html.escape(meta.get("scheme") or "Official source")
    st.markdown(
        f'<a class="src-chip" href="{html.escape(url)}" target="_blank">'
        f"Source: {label}</a>",
        unsafe_allow_html=True,
    )


def _sources(chunks: list[dict]) -> None:
    with st.expander("Sources"):
        if not chunks:
            st.write("No chunks were retrieved.")
            return
        for chunk in chunks:
            meta = chunk.get("metadata") or {}
            scheme = meta.get("scheme", "")
            url = meta.get("source_url", "")
            st.markdown(f"**{chunk.get('rank', '')}. {scheme}**")
            if url:
                st.markdown(url)
            distance = chunk.get("distance")
            if distance is not None:
                st.caption(f"distance {distance:.3f}")
            preview = (chunk.get("text") or "").strip()
            if preview:
                st.text(preview[:400])


def _header() -> None:
    left, right = st.columns([4, 1])
    with left:
        st.markdown(
            '<div class="app-header"><div class="logo-mark">F</div><div>'
            '<div class="app-title">HDFC Fund FAQ</div>'
            '<span class="app-tag">HDFC Mutual Fund</span></div></div>',
            unsafe_allow_html=True,
        )
    with right:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.memory = Memory()
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="HDFC Fund FAQ", layout="centered")
    _load_css()
    _ensure_state()

    _header()
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown(
            '<div class="welcome">Ask me factual questions about HDFC Large Cap, '
            "Flexi Cap, Mid Cap and ELSS Tax Saver, answered from the official "
            "documents.</div>",
            unsafe_allow_html=True,
        )
        columns = st.columns(3)
        for column, example in zip(columns, EXAMPLES):
            with column:
                if st.button(example, use_container_width=True):
                    st.session_state.pending = example

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            resolved = message.get("resolved")
            if message["role"] == "assistant" and resolved and resolved != _previous_user(message):
                st.caption(f"Understood as: {resolved}")
            st.markdown(message["content"])
            if message["role"] == "assistant":
                chunks = message.get("chunks") or []
                _source_chip(message["content"], chunks)
                _sources(chunks)

    typed = st.chat_input("Ask a factual question")
    pending = st.session_state.pop("pending", None)
    question = pending or typed
    if question:
        _ask(question)
        st.rerun()


def _previous_user(message: dict) -> str:
    """The user text just before this assistant reply, used to show a rewrite."""
    messages = st.session_state.messages
    index = messages.index(message)
    for earlier in reversed(messages[:index]):
        if earlier["role"] == "user":
            return earlier["content"]
    return ""


if __name__ == "__main__":
    main()
