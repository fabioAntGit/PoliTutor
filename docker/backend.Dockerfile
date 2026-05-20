# Stage 1: Builder — install all Python dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY rag/requirements.txt ./
COPY DynamicGr/requirements.txt ./requirements-dynamicgr.txt

RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip install --user --no-cache-dir -r requirements-dynamicgr.txt && \
    pip uninstall -y torchcodec

# Stage 2: Runtime — lean image, CPU-only
FROM python:3.11-slim

WORKDIR /app

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

COPY app/ ./app/
COPY rag/ ./rag/
COPY DynamicGr/ ./DynamicGr/

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -delete

EXPOSE 8000

CMD ["python3.11", "-m", "uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]