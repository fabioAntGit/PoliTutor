# Stage 1: Builder — install all Python dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY rag/requirements.txt .

# Install CPU-only PyTorch by default to keep the image small (the CUDA wheels
# add ~2.5GB and aren't used without a GPU). Installing torch first pins the
# flavor so the rest of the requirements don't pull the default CUDA build.
# Device is auto-detected at runtime (EMBEDDING_DEVICE). For a GPU host build:
#   docker build --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cu124 ...
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
RUN pip install --user --no-cache-dir torch --index-url ${TORCH_INDEX} && \
    pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime — lean image, CPU-only by default (GPU auto-used if present)
FROM python:3.11-slim

WORKDIR /app

# Runtime system dependency: libgomp1 (OpenMP) is needed by torch / sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Retrieval models (BAAI/bge-m3, BAAI/bge-reranker-base) are NOT baked into the
# image. They are downloaded on first start into the huggingface_cache volume
# (see docker-compose.hub.yml) and reused across restarts. This keeps the image
# small; the first boot needs network access.

COPY app/ ./app/
COPY rag/ ./rag/

RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -delete

EXPOSE 8000

CMD ["python3.11", "-m", "uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
