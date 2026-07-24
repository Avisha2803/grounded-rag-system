# ============================================================
# Build Stage
# ============================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt

# ------------------------------------------------------------
# Pre-download HuggingFace embedding model
# ------------------------------------------------------------
ENV HF_HOME=/tmp/huggingface
ENV TRANSFORMERS_CACHE=/tmp/huggingface

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5')"

# ============================================================
# Runtime Stage
# ============================================================
FROM python:3.11-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Python packages
COPY --from=builder /root/.local /home/appuser/.local

# Pre-downloaded HuggingFace cache
COPY --from=builder /tmp/huggingface /home/appuser/.cache/huggingface

# Application
COPY app/ ./app/
COPY ingestion/ ./ingestion/

# ------------------------------------------------------------
# IMPORTANT
# Copy your FAISS index into the container
# ------------------------------------------------------------
COPY faiss_index/ ./faiss_index/

# Optional (if you keep PDFs in the image)
COPY data/ ./data/

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# HuggingFace cache location
ENV HF_HOME=/home/appuser/.cache/huggingface
ENV TRANSFORMERS_CACHE=/home/appuser/.cache/huggingface

RUN mkdir -p \
    /home/appuser/.cache/huggingface \
    /data/faiss_index \
    /data/raw_guidelines && \
    chown -R appuser:appuser \
    /home/appuser \
    /data \
    /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]