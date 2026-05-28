# Poli-Tutor

> Socratic RAG tutor for academic course materials — FastAPI backend + React frontend + ChromaDB Cloud.

---

## Description

Poli-Tutor is a Retrieval-Augmented Generation (RAG) system that acts as a Socratic tutor for polytechnic course units. It ingests course documents (PDF, PPTX, Markdown), embeds them into ChromaDB Cloud, and answers student questions by guiding them through the material — never giving direct answers.

**Key features:**
- Multi-format document extraction via Unstructured API (PDF, PPTX, MD — hi-res, table and image aware)
- Multimodal image processing: images classified and summarised by LLM (Gemini 2.5 Flash Lite via OpenRouter), then embedded alongside text
- Source-type aware chunking strategies (`slides` vs. `apontamentos`)
- Multilingual embeddings with `BAAI/bge-m3` stored in ChromaDB Cloud
- Cross-encoder reranking (`Alibaba-NLP/gte-reranker-modernbert-base` on CPU, `jinaai/jina-reranker-v2-base-multilingual` on GPU)
- Socratic tutor generation via IAEdu API (GPT-4o) or OpenRouter — guides students through questions and hints, never gives direct answers
- Three-layer defence system: input guardrails (regex) → LLM system prompt → output guardrail (regex)
- Conversation memory: Redis for recent message cache + MongoDB for persistent summaries (background summarisation via Gemini 2.5 Flash Lite)
- `ask()` function callable by a backend, accepting per-student IAEdu credentials for production use
- Retrieval benchmark: automated dataset generation + IR evaluation (Hit Rate, MRR, NDCG, MAP, Precision, Recall via `ranx`)
- Tutor benchmark: LLM-as-judge evaluation of Socratic response quality (Faithfulness, Non-directiveness, Scaffolding, Clarity) with semantic similarity scoring and guardrail classification metrics (Precision, Recall, F1, FPR)
- Threshold calibration: data-driven distance threshold sweep for ChromaDB filtering
- Embedding visualisation via Renumics Spotlight

---

## Project Structure

```text
Poli-Tutor/
├── app/
│   ├── backend/              # FastAPI app
│   │   ├── api/              # Route handlers (v1 endpoints)
│   │   ├── core/             # Config, database, project setup
│   │   ├── repositories/     # Data access (MongoDB, Redis)
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── services/         # Business logic
│   │   └── tests/            # pytest suite (unit/)
│   └── frontend/             # React/Vite client
│       └── src/
│           ├── api/          # HTTP clients
│           ├── components/   # UI + dashboard components
│           ├── hooks/        # React hooks
│           ├── pages/        # Route pages
│           ├── services/     # Service layer
│           └── test/         # Vitest suite (setup + unit/)
├── docker/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── rag/
│   ├── .env                  # RAG environment variables (create this — see below)
│   ├── data/
│   │   ├── raw/              # Source documents by course unit
│   │   ├── processed/        # Extracted image artifacts
│   │   └── benchmark/        # Benchmark datasets and results
│   ├── src/
│   │   ├── ingestion/        # Extraction, chunking, embedding pipeline
│   │   ├── runtime/          # Retrieval, guardrails, generation
│   │   ├── evaluation/       # Retrieval and tutor benchmarks
│   │   └── shared/           # Config, models, database helpers, utilities
│   ├── Dockerfile            # One-shot ingestion pipeline container
│   └── requirements.txt
├── docker-compose.yml        # Redis + Backend + Frontend (local dev)
├── docker-compose.hub.yml    # Pre-built images from Docker Hub (deploy)
└── README.md
```

---

## File Naming Convention

Documents must follow the pattern `<source_type>.<course_code>.<description>.<ext>`.

| Example | source_type | course_code |
| --- | --- | --- |
| `slides.ED.CAP1.pdf` | `slides` | `ed` |
| `apontamentos.ED.Arvores.pptx` | `apontamentos` | `ed` |
| `apontamentos.ED.Resumo.md` | `apontamentos` | `ed` |

Valid source types are defined in `CHUNKING_STRATEGIES` inside `rag/src/shared/config.py` (currently `slides` and `apontamentos`).

Supported extensions: `.pdf`, `.pptx`, `.md`

---

## Prerequisites

| Requirement | Notes |
| --- | --- |
| Docker Desktop | Recommended for running the full stack locally |
| Python 3.11+ | Needed for the backend test suite and running the RAG pipeline without Docker |
| pip | Only needed for running without Docker |
| Node.js 20+ | Only needed for running or testing the frontend without Docker |

---

## Environment Variables

### `rag/.env` — RAG pipeline (ingestion + retrieval + generation)

```env
# Unstructured API (document extraction)
UNSTRUCTURED_API_KEY=your_key_here
UNSTRUCTURED_API_URL=https://api.unstructuredapp.io/general/v0/general

# ChromaDB Cloud (vector storage)
CHROMA_API_KEY=your_key_here
CHROMA_TENANT=your_tenant_here
CHROMA_DATABASE=your_database_here

# OpenRouter (image summarisation, benchmark dataset generation, LLM-as-judge, summarisation)
OPENROUTER_KEY=your_key_here

# IAEdu API (production tutor generation — per-student credentials supplied at request time)
# These are fallback values for local development; in production, credentials come from the frontend.
IAEDU_API_ENDPOINT=your_endpoint_here
IAEDU_API_CHANNEL=your_channel_here
IAEDU_API_KEY=your_key_here

# Data paths (optional — defaults to rag/data/raw and rag/data/raw/ED)
RAW_DATA_PATH=/path/to/data/raw
COURSE_PATH=/path/to/data/raw/ED
```

### `app/backend/.env` — Backend services

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=poli_tutor
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Generator backend

`GENERATOR_BACKEND` in `rag/src/shared/config.py` controls which LLM is used for tutor generation:

| Value | Used for |
| --- | --- |
| `"openrouter"` | Local development and benchmarks (avoids IAEdu rate limits) |
| `"iaedu"` | Production — students supply their own IAEdu credentials via the frontend |

The default is `"openrouter"`. Change it in `config.py` when deploying to production.

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/fabioAntGit/Poli-Tutor.git
cd Poli-Tutor
```

### 2. Create environment files

Copy the example files and fill in your credentials (see the **Environment Variables** section above for what each key means):

```bash
cp rag/.env.example rag/.env
cp app/backend/.env.example app/backend/.env
```

> Both files are **required** — `docker compose up` will fail to start if they are missing. The frontend only needs `app/frontend/.env` when running it outside Docker (`cp app/frontend/.env.example app/frontend/.env`).

### 3. Add your documents

Place your files inside `rag/data/raw/<course_unit>/`, following the naming convention.

---

## Running with Docker (Recommended)

### Full stack — Backend + Frontend + Redis

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

To run in detached mode:

```bash
docker compose up --build -d
```

To stop:

```bash
docker compose down
```

> **First start:** The backend downloads the retrieval models (~3.4 GB) on first start into the `huggingface_cache` volume and reuses them on subsequent runs. The first boot therefore needs network access and takes longer.

> **GPU (optional):** The stack runs on CPU by default. If you have an NVIDIA GPU with `nvidia-container-toolkit` installed, you can enable it by adding the following to the `backend` service in `docker-compose.yml`:
>
> ```yaml
> deploy:
>   resources:
>     reservations:
>       devices:
>         - driver: nvidia
>           count: all
>           capabilities: [gpu]
> ```

### Ingestion pipeline (one-shot)

The ingestion pipeline populates ChromaDB with the course documents. It is a separate one-shot container — run it once before starting the stack (or after adding new documents).

Build and run from the `rag/` folder:

```bash
cd rag
docker build -t poli-tutor-ingestion .
docker run --env-file .env poli-tutor-ingestion
```

To use a specific embedding model and collection:

```bash
docker run --env-file .env poli-tutor-ingestion \
  python -m src.ingestion.pipeline --model BAAI/bge-m3 --collection PoliTutor-Docs-bge-m3
```

---

## Deploy (pre-built images from Docker Hub)

On a push to `main`, CI builds and pushes the `backend` and `frontend` images to Docker Hub. The retrieval models are **not** baked into the image — the backend downloads them on first start into the `huggingface_cache` volume and reuses them across restarts (the first boot needs network access).

To run the whole stack on any machine with Docker — no source code or build needed:

```bash
# Only docker-compose.hub.yml + your .env files are required
docker compose -f docker-compose.hub.yml up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

Secrets are **not** baked into the images — provide them at runtime via `app/backend/.env` and `rag/.env` next to the compose file (loaded through `env_file`).

**One-time setup for the CI publish step:** add two repository secrets in GitHub (Settings → Secrets and variables → Actions):

- `DOCKERHUB_USERNAME` — your Docker Hub username
- `DOCKERHUB_TOKEN` — a Docker Hub access token with Read/Write scope

---

## Running without Docker

> **Note:** Requires manual installation of **poppler** and **tesseract** for document extraction.

**Create and activate a virtual environment (from the `rag/` folder):**

<details>
<summary>Windows</summary>

```bash
python -m venv venv
venv\Scripts\activate
```
</details>

<details>
<summary>Linux / macOS</summary>

```bash
python -m venv venv
source venv/bin/activate
```
</details>

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Run from the `rag/` folder:**

```bash
# Ingest documents into ChromaDB (default embedding model)
python -m src.ingestion.pipeline

# Ingest with a specific embedding model into a named collection
python -m src.ingestion.pipeline --model BAAI/bge-m3 --collection PoliTutor-Docs-bge-m3

# Generate retrieval benchmark Q&A datasets
python -m src.evaluation.benchmark --generate

# Evaluate retrieval with the default config (all BenchmarkQA-*.json files)
python -m src.evaluation.benchmark

# Single-file evaluation
python -m src.evaluation.benchmark data/benchmark/BenchmarkQA-slides.ED.CAP1.json

# Compare multiple embedding + reranker configurations
python -m src.evaluation.benchmark --compare

# Generate tutor benchmark dataset (stratified sample from ChromaDB)
python -m src.evaluation.benchmark_tutor --generate

# Evaluate tutor response quality (LLM-as-judge + semantic similarity, outputs PNG report)
python -m src.evaluation.benchmark_tutor --evaluate

# Calibrate the optimal ChromaDB distance threshold
python -m src.evaluation.benchmark_threshold

# Custom number of threshold values
python -m src.evaluation.benchmark_threshold --thresholds 30

# Visualise threshold sweep results
python -m src.evaluation.plot_threshold_sweep data/benchmark/results/threshold_sweep_<timestamp>.json

# Visualise embeddings with Spotlight
python -m src.evaluation.visualize
```

**Run the backend (from the project root):**

```bash
python -m uvicorn app.backend.main:app --reload --port 8000
```

**Run the frontend (from `app/frontend/`):**

```bash
npm install
npm run dev
```

---

## Testing

The project has two independent test suites: the backend runs on **pytest**, the frontend on **Vitest**. Both libraries scale from unit tests to future integration and system tests.

### Backend (pytest)

The backend test suite runs in CI on every push and pull request (see `.github/workflows/ci.yml`). To run it locally, create a Python 3.11 virtual environment and install the same dependencies CI uses:

```bash
python3.11 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

pip install -r rag/requirements.txt
pip uninstall -y torchcodec          # not needed for inference
pip install -r app/backend/tests/requirements.txt

pytest app/backend/tests/unit
```

Tests live in `app/backend/tests/unit/`. Coverage runs automatically (`pytest-cov`): a summary is printed to the terminal and a full HTML report is written to `htmlcov/` (open `htmlcov/index.html`).

> **First install:** pulls the full RAG dependency set (including PyTorch) — slow once.

### Frontend (Vitest)

```bash
cd app/frontend
npm install            # first time only
npm test               # watch mode
npm run test:run       # single run (CI)
npm run test:coverage  # single run + coverage report
```

Tests live in `app/frontend/src/test/`, mirroring the source structure under `unit/`. The coverage report (`@vitest/coverage-v8`) is printed to the terminal and written as HTML to `app/coverage/frontend/` (open `app/coverage/frontend/index.html`).

Both suites write their HTML coverage reports into a single `app/coverage/` folder — `app/coverage/backend/` and `app/coverage/frontend/`.

---

## Pipeline Overview

### Ingestion

```
Document Files (PDF / PPTX / MD)
      |
      v
extractor.py   →  Partitions documents via Unstructured API (Tables, Images, Text)
      |
      v
chunker.py     →  Segments elements into chunks while preserving page context
      |            Injects [PAGE:N] markers → splits → resolves per-chunk page lists
      |            Orphan images assigned to nearest chunk by page distance
      v
embedding.py   →  Summarises relevant images (Gemini 2.5 Flash Lite via OpenRouter)
                   Generates bge-m3 embeddings → upserts to ChromaDB Cloud
```

### Query (runtime)

```
Student question
      |
      v [input guardrails: sanitize, validate, detect injection/code request]
      |
      v retrieve() — bge-m3 embed query → ChromaDB top-20 (filtered by course)
      |
      v [distance threshold filter: discard chunks with cosine distance > 0.9301]
      |
      v [cross-encoder reranker → top 5]
      |
      v generator.py — build context prompt → call IAEdu or OpenRouter
      |
      v [output guardrail: detect direct answers → replace with Socratic redirect]
      |
      v TutorResponse(answer, sources, is_fallback, is_guardrail, is_output_guardrail)
```

---

## Tutor

`retrieval.py` exposes `ask(course, query, iaedu_creds=None)` as the primary backend integration point:

```python
from rag.src.runtime.retrieval import ask
from rag.src.shared.models import IaEduCredentials

# Development / benchmark (uses GENERATOR_BACKEND from config)
response = ask(course="ed", query="O que é uma árvore AVL?")

# Production (per-student IAEdu credentials from the frontend)
creds = IaEduCredentials(url="...", channel_id="...", api_key="...")
response = ask(course="ed", query="O que é uma árvore AVL?", iaedu_creds=creds)

print(response.answer)              # Socratic guidance from the tutor
print(response.is_fallback)         # True if no relevant content was found
print(response.is_guardrail)        # True if an input guardrail blocked the query
print(response.is_output_guardrail) # True if the LLM gave a direct answer (caught and replaced)

for source in response.sources:
    print(source.filename, source.pages)
```

### Three-layer defence

| Layer | Mechanism | When triggered |
| --- | --- | --- |
| **Input guardrail** | Regex patterns | Code requests, prompt injection, invalid input — blocked before LLM |
| **System prompt** | LLM instructions | Subtle adversarial attempts handled by the model |
| **Output guardrail** | Regex on LLM output | LLM produced a direct answer — replaced with Socratic redirect |

When no relevant content is found, a fallback `TutorResponse` is returned without calling the generation API.

---

## Retrieval

For direct access to the retrieval layer without generation (e.g. for benchmarking):

```python
from rag.src.runtime.retrieval import retrieve

results = retrieve(course="ed", query="O que é uma árvore AVL?")
```

It queries ChromaDB filtered by course unit, applies the distance threshold filter, then applies cross-encoder reranking before returning results as a structured `RetrievalResults` object.

### Distance threshold

Chunks with a ChromaDB cosine distance above `RETRIEVAL_DISTANCE_THRESHOLD` are discarded before reranking. The active threshold is **0.9301**, calibrated via `benchmark_threshold.py`.

At this value:
- Hit Rate@5 = **86.6%** across 583 benchmark questions
- Fallback rate = **0.3%**

Set `RETRIEVAL_DISTANCE_THRESHOLD = None` in `config.py` to disable filtering entirely.

### Reranker scoring

The cross-encoder reranker uses **sigmoid activation** — all scores are in [0, 1].

Best available reranker is selected based on hardware:
- **GPU** → `jinaai/jina-reranker-v2-base-multilingual`
- **CPU** → `Alibaba-NLP/gte-reranker-modernbert-base` (default)

---

## Benchmark

### Dataset generation

For each document in `COURSE_PATH`, the module extracts page content and sends it to GPT-4o (OpenRouter) to generate a question.

```bash
python -m src.evaluation.benchmark --generate
```

Output: `BenchmarkQA-<filename>.json` per document in `rag/data/benchmark/`.

### Evaluation

```bash
# Default config — all files
python -m src.evaluation.benchmark

# Single file
python -m src.evaluation.benchmark data/benchmark/BenchmarkQA-slides.ED.CAP1.json

# Multi-config comparison (all entries in BENCHMARK_COMPARISON_CONFIGS)
python -m src.evaluation.benchmark --compare
```

Comparison results are persisted to `data/benchmark/results/` as timestamped JSON files.

**Reported metrics** (via `ranx` at `@5`): Hit Rate, MRR, NDCG, MAP, Precision, Recall.

### How metrics are calculated

For each Q&A pair:
1. The question is embedded and sent to ChromaDB (filtered by course unit) to retrieve `top_k` candidates.
2. If a reranker is configured, chunks are re-scored and truncated to `reranker_top_k`.
3. A **relevance key** `<filename>_p<page>` is built for each page covered by each chunk. Multi-page chunks register all their pages so a match on any page counts.
4. The ground-truth key is `<filename>_p<page>` from the QA pair (binary relevance = 1).
5. `ranx` computes the final metrics against the ground-truth qrels.

### Multi-model ingestion

Each embedding model requires its own ChromaDB collection:

```bash
python -m src.ingestion.pipeline --model intfloat/multilingual-e5-base --collection PoliTutor-Docs-e5-base
python -m src.ingestion.pipeline --model BAAI/bge-m3 --collection PoliTutor-Docs-bge-m3
```

### Threshold Calibration

```bash
# Run with default 20 threshold values
python -m src.evaluation.benchmark_threshold

# Custom number of thresholds
python -m src.evaluation.benchmark_threshold --thresholds 30
```

Output: `data/benchmark/results/threshold_sweep_<timestamp>.json`

**Visualise results:**

```bash
python -m src.evaluation.plot_threshold_sweep data/benchmark/results/threshold_sweep_<timestamp>.json
```

Saves a PNG alongside the JSON with two panels: IR metrics vs threshold and fallback rate vs threshold, with the recommended threshold annotated.

> The sweep runs the reranker for every question at every threshold value — expect several hours on CPU with the full benchmark dataset.

---

## Tutor Benchmark

Evaluates the **generation stage** independently from retrieval — given a student question, does the tutor produce a pedagogically sound Socratic response?

### Dataset generation

A stratified random sample of pages is drawn directly from ChromaDB (50 from slides, 50 from apontamentos, with a per-document cap). For each page, GPT-4o generates 2 questions:

| Type | Description |
| --- | --- |
| **regular** | A genuine question a student might ask while studying the material |
| **adversarial** | A question designed to pressure the tutor into bypassing the Socratic method |

Each question includes an `expected_answer` — the ideal Socratic response for that question (used only for semantic similarity scoring).

```bash
python -m src.evaluation.benchmark_tutor --generate
```

Output: `data/benchmark/BenchmarkTutor-sample.json`

> The dataset file is not overwritten automatically. Delete it manually before regenerating.

### Evaluation

```bash
python -m src.evaluation.benchmark_tutor --evaluate
python -m src.evaluation.benchmark_tutor --evaluate data/benchmark/BenchmarkTutor-sample.json
```

Output per run in `data/benchmark/results/`:

| File | Description |
| --- | --- |
| `benchmark_tutor_{timestamp}.png` | Visual report (3×2 grid) |
| `benchmark_tutor_similarity_{timestamp}.json` | All normal results sorted by semantic similarity |

**Response classification:**

| Case | Description | Scored? |
| --- | --- | --- |
| **Normal** | Tutor generated a Socratic response | ✅ LLM-judge + semantic similarity |
| **Input guardrail** | Regex blocked the query | ❌ Contributes to guardrail activation rate |
| **Output guardrail** | LLM gave direct answer, replaced with redirect | ❌ Contributes to output guardrail rate |
| **Fallback** | Retriever found no relevant chunks | ❌ Contributes to fallback rate |

**LLM-as-judge criteria (GPT-4o, 1–5 scale):**

| Criterion | Description |
| --- | --- |
| **Faithfulness** | Response grounded in retrieved context? Avoids external information? |
| **Non-directiveness** | Tutor avoids giving the direct answer and guides instead? |
| **Scaffolding** | Provides just enough help to move forward without revealing too much? |
| **Clarity** | Response clearly formulated and easy for the student to act on? |

**Semantic similarity:** cosine similarity between bge-m3 embeddings of the actual response and `expected_answer`.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/chat` | Create a new conversation |
| `GET` | `/chat/{conversation_id}` | Fetch conversation history |
| `POST` | `/chat/{conversation_id}/messages` | Send a message and receive a tutor response |
| `GET` | `/projects` | List projects |
| `POST` | `/projects` | Create a project |

Interactive API docs: http://localhost:8000/docs

### Auth headers

All endpoints require IAEdu headers:

| Header | Description |
| --- | --- |
| `X-Channel-Id` | IAEdu channel identifier |
| `X-Api-Key` | IAEdu API key (required for message endpoints) |
| `X-Api-Endpoint` | IAEdu API endpoint URL (required for message endpoints) |

---

## Technology Stack

| Layer | Technology |
| --- | --- |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **Persistence** | MongoDB (async pymongo), Redis (async redis.asyncio) |
| **RAG / ML** | LangChain, Sentence Transformers, ChromaDB Cloud |
| **Document parsing** | Unstructured API |
| **LLM** | IAEdu (GPT-4o), OpenRouter (GPT-4o, Gemini 2.5 Flash Lite) |
| **Evaluation** | ranx, NumPy, Pandas, Matplotlib |
| **Frontend** | React 19, React Router 7, Vite, Tailwind CSS, Shadcn/Radix UI, Axios |
| **Testing** | pytest (backend), Vitest + Testing Library (frontend) |
| **Containerisation** | Docker, Docker Compose, Nginx |
