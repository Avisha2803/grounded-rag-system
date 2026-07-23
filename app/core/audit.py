import sqlite3
import json
import time
import hashlib
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Every query is logged for compliance/traceability — required for anything
    touching clinical decision support. SQLite is fine for v1; swap for
    Postgres/append-only storage in a real production deployment.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    api_key_hash TEXT,
                    query TEXT,
                    retrieved_chunks TEXT,
                    answer TEXT,
                    grounding_verified INTEGER,
                    grounding_score REAL,
                    latency_ms REAL
                )
            """)

    @staticmethod
    def _hash_key(api_key: str) -> str:
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    def log_query(
        self,
        api_key: str,
        query: str,
        retrieved_docs,
        answer: str,
        grounding_verified: bool,
        grounding_score: float,
        latency_ms: float,
    ):
        chunk_meta = [
            {
                "source_org": d.metadata.get("source_org"),
                "doc_title": d.metadata.get("doc_title"),
                "page": d.metadata.get("page"),
                "score": round(float(s), 4),
            }
            for d, s in retrieved_docs
        ]
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO audit_log
                   (timestamp, api_key_hash, query, retrieved_chunks, answer,
                    grounding_verified, grounding_score, latency_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    time.time(),
                    self._hash_key(api_key),
                    query,
                    json.dumps(chunk_meta),
                    answer,
                    int(grounding_verified),
                    grounding_score,
                    latency_ms,
                ),
            )

    def recent_logs(self, limit: int = 50) -> list[dict]:
        with self._conn() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
