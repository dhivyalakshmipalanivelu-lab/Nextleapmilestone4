"""Streamlit chat for the facts-only FAQ. Does not load or ingest documents."""

from __future__ import annotations

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
    except Exception:
        result = {
            "text": "The answer service failed. No answer was generated.",
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


def main() -> None:
    st.set_page_config(page_title="HDFC Fund FAQ", layout="centered")
    _ensure_state()

    st.title("HDFC Fund FAQ")
    st.write(
        "This assistant answers factual questions about HDFC Large Cap, Flexi Cap, "
        "Mid Cap, and ELSS Tax Saver from the official documents already loaded."
    )
    st.markdown(f"**{DISCLAIMER}**")

    header = st.columns([4, 1])
    with header[1]:
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.memory = Memory()
            st.rerun()

    st.write("Try an example:")
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
                _sources(message.get("chunks") or [])

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
