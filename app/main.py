import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, query, ingest, audit

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Healthcare Clinical Guideline RAG API",
    description="Citation-grounded retrieval over WHO/ICMR clinical guidelines",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(query.router, prefix="/api/v1", tags=["query"])
app.include_router(ingest.router, prefix="/api/v1", tags=["ingest"])
app.include_router(audit.router, prefix="/api/v1", tags=["audit"])
