from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)
    source_filter: Optional[list[str]] = Field(
        default=None, description="e.g. ['WHO', 'ICMR']"
    )
    doc_type_filter: Optional[str] = Field(
        default=None, description="e.g. 'guideline', 'protocol'"
    )
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class Citation(BaseModel):
    source_org: str
    doc_title: str
    section: str
    page: int
    version: Optional[str] = None
    relevance_score: float


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    grounding_verified: bool
    grounding_score: float
    latency_ms: float
    disclaimer: str = (
        "This output is a clinical decision-SUPPORT reference generated from "
        "indexed guideline documents. It does not constitute a diagnosis or "
        "treatment decision and must be reviewed by a qualified clinician."
    )


class IngestResponse(BaseModel):
    documents_processed: int
    chunks_created: int
    status: str
