# ---- Build stage ----
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Runtime stage ----
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ ./app/
COPY ingestion/ ./ingestion/

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

RUN mkdir -p /data/faiss_index /data/raw_guidelines && \
    chown -R appuser:appuser /data /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
