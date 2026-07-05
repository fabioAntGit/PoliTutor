# Running Poli-Tutor

This document explains how to run the application locally, with Docker or without Docker, and how to run the test suites.

## Recommended Path

Use Docker Compose for normal development or demonstration. It starts:

- Redis
- FastAPI backend
- React frontend

It does not start MongoDB because this project is configured to use MongoDB Atlas. It also does not start ChromaDB because the vector store is ChromaDB Cloud.

## Prerequisites

| Requirement | Needed for | Notes |
| --- | --- | --- |
| Docker Desktop | Running the app with Docker | Recommended path |
| MongoDB Atlas | Application database | Set through `app/backend/.env` |
| ChromaDB Cloud | RAG vector store | Set through `rag/.env` |
| OpenRouter key | Tutor generation and memory summaries | Set through `rag/.env` |
| Unstructured API key | Ingestion only | Not required just to start the app |
| Python 3.11+ | Running backend/RAG without Docker | Optional |
| Node.js 20+ | Running frontend without Docker | Optional |

## Environment Files

Create the backend and RAG environment files:

```bash
cp app/backend/.env.example app/backend/.env
cp rag/.env.example rag/.env
```

### `app/backend/.env`

This file is used by the backend container.

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/
MONGODB_DB=Database-MongoDB
REDIS_HOST=localhost
REDIS_PORT=6379
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

When running with `docker compose`, `REDIS_HOST` and `REDIS_PORT` are overridden so the backend connects to the Redis container.

### `rag/.env`

This file is used by the RAG runtime and by ingestion scripts.

```env
CHROMA_API_KEY=your_key_here
CHROMA_TENANT=your_tenant_here
CHROMA_DATABASE=your_database_here
OPENROUTER_KEY=your_key_here

# Only needed when re-running ingestion
UNSTRUCTURED_API_KEY=your_key_here
UNSTRUCTURED_API_URL=https://api.unstructuredapp.io/general/v0/general
```

Optional path overrides:

```env
RAW_DATA_PATH=/path/to/data/raw
COURSE_PATH=/path/to/data/raw/ED
```

### `app/frontend/.env`

Only needed when running the frontend outside Docker.

```bash
cp app/frontend/.env.example app/frontend/.env
```

Default value:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Run With Docker Compose

From the repository root:

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

Run in the background:

```bash
docker compose up --build -d
```

Stop the stack:

```bash
docker compose down
```

Stop and remove volumes:

```bash
docker compose down -v
```

The first backend start downloads the embedding and reranker models into the `huggingface_cache` Docker volume. This can take a while and needs network access.

## What Docker Compose Does Not Do

The main Compose file does not run ingestion automatically. It assumes the ChromaDB collection already contains embedded course documents.

To ingest documents, follow [INGESTION.md](INGESTION.md).

The main Compose file also does not run MongoDB locally. The backend uses the MongoDB Atlas URI in `app/backend/.env`.

## Run Pre-Built Images

The project includes `docker-compose.hub.yml` for running published images:

```bash
docker compose -f docker-compose.hub.yml up -d
```

You still need the same environment files:

```text
app/backend/.env
rag/.env
```

## Run Without Docker

This path is useful for debugging. It requires local Python and Node.js installations.

### Backend

From the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate

pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r rag/requirements.txt
pip install -r app/backend/tests/requirements.txt

python -m uvicorn app.backend.main:app --reload --port 8000
```

The backend reads:

- `app/backend/.env`
- `rag/.env`

### Frontend

From `app/frontend/`:

```bash
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

When running outside Docker, make sure `app/frontend/.env` points to:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Tests

### Backend Unit Tests

```bash
python3.11 -m venv .venv
source .venv/bin/activate

pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r rag/requirements.txt
pip install -r app/backend/tests/requirements.txt

pytest app/backend/tests/unit
```

### Backend Integration Tests

```bash
pytest app/backend/tests/integration
```

### Frontend Tests

From `app/frontend/`:

```bash
npm install
npm test
npm run test:run
npm run test:coverage
```

### System Tests

The CI system tests use `docker-compose.test.yml`, which starts isolated Redis and MongoDB containers, a seed container, the backend and the frontend.

```bash
docker compose -f docker-compose.test.yml up -d --build --wait

cd app/frontend
npm run test:e2e
```

Afterwards:

```bash
docker compose -f docker-compose.test.yml down -v
```

## Deployment Notes

On pushes to `main`, CI builds and publishes the backend and frontend images.

Required GitHub repository secrets:

```text
DOCKERHUB_USERNAME
DOCKERHUB_TOKEN
MONGODB_URI
JWT_SECRET_KEY
```

The published backend image does not bake in Hugging Face models. Models are downloaded at first startup into the `huggingface_cache` volume.

## Optional GPU Backend Build

The default backend image installs CPU-only PyTorch to keep the image smaller. To build with CUDA wheels:

```bash
docker build \
  -f docker/backend.Dockerfile \
  --build-arg TORCH_INDEX=https://download.pytorch.org/whl/cu124 \
  -t poli-tutor:backend-gpu .
```

Run it on a host with NVIDIA drivers and `nvidia-container-toolkit`, granting GPU access through Docker.

## Troubleshooting

### Backend cannot connect to MongoDB

Check:

- `MONGODB_URI` is a MongoDB Atlas URI, not `localhost`.
- Your current IP is allowed in MongoDB Atlas Network Access.
- `MONGODB_DB` matches the database name you expect.

### Backend cannot retrieve course content

Check:

- `CHROMA_API_KEY`, `CHROMA_TENANT` and `CHROMA_DATABASE` are set.
- The ChromaDB collection has already been populated through ingestion.
- Course codes in MongoDB match the course metadata generated from filenames.

### First Docker boot is slow

The backend downloads embedding/reranker models on first startup. Subsequent starts reuse the `huggingface_cache` volume.

### Frontend cannot reach backend

Check:

- Docker path: backend is available at `http://localhost:8000`.
- Local Vite path: `app/frontend/.env` uses `VITE_API_BASE_URL=http://localhost:8000/api/v1`.
