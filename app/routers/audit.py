from fastapi import APIRouter, Depends, Query
from app.dependencies import get_audit_logger
from app.middleware.security import api_key_auth

router = APIRouter()


@router.get("/audit/recent")
def recent_audit_logs(
    limit: int = Query(default=50, ge=1, le=500),
    api_key: str = Depends(api_key_auth),
):
    """
    Exposes recent audit trail entries — used by the Streamlit compliance
    dashboard. In a real deployment, restrict this to an admin-scoped API key.
    """
    audit = get_audit_logger()
    return {"logs": audit.recent_logs(limit=limit)}
