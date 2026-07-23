from app.core.rag_chain import GroundedRAGChain
from langchain_core.documents import Document


def _fake_chain():
    # Bypass __init__ so no real LLM/embeddings are instantiated for this unit test.
    return GroundedRAGChain.__new__(GroundedRAGChain)


def test_verify_grounding_rejects_hallucinated_citation():
    chain = _fake_chain()
    retrieved = [
        (
            Document(
                page_content="x",
                metadata={
                    "source_org": "WHO",
                    "doc_title": "Hypertension Guideline",
                    "section": "2. FIRST-LINE THERAPY",
                    "page": 3,
                },
            ),
            0.9,
        ),
    ]
    answer = (
        "Thiazide diuretics are first-line. "
        "[Source: WHO, Hypertension Guideline, Section 2. FIRST-LINE THERAPY, p.3] "
        "Also see [Source: ICMR, Fake Guideline, Section 9, p.99]"
    )

    verified, score, citations = chain._verify_grounding(answer, retrieved)

    assert verified is False  # one of two citations is fabricated
    assert 0 < score < 1
    assert any(c["verified"] for c in citations)
    assert any(not c["verified"] for c in citations)


def test_verify_grounding_accepts_fully_grounded_answer():
    chain = _fake_chain()
    retrieved = [
        (
            Document(
                page_content="x",
                metadata={
                    "source_org": "ICMR",
                    "doc_title": "Diabetes Guideline",
                    "section": "3. FIRST-LINE PHARMACOTHERAPY",
                    "page": 5,
                },
            ),
            0.95,
        ),
    ]
    answer = (
        "Metformin is recommended as first-line therapy. "
        "[Source: ICMR, Diabetes Guideline, Section 3. FIRST-LINE PHARMACOTHERAPY, p.5]"
    )

    verified, score, citations = chain._verify_grounding(answer, retrieved)

    assert verified is True
    assert score == 1.0
    assert citations[0]["verified"] is True
