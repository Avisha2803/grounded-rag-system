from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


def load_pdf_with_metadata(
    path: str,
    source_org: str,
    doc_title: str,
    doc_type: str,
    version: str | None,
    category: str = "General",
    keywords: list | None = None,
) -> list[Document]:
    """
    Load a PDF page-by-page and attach structured metadata to every page.

    Metadata attached:
        - source_org
        - doc_title
        - doc_type
        - version
        - category
        - keywords
        - file_name
        - file_path
        - page
        - section
    """

    if keywords is None:
        keywords = []

    pdf_path = Path(path)

    reader = PdfReader(str(pdf_path))

    documents = []

    for page_num, page in enumerate(reader.pages, start=1):

        text = page.extract_text()

        if text is None:
            continue

        text = text.strip()

        if len(text) < 20:
            continue

        metadata = {
            "source_org": source_org,
            "doc_title": doc_title,
            "doc_type": doc_type,
            "version": version or "Latest",
            "category": category,
            "keywords": keywords,
            "file_name": pdf_path.name,
            "file_path": str(pdf_path),
            "page": page_num,
            "section": "Unassigned",
        }

        documents.append(
            Document(
                page_content=text,
                metadata=metadata,
            )
        )

    return documents