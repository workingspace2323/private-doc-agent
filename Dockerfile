# ── Dockerfile ────────────────────────────────────────────────────────────────
# Multi-stage build for the Private Document Agent
# Usage:
#   docker build -t docagent .
#   docker run -p 8000:8000 \
#     -e ANTHROPIC_API_KEY=sk-ant-xxx \
#     -v $(pwd)/data:/app/data \
#     docagent

FROM python:3.11-slim AS base

# System dependencies for PDF and DOCX processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model so it's baked into the image
# (avoids ~90MB download at container start time)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ── Copy application code ─────────────────────────────────────────────────────
COPY core/     ./core/
COPY utils/    ./utils/
COPY static/   ./static/
COPY app.py    .
COPY main.py   .

# ── Data directories (override with volume mounts) ────────────────────────────
RUN mkdir -p data/documents data/vectorstore

# ── Environment defaults ──────────────────────────────────────────────────────
ENV VECTOR_STORE_PATH=/app/data/vectorstore
ENV DOCUMENTS_PATH=/app/data/documents
ENV CHUNK_SIZE=3200
ENV CHUNK_OVERLAP=400
ENV TOP_K_RESULTS=5

EXPOSE 8000

# ── Healthcheck ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/status')" || exit 1

# ── Entrypoint ────────────────────────────────────────────────────────────────
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
