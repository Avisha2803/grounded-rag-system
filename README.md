# Healthcare RAG System for Clinical Decision Support

Citation-grounded Retrieval-Augmented Generation over WHO/ICMR-style clinical
guidelines, with a FastAPI backend, FAISS vector retrieval, HuggingFace
medical-domain embeddings, a compliance audit trail, and a Streamlit demo UI.

> ⚠️ This is a decision-**support** reference tool. It does not diagnose or
> prescribe treatment, and every response must be reviewed by a qualified
> clinician. See `app/models.py::QueryResponse.disclaimer`.

## Architecture

```
Streamlit UI  ──HTTP──►  FastAPI (auth + rate limit)
                                │
                                ▼
                   Retriever: FAISS + metadata filter
                   (source_org, doc_type, section, page)
                                │
                                ▼
                 Citation-Grounded Prompt → LLM (Claude/GPT)
                                │
                                ▼
              Grounding Verifier (regex-checks every citation
              against the actually-retrieved chunk metadata)
                                │
                                ▼
             Audit Logger (SQLite: query, chunks used,
             grounding score, latency, timestamp)
                                │
                                ▼
                  JSON response with verified citations
```

### Why this is more than a notebook demo

1. **Grounding is enforced twice.** The prompt instructs the LLM to cite
   every claim in a strict format; a separate regex-based verifier then
   checks each citation against the metadata of chunks *actually retrieved*
   for that query. An LLM can still fabricate a citation — the verifier
   catches it and reports a `grounding_score` instead of trusting the model.
2. **Metadata-first retrieval.** Every chunk carries
   `{source_org, doc_title, section, page, version, doc_type}`, so queries
   can be filtered (e.g. "ICMR only") before semantic search runs.
3. **Explicit refusal path.** If retrieval confidence is below
   `SCORE_THRESHOLD`, the API returns `INSUFFICIENT_GROUNDED_INFORMATION`
   instead of letting the LLM guess.
4. **Audit trail** is a first-class citizen — every query, the chunks used,
   and the grounding score are logged for traceability, a baseline
   compliance requirement for clinical-adjacent tooling.
5. **Pluggable LLM provider** (Anthropic or OpenAI) via env var — no vendor
   lock-in baked into the code.

### Known limitations (worth stating out loud, not hiding)

- The rate limiter is in-memory and per-instance — swap for Redis before
  running more than one API replica.
- The audit log is SQLite — fine for a demo/single-instance deployment,
  swap for Postgres/append-only storage for real production traffic.
- API-key auth is a placeholder for a real IdP (OAuth2/OIDC) integration.

## Project structure

```
healthcare-rag/
├── app/                    # FastAPI backend
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── dependencies.py
│   ├── core/                # RAG chain, vector store, prompts, audit
│   ├── middleware/           # API-key auth + rate limiting
│   └── routers/               # /query, /ingest, /health, /audit/recent
├── ingestion/               # PDF loading, section-aware chunking, index build
├── scripts/                 # Synthetic demo-data generator
├── streamlit_app/           # Demo UI (thin HTTP client over the API)
├── tests/                   # Unit tests, including grounding-verifier tests
├── Dockerfile               # API image
├── streamlit_app/Dockerfile # UI image
└── docker-compose.yml       # Runs both services together
```

## Quickstart

### 1. Configure environment

```bash
cp .env.example .env
```

Then set `LLM_PROVIDER` and the matching API key in `.env`. Supported providers:

| `LLM_PROVIDER` | Cost | Get a key |
|---|---|---|
| `groq` (default) | Free, no credit card | https://console.groq.com/keys |
| `gemini` | Free, no credit card | https://aistudio.google.com/apikey |
| `openrouter` | Free `:free`-suffixed models | https://openrouter.ai/keys |
| `anthropic` | Paid | https://console.anthropic.com |
| `openai` | Paid | https://platform.openai.com |

Make sure `LLM_MODEL` matches the provider (e.g. `llama-3.3-70b-versatile` for
Groq, `gemini-2.5-flash` for Gemini) — see the comments in `.env.example`.

### 2. Install dependencies

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 3. Generate demo guideline PDFs (synthetic — swap for real WHO/ICMR PDFs later)

```bash
python scripts/generate_sample_data.py
```

To use real guidelines instead: drop PDFs into `data/raw_guidelines/`, plus a
sidecar `<filename>.meta.json` per file, e.g.:

```json
{"source_org": "WHO", "doc_title": "Guideline for Malaria Treatment", "doc_type": "guideline", "version": "2024"}
```

### 4. Build the FAISS index

```bash
python -m ingestion.build_index
```

### 5. Run the API

```bash
uvicorn app.main:app --reload
```

### 6. Run the Streamlit demo UI (separate terminal)

```bash
export RAG_API_BASE_URL=http://localhost:8000/api/v1
export RAG_API_KEY=demo-key-123
streamlit run streamlit_app/app.py
```

Open http://localhost:8501 — you get three tabs: **Ask a question**,
**Ingest a guideline**, and **Audit trail**.

### Or run everything via Docker Compose

```bash
docker compose up --build
```

- API → http://localhost:8000/docs (interactive OpenAPI docs)
- Streamlit UI → http://localhost:8501

## Example API call

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: demo-key-123" \
  -H "Content-Type: application/json" \
  -d '{
        "question": "What is first-line pharmacotherapy for type 2 diabetes?",
        "source_filter": ["ICMR"]
      }'
```

## Running tests

```bash
pytest tests/ -v
```

`tests/test_grounding.py` is the most important test file here — it directly
exercises the citation-verification logic that underpins the "near-zero
hallucination" claim, independent of any live LLM call.
