from fastapi import APIRouter
from app.dependencies import get_vectorstore

router = APIRouter()


@router.get("/health")
def health_check():
    vs = get_vectorstore()
    return {
        "status": "ok",
        "index_loaded": vs.store is not None,
    }
