import os
import tempfile
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from app.models import IngestResponse
from app.dependencies import get_vectorstore
from app.middleware.security import api_key_auth
from ingestion.loader import load_pdf_with_metadata
from ingestion.chunker import chunk_document

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile,
    source_org: str,
    doc_title: str,
    doc_type: str = "guideline",
    version: str | None = None,
    api_key: str = Depends(api_key_auth),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF ingestion is supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        pages = load_pdf_with_metadata(
            tmp_path, source_org=source_org, doc_title=doc_title,
            doc_type=doc_type, version=version,
        )
        chunks = chunk_document(pages)

        vs = get_vectorstore()
        vs.add_documents(chunks)

        return IngestResponse(
            documents_processed=1, chunks_created=len(chunks), status="success"
        )
    finally:
        os.unlink(tmp_path)
