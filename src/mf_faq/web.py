"""Serve the facts-only chat page. Does not ingest documents."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from mf_faq.answer import answer_question
from mf_faq.memory import Memory

STATIC_DIR = Path(__file__).resolve().parent / "static"
COOKIE = "mf_session"

app = FastAPI(title="Facts-Only MF Assistant")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_sessions: dict[str, Memory] = {}


def _session(request: Request) -> tuple[str, Memory, bool]:
    sid = request.cookies.get(COOKIE, "")
    if sid and sid in _sessions:
        return sid, _sessions[sid], False
    sid = uuid.uuid4().hex
    memory = Memory()
    _sessions[sid] = memory
    return sid, memory, True


def _public_chunks(chunks: list[dict]) -> list[dict]:
    public = []
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        public.append(
            {
                "rank": chunk.get("rank"),
                "scheme": meta.get("scheme", ""),
                "url": meta.get("source_url", ""),
                "distance": chunk.get("distance"),
                "preview": (chunk.get("text") or "").strip()[:400],
            }
        )
    return public


@app.get("/")
def home() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/chat")
async def chat(request: Request) -> JSONResponse:
    body = await request.json()
    question = str(body.get("question", "")).strip()
    if not question:
        return JSONResponse({"text": "Type a factual question.", "kind": "empty", "chunks": []}, status_code=400)
    sid, memory, is_new = _session(request)
    try:
        result = answer_question(question, memory)
    except RuntimeError as exc:
        result = {"text": str(exc), "chunks": [], "question": question, "kind": "error"}
    except Exception:
        result = {
            "text": "The answer service failed. No answer was generated.",
            "chunks": [],
            "question": question,
            "kind": "error",
        }
    response = JSONResponse(
        {
            "text": result["text"],
            "question": result.get("question", question),
            "kind": result.get("kind", "ok"),
            "chunks": _public_chunks(result.get("chunks") or []),
        }
    )
    if is_new:
        response.set_cookie(COOKIE, sid, httponly=True, samesite="lax")
    return response


@app.post("/api/clear")
def clear(request: Request) -> JSONResponse:
    sid = request.cookies.get(COOKIE, "")
    if sid:
        _sessions.pop(sid, None)
    new_id = uuid.uuid4().hex
    _sessions[new_id] = Memory()
    response = JSONResponse({"cleared": True})
    response.set_cookie(COOKIE, new_id, httponly=True, samesite="lax")
    return response
