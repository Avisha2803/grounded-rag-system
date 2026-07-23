from langchain_core.documents import Document
from ingestion.chunker import chunk_document, detect_section


def test_detect_section_finds_numbered_heading():
    text = "2. FIRST-LINE THERAPY\n\nSome clinical content here."
    assert detect_section(text, fallback="Intro") == "2. FIRST-LINE THERAPY"


def test_chunk_document_preserves_metadata():
    pages = [
        Document(
            page_content="1. INTRODUCTION\n\n" + ("clinical text " * 200),
            metadata={
                "source_org": "WHO",
                "doc_title": "Test Doc",
                "page": 1,
                "doc_type": "guideline",
                "version": "1",
            },
        )
    ]
    chunks = chunk_document(pages, chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    for c in chunks:
        assert c.metadata["source_org"] == "WHO"
        assert c.metadata["page"] == 1
        assert c.metadata["section"] == "1. INTRODUCTION"
