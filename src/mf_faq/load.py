"""Fetch official HTML pages and PDFs. Does not chunk, embed, or call a model."""

from __future__ import annotations

import re
from io import BytesIO
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from mf_faq.config import MIN_TEXT_CHARS, RAW_DIR, REQUEST_TIMEOUT_SECONDS, SOURCES_MD_PATH
from mf_faq.sources import FUND_SCHEMES, SOURCES

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

_DROP_TAGS = ("script", "style", "noscript", "nav", "footer", "header", "iframe", "svg", "form")


def load_all() -> dict:
    """Fetch every source. Write kept text under data/raw and a report to data/sources.md."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for old in RAW_DIR.glob("*.txt"):
        old.unlink()

    kept: list[dict] = []
    dropped: list[dict] = []

    for index, source in enumerate(SOURCES, start=1):
        try:
            document = fetch_document(source)
        except Exception as exc:  # one bad URL must not stop the run
            dropped.append({"url": source["url"], "reason": _one_line(exc)})
            print(f"DROP {index:02d} {source['url']} — {_one_line(exc)}")
            continue

        reason = rejection_reason(document["text"])
        if reason:
            dropped.append({"url": source["url"], "reason": reason})
            print(f"DROP {index:02d} {source['url']} — {reason}")
            continue

        slug = slug_for(index, source["url"])
        path = RAW_DIR / f"{slug}.txt"
        path.write_text(render_raw(document), encoding="utf-8")
        kept.append({**document, "slug": slug, "chars": len(document["text"])})
        print(f"KEEP {index:02d} {source['scheme']} ({source['plan']}) {len(document['text'])} chars")

    schemes_kept = {item["scheme"] for item in kept}
    missing = [scheme for scheme in FUND_SCHEMES if scheme not in schemes_kept]
    note = ""
    if missing:
        note = (
            "No usable text for: "
            + ", ".join(missing)
            + ". Do not add outside URLs; decide with a human before continuing."
        )
        print(note)

    SOURCES_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOURCES_MD_PATH.write_text(render_sources_md(kept, dropped, note), encoding="utf-8")
    print(f"Wrote {len(kept)} files to {RAW_DIR}")
    print(f"Wrote {SOURCES_MD_PATH}")
    return {"kept": kept, "dropped": dropped}


def fetch_document(source: dict) -> dict:
    response = requests.get(
        source["url"],
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "")
    is_pdf = "pdf" in content_type.lower() or source["url"].lower().endswith(".pdf")
    if is_pdf:
        title, text = pdf_text(response.content)
    else:
        title, text = html_text(response.text)
    if not title:
        title = source["scheme"]
    return {
        "source_url": source["url"],
        "scheme": source["scheme"],
        "plan": source["plan"],
        "doc_title": title,
        "text": text,
    }


def html_text(html: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    for tag in soup.find_all(_DROP_TAGS):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    text = root.get_text(separator="\n")
    return _clean_title(title), _clean_text(text)


def pdf_text(content: bytes) -> tuple[str, str]:
    reader = PdfReader(BytesIO(content))
    title = ""
    if reader.metadata and reader.metadata.title:
        title = str(reader.metadata.title).strip()
    pages = [(page.extract_text() or "") for page in reader.pages]
    return _clean_title(title), _clean_text("\n".join(pages))


def rejection_reason(text: str) -> str | None:
    if len(text) < MIN_TEXT_CHARS:
        return f"too little extractable text ({len(text)} characters)"
    head = text[:1500].lower()
    blocked_markers = (
        "just a moment",
        "enable javascript",
        "access denied",
        "cf-browser-verification",
        "attention required",
    )
    if any(marker in head for marker in blocked_markers) and len(text) < 2500:
        return "page is a bot check or empty shell, not scheme text"
    return None


def slug_for(index: int, url: str) -> str:
    path = urlparse(url).path.strip("/")
    parts = [part for part in path.split("/") if part and part not in {"s3fs-public", "Others"}]
    tail = "-".join(parts[-3:]) if parts else "source"
    tail = re.sub(r"[^a-zA-Z0-9._-]+", "-", tail)
    tail = re.sub(r"-+", "-", tail).strip("-").lower()
    return f"{index:02d}-{tail[:80]}"


def render_raw(document: dict) -> str:
    header = "\n".join(
        [
            f"url: {document['source_url']}",
            f"scheme: {document['scheme']}",
            f"plan: {document['plan']}",
            f"title: {document['doc_title']}",
            "",
        ]
    )
    return header + document["text"].rstrip() + "\n"


def render_sources_md(kept: list[dict], dropped: list[dict], note: str) -> str:
    lines = ["# Sources loaded", ""]
    if note:
        lines.extend([note, ""])
    lines.extend(
        [
            "## Kept",
            "",
            "| URL | Scheme | Plan | Title | Characters |",
            "|---|---|---|---|---|",
        ]
    )
    if not kept:
        lines.append("| — | — | — | — | 0 |")
    for item in kept:
        title = item["doc_title"].replace("|", "/")
        lines.append(
            f"| {item['source_url']} | {item['scheme']} | {item['plan']} | {title} | {len(item['text'])} |"
        )
    lines.extend(["", "## Dropped", "", "| URL | Reason |", "|---|---|"])
    if not dropped:
        lines.append("| — | — |")
    for item in dropped:
        reason = item["reason"].replace("|", "/")
        lines.append(f"| {item['url']} | {reason} |")
    lines.append("")
    return "\n".join(lines)


def _clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()


def _clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()


def _one_line(exc: BaseException) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    return re.sub(r"\s+", " ", message)[:300]
