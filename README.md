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

## Disclaimer

**Facts-only. No investment advice.** This assistant reports facts found in official HDFC Mutual Fund documents. It does not recommend funds, compare returns, or say whether to buy or sell. Do not enter PAN, Aadhaar, account numbers, OTPs, emails or phone numbers. For decisions about your money, consult a SEBI-registered adviser.

## Sources

All 15 sources are official HDFC Mutual Fund PDFs. The same list is in `data/sources.md`.

**HDFC Large Cap Fund**

1. [SID](https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Large%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf)
2. [Fund Facts, Aug 2026](https://files.hdfcfund.com/s3fs-public/Others/2026-09/Fund%20Facts%20-%20HDFC%20Large%20Cap%20Fund_August%2026.pdf)
3. [KIM](https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Large%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf)
4. [Leaflet](https://files.hdfcfund.com/s3fs-public/Others/2026-02/HDFC%20Large%20Cap%20Fund%20Leaflet%20%28Jan%202026%29.pdf)

**HDFC Flexi Cap Fund**

5. [SID](https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf)
6. [Fund Facts, Aug 2026](https://files.hdfcfund.com/s3fs-public/Others/2026-09/Fund%20Facts%20-%20HDFC%20Flexi%20Cap%20Fund_August%2026.pdf)
7. [KIM](https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20November%2021%2C%202025_1.pdf)
8. [Leaflet](https://files.hdfcfund.com/s3fs-public/Others/2026-06/Leaflet-HDFC%20Flexi%20Cap%20Fund-May%202026.pdf)

**HDFC Mid Cap Fund**

9. [SID](https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Mid%20Cap%20Fund%20dated%20November%2021%2C%202025_1.pdf)
10. [Fund Facts, Aug 2026](https://files.hdfcfund.com/s3fs-public/Others/2026-09/Fund%20Facts%20-%20HDFC%20Mid-Cap%20Fund_August%2026.pdf)
11. [KIM](https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Mid%20Cap%20Fund%20dated%20November%2021%2C%202025_1.pdf)
12. [Leaflet](https://files.hdfcfund.com/s3fs-public/Others/2026-07/HDFC%20Mid%20Cap%20Fund%20Leaflet%20%28As%20of%20May%2029%2C%202026%29.pdf)

**HDFC ELSS Tax Saver**

13. [SID](https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20ELSS%20Tax%20Saver%20dated%20November%2021%2C%202025.pdf)
14. [Fund Facts, Jul 2026](https://files.hdfcfund.com/s3fs-public/Others/2026-07/Fund%20Facts%20-%20HDFC%20TaxSaver%20Fund_July%2026.pdf)
15. [KIM](https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20ELSS%20Tax%20Saver%20dated%20November%2021%2C%202025_0.pdf)

## Sample Q&A

**Q: What is the lock-in period for HDFC ELSS Tax Saver?**
A: The HDFC ELSS Tax Saver scheme has a statutory lock‑in period of 3 years. 
Source: https://files.hdfcfund.com/s3fs-public/Others/2026-07/Fund%20Facts%20-%20HDFC%20TaxSaver%20Fund_July%2026.pdf 
Last updated from sources: 2026-09-29

**Q: What is the minimum SIP for HDFC Flexi Cap Fund?**
A: The minimum SIP for HDFC Flexi Cap Fund is Rs. 100 per installment.
Source: https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf
Last updated from sources: 2026-09-29

**Q: Should I buy HDFC Mid Cap Fund?**
A:I don't give investment advice. I can only quote facts that appear in the official HDFC documents loaded for this demo. 

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

## Deploy on Streamlit Community Cloud

Render runs out of memory when the build installs PyTorch and rebuilds the index. Streamlit Community Cloud serves the app that is already in this repo. The index in `data/chroma` is committed, so the cloud app does not ingest.

1. Open https://share.streamlit.io and create an app from this GitHub repo.
2. Branch: `main`
3. Main file path: `src/mf_faq/app.py`
4. In the app settings, open Secrets and paste:

```toml
GROQ_API_KEY = "your-key"
GROQ_MODEL = "llama-3.3-70b-versatile"
```

Do not put the key in the repository. After the app is live, ask a question there. It does not run `scripts/ingest.py`.

## Chat UI

From this folder, with the virtualenv active:

```powershell
streamlit run src/mf_faq/app.py
```

Open the local URL Streamlit prints. The page does not ingest or re-embed.

The Stitch page is still available locally with FastAPI:

```powershell
uvicorn mf_faq.web:app --app-dir src --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000.

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
- `data/chunks.txt` is the readable chunk dump. `data/chroma` is the same chunks as vectors and is committed so Streamlit Community Cloud can answer without rebuilding the index.

See also `docs/PRD.md` section 14, `docs/sample_qa.md`, and `docs/disclaimer.md`.
