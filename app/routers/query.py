import logging
from fastapi import APIRouter, Depends
from app.models import QueryRequest, QueryResponse, Citation
from app.dependencies import get_rag_chain, get_audit_logger
from app.middleware.security import api_key_auth

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_guidelines(
    body: QueryRequest,
    api_key: str = Depends(api_key_auth),
):
    chain = get_rag_chain()
    audit = get_audit_logger()

    result = chain.answer(
        question=body.question,
        source_filter=body.source_filter,
        doc_type_filter=body.doc_type_filter,
        top_k=body.top_k,
    )

    audit.log_query(
        api_key=api_key,
        query=body.question,
        retrieved_docs=result["retrieved_docs"],
        answer=result["answer"],
        grounding_verified=result["grounding_verified"],
        grounding_score=result["grounding_score"],
        latency_ms=result["latency_ms"],
    )

    citations = [
        Citation(
            source_org=c["source_org"],
            doc_title=c["doc_title"],
            section=c["section"],
            page=c["page"],
            relevance_score=next(
                (s for d, s in result["retrieved_docs"]
                 if d.metadata.get("doc_title") == c["doc_title"]),
                0.0,
            ),
        )
        for c in result["citations"]
        if c["verified"]
    ]

    return QueryResponse(
        answer=result["answer"],
        citations=citations,
        grounding_verified=result["grounding_verified"],
        grounding_score=result["grounding_score"],
        latency_ms=result["latency_ms"],
    )
