# Implementation guide

Use this file to build the Mutual Fund FAQ assistant one phase at a time. The design is in `docs/architecture.md`. The product rules are in `docs/PRD.md`.

Finish a phase and check its "Done when" list before starting the next one. Do not pull later phases forward. In particular, do not write embedding or Chroma code until Phase 2 has inspected the loaded text and recorded the chunking decision.

## How to run a phase in Cursor

Paste the prompt for that phase only. Add: "Follow `docs/implementation.md` for this phase and `docs/architecture.md`. Do not implement later phases."

## Target layout

Create this shape in Phase 0 and fill it in later phases. Paths can move slightly if a phase says why. Responsibilities cannot.

```text
.env.example
.gitignore
requirements.txt
README.md                  # started in Phase 0, finished in Phase 7
data/
  raw/                     # one text file per loaded source
  chunks.txt               # readable chunk dump
  sources.md               # URLs kept and dropped
  ingested_at.txt          # date used in answers
  chroma/                  # persisted Chroma collection (gitignored)
src/mf_faq/
  config.py                # paths, model name, top-k, Groq model name
  sources.py               # the 15 URLs and scheme metadata
  load.py                  # HTML and PDF to text
  chunk.py                 # split text; write chunks.txt
  store.py                 # embed and persist Chroma
  retrieve.py              # embed a question; return top chunks
  guard.py                 # PII, advice, and returns checks
  answer.py                # Groq call and answer formatting
  app.py                   # Streamlit UI
scripts/
  ingest.py                # load → chunk → embed → store
```

Stack for every phase:

- Python 3.11+.
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2` only. Local. 384 dimensions. Same model for chunks and questions.
- Vector store: ChromaDB persisted at `data/chroma`. Ingestion does not run on app startup.
- LLM: Groq. Key from `GROQ_API_KEY` in `.env`. Never hardcode it. Never log it.
- UI: Streamlit, server-side, so the browser never sees the key.
- No accounts, no chat history stored on disk, no PII.

## Phase 0 — Project skeleton

**Goal.** A runnable empty project with config, ignore rules, and the source list. No fetching and no models yet.

**Build**

- `requirements.txt` with pinned, known-good packages: `requests`, `beautifulsoup4`, `pypdf`, `sentence-transformers`, `chromadb`, `python-dotenv`, `groq`, `streamlit`. Add a PDF fallback such as `pdfminer.six` only if you already know `pypdf` will be insufficient. Do not add a web framework besides Streamlit.
- `.gitignore` that ignores `.env`, `data/chroma/`, `data/raw/`, `__pycache__/`, and virtualenvs. Do not ignore `data/chunks.txt`, `data/sources.md`, or `data/ingested_at.txt`. Those are submission artifacts.
- `.env.example` containing only `GROQ_API_KEY=` and `GROQ_MODEL=llama-3.3-70b-versatile`. Do not create a real `.env` with a secret in the repo.
- `src/mf_faq/config.py` with the embedding model name, Chroma path, top-k default `4`, chunk size and overlap left as `None` until Phase 2, and paths for `data/raw`, `data/chunks.txt`, `data/sources.md`, and `data/ingested_at.txt`.
- `src/mf_faq/sources.py` with the 15 URLs from PRD section 6. Each entry has `url`, `scheme`, and `plan` (`direct`, `regular`, or `unknown`). Plan comes from the URL path when it contains `/direct` or `/regular`.
- README stub: how to create a virtualenv, install requirements, copy `.env.example` to `.env`, and the five scheme names. Leave setup commands accurate. Leave "Known limits" as a pointer to PRD section 14.

**Do not**

- Fetch URLs.
- Import the embedding model.
- Call Groq.
- Build the UI.

**Done when**

- `pip install -r requirements.txt` succeeds in a fresh virtualenv.
- Importing `mf_faq.config` and `mf_faq.sources` works, and `sources` lists 15 URLs.
- `.env` is gitignored. `.env.example` has no real key.

**Cursor prompt**

```text
Implement Phase 0 only from docs/implementation.md. Follow docs/architecture.md and docs/PRD.md.
Create the project skeleton, requirements, gitignore, .env.example, config, and the 15-source list.
Do not fetch pages, embed, call Groq, or build the UI.
```

## Phase 1 — Load

**Goal.** Turn each official URL into plain text plus metadata. Record what was kept and what was dropped.

**Build**

- `src/mf_faq/load.py`:
  - Fetch HTML with a normal browser user-agent and a timeout.
  - Strip scripts, styles, and navigation chrome. Keep main text.
  - Download PDFs and extract text with `pypdf`.
  - Return documents shaped as `{source_url, scheme, plan, doc_title, text}`.
  - On HTTP errors, timeouts, empty text, or PDF parse failure: skip that URL, store a one-line reason, continue.
- Write each kept document to `data/raw/<slug>.txt` with a short header (url, scheme, plan, title) and then the text.
- Write `data/sources.md` with two tables: kept (url, scheme, plan, title, character count) and dropped (url, reason).
- A small `python -m` or `scripts/load_only.py` entry point so this phase can run without chunking or Chroma. Phase 3's `scripts/ingest.py` will call the same function later.

**Do not**

- Chunk.
- Embed.
- Create a Chroma collection.
- Add blogs or any URL that is not in `sources.py`. If a page is empty, drop it. Do not replace it with a third-party page in this phase. If fewer than five schemes survive, note that in `data/sources.md` and stop for a human decision.

**Done when**

- Running the loader creates `data/raw/*.txt` and `data/sources.md`.
- A dropped URL does not crash the run.
- Opening two raw files shows real scheme text (fees, load, SIP, or fund facts), not a cookie wall or an empty string. If a file is a cookie wall, mark that URL dropped and say so.

**Cursor prompt**

```text
Implement Phase 1 only from docs/implementation.md.
Load the 15 official URLs into data/raw and write data/sources.md.
Skip failures with a reason. Do not chunk, embed, or call the LLM.
```

## Phase 2 — Inspect and chunk

**Goal.** Choose chunk size and overlap from the loaded text, write that decision down, then emit `data/chunks.txt`. No vectors yet.

The milestone requires the chunking strategy to be chosen after the data is inspected and before embedding code is written.

**Build**

1. Read `data/raw/`. Note typical length, whether facts sit in short lines (expense ratio, exit load, minimum SIP, lock-in) or long paragraphs, and how PDF text differs from HTML.
2. Write the decision into README under "Chunking":
   - chunk size and overlap in characters
   - why this fits this corpus
   - metadata on every chunk: `source_url`, `scheme`, `plan`, `doc_title`, `chunk_index`
   - confirmation that a chunk never crosses two source documents
3. Set those numbers in `config.py`.
4. Implement `src/mf_faq/chunk.py`:
   - Split on paragraph boundaries when possible, then pack into the chosen size with the chosen overlap.
   - Do not split a single short fact line in the middle if it already fits in one chunk.
   - Write every chunk to `data/chunks.txt` as a readable block: metadata header, blank line, text, then a separator such as `---`.
5. Print a summary: document count, chunk count, min/max chunk length.

**Do not**

- Import `sentence_transformers` or `chromadb` in this phase.
- Call Groq.
- Tune chunk size by retrieval quality. That feedback does not exist yet. Pick a size a person can read in `chunks.txt`.

**Done when**

- README states size, overlap, and why.
- `data/chunks.txt` is readable and contains only text from `data/raw/`.
- Spot-checking a few chunks shows `source_url` and `scheme` on each one.
- No chunk mixes two URLs.

**Cursor prompt**

```text
Implement Phase 2 only from docs/implementation.md.
Inspect data/raw first. Record chunk size, overlap, and why in the README.
Then implement chunking and write data/chunks.txt.
Do not add embedding or Chroma code.
```

## Phase 3 — Embed and store

**Goal.** Embed the Phase 2 chunks with MiniLM and persist them in Chroma. Ingestion becomes a single command.

**Build**

- `src/mf_faq/store.py`:
  - Load `sentence-transformers/all-MiniLM-L6-v2`.
  - Embed chunk texts. Assert vector length is 384 on the first batch.
  - Open a persistent Chroma client at `config.CHROMA_PATH`.
  - Delete the collection if it exists, then create it again, so a re-run cannot leave stale chunks.
  - Store document text plus metadata (`source_url`, `scheme`, `plan`, `doc_title`, `chunk_index`). Chroma metadata values must be strings, numbers, or bools.
  - Write today's date (ISO, local) to `data/ingested_at.txt` only after the upsert succeeds.
- `scripts/ingest.py` runs load, chunk, and store in that order. Loading stays idempotent: it refreshes `data/raw` and `data/sources.md`.
- Do not download the embedding model inside the query app in a way that also re-runs ingestion.

**Do not**

- Call Groq.
- Build the UI.
- Embed on application import.

**Done when**

- `python scripts/ingest.py` finishes and prints chunk count.
- `data/chroma/` exists after the script exits.
- A second run replaces the collection rather than duplicating it (chunk count stays stable if the raw text did not change).
- `data/ingested_at.txt` has one date.
- Stopping the script and starting it again does not re-download pages unless ingest is invoked again. The persistent directory is enough.

**Cursor prompt**

```text
Implement Phase 3 only from docs/implementation.md.
Embed the existing chunks with sentence-transformers/all-MiniLM-L6-v2 and persist them in Chroma at data/chroma.
Add scripts/ingest.py for load, chunk, then store. Do not call Groq and do not build the UI.
```

## Phase 4 — Retrieve

**Goal.** Given a question string, return the top-k chunks from the existing collection. Prove retrieval before any LLM call.

**Build**

- `src/mf_faq/retrieve.py`:
  - Load the same MiniLM model.
  - Open the persisted collection. If `data/chroma` or the collection is missing, raise a clear error: run `python scripts/ingest.py`. Do not ingest from this function.
  - Embed the question and query top-k from config.
  - Return chunk text, metadata, and distance.
- A tiny CLI (`python -m mf_faq.retrieve "expense ratio of HDFC Large Cap Fund Direct"`) that prints rank, scheme, url, distance, and the first line of text.
- If the best distance is worse than a config threshold, still return the chunks but mark them `low_confidence`. Phase 5 uses that flag to avoid inventing a number. Pick the threshold by running the sample questions below and writing the chosen value, plus why, in the README.

Run these questions by hand and note whether the top chunk is about the right scheme:

1. Expense ratio of HDFC Large Cap Fund Direct.
2. Lock-in period for HDFC ELSS Tax Saver.
3. Minimum SIP for HDFC Flexi Cap Fund.
4. Exit load for HDFC Small Cap Fund.
5. What is the benchmark of HDFC Mid Cap Fund?

**Do not**

- Call Groq.
- Build the UI.
- Re-chunk or change chunk size in this phase unless a question's top hit is clearly the wrong document. If you change it, re-run Phase 3 and update the README.

**Done when**

- The CLI works against the on-disk collection.
- At least four of the five questions above surface the right scheme in the top two chunks.
- Missing Chroma produces the ingest instruction and does not start a download of the corpus.

**Cursor prompt**

```text
Implement Phase 4 only from docs/implementation.md.
Add retrieval over the persisted Chroma collection using the same MiniLM model.
Add a CLI to print top chunks for a question. Do not call Groq and do not build the UI.
```

## Phase 5 — Guard and answer

**Goal.** Turn retrieved chunks into a facts-only answer with one citation. Refuse advice, returns math, and personal data before the model is called.

**Build**

- `src/mf_faq/guard.py`, checked before retrieval:
  - PII: PAN-like strings, Aadhaar-like 12-digit numbers, account-number phrasing, OTP, email addresses, phone numbers. Response: the assistant does not take that information. Do not echo the matched value. Do not write the question to disk.
  - Advice: buy, sell, hold, "should I", "good for me", portfolio, allocate. Response: a short facts-only refusal and one educational link. Use a kept URL from `data/sources.md` (an official scheme page). Do not recommend a scheme.
  - Returns: returns, CAGR, "which performed better", "higher returns", compare performance. Do not compute. Point to the official factsheet or fund-facts URL already in metadata. If retrieval has not run, use a kept Mid Cap fund-facts URL or another kept official page. Still do not calculate.
- `src/mf_faq/answer.py`:
  - If the guard triggers, return its message and do not call Groq.
  - Otherwise retrieve. If `low_confidence` or the chunks do not contain the asked fact, say the figure is not in the ingested sources and cite the nearest official URL from the chunks. Do not fill the gap from model memory.
  - Otherwise call Groq with only those chunks, the system rules, and the date from `data/ingested_at.txt`.
  - System rules: answer only from the chunks; at most three sentences; exactly one source URL and it must be one of the chunk `source_url` values; end with `Last updated from sources: <date>`; no advice; no return calculations.
  - If the model cites a URL that was not retrieved, replace the citation with the top chunk's `source_url`.
  - If Groq fails, return a short error. Do not invent an answer.
- CLI: `python -m mf_faq.answer "..."`.
- Load `GROQ_API_KEY` with `python-dotenv`. If it is missing, exit with "set GROQ_API_KEY in .env".

**Do not**

- Send the full corpus, `chunks.txt`, or raw files to Groq.
- Store questions or answers.
- Add a second LLM provider.

**Done when**

- The five retrieval questions from Phase 4 return at most three sentences, one in-corpus URL, and the last-updated line.
- "Should I buy HDFC Large Cap Fund?" refuses and does not name a winner.
- "Which of these funds has higher returns?" does not give numbers and links to an official factsheet or fund-facts page.
- "My PAN is ABCDE1234F, what is my balance?" does not repeat the PAN.
- A nonsense question ("What is the NAV of a gold ETF?") does not invent a figure.

**Cursor prompt**

```text
Implement Phase 5 only from docs/implementation.md.
Add the guard and the Groq answer path. Answers must use only retrieved chunks, cite one source URL from those chunks, and stay within three sentences.
Do not build the UI in this phase.
```

## Phase 6 — UI

**Goal.** A single-page chat a reviewer can use without the CLI.

**Build**

- `src/mf_faq/app.py` with Streamlit:
  - Welcome line that names the assistant and the five schemes: HDFC Large Cap, Flexi Cap, ELSS Tax Saver, Mid Cap, and Small Cap.
  - Three buttons that send the example questions from PRD section 7.
  - Persistent disclaimer, visible without a click: "Facts-only. No investment advice."
  - One text input and a send button.
  - The answer shows the reply, one link, and `Last updated from sources:`.
- The app calls `answer.py` only. It does not import the loader and it does not run ingestion.
- `streamlit run src/mf_faq/app.py` documented in the README.
- If Chroma is missing, the page shows the ingest command instead of a stack trace.

**Do not**

- Add login, history files, file upload, or a second page.
- Put the API key in the frontend or in Streamlit secrets committed to git.

**Done when**

- Asking an example question in the browser returns a cited answer.
- Clicking an example button fills and sends that question.
- The disclaimer is on screen before the first question.
- Restarting Streamlit does not re-embed the corpus.

**Cursor prompt**

```text
Implement Phase 6 only from docs/implementation.md.
Add the Streamlit UI described in the PRD: welcome line, three example questions, facts-only disclaimer, and answers with one source link.
The UI must call the existing answer function and must not run ingestion.
```

## Phase 7 — Demo pack

**Goal.** The submission files from PRD section 12, checked against the acceptance criteria.

**Build**

- Finish the README:
  - virtualenv, install, `.env`, `python scripts/ingest.py`, `streamlit run src/mf_faq/app.py`
  - AMC and the five schemes
  - chunk size, overlap, and why (already written in Phase 2; keep it accurate)
  - known limits from PRD section 14, plus any URLs dropped in `data/sources.md`
- `docs/sample_qa.md`: 5–10 real CLI or UI answers, each with the question, the answer text, and the link. Include at least one refusal and one returns question. Paste actual outputs. Do not hand-write imagined answers.
- `docs/disclaimer.md`: the exact disclaimer string shown in the UI.
- Confirm `data/sources.md` and `data/chunks.txt` are present and useful.

**Do not**

- Change retrieval behavior in this phase unless a sample answer violates an acceptance criterion. If you change it, regenerate the sample file.

**Done when**

- A new terminal can follow the README from install through one question without re-running ingest after the first ingest.
- Sample Q&A has 5–10 real entries.
- Acceptance criteria in PRD section 13 hold for the questions you tried.

**Cursor prompt**

```text
Implement Phase 7 only from docs/implementation.md.
Finish the README and add docs/sample_qa.md plus docs/disclaimer.md from real assistant outputs.
Do not expand the corpus or change the architecture.
```

## Rules that apply in every phase

- Public HDFC, SEBI, and AMFI pages only. No third-party blogs as sources.
- Do not compute or compare returns.
- Do not accept or store personal data.
- Do not commit `.env`.
- Do not answer from model memory when the chunks do not contain the fact.
- Keep the two stages separate: ingest once, retrieve on each question.
