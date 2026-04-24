"""
KnowShift — Ingestion Router  (Phase 2 — adds selective re-indexing)
Handles PDF document upload, text extraction, chunking, embedding, and storage.
After chunk insertion, runs selective_reindex() to deprecate overlapping old content.

POST /ingest/upload
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.database import supabase
from app.services import chunker, embedder
from app.services.freshness_engine import compute_freshness_score, selective_reindex

logger = logging.getLogger(__name__)

router = APIRouter()

_VALID_DOMAINS = {"medical", "finance", "ai_policy"}
_STORAGE_BUCKET = "documents"
_EMBED_SLEEP_SECONDS = 1  # Honour free-tier Gemini rate limit (15 req/min)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(..., description="PDF document to ingest"),
    domain: str = Form(..., description="Knowledge domain: medical | finance | ai_policy"),
    source_name: str = Form(..., description="Human-readable name for the source"),
    source_url: Optional[str] = Form(None, description="URL of the original source (optional)"),
    published_at: Optional[str] = Form(None, description="ISO 8601 publication date (optional)"),
) -> dict:
    """Upload and fully ingest a PDF document with self-healing re-indexing.

    Processing pipeline:
      1. Validate inputs.
      2. Upload raw PDF to Supabase Storage.
      3. Insert document metadata into `documents` table.
      4. Extract text → chunk text.
      5. Embed each chunk (Gemini text-embedding-004, rate-limited).
      6. Batch-insert chunks with embeddings into `chunks` table.
      7. Run selective_reindex() — deprecate semantically overlapping old chunks.

    Returns:
        {
            "document_id": str,
            "chunks_ingested": int,
            "deprecated_old_chunks": int,
            "self_healing_triggered": bool
        }
    """
    # -------------------------------------------------------------------------
    # 1. Validate domain
    # -------------------------------------------------------------------------
    if domain not in _VALID_DOMAINS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid domain '{domain}'. Must be one of: {sorted(_VALID_DOMAINS)}",
        )

    # -------------------------------------------------------------------------
    # 2. Read file bytes
    # -------------------------------------------------------------------------
    try:
        file_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not read uploaded file.")

    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    # -------------------------------------------------------------------------
    # 3. Upload raw PDF to Supabase Storage
    # -------------------------------------------------------------------------
    doc_uuid = str(uuid.uuid4())
    storage_path = f"{domain}/{doc_uuid}.pdf"

    try:
        supabase.storage.from_(_STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"},
        )
        logger.info("PDF uploaded to storage | path=%s", storage_path)
    except Exception as exc:
        logger.error("Supabase Storage upload failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload PDF to storage: {exc}",
        )

    # -------------------------------------------------------------------------
    # 4. Insert document metadata
    # -------------------------------------------------------------------------
    published_at_dt: Optional[str] = None
    if published_at:
        try:
            published_at_dt = datetime.fromisoformat(published_at).isoformat()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid published_at format '{published_at}'. Use ISO 8601.",
            )

    doc_record = {
        "id":            doc_uuid,
        "domain":        domain,
        "source_url":    source_url,
        "source_name":   source_name,
        "published_at":  published_at_dt,
        "last_verified": datetime.now(timezone.utc).isoformat(),
        "stale_flag":    False,
    }

    try:
        supabase.table("documents").insert(doc_record).execute()
        logger.info("Document metadata inserted | id=%s | domain=%s", doc_uuid, domain)
    except Exception as exc:
        logger.error("Failed to insert document metadata: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to insert document record: {exc}",
        )

    # -------------------------------------------------------------------------
    # 5. Extract text from PDF
    # -------------------------------------------------------------------------
    try:
        raw_text = chunker.extract_text_from_pdf(file_bytes)
    except ValueError as exc:
        logger.error("PDF parsing failed for document %s: %s", doc_uuid, exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"PDF parsing error: {exc}",
        )

    if not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No text could be extracted from the PDF. It may be image-only.",
        )

    # -------------------------------------------------------------------------
    # 6. Chunk the text
    # -------------------------------------------------------------------------
    chunks = chunker.chunk_text(raw_text)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text chunking produced zero chunks.",
        )

    logger.info("Chunks created | count=%d | document_id=%s", len(chunks), doc_uuid)

    # Initial freshness is 1.0 for a freshly ingested document
    initial_freshness = compute_freshness_score(
        last_verified=datetime.now(timezone.utc),
        domain=domain,
    )

    # -------------------------------------------------------------------------
    # 7. Embed each chunk — stored separately so we can reuse for re-indexing
    # -------------------------------------------------------------------------
    embeddings_list: list = []
    chunk_records: list = []

    for idx, chunk_text_val in enumerate(chunks):
        try:
            embedding = embedder.embed_text(chunk_text_val)
        except Exception as exc:
            logger.error("Embedding failed for chunk %d of document %s: %s", idx, doc_uuid, exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini embedding error on chunk {idx}: {exc}",
            )

        embeddings_list.append(embedding)
        chunk_records.append({
            "document_id":   doc_uuid,
            "chunk_text":    chunk_text_val,
            "embedding":     embedding,
            "freshness_score": initial_freshness,
            "is_deprecated": False,
        })

        # Respect Gemini free-tier rate limit between calls
        if idx < len(chunks) - 1:
            time.sleep(_EMBED_SLEEP_SECONDS)

    # -------------------------------------------------------------------------
    # 8. Batch-insert all chunks
    # -------------------------------------------------------------------------
    try:
        supabase.table("chunks").insert(chunk_records).execute()
        logger.info("Chunks inserted | count=%d | document_id=%s", len(chunk_records), doc_uuid)
    except Exception as exc:
        logger.error("Failed to insert chunks for document %s: %s", doc_uuid, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to store chunks: {exc}",
        )

    # -------------------------------------------------------------------------
    # 9. Selective re-indexing — deprecate semantically overlapping old chunks
    # -------------------------------------------------------------------------
    reindex_result = {"deprecated_chunks": 0, "deprecated_ids": []}
    try:
        reindex_result = selective_reindex(
            new_doc_id=doc_uuid,
            domain=domain,
            new_chunk_embeddings=embeddings_list,
        )
        logger.info(
            "Selective re-index | deprecated=%d | document_id=%s",
            reindex_result["deprecated_chunks"], doc_uuid,
        )
    except Exception as exc:
        # Non-fatal: log the failure but don't fail the whole upload
        logger.error("selective_reindex failed (non-fatal) for doc %s: %s", doc_uuid, exc)

    deprecated_count = reindex_result["deprecated_chunks"]

    return {
        "document_id":           doc_uuid,
        "chunks_ingested":       len(chunk_records),
        "deprecated_old_chunks": deprecated_count,
        "self_healing_triggered": deprecated_count > 0,
    }
