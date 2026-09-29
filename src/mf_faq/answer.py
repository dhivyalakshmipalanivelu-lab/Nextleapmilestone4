"""Answer from retrieved chunks only. The Groq call happens inside answer_question."""

from __future__ import annotations

import re
import sys

from mf_faq.config import GROQ_API_KEY, GROQ_MODEL, INGESTED_AT_PATH
from mf_faq.guard import decide
from mf_faq.memory import Memory
from mf_faq.retrieve import retrieve

_URL = re.compile(r"https?://\S+")


def answer_question(question: str, memory: Memory | None = None) -> dict:
    """Return the reply text and the chunks that were retrieved, if any."""
    pre = decide(question)
    if pre is not None and pre.skip_retrieval and pre.kind == "pii":
        return {"text": pre.message, "chunks": [], "question": question, "kind": pre.kind}

    rewritten = question
    if memory is not None and memory.messages:
        rewritten = memory.rewrite(question)

    pre = decide(rewritten)
    if pre is not None and pre.skip_retrieval:
        if memory is not None:
            memory.add("user", rewritten)
            memory.add("assistant", pre.message)
        return {"text": pre.message, "chunks": [], "question": rewritten, "kind": pre.kind}

    found = retrieve(rewritten)
    verdict = decide(rewritten, found)
    chunks = found["chunks"]
    if verdict is None or verdict.kind != "ok":
        text = verdict.message if verdict else "I don't know."
        text = _with_updated_line(text)
        if memory is not None:
            memory.add("user", rewritten)
            memory.add("assistant", text)
        return {"text": text, "chunks": chunks, "question": rewritten, "kind": verdict.kind if verdict else "unknown"}

    if not GROQ_API_KEY:
        raise RuntimeError("set GROQ_API_KEY in .env")

    text = _ask_groq(rewritten, chunks)
    if memory is not None:
        memory.add("user", rewritten)
        memory.add("assistant", text)
    return {"text": text, "chunks": chunks, "question": rewritten, "kind": "ok"}


def _ask_groq(question: str, chunks: list[dict]) -> str:
    from groq import Groq

    allowed = [chunk["metadata"].get("source_url", "") for chunk in chunks]
    updated = _updated_line()
    system = (
        "You answer questions about HDFC mutual fund schemes using only the chunks provided. "
        "If the chunks do not contain the fact, say you do not know. "
        "A minimum SIP is the minimum application or purchase amount in rupees for that scheme, "
        "including systematic investments, when the chunks state that amount. "
        "Do not say the amount is missing when those chunks show a rupee minimum for the named scheme. "
        "Audited actual expenses for the Regular Plan and the Direct Plan are the expense ratio. "
        "Quote both percentages when they appear. "
        "Do not say the percentage is missing when those audited figures are in the chunks. "
        "A statutory lock-in of 3 years is the lock-in period when a chunk states that for the named scheme. "
        "When a chunk says the benchmark of the scheme is a named index, quote that index. "
        "Do not answer with a benchmark from a comparison table for a different scheme. "
        "Write at most 3 sentences. "
        "Include exactly one source URL, and it must be copied from a chunk. "
        "Do not give investment advice. Do not calculate or compare returns. "
        f"End with this exact line: {updated}"
    )
    blocks = []
    for chunk in chunks:
        meta = chunk["metadata"]
        blocks.append(
            f"[{chunk['rank']}] scheme: {meta.get('scheme', '')}\n"
            f"source_url: {meta.get('source_url', '')}\n"
            f"{chunk['text']}"
        )
    user = "Chunks:\n\n" + "\n\n".join(blocks) + f"\n\nQuestion: {question}"
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        raw = completion.choices[0].message.content or ""
    except Exception:
        return "The answer service failed. No answer was generated."
    return _enforce(raw.strip(), allowed, updated)


def _enforce(text: str, allowed: list[str], updated: str) -> str:
    body = text.replace(updated, "").strip()
    found_urls = _URL.findall(body)
    kept = next((url.rstrip(").,") for url in found_urls if url.rstrip(").,") in allowed), "")
    if not kept and allowed:
        kept = allowed[0]
    for url in found_urls:
        body = body.replace(url, "")
    body = re.sub(r"\s+", " ", body).strip()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", body) if part.strip()]
    body = " ".join(sentences[:3]).strip()
    if kept and kept not in body:
        body = f"{body} {kept}".strip()
    return _with_updated_line(body)


def _updated_line() -> str:
    if INGESTED_AT_PATH.exists():
        date = INGESTED_AT_PATH.read_text(encoding="utf-8").strip()
    else:
        date = "unknown"
    return f"Last updated from sources: {date}"


def _with_updated_line(text: str) -> str:
    line = _updated_line()
    body = text.replace(line, "").strip()
    return f"{body}\n{line}" if body else line


def _print_result(result: dict, typed: str) -> None:
    resolved = result.get("question", typed)
    if resolved != typed:
        print(f"Understood as: {resolved}")
        print()
    print(result["text"])
    print()
    print("Retrieved chunks:")
    if not result["chunks"]:
        print("(none)")
        return
    for chunk in result["chunks"]:
        meta = chunk["metadata"]
        first = next((line for line in chunk["text"].splitlines() if line.strip()), "")
        print(
            f"{chunk['rank']}. {meta.get('scheme', '')} | {meta.get('source_url', '')} "
            f"| {chunk['distance']:.4f}"
        )
        print(f"   {first}")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    question = " ".join(args).strip()
    if question:
        return _run_one(question)
    print("Type a question, or 'quit' to stop.")
    memory = Memory()
    while True:
        try:
            typed = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not typed or typed.lower() in {"quit", "exit"}:
            return 0
        code = _run_one(typed, memory)
        if code != 0:
            return code
        print()


def _run_one(question: str, memory: Memory | None = None) -> int:
    try:
        result = answer_question(question, memory)
    except RuntimeError as exc:
        print(exc)
        return 1
    _print_result(result, question)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
