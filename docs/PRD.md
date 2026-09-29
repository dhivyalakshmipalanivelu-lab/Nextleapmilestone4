# Product Requirements Document

## Mutual Fund FAQ Assistant (Facts-Only RAG Chatbot)

| | |
|---|---|
| Product | Facts-only FAQ chatbot for HDFC mutual fund schemes |
| Type | Class demo prototype (Nextleap Milestone 4) |
| AMC | HDFC Mutual Fund |
| Status | Draft for build |

## 1. Problem

Retail users and support or content teams repeatedly ask the same factual questions about mutual fund schemes: expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer, benchmark, and how to download statements. Answers today are scattered across official AMC pages and PDFs. People also get investment opinions when they only needed a fact and a source.

This product answers those questions from official public pages only, cites one source on every answer, and refuses advice.

## 2. Product summary

A small Retrieval-Augmented Generation (RAG) chatbot. It answers using only documents ingested from public HDFC, SEBI, and AMFI pages for five HDFC schemes. It does not use general model knowledge as the source of facts.

Every answer is at most three sentences, includes one citation link, and ends with a “Last updated from sources” line. The UI states that the assistant is facts-only and does not give investment advice.

## 3. Who it is for

- Retail users comparing schemes and looking up a published fact.
- Support and content teams answering repetitive mutual fund questions.

The demo is a class prototype, not a production support tool.

## 4. Goals

1. Answer factual scheme questions from the scoped corpus.
2. Show one clear source link in every answer.
3. Refuse buy, sell, and portfolio questions with a polite facts-only message and a relevant educational link.
4. Run a full RAG pipeline: ingest once, retrieve on each question.
5. Ship a working prototype a reviewer can try, plus the written deliverables in section 12.

## 5. Non-goals

- Investment advice, suitability, or portfolio construction.
- Computing, ranking, or comparing returns or performance.
- Accepting or storing personal data (PAN, Aadhaar, account numbers, OTPs, email, phone).
- Using third-party blogs, news, or screenshots of internal systems as sources.
- Covering AMCs or schemes outside the corpus below.
- Production auth, multi-user accounts, or live statement downloads on behalf of a user.

## 6. Corpus

One AMC, five schemes. Sources are official public pages only.

### Schemes

1. HDFC Large Cap Fund
2. HDFC Flexi Cap Fund
3. HDFC ELSS Tax Saver
4. HDFC Mid Cap Fund (Mid-Cap Opportunities)
5. HDFC Small Cap Fund

### Source URLs

| # | Scheme | URL |
|---|---|---|
| 1 | Large Cap | https://www.hdfcfund.com/explore/mutual-funds/hdfc-large-cap-fund/regular |
| 2 | Large Cap | https://hdfcfund.com/explore/mutual-funds/hdfc-large-cap-fund/direct |
| 3 | Large Cap | https://www.hdfcfund.com/product-solutions/overview/hdfc-large-cap-fund/direct |
| 4 | Flexi Cap | https://hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct |
| 5 | Flexi Cap | https://www.hdfcfund.com/mutual-funds/hdfc-flexi-cap-fund |
| 6 | ELSS Tax Saver | https://www.hdfcfund.com/explore/mutual-funds/hdfc-elss-tax-saver-fund/direct |
| 7 | ELSS Tax Saver | https://www.hdfcfund.com/product-solutions/overview/hdfc-elss-tax-saver/direct |
| 8 | ELSS Tax Saver | https://www.hdfcfund.com/product-solutions/overview/hdfc-elss-tax-saver/regular |
| 9 | Mid Cap | https://www.hdfcfund.com/product-solutions/overview/hdfc-mid-cap-opportunities-fund/direct |
| 10 | Mid Cap | https://www.hdfcfund.com/product-solutions/overview/hdfc-mid-cap-opportunities-fund/regular |
| 11 | Mid Cap (PDF) | https://files.hdfcfund.com/s3fs-public/Others/2026-07/Fund%20Facts%20-%20HDFC%20Mid-Cap%20Fund_July%2026.pdf |
| 12 | Mid Cap (PDF) | https://files.hdfcfund.com/s3fs-public/Others/2026-06/Fund%20Facts%20-%20HDFC%20Mid-Cap%20Fund_June%2026.pdf |
| 13 | Small Cap | https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/direct |
| 14 | Small Cap | https://www.hdfcfund.com/explore/mutual-funds/hdfc-small-cap-fund/regular |
| 15 | Small Cap | https://www.hdfcfund.com/product-solutions/overview/hdfc-small-cap-fund/direct |

The milestone also asks for a submitted source list of the URLs actually used (CSV or Markdown). Ingestion may drop a URL if the page is unreachable or has no extractable text; the source list and README must record what was kept and why anything was dropped.

Preferred page types when a URL is thin or broken: factsheets, KIM/SID, scheme FAQs, fee and charges pages, riskometer and benchmark notes, and statement or tax-document guides from the AMC, SEBI, or AMFI.

## 7. User experience

Tiny chat UI:

- Welcome line that names the assistant and the five schemes.
- Three example questions the user can click or copy.
- Persistent note: **Facts-only. No investment advice.**
- A single text input and a send action.
- Each answer shows the reply text, one citation link, and `Last updated from sources: <date>`.

### Example questions (UI)

1. What is the expense ratio of HDFC Large Cap Fund Direct?
2. What is the lock-in period for HDFC ELSS Tax Saver?
3. What is the minimum SIP for HDFC Flexi Cap Fund?

### Answer rules

- Facts only, drawn from retrieved chunks.
- At most three sentences.
- Exactly one clear citation link (the source URL for the chunk used).
- If the fact is not in the corpus, say so and point to the most relevant official page. Do not invent a number.
- Performance or returns questions: do not calculate or compare. Link to the official factsheet.
- Advice questions (“Should I buy or sell?”, “Is this good for me?”, portfolio allocation): refuse. Reply with a short facts-only message and one educational link (for example an official scheme page or a SEBI/AMFI investor-education page already in scope).

## 8. Functional requirements

| ID | Requirement |
|---|---|
| FR-1 | User can ask a natural-language question in the UI. |
| FR-2 | System embeds the question with the same model used at ingestion and retrieves the top matching chunks from ChromaDB. |
| FR-3 | The LLM answers only from retrieved context. |
| FR-4 | Every successful factual answer includes one source URL. |
| FR-5 | Answers are at most three sentences and include “Last updated from sources:”. |
| FR-6 | Opinion, advice, and portfolio questions are refused as specified in section 7. |
| FR-7 | The assistant does not ask for or store PAN, Aadhaar, account numbers, OTPs, email, or phone numbers. If a user pastes them, the assistant declines to use or repeat them. |
| FR-8 | Ingestion can be run once; the app answers questions on later starts without re-embedding the corpus. |
| FR-9 | Chunks are written to a readable `.txt` file so a reviewer can inspect them. |

## 9. RAG architecture

Two stages. Both are required. The app must not call the LLM on the full corpus or answer from parametric memory.

### Ingestion (run once)

`Load → Chunk → Embed → Store in vector DB`

1. **Load.** Fetch the scoped HTML pages and PDFs. Keep source URL, scheme name, plan (direct or regular) when known, and document title.
2. **Chunk.** Split loaded text before any embedding code is written. The chunking choice must be written down: why it fits this data, chunk size, overlap, and metadata kept on each chunk. Save all chunks to a readable `.txt` file.
3. **Embed.** `sentence-transformers/all-MiniLM-L6-v2`, local, no API key, 384-dimension vectors.
4. **Store.** Persist embeddings and metadata in ChromaDB on disk.

### Query (every question)

`Question → Embed → Retrieve top chunks → LLM → Answer`

1. Embed the user question with the same MiniLM model.
2. Retrieve the top chunks from the persisted Chroma collection.
3. Send only those chunks plus the answer rules to Groq.
4. Return the answer, one citation, and the last-updated line.

### Chunk metadata (minimum)

- `source_url`
- `scheme`
- `plan` (direct, regular, or unknown)
- `doc_title` or filename
- `chunk_index`

Chunk size, overlap, and any extra metadata are decided after the loaded text is inspected, then recorded in the README.

## 10. Technical constraints

| Piece | Choice |
|---|---|
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (local, 384-d). Same model for chunks and questions. |
| Vector store | ChromaDB, persisted to disk. Ingestion does not run on every app restart. |
| LLM | Groq. API key in `.env` only. `.env` is gitignored and never committed. |
| Sources | Public AMC / SEBI / AMFI pages in section 6. No third-party blogs. |
| Secrets | No API keys, credentials, or personal data in the repo or in logs. |

## 11. Safety and compliance

- Public sources only.
- No PII collection or storage.
- No performance claims and no return calculations.
- No investment advice.
- Answers stay short and cite a source.
- UI disclaimer is visible without opening a menu: facts-only, no advice.

Suggested disclaimer (UI and submitted snippet):

> Facts-only. No investment advice. Answers are short summaries of official public pages for the listed HDFC schemes, with one source link. This assistant does not recommend buying, selling, or holding any scheme.

## 12. Deliverables

1. Working prototype (hosted app or notebook). If hosting is not possible, a demo video of at most 3 minutes.
2. Source list (CSV or Markdown) of the URLs actually used.
3. README: setup steps, AMC and schemes in scope, chunking decision, and known limits.
4. Sample Q&A file: 5–10 queries with the assistant’s answers and links.
5. Disclaimer snippet used in the UI.
6. Inspectable chunk dump (`.txt`) from ingestion.

## 13. Acceptance criteria

- A reviewer can start the app using the README and ask a question without re-running ingestion.
- Expense ratio, exit load, minimum SIP, ELSS lock-in, riskometer or benchmark, and statement-download questions for in-scope schemes return a factual answer of at most three sentences and one official link.
- “Should I buy this fund?” is refused and does not recommend a scheme.
- “Which fund has higher returns?” does not compute or compare returns; it points to an official factsheet.
- A question outside the corpus does not invent a figure.
- Chunks exist in Chroma on disk and in the readable `.txt` dump.
- `.env` is not in git. The Groq key is read from the environment.

## 14. Known limits (expected)

- Corpus is five HDFC schemes and the URLs in section 6. Other funds are out of scope.
- Facts can go stale when the AMC updates a page after the last ingestion. The “Last updated from sources” line is the transparency control, not a live crawl.
- HTML and PDF extraction can miss text inside images or interactive widgets.
- The prototype is a demo. It is not a substitute for the scheme information document or for advice from a registered advisor.
