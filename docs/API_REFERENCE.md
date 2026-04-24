# KnowShift — API Reference

Base URL (local): `http://localhost:8000`  
Base URL (prod):  `https://knowshift-api.onrender.com`

Interactive docs: `{BASE_URL}/docs` (Swagger UI)

---

## System Endpoints

### `GET /health`

Enhanced health check with per-component status.

**Response**
```json
{
  "status":      "ok",
  "components":  { "supabase": "ok", "gemini": "ok" },
  "version":     "1.0.0",
  "environment": "production",
  "timestamp":   "2025-04-24T12:00:00+00:00"
}
```

`status` is `"ok"` when all components pass; `"degraded"` otherwise.

---

### `GET /stats`

System-wide document and chunk counts.

**Response**
```json
{
  "total_documents":     6,
  "total_chunks":      120,
  "deprecated_chunks":  18,
  "active_chunks":     102,
  "total_change_events": 24,
  "self_healing_events": 24
}
```

---

## Query Endpoints

### `POST /query/ask`

Main RAG endpoint. Embeds the question, retrieves chunks, reranks temporally, and generates an answer via Gemini.

**Request body**
```json
{
  "question":       "What is the first-line treatment for Type 2 Diabetes?",
  "domain":         "medical",
  "include_stale":  false,
  "top_k":          10,
  "return_sources": true
}
```

| Field          | Type    | Required | Default | Notes                        |
|----------------|---------|----------|---------|------------------------------|
| question       | string  | ✅       | —       | 5–500 characters             |
| domain         | string  | ✅       | —       | medical / finance / ai_policy|
| include_stale  | boolean | ❌       | false   | Include stale-flagged chunks |
| top_k          | int     | ❌       | 10      | 1–20                         |
| return_sources | boolean | ❌       | true    | Include source metadata      |

**Response**
```json
{
  "answer":                "GLP-1 receptor agonists are now first-line...",
  "freshness_confidence":  0.87,
  "staleness_warning":     false,
  "sources": [
    {
      "source_name":    "ADA Standards of Care 2024",
      "last_verified":  "2024-01-15T00:00:00",
      "freshness_score": 0.91,
      "chunk_preview":   "GLP-1 receptor agonists and SGLT2 inhibitors..."
    }
  ],
  "ranking_conflicts": [],
  "processing_time_ms": 1842
}
```

**Errors**
| Code | Reason                          |
|------|---------------------------------|
| 422  | Validation error (bad domain, empty question) |
| 500  | Gemini API failure or Supabase error          |

---

### `GET /query/compare`

Runs the same question through both the stale and fresh indexes.
Used by the ChangeMap UI component.

**Query params**
```
question=What+is+the+first-line+treatment...
domain=medical
```

**Response**
```json
{
  "stale_answer": { ...QueryResponse... },
  "fresh_answer": { ...QueryResponse... },
  "difference_detected": true
}
```

> ⚠️ This calls `/query/ask` twice in sequence.
> Expect ~10–15 s on free-tier Gemini.

---

## Ingestion Endpoints

### `POST /ingest/upload`

Ingest a PDF document. Automatically triggers selective re-indexing.

**Request** — `multipart/form-data`

| Field       | Type   | Required | Notes                          |
|-------------|--------|----------|--------------------------------|
| file        | File   | ✅       | PDF only                       |
| domain      | string | ✅       | medical / finance / ai_policy  |
| source_name | string | ✅       | Human-readable name            |
| source_url  | string | ❌       | Canonical URL of the source    |
| published_at| string | ❌       | ISO-8601 datetime              |

**Response**
```json
{
  "document_id":          "uuid-xxx",
  "chunks_ingested":       12,
  "deprecated_old_chunks":  5,
  "self_healing_triggered": true
}
```

> ℹ️ Chunk embedding calls Gemini; rate-limiting adds ~1 s per chunk.
> A 10-page PDF typically takes 30–60 s.

---

## Freshness Endpoints

### `POST /freshness/scan`

Sweep all documents, recompute freshness scores, flag stale.

**Response**
```json
{
  "newly_flagged": 3,
  "total_scanned": 6,
  "timestamp":    "2025-04-24T12:00:00+00:00"
}
```

---

### `GET /freshness/dashboard/{domain}`

Freshness category breakdown for the given domain.

**Path params**: `domain` — medical / finance / ai_policy

**Response**
```json
{
  "domain":     "medical",
  "total":       60,
  "fresh":       35,
  "aging":       12,
  "stale":        8,
  "deprecated":   5
}
```

Note: `total = fresh + aging + stale + deprecated`

---

### `GET /freshness/change-log/{domain}`

Paginated audit trail of all knowledge mutations.

**Query params**

| Param       | Default | Notes                                       |
|-------------|---------|---------------------------------------------|
| limit       | 50      | Max rows to return                          |
| change_type | null    | Filter: deprecated / updated / re-indexed / stale_flagged |

**Response**
```json
{
  "domain":        "medical",
  "total_changes":  18,
  "changes": [
    {
      "id":          "uuid",
      "change_type": "re-indexed",
      "reason":      "Superseded by newer document (similarity: 0.923)",
      "changed_at":  "2025-04-24T11:30:00+00:00",
      "documents":   { "source_name": "ADA 2021", "domain": "medical" }
    }
  ]
}
```

---

### `GET /freshness/reindex-candidates/{domain}`

Documents that are stale and should be replaced with newer sources.

**Response**
```json
{
  "domain":            "finance",
  "candidates_count":   2,
  "candidates": [
    {
      "document_id":         "uuid",
      "source_name":         "Income Tax Rates FY 2021-22",
      "last_verified":       "2021-02-01T00:00:00",
      "avg_freshness":        0.08,
      "active_chunks":        6,
      "recommended_action":  "Re-index with updated source"
    }
  ]
}
```

---

### `POST /freshness/trigger-reindex/{document_id}`

Queue a manual re-index for a specific document.

**Response**
```json
{
  "status":      "Re-index queued",
  "document_id": "uuid-xxx"
}
```

---

## Common HTTP Codes

| Code | Meaning                                   |
|------|-------------------------------------------|
| 200  | Success                                   |
| 201  | Created (some insert operations)          |
| 422  | Unprocessable Entity (Pydantic validation)|
| 500  | Internal server error                     |

All 500 responses include:

```json
{
  "error":  "Internal server error",
  "detail": "..." // full message in dev; safe message in prod
}
```

All responses include the header `X-Process-Time-Ms` (request duration in ms).
