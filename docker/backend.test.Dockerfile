# Backend test image — Python 3.11 with full deps + pytest.
# Source is mounted at run time (see docker-compose.test.yml) so tests
# pick up live code without rebuilding.
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install the heavy RAG deps first so this layer stays cached when only the
# (small, faster-changing) test deps are updated.
COPY rag/requirements.txt ./rag-requirements.txt
RUN pip install --user --no-cache-dir -r rag-requirements.txt && \
    pip uninstall -y torchcodec

COPY app/backend/tests/requirements.txt ./test-requirements.txt
RUN pip install --user --no-cache-dir -r test-requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["pytest", "app/backend/tests/unit"]
