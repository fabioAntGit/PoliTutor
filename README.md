# Poli-Tutor

> Python project structured for document processing with **RAG (Retrieval-Augmented Generation)** capabilities, targeted at academic course materials.

---

## Description

Poli-Tutor implements a modular RAG pipeline for ingesting, chunking, embedding and retrieving documents (slides, notes) from polytechnic course units. The system supports PDF, PPTX and Markdown files, multimodal image processing, cross-encoder reranking, Socratic tutor generation, and a full evaluation benchmark.

**Key features:**
- Multi-format extraction via Unstructured API (PDF, PPTX, MD — hi-res, table and image aware)
- Multimodal image processing: images classified and summarised by an LLM (OpenRouter/Gemini), then embedded alongside text
- Source-type aware chunking strategies (slides vs. notes)
- Multilingual embeddings stored in ChromaDB Cloud
- Cross-encoder reranking
- Socratic tutor generation via IAEdu API (GPT-4o) — guides students through questions and hints, never gives direct answers
- Three-layer defence system: input guardrails (regex) → LLM system prompt → output guardrail
- `ask()` function callable by a backend, accepting per-student IAEdu credentials for production use
- Retrieval benchmark: automated dataset generation and evaluation (Hit Rate, MRR, Recall)
- Tutor benchmark: LLM-as-judge evaluation of Socratic response quality (Faithfulness, Non-directiveness, Scaffolding, Clarity) with semantic similarity scoring, guardrail classification metrics (Precision, Recall, F1, FPR) and layered robustness metrics
- Interactive CLI chat for local testing (`chat.py`)
- Embedding visualisation via Renumics Spotlight

---

## Project Structure

```text
Poli-Tutor/
|-- app/
|   |-- backend/                  # FastAPI app, repositories, services, schemas
|   `-- frontend/                 # React/Vite client
|-- docker/
|   |-- backend.Dockerfile
|   `-- frontend.Dockerfile
|-- rag/
|   |-- data/
|   |   |-- raw/                  # Source documents by course
|   |   |-- processed/            # Extracted image artifacts and derived assets
|   |   `-- benchmark/            # Benchmark datasets and results
|   |-- src/
|   |   |-- ingestion/            # Extraction, chunking, embedding pipeline
|   |   |-- runtime/              # Retrieval, guardrails, generation
|   |   |-- evaluation/           # Retrieval and tutor benchmarks
|   |   `-- shared/               # Config, models, database helpers, utilities
|   |-- Dockerfile
|   `-- requirements.txt
|-- docker-compose.yml
`-- README.md
```

---

## File Naming Convention

Documents must follow the pattern `<source_type>.<course_code>.<description>.<ext>`.

| Example | source_type | course_code |
| --- | --- | --- |
| `slides.ED.CAP1.pdf` | `slides` | `ed` |
| `apontamentos.ED.Arvores.pptx` | `apontamentos` | `ed` |
| `apontamentos.ED.Resumo.md` | `apontamentos` | `ed` |

Valid source types are defined in `CHUNKING_STRATEGIES` inside `config.py` (currently `slides` and `apontamentos`).

Supported extensions: `.pdf`, `.pptx`, `.md`

---

## Prerequisites

| Requirement | Notes |
| --- | --- |
| Docker Desktop | Recommended |
| Python 3.12+ | Only for running without Docker |
| pip | Only for running without Docker |

---

## Environment Variables

Create a `.env` file inside the **`rag/`** folder:

```env
# Unstructured API (document extraction)
UNSTRUCTURED_API_KEY=your_key_here
UNSTRUCTURED_API_URL=https://api.unstructuredapp.io/general/v0/general

# ChromaDB Cloud (vector storage)
CHROMA_API_KEY=your_key_here
CHROMA_TENANT=your_tenant_here
CHROMA_DATABASE=your_database_here

# OpenRouter (image summarisation, benchmark dataset generation, benchmark evaluation)
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

### Backend selection

`GENERATOR_BACKEND` in `config.py` controls which LLM is used for generation:

| Value | Used for |
| --- | --- |
| `"openrouter"` | Local development and benchmarks (avoids IAEdu rate limits) |
| `"iaedu"` | Production — students supply their own IAEdu credentials via the Next.js frontend |

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/fabioAntGit/Poli-Tutor.git
cd Poli-Tutor
```

### 2. Add your documents

Place your files inside `rag/data/raw/<course_unit>/`, following the naming convention above.

---

### 3. Running with Docker (Recommended)

**Build the image:**
```bash
docker build -t poli-tutor .
```

**Run the ingestion pipeline:**
```bash
docker run --env-file .env poli-tutor
```

---

### 4. Running without Docker

> **Note:** Requires manual installation of **poppler** and **tesseract**.

**Create and activate a virtual environment:**

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
python src/pipeline.py

# Ingest with a specific embedding model into a named collection
python src/pipeline.py --model BAAI/bge-m3 --collection PoliTutor-Docs-bge-m3

# Generate retrieval benchmark Q&A datasets
python src/benchmark.py --generate

# Evaluate retrieval with the default config (all BenchmarkQA-*.json files)
python src/benchmark.py

# Compare multiple embedding + reranker configurations
python src/benchmark.py --compare

# Interactive CLI chat (local testing)
python src/chat.py --course ed

# Generate tutor benchmark dataset (stratified sample from ChromaDB)
python src/benchmark_tutor.py --generate

# Evaluate tutor response quality (LLM-as-judge + semantic similarity, outputs PNG report)
python src/benchmark_tutor.py --evaluate

# Visualise embeddings with Spotlight
python src/visualize.py
# Or for a specific collection: python src/visualize.py --collection PoliTutor-Docs-e5-base
```

---

## Pipeline Overview

### Ingestion
```
Document Files (PDF / PPTX / MD)
      |
      v
pipeline.py     →  Orchestrates the ingestion flow & validates file metadata
      |
      v
extractor.py    →  Partitions documents via Unstructured API (Tables, Images, Text)
      |
      v
chunker.py      →  Segments elements into chunks while preserving page context
      |
      v
embedding.py    →  Summarizes relevant images (LLM) and generates vector
                   embeddings for storage in ChromaDB Cloud
```

### Query (backend integration)
```
Student question
      |
      v
retrieval.py    →  ask(course, query, iaedu_creds=None)
      |                    |
      |           [Input guardrails] — sanitize, validate, detect injection/code request
      |                    |
      |           retrieve() — embeds query, searches ChromaDB (top 20)
      |                    |
      |           [Distance threshold] — discards chunks with cosine distance > 0.9301
      |                    |
      |           reranker — scores remaining chunks, keeps top 5
      |                    |
      v           generator.py — builds context from chunks, calls IAEdu or OpenRouter
                             |
                        [Output guardrail] — detects direct answers, replaces with redirect
                             |
                             v
                   TutorResponse(answer, sources, is_fallback, is_guardrail, is_output_guardrail)
```

---

## Tutor

`retrieval.py` exposes an `ask(course, query, iaedu_creds=None)` function as the primary backend integration point:

```python
from retrieval import ask
from models import IaEduCredentials

# Development / benchmark (uses env vars or OpenRouter)
response = ask(course="ed", query="O que é uma árvore AVL?")

# Production (per-student IAEdu credentials from the Next.js frontend)
creds = IaEduCredentials(url="...", channel_id="...", api_key="...")
response = ask(course="ed", query="O que é uma árvore AVL?", iaedu_creds=creds)

print(response.answer)             # Socratic guidance from the tutor
print(response.is_fallback)        # True if no relevant content was found
print(response.is_guardrail)       # True if an input guardrail blocked the query
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

## Retrieval

For direct access to the retrieval layer without generation (e.g. for benchmarking), use `retrieve()`:

```python
from retrieval import retrieve

results = retrieve(course="ed", query="O que é uma árvore AVL?")
```

It queries ChromaDB filtered by course unit, applies the distance threshold filter, then applies cross-encoder reranking before returning results as a structured `RetrievalResults` object.

### Distance threshold

Chunks with a ChromaDB cosine distance above `RETRIEVAL_DISTANCE_THRESHOLD` are discarded before reranking. This prevents the reranker from scoring clearly irrelevant chunks and ensures the system returns a fallback when no sufficiently close content exists in the course materials.

The active threshold is **0.9301**, calibrated via `benchmark_threshold.py` (see [Threshold Calibration](#threshold-calibration) below). At this value:
- Hit Rate@5 = **86.6%** across 583 benchmark questions
- Fallback rate = **0.3%** (2 questions with no relevant chunks in the corpus)

Set `RETRIEVAL_DISTANCE_THRESHOLD = None` in `config.py` to disable filtering entirely.

### Reranker scoring

The cross-encoder reranker is initialised with a **sigmoid activation**, so all scores are in the range [0, 1]:

- `0.0` — the model considers the chunk completely irrelevant to the query
- `0.5` — neutral (model is uncertain)
- `1.0` — the model considers the chunk highly relevant

The best available reranker is selected automatically based on hardware:
- **GPU** → `jinaai/jina-reranker-v2-base-multilingual`
- **CPU** → `Alibaba-NLP/gte-reranker-modernbert-base`

---

## Benchmark

The benchmark module generates Q&A pairs from page content and evaluates ChromaDB retrieval quality across configurable combinations of embedding models and rerankers.

### Dataset generation

For each document in `COURSE_PATH`, the module extracts page content and sends it to the LLM (OpenRouter) to generate a question. Results are saved to `rag/data/benchmark/`.

```bash
python src/benchmark.py --generate
```

Output: `BenchmarkQA-<filename>.json` — one file per ingested document. Each entry contains `filename`, `page`, and `question`.

### Evaluation

**Default config** (embedding + reranker as defined in `config.py`):
```bash
python src/benchmark.py                                                    # all files
python src/benchmark.py data/benchmark/BenchmarkQA-slides.ED.CAP1.json    # single file
```

**Multi-config comparison** — runs all configurations in `BENCHMARK_COMPARISON_CONFIGS` and prints a side-by-side metrics table:
```bash
python src/benchmark.py --compare
```

All comparison results are persisted to `data/benchmark/results/` as timestamped JSON files.

Example comparison output:
```
-------------------------------------------------------------
Config                     hit_rate@5         mrr@5      recall@5
-------------------------------------------------------------
e5-large + mMiniLM             0.8400        0.7100        0.8400
e5-base + mMiniLM              0.8200        0.7000        0.8200
-------------------------------------------------------------
```

### Multi-model ingestion

Each embedding model produces vectors with different dimensions, so each requires its own ChromaDB collection. Before running a comparison, ingest documents with each model:

```bash
# Default model (already ingested)
python src/pipeline.py

# Additional models
python src/pipeline.py --model intfloat/multilingual-e5-base --collection PoliTutor-Docs-e5-base
python src/pipeline.py --model BAAI/bge-m3 --collection PoliTutor-Docs-bge-m3
```

### How metrics are calculated

For each Q&A pair in the dataset:

1. The question is sent to ChromaDB (filtered by course unit) to retrieve `top_k` candidate chunks.
2. If a reranker is configured, chunks are re-scored by the cross-encoder (sigmoid output) and truncated to `reranker_top_k`.
3. A **relevance key** `<filename>_p<page>` is built for each page covered by each returned chunk. When a chunk spans multiple pages, all of them are registered with the same score so that a match on any page counts.
4. The ground-truth relevant document is `<filename>_p<page>` from the QA pair (binary relevance = 1).
5. `ranx` computes the final metrics by comparing the ranked run against the ground-truth qrels.

**Reported metrics** (via `ranx` at `@5`): Hit Rate, MRR, Recall.

### Customising configurations

Edit `BENCHMARK_COMPARISON_CONFIGS` in `config.py` to add, remove, or modify configurations. Each entry accepts:

| Key | Description |
| --- | --- |
| `name` | Label shown in the output table |
| `embedding_model` | HuggingFace model name for query embedding |
| `collection_name` | ChromaDB collection to query (must be pre-indexed with the right model) |
| `reranker_model` | Cross-encoder model name, or `null` to skip reranking |

### Threshold Calibration

`benchmark_threshold.py` determines the optimal ChromaDB distance threshold using a sweep over the observed distance range. This is a one-off calibration step — run it after changing the embedding model or reindexing the collection.

**How it works:**

1. **Distance collection** — runs retrieval without threshold or reranking for every benchmark question, collecting raw ChromaDB cosine distances. Each chunk is classified as a *hit* (covers the expected page) or *miss*.
2. **Threshold sweep** — evaluates `N` evenly-spaced threshold values across `[d_min, d_max]`. For each value, the full retrieve → filter → rerank pipeline is executed and IR metrics + fallback rate are computed.
3. **Suggestion** — two criteria are applied: the second-derivative elbow on Hit Rate@5, and a composite score `Hit@5 − α × fallback_rate`.

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

Saves a publication-ready PNG alongside the JSON with two panels: IR metrics vs threshold (Hit@5, NDCG@5, MRR@5) and fallback rate vs threshold, with the recommended threshold annotated.

> The sweep runs the reranker for every question at every threshold value — expect several hours on CPU with the full benchmark dataset. The active threshold is set via `RETRIEVAL_DISTANCE_THRESHOLD` in `config.py`.

---

## Tutor Benchmark

The tutor benchmark evaluates the **generation stage** independently from retrieval — given a student question, does the tutor produce a pedagogically sound Socratic response?

Unlike the retrieval benchmark (which measures whether the right chunks were found), this benchmark measures the quality of the response itself using **LLM-as-judge** (GPT-4o via OpenRouter) and **semantic similarity** (bge-m3 embeddings).

### Dataset generation

A stratified random sample of pages is drawn directly from ChromaDB (not from raw files), ensuring questions are generated from the same text units the retriever uses. For a target of 200 questions, 100 pages are sampled — 50 from slides and 50 from apontamentos — with a per-document cap to prevent any single document from dominating the dataset.

For each sampled page, GPT-4o generates exactly **2 questions**:

| Type | Description |
| --- | --- |
| **regular** | A genuine question a student might ask while studying the material |
| **adversarial** | A question designed to pressure the tutor into bypassing the Socratic method: direct code demand, prompt injection, role override, or frustrated/rude language |

Each question includes an `expected_answer` — the **ideal Socratic response** for that specific question (not the factual answer). For regular questions this is guiding questions and scaffolding; for adversarials it models resistance and constructive redirection. This reference is used exclusively for semantic similarity scoring and is never passed to the judge.

```bash
python src/benchmark_tutor.py --generate
```

Output: `data/benchmark/BenchmarkTutor-sample.json` — a single file with all entries. Each entry contains `filename`, `page`, `question`, `question_type`, `expected_answer`, and `context`.

> The dataset file is not overwritten automatically. Delete it manually before regenerating.

### Evaluation

For each question, the full tutor pipeline is executed via `ask()` under real conditions. Results are classified into four distinct cases before scoring:

| Case | Description | Scored? |
| --- | --- | --- |
| **Normal** | Tutor generated a Socratic response | ✅ LLM-judge + semantic similarity |
| **Input guardrail** | Regex blocked the query before the LLM | ❌ Contributes to guardrail activation rate |
| **Output guardrail** | LLM produced a direct answer, replaced with redirect | ❌ Contributes to output guardrail rate |
| **Fallback** | Retriever found no relevant chunks | ❌ Contributes to fallback rate |

This separation ensures that pedagogical metrics reflect only cases where the tutor actually generated a response — failures at other layers are reported separately as robustness indicators.

Normal responses are scored by two independent mechanisms:

**LLM-as-judge** — GPT-4o evaluates four pedagogical criteria on a 1–5 scale:

| Criterion | Description |
| --- | --- |
| **Faithfulness** | Is the response grounded in the retrieved context? Does it avoid external information? |
| **Non-directiveness** | Does the tutor avoid giving the direct answer and guide instead? |
| **Scaffolding** | Does it provide just enough help to move forward without revealing too much? |
| **Clarity** | Is the response clearly formulated and easy for the student to act on? |

**Semantic similarity** — cosine similarity between the bge-m3 embedding of the actual response and the `expected_answer`. Captures semantic alignment with the ideal Socratic style independently of lexical variation, unlike token-matching metrics (e.g. F1) which penalise valid paraphrasing.

```bash
python src/benchmark_tutor.py --evaluate           # all BenchmarkTutor-*.json files
python src/benchmark_tutor.py --evaluate <file>    # single file
```

Output: two files per run in `data/benchmark/results/`, both sharing the same timestamp:

| File | Description |
| --- | --- |
| `benchmark_tutor_{timestamp}.png` | Visual report (3×2 grid, see below) |
| `benchmark_tutor_similarity_{timestamp}.json` | All normal results sorted by semantic similarity (highest → lowest), with `question`, `actual_response`, `expected_answer` and `similarity` — ready to extract high/low similarity examples for the written report |

The PNG report contains a **3×2 grid** of subplots:

| Subplot | Description |
| --- | --- |
| **LLM-judge scores** | Mean ± std per criterion — normal responses only |
| **Score distribution** | Histogram of overall mean score per response — normal responses only |
| **Semantic similarity** | Mean ± std by question type (regular vs. adversarial not blocked) |
| **System robustness** | Fallback rate (% of total), input guardrail rate and output guardrail rate (% of adversarials) |
| **Guardrail classification** | Confusion matrix (TP, FN, FP, TN) and binary classification metrics for the input guardrail: Precision, Recall/TPR, F1-Score, FPR |
| *(reserved)* | Reserved for future threshold analysis |

The robustness subplot surfaces the full three-layer defence picture: what was caught by regex, what the LLM failed on (and was corrected), and what proportion of adversarials the system prompt handled correctly (inferred as 100% − input guardrail rate − output guardrail rate).

The guardrail classification subplot treats the input guardrail as a binary classifier (positive = adversarial) and reports standard IR/classification metrics, as recommended for this type of system evaluation.

Both generation and judge prompts are configurable via `TUTOR_BENCHMARK_GENERATION_PROMPT` and `TUTOR_BENCHMARK_JUDGE_PROMPT` in `config.py`.

---

## Chat

`chat.py` provides an interactive CLI for testing the tutor locally without a backend:

```bash
python src/chat.py --course ed
`````