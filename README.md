# ⚖️ LegiFlow — AI Legal Notice & Contract Analysis Engine

[![Tests](https://github.com/saish-vc/promptwars-2/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/saish-vc/promptwars-2/actions/workflows/backend-tests.yml)
[![Frontend](https://img.shields.io/badge/Vercel-Live-brightgreen)](https://promptwars-2-psi.vercel.app)
[![Backend API](https://img.shields.io/badge/Render-Live-blue)](https://legiflow-api.onrender.com)
[![Inference](https://img.shields.io/badge/LLM-Groq%20%7C%20NVIDIA%20NIM-green)](https://integrate.api.nvidia.com)

---

## 🎯 Who Is This For?

LegiFlow is built for **small-business owners, freelancers, and operators** who regularly receive or send legal notices — breach demands, vendor contracts, SaaS agreements — and need to understand their obligations, risks, and negotiation options **without a lawyer on retainer for every document**. It is a hackathon demo tool, not a legal service.

---

## 🏗️ Architecture

```
User (Browser)
    │
    ▼
Vite + React SPA  ──────────────────────────────── Vercel CDN
    │  (VITE_API_URL → legiflow-api.onrender.com)
    │
    ▼ REST / JSON
FastAPI backend  ─────────────────────────────────  Render (free tier)
    │
    ├── LLM Provider (dual)
    │     ├── Groq (active in production: openai/gpt-oss-120b)
    │     └── NVIDIA NIM (meta/llama-3.2-11b-vision-instruct) ← key in .env
    │
    ├── Redis  ──────────────── Prompt cache + circuit-breaker
    │   (REDIS_URL empty on Render → caching disabled in production)
    │
    ├── PostgreSQL (async, SQLAlchemy)
    │     └── pgvector extension → document_chunks table
    │         (EMBEDDING_ENABLED=false on Render → keyword fallback active)
    │
    └── S3 / MinIO blob storage
          (S3 creds empty on Render → local disk fallback active)
```

---

## 🤖 GenAI Architecture Mapping

| Endpoint | AI Technique | Model |
|---|---|---|
| `POST /documents/upload` · `/paste` | Structured text extraction | (sync, no LLM) |
| `POST /analyze/contract` | Structured generation — risk scoring, obligation extraction | NIM / Groq |
| `POST /compare/contracts` | Structured generation — dual-document diff analysis | NIM / Groq |
| `POST /generate/checklist` | Structured generation — action items + lawyer questions | NIM / Groq |
| `POST /generate/negotiation` | Structured generation — counter-clause drafting | NIM / Groq |
| `POST /chat/contract` | **Retrieval-Augmented Generation (RAG)** — hybrid pgvector + BM25 retrieval, confidence scoring, source citation | NIM / Groq |
| `POST /export/lawyer-pack` | Generation — narrative summary bundling all prior outputs | NIM / Groq |
| `POST /documents/embed` | Dense embedding for vector indexing | NVIDIA NIM (`nvidia/nv-embedqa-e5-v5`) |

---

## ⚡ Live Deployments

- **Frontend (Vercel):** <https://promptwars-2-psi.vercel.app>
- **Backend API (Render):** <https://legiflow-api.onrender.com>
- **Swagger Docs:** <https://legiflow-api.onrender.com/docs>

---

## ⚠️ Known Limitations

1. **Free-tier cold start:** Render's free tier spins down after 15 minutes of inactivity. The first request after a cold start can take **30–60 seconds** — this is expected; the app is not broken.

2. **Embedding / RAG path disabled in production:** `EMBEDDING_ENABLED=false` on Render. All chat/RAG queries use the **keyword-intersection fallback** (not pgvector). Turning this on requires: (a) a Postgres instance with the `pgvector` extension installed (Render's free Postgres does not include it — you need at least Supabase free tier or Neon free tier), (b) a populated `document_chunks` table (documents must be uploaded and embedded after the flag is enabled), and (c) `NIM_API_KEY` set for the embedding model.

3. **No document persistence across redeploys:** `ENABLE_FALLBACK_MODE=true` + no S3 credentials means uploaded documents are written to Render's **ephemeral local disk** (`/tmp/legiflow.db`). Any restart or redeploy **wipes all uploaded documents**. For a live demo, upload documents fresh at the start of the session.

4. **No encryption at rest:** Documents uploaded to the fallback SQLite store are not encrypted. Do not upload real sensitive contracts to this demo instance.

5. **Prompt caching disabled:** `REDIS_URL` is empty on Render, so Redis caching and the circuit-breaker state are not active. Repeated identical prompts will hit the LLM API each time.

---

## 💻 Local Development Setup

```bash
# 1. Clone and configure
cp .env.example .env          # Fill in your API keys

# 2. Run backend (SQLite fallback — no Docker needed)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. Run frontend
cd frontend
npm install
npm run dev

# 4. Run tests
cd backend
pytest --tb=short
```

### Full stack with Docker Compose (PostgreSQL + MinIO + Redis)

```bash
docker compose up
```

---

## 🗑️ Data Retention

Uploaded documents are kept **only for the duration of the current server session** (no persistence across restarts in the free-tier deployment). This is a hackathon demo — do not use it to store real sensitive contracts.
