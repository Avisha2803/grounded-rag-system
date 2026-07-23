from functools import lru_cache
from app.config import get_settings
from app.core.vectorstore import VectorStoreManager
from app.core.rag_chain import GroundedRAGChain
from app.core.audit import AuditLogger


@lru_cache
def get_vectorstore() -> VectorStoreManager:
    settings = get_settings()
    return VectorStoreManager(settings.faiss_index_dir, settings.embedding_model)


@lru_cache
def get_rag_chain() -> GroundedRAGChain:
    settings = get_settings()
    return GroundedRAGChain(get_vectorstore(), settings)


@lru_cache
def get_audit_logger() -> AuditLogger:
    settings = get_settings()
    return AuditLogger(settings.audit_db_path)
