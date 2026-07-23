"""
CLI script to (re)build the FAISS index from all PDFs in RAW_DOCS_DIR.

Usage:
    python -m ingestion.build_index
"""

import os
import logging

from app.config import get_settings
from app.core.vectorstore import VectorStoreManager
from ingestion.metadata import extract_metadata
from ingestion.loader import load_pdf_with_metadata
from ingestion.chunker import chunk_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    settings = get_settings()

    logger.info("=" * 70)
    logger.info("Starting Healthcare RAG Index Builder")
    logger.info("=" * 70)

    vs = VectorStoreManager(
        settings.faiss_index_dir,
        settings.embedding_model,
    )

    all_chunks = []

    pdf_files = [
        f for f in os.listdir(settings.raw_docs_dir)
        if f.lower().endswith(".pdf")
    ]

    logger.info("Found %d PDF files", len(pdf_files))

    for idx, fname in enumerate(pdf_files, start=1):

        logger.info("[%d/%d] Processing %s", idx, len(pdf_files), fname)

        path = os.path.join(settings.raw_docs_dir, fname)

        # -----------------------------
        # Automatically extract metadata
        # -----------------------------
        try:
            meta = extract_metadata(path)

        except Exception as e:
            logger.warning(
                "Metadata extraction failed for %s: %s",
                fname,
                e,
            )

            meta = {
                "source_org": "UNKNOWN",
                "doc_title": fname,
                "doc_type": "Clinical Guideline",
                "version": "Latest",
                "category": "General",
                "keywords": [],
            }

        # -----------------------------
        # Load PDF and create chunks
        # -----------------------------
        try:
            pages = load_pdf_with_metadata(path, **meta)

            chunks = chunk_document(pages)

            logger.info(
                "%s -> %d pages -> %d chunks",
                fname,
                len(pages),
                len(chunks),
            )

            all_chunks.extend(chunks)

        except Exception as e:
            logger.exception(
                "Skipping %s due to error: %s",
                fname,
                e,
            )
            continue

    logger.info("=" * 70)
    logger.info("Total chunks created: %d", len(all_chunks))
    logger.info("=" * 70)

    if not all_chunks:
        logger.error("No valid chunks were created!")
        return

    logger.info("Starting FAISS index creation...")

    try:
        vs.build_from_documents(all_chunks)

    except Exception:
        logger.exception("FAISS index creation failed!")
        raise

    logger.info("FAISS index successfully created.")
    logger.info("Saving FAISS index...")

    logger.info("=" * 70)
    logger.info("SUCCESS!")
    logger.info("Built index with %d chunks", len(all_chunks))
    logger.info("Saved to: %s", settings.faiss_index_dir)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()