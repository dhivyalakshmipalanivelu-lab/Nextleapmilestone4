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
