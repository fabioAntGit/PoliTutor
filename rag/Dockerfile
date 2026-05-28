# Stage 1: Builder — install Python dependencies separately to cache them
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-ingestion.txt .

# CPU-only PyTorch by default (override with TORCH_INDEX for a GPU host).
ARG TORCH_INDEX=https://download.pytorch.org/whl/cpu
RUN pip install --user --no-cache-dir torch --index-url ${TORCH_INDEX} && \
    pip install --user --no-cache-dir -r requirements-ingestion.txt

# Stage 2: Runtime — slim image with OCR/PDF tools needed by Unstructured
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libmagic-dev \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.ingestion.pipeline"]
