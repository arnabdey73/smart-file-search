# Smart File Search — Architecture Overview

## Goal
Build a secure, fast, and intelligent system to search across **shared folders** containing heterogeneous files (PDF, DOCX, PPTX, XLSX/XLS, CSV, TXT/MD, HTML/XML, JSON, ZIP). The solution combines:

- **Local full‑text search** via SQLite **FTS5**
- Optional **semantic reranking** (Sentence‑Transformers)
- **Natural‑language query understanding & summarization** using **GPT‑4.1 mini**
- A **standardized MCP server** exposing tools (index/search/preview/summarize)
- An **internal Web UI** (React + FastAPI backend) reachable only on an internal IP

---

## High‑Level System Flow

```
User (Browser, internal IP)
   ↓
Web UI (React + Tailwind)
   ↓
UI Backend (FastAPI REST)
   ↓
MCP Server (standard tools)
   ↓
Search Agent  +  GPT‑4.1 mini
   ↓
SQLite FTS Index  +  Shared Folder (read‑only)
```

---

## Components

### 1) Search Agent (`search_agent/`)
Responsible for **indexing** and **retrieval**.

- Recursively scans allow‑listed roots (UNC or mounted paths)
- Extracts text & metadata from: `.pdf, .docx, .pptx, .xlsx/.xls, .csv, .txt, .md, .json, .xml, .html/.htm, .zip`
- Stores segments with pointers (page/slide/sheet) into **SQLite FTS5**
- Incremental re‑index by size/mtime (skips unchanged files)
- Optional embeddings for hybrid ranking (MiniLM or similar)
- CLI:
  - `python cli.py index /mnt/shared`
  - `python cli.py search "vendor X 2021 ppt/docx"`

**Data model (SQLite):**
- `files(id, path, size, mtime, ext)`
- `docs(file_id, pointer, content)` — **FTS5** virtual table
- `vecs(doc_rowid, vec)` — optional embeddings for reranking

---

### 2) LLM Layer (`llm/`)
Uses **GPT‑4.1 mini** for:

- **Query rewrite** → structured filters `{keywords, years, exts}` and an FTS query string
- **Summarization** → concise answer from top‑K snippets with citations/paths

**Guardrails:** never send raw files; only minimal snippets + metadata. API key from `.env`.

---

### 3) MCP Server (`mcp_server/`)
Provides a **standard interface** and policy enforcement.

**Tools exposed:**
- `indexFolder(root)` → triggers (re)index; returns counts `{indexed, skipped, removed}`
- `searchFiles(query, k)` → returns ranked list `{path, pointer, snippet, score}`
- `openFile(path, pointer?)` → safe preview (bounded length, redacted)
- `summarizeResults(query, results[])` → GPT‑4.1 mini summary

**Security & governance:** path allow‑list, snippet caps, regex redaction, rate limits, audit logs.

---

### 4) UI Layer (`ui/`)

**Frontend (React + Tailwind):**
- Search bar with chips (file types, years)
- Results list with filename, pointer, snippet, score
- Preview drawer (safe snippet)

**Backend (FastAPI):**
- REST endpoints consumed by React: `/api/search`, `/api/file-preview`, `/api/roots`
- Proxies requests to MCP server; enforces auth and response shaping

---

## Deployment & Networking

- **Internal‑only access**: expose frontend at `http://<internal-ip>:8080`, backend at `:8081`
- MCP server and search agent run on the same host that mounts the share
- **Volumes**: shared folder mounted **read‑only**; index DB stored under `./data/`
- Optional **Docker Compose** with three services: `mcp_server`, `ui_backend`, `ui_frontend`

---

## Configuration

- `.env`: `GPT_API_KEY`, `DB_PATH=./data/file_index.sqlite3`, `ALLOWED_ROOTS=/mnt/shared,...`
- `config/settings.yaml`: indexing options (chunk sizes, truncation), UI settings
- `config/logging.yaml`: structured logs, rotation policy

---

## Security Considerations

1. **Read‑only mounts** for shared folders
2. **Path allow‑lists** at MCP layer; deny traversal outside roots
3. **Snippet limits** (e.g., 1–2 kB) and **redaction** (emails, secrets, IDs)
4. **Audit logging** of tool calls (query, caller, time, counts)
5. Optional SSO/API‑key on UI backend; network ACLs for internal IP range

---

## Data Flow (Detailed)

1. User enters natural‑language query in UI
2. UI Backend → MCP `searchFiles` with `query`
3. MCP → (Optionally) LLM `rewriteQuery` → build FTS query + filters
4. MCP → Search Agent: run FTS + (optional) semantic rerank → top‑K `{path, pointer, snippet, score}`
5. UI renders results; user may request preview → MCP `openFile` returns safe snippet
6. (Optional) UI requests `summarizeResults` → LLM produces answer with citations

---

## Observability

- **Logs**: indexing stats, search latency, tool invocations, LLM usage
- **Metrics**: index size, docs count, ingestion lag, p95 search latency
- **Health checks**: `/healthz` on UI backend and MCP server

---

## Scaling & Performance

- **Indexing**: incremental; schedule periodic re‑index per root
- **Sharding**: split DB per department if very large; route by root
- **Caching**: memoize recent queries in backend (e.g., Redis)
- **Concurrency**: thread pool for extraction; cap per‑file size to avoid heavy binaries

---

## Failure Modes & Mitigations

- **Corrupt file** → extractor error captured; segment skipped, logged
- **DB locked** → WAL mode + retry/backoff
- **Share unavailable** → surface as `503` with clear message; keep last good index
- **LLM outage** → degrade gracefully (keyword search still works)

---

## Suggested Repository Layout

```
smart-file-search/
├─ docs/
│   └─ architecture.md
├─ mcp_server/
│   ├─ server.py
│   └─ tools/{index_tool.py,search_tool.py,open_file_tool.py,summarize_tool.py}
├─ search_agent/
│   ├─ cli.py  extractor.py  indexer.py  search.py  schema.sql
├─ llm/
│   ├─ client.py  prompt_templates/{query_rewrite.txt,summarization.txt}
├─ ui/
│   ├─ backend/{api.py,config.py}
│   └─ frontend/{src/...}
├─ config/{settings.yaml,logging.yaml}
├─ docker/{Dockerfile*, docker-compose.yaml}
├─ .env  requirements.txt  README.md
```

---

## API (UI Backend → MCP) — Brief

- `GET /api/search?query=...&k=10` → list of results
- `GET /api/file-preview?path=...&pointer=...` → safe snippet
- `GET /api/roots` → allow‑listed roots

MCP tools mirror these with structured schemas.

---

## Non‑Goals (v1)

- Editing files through the UI (search is read‑only)
- Cross‑tenant search outside allow‑listed roots
- Full document rendering; previews are text‑only snippets

---

## Summary
A pragmatic, privacy‑preserving document search system: **FTS5** does the heavy lifting, **GPT‑4.1 mini** improves query intent & summaries, and the **MCP server** standardizes access with strong guardrails. The web UI exposes a simple, internal dashboard for your team to discover the right files quickly and safely.

