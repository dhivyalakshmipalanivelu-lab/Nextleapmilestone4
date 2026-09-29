"""Refuse off-topic and advice questions. Say so when the chunks do not answer."""

from __future__ import annotations

import re
from dataclasses import dataclass

from mf_faq.sources import FUND_SCHEMES, SOURCES

_ADVICE = re.compile(
    r"\b(should i|buy|sell|hold|portfolio|allocate|good for me|recommend)\b",
    re.IGNORECASE,
)
_RETURNS = re.compile(
    r"\b(returns|cagr|performed better|higher returns|compare performance)\b",
    re.IGNORECASE,
)
_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
_AADHAAR = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")
_PHONE = re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b")
_OTP = re.compile(r"\botp\b", re.IGNORECASE)
_ACCOUNT = re.compile(r"\b(account number|a/c no|acct)\b", re.IGNORECASE)
_SCHEME_PHRASES = (
    ("elss", "HDFC ELSS Tax Saver"),
    ("tax saver", "HDFC ELSS Tax Saver"),
    ("flexi cap", "HDFC Flexi Cap Fund"),
    ("flexicap", "HDFC Flexi Cap Fund"),
    ("large cap", "HDFC Large Cap Fund"),
    ("mid cap", "HDFC Mid Cap Fund"),
    ("midcap", "HDFC Mid Cap Fund"),
    ("small cap", None),
)
_FACT_TERMS = (
    "expense",
    "exit load",
    "sip",
    "lock-in",
    "lock in",
    "benchmark",
    "riskometer",
    "minimum",
)


@dataclass(frozen=True)
class Verdict:
    message: str
    skip_retrieval: bool
    show_chunks: bool
    kind: str


def official_url(prefer_facts: bool = False) -> str:
    """A kept official URL. Fact-sheet links are preferred for returns questions."""
    facts = [source["url"] for source in SOURCES if "Fund%20Facts" in source["url"] or "Fund Facts" in source["url"]]
    if prefer_facts and facts:
        for url in facts:
            if "Mid-Cap" in url or "Mid%20Cap" in url or "Mid Cap" in url:
                return url
        return facts[0]
    return facts[0] if facts else SOURCES[0]["url"]


def decide(question: str, found: dict | None = None) -> Verdict | None:
    """Return a refusal, or None when retrieval should run first."""
    if _has_pii(question):
        return Verdict(
            message=(
                "This assistant does not take personal information such as PAN, "
                "Aadhaar, account numbers, OTPs, email addresses, or phone numbers."
            ),
            skip_retrieval=True,
            show_chunks=False,
            kind="pii",
        )

    if _ADVICE.search(question):
        return Verdict(
            message=(
                "I don't give investment advice. I can only quote facts that appear "
                "in the official HDFC documents loaded for this demo. "
                f"{official_url()}"
            ),
            skip_retrieval=True,
            show_chunks=False,
            kind="advice",
        )

    if _RETURNS.search(question):
        return Verdict(
            message=(
                "I don't calculate or compare returns. See the official fund facts: "
                f"{official_url(prefer_facts=True)}"
            ),
            skip_retrieval=True,
            show_chunks=False,
            kind="returns",
        )

    named = _named_scheme(question)
    if named is False:
        return Verdict(
            message=(
                "I don't know. That is outside the HDFC Large Cap, Flexi Cap, "
                "Mid Cap, and ELSS documents I have."
            ),
            skip_retrieval=True,
            show_chunks=False,
            kind="off_topic",
        )

    if found is None:
        return None

    if found.get("low_confidence") or not _context_answers(question, found, named):
        nearest = ""
        chunks = found.get("chunks") or []
        if chunks:
            nearest = chunks[0]["metadata"].get("source_url", "")
        return Verdict(
            message=(
                "I don't know. That figure is not in the ingested sources. "
                f"{nearest}".rstrip()
            ),
            skip_retrieval=False,
            show_chunks=True,
            kind="unknown",
        )

    return Verdict(
        message="In scope. Top chunks from the official documents:",
        skip_retrieval=False,
        show_chunks=True,
        kind="ok",
    )


def _has_pii(question: str) -> bool:
    return any(
        pattern.search(question)
        for pattern in (_PAN, _AADHAAR, _EMAIL, _PHONE, _OTP, _ACCOUNT)
    )


def _named_scheme(question: str) -> str | None | bool:
    """Return the in-corpus scheme, None if unnamed, or False if clearly outside the corpus."""
    lowered = question.lower()
    for phrase, scheme in _SCHEME_PHRASES:
        if phrase in lowered:
            return scheme if scheme in FUND_SCHEMES else False
    if re.search(r"\b(gold|etf|stock|crypto|bitcoin|weather)\b", lowered):
        return False
    return None


_STOPWORDS = {
    "what",
    "which",
    "when",
    "where",
    "does",
    "have",
    "this",
    "that",
    "with",
    "from",
    "about",
    "fund",
    "hdfc",
    "large",
    "flexi",
    "mid",
    "elss",
    "tax",
    "saver",
    "direct",
    "regular",
    "period",
    "scheme",
}


def _context_answers(question: str, found: dict, named: str | None) -> bool:
    chunks = found.get("chunks") or []
    if not chunks:
        return False
    if isinstance(named, str):
        top_schemes = [chunk["metadata"].get("scheme") for chunk in chunks[:2]]
        if named not in top_schemes:
            return False
    text = "\n".join(chunk["text"] for chunk in chunks).lower()
    lowered = question.lower()
    asked = [term for term in _FACT_TERMS if term in lowered]
    if asked:
        return any(term in text for term in asked)
    words = [
        word
        for word in re.findall(r"[a-z0-9-]+", lowered)
        if len(word) > 3 and word not in _STOPWORDS
    ]
    return any(word in text for word in words)
