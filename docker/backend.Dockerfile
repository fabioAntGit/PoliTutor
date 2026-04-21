# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies into a local folder
COPY rag/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt && \
    pip uninstall -y torchcodec

# Stage 2: Final Runtime
# We use a runtime-only CUDA image which is smaller than the dev or pytorch-official ones
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

# Install only the bare minimum python needed for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only the installed python packages from the builder stage
COPY --from=builder /root/.local /root/.local

# Ensure the app code is copied
COPY app/ ./app/
COPY rag/ ./rag/

# Set environment variables
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Clean up any potential pyc files or caches to save space
RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -delete

EXPOSE 8000

CMD ["python3.11", "-m", "uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
