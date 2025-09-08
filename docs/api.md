# Smart File Search — API Documentation

This document defines the **UI Backend REST API** that the React frontend uses. The backend acts as a thin proxy to the MCP tools and enforces access controls, redaction, and response shaping.

> Base URL (internal only): `http://<internal-ip>:8081/api`

---

## Authentication

- Default: **Internal network only** (no auth).
- Optional: **API key** via header `X-API-Key: <token>` when enabled in configuration.
- TLS termination recommended at ingress if exposed beyond a trusted VLAN.

---

## Conventions

- All responses are JSON.
- Times are ISO 8601 (UTC).
- Errors follow a standard problem shape:

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Query parameter 'query' is required",
    "details": {"field": "query"}
  }
}
```

---

## Endpoints

### 1) Search Files

**GET** `/search`

Search within allow‑listed shared folders using a natural‑language query. The backend may call GPT‑4.1 mini for query rewrite, then the Search Agent (FTS5 + optional semantic rerank).

**Query Parameters**
| Name     | Type   | Default | Description |
|----------|--------|---------|-------------|
| `query`  | string | —       | Natural‑language query. Required. |
| `k`      | int    | 10      | Max number of results to return (1–100). |
| `offset` | int    | 0       | Results offset for pagination. |
| `exts`   | string | —       | Optional comma‑separated list of extensions (e.g. `pdf,docx,pptx`). |
| `years`  | string | —       | Optional comma‑separated list of years (e.g. `2020,2021`). |

**Response 200**
```json
{
  "items": [
    {
      "path": "/mnt/shared/contracts/vendor_x_contract.docx",
      "pointer": "page 3",
      "snippet": "This contract between Vendor X and ...",
      "score": 0.92,
      "modified": "2024-11-05T14:03:11Z",
      "ext": ".docx"
    }
  ],
  "pagination": {"offset": 0, "returned": 10, "total_estimate": 234}
}
```

**Possible Errors**: `400 BAD_REQUEST`, `500 INTERNAL_ERROR`

**Examples**
```bash
curl "http://10.10.1.50:8081/api/search?query=vendor%20x%202021%20ppt%20docx&k=10"
```

---

### 2) File Preview (Safe Snippet)

**GET** `/file-preview`

Fetch a **safe, redacted** excerpt of a file to preview context. Raw files are never returned.

**Query Parameters**
| Name      | Type   | Required | Description |
|-----------|--------|----------|-------------|
| `path`    | string | Yes      | Absolute path of the file within allow‑listed roots. |
| `pointer` | string | No       | Optional pointer (e.g., `page 3`, `slide 5`, `sheet 'Q2'`). |
| `before`  | int    | No       | Extra characters before the hit (default 200). |
| `after`   | int    | No       | Extra characters after the hit (default 200). |

**Response 200**
```json
{
  "path": "/mnt/shared/contracts/vendor_x_contract.docx",
  "pointer": "page 3",
  "preview": "... Vendor X agrees to provide ...",
  "truncated": true
}
```

**Possible Errors**: `400 BAD_REQUEST`, `404 NOT_FOUND`, `403 FORBIDDEN` (path not allowed), `500 INTERNAL_ERROR`

**Example**
```bash
curl "http://10.10.1.50:8081/api/file-preview?path=%2Fmnt%2Fshared%2Fcontracts%2Fvendor_x_contract.docx&pointer=page%203"
```

---

### 3) List Allow‑Listed Roots

**GET** `/roots`

Return the roots (directories) that the backend/MCP server will search.

**Response 200**
```json
{
  "roots": [
    "/mnt/shared/finance",
    "/mnt/shared/hr"
  ]
}
```

---

### 4) Summarize Results

**POST** `/summarize`

Generate a short, user‑friendly summary of search hits using **GPT‑4.1 mini**. The backend forwards only minimal snippets and metadata, never raw files.

**Request Body**
```json
{
  "query": "vendor x 2021 contracts",
  "results": [
    {"path": "/mnt/shared/contracts/vendor_x_contract.docx", "snippet": "Vendor X agrees to ..."},
    {"path": "/mnt/shared/contracts/vendor_x_summary.pptx", "snippet": "Slide mentions contract scope ..."}
  ],
  "style": "bullets"  
}
```

**Response 200**
```json
{
  "summary": "In 2021, Vendor X signed multiple contracts covering services and deliveries. Key files: vendor_x_contract.docx, vendor_x_summary.pptx.",
  "tokens_used": {"prompt": 1421, "completion": 128}
}
```

**Possible Errors**: `400 BAD_REQUEST`, `429 RATE_LIMITED`, `502 LLM_UPSTREAM`, `500 INTERNAL_ERROR`

---

### 5) Health Check

**GET** `/healthz`

Lightweight liveness/readiness signal for monitoring.

**Response 200**
```json
{"status":"ok","time":"2025-09-08T09:00:00Z"}
```

---

## Error Codes

| HTTP | Code              | Meaning |
|------|-------------------|---------|
| 400  | BAD_REQUEST       | Invalid input parameters. |
| 401  | UNAUTHORIZED      | Missing/invalid auth when enabled. |
| 403  | FORBIDDEN         | Path/root not allow‑listed. |
| 404  | NOT_FOUND         | File, root, or resource not found. |
| 409  | CONFLICT          | Index is locked or concurrent op conflict. |
| 429  | RATE_LIMITED      | Too many requests. |
| 500  | INTERNAL_ERROR    | Unhandled backend error. |
| 502  | LLM_UPSTREAM      | LLM provider error/timeout. |

---

## Rate Limiting (Optional)

- Global: 60 requests/minute per IP.
- `file-preview`: 30 requests/minute per IP.
- Headers:
  - `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.

---

## Redaction & Safety

- Regex rules remove emails, phone numbers, secrets, access tokens from previews.
- Snippets capped to 1–2 kB.
- Binary/large files return metadata only.

---

## Pagination Strategy

- `offset` + `k` (limit) cursor.
- `total_estimate` is a best‑effort count from the index.

---

## OpenAPI Sketch

```yaml
openapi: 3.0.3
info:
  title: Smart File Search UI API
  version: 1.0.0
servers:
  - url: http://<internal-ip>:8081/api
paths:
  /search:
    get:
      parameters:
        - in: query
          name: query
          required: true
          schema: {type: string}
        - in: query
          name: k
          schema: {type: integer, minimum: 1, maximum: 100, default: 10}
        - in: query
          name: offset
          schema: {type: integer, minimum: 0, default: 0}
        - in: query
          name: exts
          schema: {type: string}
        - in: query
          name: years
          schema: {type: string}
      responses:
        '200': {description: OK}
  /file-preview:
    get:
      parameters:
        - in: query
          name: path
          required: true
          schema: {type: string}
        - in: query
          name: pointer
          schema: {type: string}
        - in: query
          name: before
          schema: {type: integer, default: 200}
        - in: query
          name: after
          schema: {type: integer, default: 200}
      responses:
        '200': {description: OK}
  /roots:
    get:
      responses:
        '200': {description: OK}
  /summarize:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                query: {type: string}
                results:
                  type: array
                  items:
                    type: object
                    properties:
                      path: {type: string}
                      snippet: {type: string}
                style: {type: string}
      responses:
        '200': {description: OK}
  /healthz:
    get:
      responses:
        '200': {description: OK}
```

---

## Examples (cURL)

```bash
# Search
curl "http://10.10.1.50:8081/api/search?query=vendor%20x%202021%20ppt%20docx&k=10"

# Preview
curl "http://10.10.1.50:8081/api/file-preview?path=%2Fmnt%2Fshared%2Fcontracts%2Fvendor_x_contract.docx&pointer=page%203"

# Roots
curl "http://10.10.1.50:8081/api/roots"

# Summarize
curl -X POST "http://10.10.1.50:8081/api/summarize" \
  -H 'Content-Type: application/json' \
  -d '{
        "query": "vendor x 2021 contracts",
        "results": [
          {"path": "/mnt/shared/contracts/vendor_x_contract.docx", "snippet": "Vendor X agrees to ..."}
        ],
        "style": "bullets"
      }'
```

