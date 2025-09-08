# Smart File Search — MCP Tools Specification

This document defines the **Model Context Protocol (MCP)** tools exposed by the Smart File Search server. MCP provides a secure, standardized interface so assistants, IDEs, and services can use the search capabilities with strong guardrails.

Version: **v1.0.0**  
Status: **Stable**

---

## Conventions
- **All tools** return JSON.
- **Paths** must resolve inside configured **allow‑listed roots**.
- **Snippets** are **text‑only** and **redacted**. Raw files are never returned.
- **Pointer** is a human‑friendly locator (e.g., `page 3`, `slide 7`, `sheet 'Q2'`).
- Timeouts, rate limits, and snippet caps are enforced server‑side.

---

## Common Error Shape
```json
{
  "error": {
    "code": "FORBIDDEN|BAD_REQUEST|NOT_FOUND|RATE_LIMITED|INTERNAL_ERROR|LLM_UPSTREAM",
    "message": "human readable",
    "details": {"hint": "optional context"}
  }
}
```

---

## Tool: `listRoots`
Return the allow‑listed root directories.

**Request**
```json
{}
```

**Response**
```json
{
  "roots": [
    "/mnt/shared/finance",
    "/mnt/shared/hr"
  ]
}
```

**Errors**: none (unless configuration missing → `INTERNAL_ERROR`).

---

## Tool: `indexFolder`
Schedule or run indexing for a folder inside the allow‑listed roots. Performs incremental re‑indexing based on file size and mtime.

**Request**
```json
{
  "root": "/mnt/shared/finance",
  "full": false,
  "priority": "normal"  
}
```
- `root` (string, required): target directory (must be within allow‑list).
- `full` (bool, default `false`): if `true`, force rebuild (drops prior docs for files in this root).
- `priority` (enum: `low|normal|high`): scheduler hint.

**Response**
```json
{
  "indexed": 150,
  "skipped": 20,
  "removed": 3,
  "duration_ms": 8421
}
```

**Errors**: `FORBIDDEN` (root not allowed), `NOT_FOUND` (path missing), `CONFLICT` (index busy), `INTERNAL_ERROR`.

---

## Tool: `searchFiles`
Keyword + optional semantic search using the index. Supports simple filter extraction (exts/years) and returns ranked results with snippets.

**Request**
```json
{
  "query": "contracts about vendor X from 2021 in ppt or docx",
  "k": 10,
  "offset": 0,
  "exts": [".pptx", ".docx"],
  "years": ["2021"],
  "roots": ["/mnt/shared/finance"]
}
```
- `query` (string, required): natural‑language query.
- `k` (int, default 10, 1–100): max results.
- `offset` (int, default 0): pagination offset.
- `exts` (array<string>, optional): restrict to extensions.
- `years` (array<string>, optional): only results containing these years (filename or content).
- `roots` (array<string>, optional): restrict search to specific allow‑listed roots.

**Response**
```json
{
  "items": [
    {
      "path": "/mnt/shared/contracts/vendor_x_contract.docx",
      "pointer": "page 3",
      "snippet": "This contract between Vendor X and …",
      "score": 0.91,
      "ext": ".docx",
      "modified": "2024-11-05T14:03:11Z"
    }
  ],
  "pagination": {"offset": 0, "returned": 10, "total_estimate": 234}
}
```

**Errors**: `BAD_REQUEST` (missing query), `FORBIDDEN` (roots not allowed), `INTERNAL_ERROR`.

---

## Tool: `openFile`
Return a **safe preview** (snippet) for a given file and optional pointer. Enforces snippet length limits and redaction.

**Request**
```json
{
  "path": "/mnt/shared/contracts/vendor_x_contract.docx",
  "pointer": "page 3",
  "before": 200,
  "after": 200
}
```
- `path` (string, required): absolute file path within allow‑listed roots.
- `pointer` (string, optional): locator for finer context.
- `before`/`after` (int, optional): additional characters surrounding hit (caps applied server‑side).

**Response**
```json
{
  "path": "/mnt/shared/contracts/vendor_x_contract.docx",
  "pointer": "page 3",
  "preview": "… Vendor X agrees to provide …",
  "truncated": true
}
```

**Errors**: `FORBIDDEN` (path not allowed), `NOT_FOUND` (file missing), `INTERNAL_ERROR`.

---

## Tool: `summarizeResults`
Produce a concise summary using **GPT‑4.1 mini** from a limited set of snippets. Never sends raw documents.

**Request**
```json
{
  "query": "vendor x 2021 contracts",
  "results": [
    {"path": "/mnt/shared/contracts/vendor_x_contract.docx", "snippet": "Vendor X agrees to …"},
    {"path": "/mnt/shared/contracts/vendor_x_summary.pptx", "snippet": "Slide mentions contract scope …"}
  ],
  "style": "bullets",
  "max_tokens": 400
}
```
- `query` (string, required)
- `results` (array<object>, required): path + snippet items
- `style` (string, optional): `bullets|paragraph|table`
- `max_tokens` (int, optional): cap on completion length

**Response**
```json
{
  "summary": "In 2021, Vendor X signed multiple contracts covering services and deliveries. Key files: vendor_x_contract.docx, vendor_x_summary.pptx.",
  "tokens_used": {"prompt": 1421, "completion": 128}
}
```

**Errors**: `LLM_UPSTREAM` (provider error/timeout), `RATE_LIMITED`, `INTERNAL_ERROR`.

---

## Tool: `rewriteQuery` (optional)
Translate a natural‑language query into structured filters and an FTS‑ready string using GPT‑4.1 mini.

**Request**
```json
{
  "query": "Find vendor X contracts from 2021 in ppt or docx"
}
```

**Response**
```json
{
  "fts": "vendor NEAR/5 contract AND (2021)",
  "filters": {"exts": [".pptx", ".docx"], "years": ["2021"]},
  "notes": "NEAR/5 used to pair 'vendor' and 'contract'"
}
```

**Errors**: `LLM_UPSTREAM`, `INTERNAL_ERROR`.

---

## Permissions & Guardrails
- **Allow‑list**: `roots` and `path` values must be children of configured directories.
- **Snippet caps**: previews limited to 1–2 kB; server may reduce `before/after` automatically.
- **Redaction**: email, phone, secret/token patterns removed from previews.
- **Rate limits** (suggested defaults):
  - `searchFiles`: 60 req/min per client
  - `openFile`: 30 req/min per client
  - `summarizeResults`: 20 req/min per client
- **Audit**: log tool name, caller, timestamp, counts, latency; omit sensitive query contents when configured.

---

## Versioning
- Tools include a response header/field `mcp_version: v1.0.0`.
- Backward‑compatible changes bump **minor**; breaking changes bump **major** with deprecation window.

---

## Examples (Pseudo‑invocations)

```jsonc
// 1) list roots
{"tool": "listRoots", "args": {}}

// 2) index finance folder
{"tool": "indexFolder", "args": {"root": "/mnt/shared/finance", "full": false}}

// 3) search files
{"tool": "searchFiles", "args": {"query": "vendor x 2021 ppt docx", "k": 10}}

// 4) preview a file
{"tool": "openFile", "args": {"path": "/mnt/shared/contracts/vendor_x_contract.docx", "pointer": "page 3"}}

// 5) summarize results
{"tool": "summarizeResults", "args": {"query": "vendor x 2021 contracts", "results": [{"path": "…", "snippet": "…"}]}}
```

---

## Notes for Implementers
- Consider running the MCP server **co‑located** with the share (low latency I/O).
- Use SQLite **WAL** mode and periodic `VACUUM` for index health.
- Use a worker queue for `indexFolder` (watchdog/cron) to avoid API timeouts.
- Provide health checks and metrics (`/healthz`, `/metrics`) for ops.

---

## Change Log
- **v1.0.0**: Initial stable spec with `listRoots`, `indexFolder`, `searchFiles`, `openFile`, `summarizeResults`, and optional `rewriteQuery`.

