# Mutual Fund FAQ Assistant

Facts-only RAG chatbot for HDFC Mutual Fund. It answers from official public PDFs and does not give investment advice.

## Schemes

AMC: HDFC Mutual Fund.

Loaded schemes:

- HDFC Large Cap Fund
- HDFC Flexi Cap Fund
- HDFC ELSS Tax Saver
- HDFC Mid Cap Fund

HDFC Small Cap and every other fund are outside this demo.

## Setup

From this folder, in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set `GROQ_API_KEY`. Do not commit that file.

Ingest once. This downloads the 15 official PDFs, writes `data/chunks.txt` and `data/sources.md`, and stores the vectors in `data/chroma`. Later questions and app restarts do not ingest again. If `data/chroma` is already on disk, skip this step.

```powershell
python scripts/ingest.py
```

Check that the source list imports:

```powershell
$env:PYTHONPATH = "src"
python -c "from mf_faq.sources import SOURCES; print(len(SOURCES))"
```

That prints `15`.

Ask one question without ingesting again:

```powershell
$env:PYTHONPATH = "src"
python -m mf_faq.answer "What is the benchmark of HDFC Mid Cap Fund?"
```

## Chat UI

From this folder, with the virtualenv active:

```powershell
uvicorn mf_faq.web:app --app-dir src --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000. The page does not ingest or re-embed. If the vector store is missing, the reply shows `python scripts/ingest.py`.

On Render, the start command is:

```bash
uvicorn mf_faq.web:app --app-dir src --host 0.0.0.0 --port $PORT
```

## Chunking

Inspected `data/raw/` before choosing these numbers. The loader kept 15 official PDFs: a Scheme Information Document, a fund-facts sheet, and a Key Information Memorandum for each of the four schemes, plus a leaflet for Large Cap, Flexi Cap, and Mid Cap. The text is short lines and two-to-three-line wraps. There are almost no blank-line paragraphs. `data/sources.md` lists every kept URL. Its dropped table is empty.

- Chunk size: **600** characters.
- Overlap: **100** characters.
- A new chunk starts at fact headings such as "Minimum Application", "Exit Load", "Actual expenses", "The benchmark of the scheme is", and a line that states a statutory lock-in. Those chunks do not inherit the previous section.
- Each chunk starts with the scheme name. The expense-ratio table does not repeat the scheme, so a question that names the fund was matching other pages instead.
- Why: 600 characters still holds one fact block, and the smaller window keeps a minimum-application table from being embedded as part of the previous cut-off-time section. The overlap is about two wrapped lines. A line that already fits in 600 characters is never split.
- Every chunk keeps `source_url`, `scheme`, `plan`, `doc_title`, and `chunk_index`.
- A chunk never crosses two source documents. Each raw file is split on its own.

## Retrieval

Questions are embedded with the same MiniLM model and matched to the persisted Chroma collection. The query returns the top **8** chunks. Distance is L2, so a smaller number is a closer match.

- Low-confidence threshold: **0.90**.
- Why: the in-scope fact questions (expense ratio, lock-in, minimum SIP, benchmark) scored between 0.40 and 0.71. Unrelated questions scored 1.03 and above. 0.90 sits in that gap. A weaker match is still returned, but it is marked low confidence and the reply is "I don't know."
- Advice questions are refused before retrieval. Questions about products outside these four schemes, including HDFC Small Cap, are refused as outside the documents.
- A chat session keeps the last **10** messages. A follow-up is rewritten into a standalone question before retrieval, so "what about its fees?" uses the scheme from the earlier turns. A question that includes a PAN, Aadhaar number, email, or phone number is not stored.
- A factual question whose top chunks do not contain the asked fact also gets "I don't know." The reply does not add a number from outside the chunks.

## Known limits

- The corpus is HDFC Large Cap, Flexi Cap, Mid Cap, and ELSS Tax Saver. Other funds, including HDFC Small Cap, are out of scope.
- No URL in the current source list was dropped. `data/sources.md` records that. Account-statement and other website pages are not in this set, so the assistant cannot answer a statement-download question from these files.
- Facts can go stale when HDFC Mutual Fund updates a PDF after the last ingestion. `Last updated from sources` is the date of that ingestion, not a live crawl.
- PDF extraction can miss text that sits inside an image.
- This is a class demo. It is not a substitute for the scheme information document or for advice from a registered advisor.
- `data/chunks.txt` is the readable chunk dump. `data/chroma` holds the same chunks as vectors and is created by ingest, not committed.

See also `docs/PRD.md` section 14, `docs/sample_qa.md`, and `docs/disclaimer.md`.
