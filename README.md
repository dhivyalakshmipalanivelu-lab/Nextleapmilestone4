# Mutual Fund FAQ Assistant

Facts-only RAG chatbot for five HDFC mutual fund schemes. It answers from official public pages and does not give investment advice.

## Schemes

- HDFC Large Cap Fund
- HDFC Flexi Cap Fund
- HDFC ELSS Tax Saver
- HDFC Mid Cap Fund

## Setup

From this folder, in PowerShell:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and set `GROQ_API_KEY`. Do not commit that file.

Check that the source list imports:

```powershell
$env:PYTHONPATH = "src"
python -c "from mf_faq.sources import SOURCES; print(len(SOURCES))"
```

That prints `15`.

## Chat UI

From this folder, with the virtualenv active:

```powershell
streamlit run src/mf_faq/app.py
```

The page does not ingest or re-embed. If the vector store is missing, it shows `python scripts/ingest.py`.

## Chunking

Inspected `data/raw/` before choosing these numbers. The loader kept two HDFC Mid Cap fund-facts PDFs (about 6,500 characters each). The HTML pages were dropped, so this corpus is PDF text: short lines and two-to-three-line wraps for facts such as benchmark, exit load, AUM, plans, and riskometer. There are almost no blank-line paragraphs.

- Chunk size: **600** characters.
- Overlap: **100** characters.
- A new chunk starts at fact headings such as "Minimum Application", "Exit Load", and "Actual expenses", without inheriting the previous section.
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

See `docs/PRD.md` section 14.
