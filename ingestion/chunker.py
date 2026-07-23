import re

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# ------------------------------------------------------------
# Detect common clinical guideline headings
# ------------------------------------------------------------

HEADING_PATTERNS = [

    # 1. Introduction
    re.compile(r"^\d+\.\s+[A-Z].{3,100}$", re.MULTILINE),

    # 1.2 Treatment
    re.compile(r"^(?:\d+\.)+\d*\s+[A-Z].{3,100}$", re.MULTILINE),

    # INTRODUCTION
    re.compile(r"^[A-Z][A-Z\s]{3,80}$", re.MULTILINE),

    # Introduction
    re.compile(
        r"^(Introduction|Background|Recommendations?|Diagnosis|Treatment|"
        r"Management|Prevention|Screening|Monitoring|Follow[- ]?up|"
        r"Implementation|Annex.*|Appendix.*|References?)$",
        re.IGNORECASE | re.MULTILINE,
    ),
]


# ------------------------------------------------------------
# Detect current section
# ------------------------------------------------------------

def detect_section(text: str, fallback: str) -> str:

    for pattern in HEADING_PATTERNS:

        match = pattern.search(text)

        if match:

            heading = match.group(0).strip()

            heading = re.sub(r"\s+", " ", heading)

            return heading

    return fallback


# ------------------------------------------------------------
# Chunk document
# ------------------------------------------------------------

def chunk_document(
    pages: list[Document],
    chunk_size: int = 600,
    chunk_overlap: int = 100,
) -> list[Document]:

    """
    Splits PDF pages into retrieval chunks while preserving metadata.

    Metadata preserved:
        - page
        - source_org
        - doc_title
        - category
        - keywords
        - section
    """

    splitter = RecursiveCharacterTextSplitter(

        chunk_size=chunk_size,

        chunk_overlap=chunk_overlap,

        separators=[
            "\n\n",
            "\n",
            ". ",
            "; ",
            ", ",
            " ",
        ],

        keep_separator=True,
    )

    chunks = []

    current_section = "Introduction"

    for page in pages:

        page_text = page.page_content.strip()

        if not page_text:
            continue

        current_section = detect_section(
            page_text,
            current_section,
        )

        pieces = splitter.split_text(page_text)

        for idx, piece in enumerate(pieces):

            piece = piece.strip()

            if len(piece) < 50:
                continue

            metadata = dict(page.metadata)

            metadata["section"] = current_section

            metadata["chunk_id"] = idx

            chunks.append(

                Document(

                    page_content=piece,

                    metadata=metadata,

                )

            )

    return chunks