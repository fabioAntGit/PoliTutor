# Poli-Tutor

> Python project structured for document processing with **RAG (Retrieval-Augmented Generation)** capabilities, targeted at academic course materials.

---

## Description

Poli-Tutor implements a modular RAG pipeline for ingesting, chunking, embedding and retrieving documents (slides, notes) from polytechnic course units. The system supports PDF, PPTX and Markdown files, multimodal image processing, cross-encoder reranking, and a full evaluation benchmark.

**Key features:**
- Multi-format extraction via Unstructured API (PDF, PPTX, MD — hi-res, table and image aware)
- Multimodal image processing: images classified and summarised by an LLM (OpenRouter/Gemini), then embedded alongside text
- Source-type aware chunking strategies (slides vs. notes)
- Multilingual embeddings stored in ChromaDB Cloud
- Cross-encoder reranking
- `retrieve()` function callable by a backend integrating seamlessly into downstream endpoints
- Automated benchmark generation and evaluation (Hit Rate, MRR, NDCG, MAP, Precision, Recall)
- Embedding visualisation via Renumics Spotlight

---

## Project Structure

```
Poli-Tutor/
└── rag/
    ├── data/
    │   ├── raw/                        # Raw documents organised by course unit
    │   │   └── ED/
    │   ├── processed/
    │   │   └── images/                 # Images extracted from documents
    │   └── benchmark/                  # Generated BenchmarkQA JSON files
    │       └── results/                 # Persisted benchmark metric results
    │
    ├── src/
    │   ├── config.py                   # All configuration and constants
    │   ├── utils.py                    # Filename parsing and metadata extraction
    │   ├── models.py                   # Shared data structures (RetrievalResults)
    │   ├── extractor.py                # File partitioning and page grouping
    │   ├── chunker.py                  # Text splitting with page tracking
    │   ├── embedding.py                # HuggingFace embedder + image LLM summarisation
    │   ├── database.py                 # ChromaDB Cloud client
    │   ├── reranker.py                 # Cross-encoder reranker
    │   ├── retrieval.py                # Core search logic for backend integration
    │   ├── pipeline.py                 # Main ingestion pipeline (entry point)
    │   ├── benchmark.py                # Benchmark generation and evaluation
    │   └── visualize.py                # Spotlight embedding visualiser
    │
    ├── .env                            # Environment variables (not committed)
    ├── Dockerfile
    └── requirements.txt
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

# OpenRouter (image summarisation via LLM)
OPENROUTER_KEY=your_key_here

# IAEdu API (benchmark Q&A generation)
IAEDU_API_ENDPOINT=your_endpoint_here
IAEDU_API_CHANNEL=your_channel_here
IAEDU_API_KEY=your_key_here

# Data paths (optional — defaults to rag/data/raw and rag/data/raw/ED)
RAW_DATA_PATH=/path/to/data/raw
COURSE_PATH=/path/to/data/raw/ED
```

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

# Generate benchmark Q&A datasets
python src/benchmark.py --generate

# Evaluate retrieval with the default config (all BenchmarkQA-*.json files)
python src/benchmark.py

# Find the best embedding + reranker combo, then sweep thresholds automatically
python src/benchmark.py --find-best

# Visualise embeddings with Spotlight
python src/visualize.py
# Or for a specific collection: python src/visualize.py --collection PoliTutor-Docs-e5-base
```

---

## Pipeline Overview

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

---

## Retrieval

`retrieval.py` exposes a `retrieve(course, query)` function intended to be called by a backend service:

```python
from retrieval import retrieve

results = retrieve(course="ed", query="O que é uma árvore AVL?")
```

It queries ChromaDB filtered by course unit, then applies cross-encoder reranking before returning results as a structured `RetrievalResults` object.

---

## Benchmark

The benchmark module generates Q&A pairs from page content and evaluates ChromaDB retrieval quality across configurable combinations of embedding model, reranker, and score threshold.

### Dataset generation

Requires IAEdu API. For each document in `COURSE_PATH`, the module extracts page content and sends it to the LLM to generate a Q&A pair. Results are saved to `rag/data/benchmark/`.

```bash
python src/benchmark.py --generate
```

Output: `BenchmarkQA-<filename>.json` — one file per ingested document.

### Evaluation

**Default config** (embedding + reranker as defined in `config.py`):
```bash
python src/benchmark.py                                                    # all files
python src/benchmark.py data/benchmark/BenchmarkQA-slides.ED.CAP1.json    # single file
```

**Find best** — two-phase automatic benchmark: (1) compares configs in `config.py`, picks the best by `ndcg@5`, then (2) sweeps score thresholds on the winner:
```bash
python src/benchmark.py --find-best
```

All comparison and sweep results are persisted to `data/benchmark/results/` as timestamped JSON files.

Example comparison output:
```
-------------------------------------------------------------------------------------------------------
Config                                   hit_rate@5         mrr@5        ndcg@5         map@5  precision@5      recall@5
-------------------------------------------------------------------------------------------------------
e5-large + mMiniLM                           0.8400        0.7100        0.7600        0.7000       0.1680        0.8400
e5-base + mMiniLM                            0.8200        0.7000        0.7400        0.6800       0.1640        0.8200
bge-m3 + mMiniLM                             0.7800        0.6800        0.7100        0.6500       0.1560        0.7800
MiniLM-L12 + mMiniLM                         0.7000        0.6200        0.6600        0.5900       0.1400        0.7000
-------------------------------------------------------------------------------------------------------
```

### Multi-model ingestion

Each embedding model produces vectors with different dimensions, so each requires its own ChromaDB collection. Before running `--compare` or `--find-best`, ingest documents with each model:

```bash
# Default model (already ingested)
python src/pipeline.py

# Additional models
python src/pipeline.py --model intfloat/multilingual-e5-base --collection PoliTutor-Docs-e5-base
python src/pipeline.py --model BAAI/bge-m3 --collection PoliTutor-Docs-bge-m3
python src/pipeline.py --model sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 --collection PoliTutor-Docs-MiniLM-L12
```

### How metrics are calculated

For each Q&A pair in the dataset:

1. The question is sent to ChromaDB (filtered by course unit) to retrieve `top_k` candidate chunks.
2. If a reranker is configured, chunks are re-scored by a cross-encoder and truncated to `reranker_top_k`.
3. If a `score_threshold` is set, chunks with score below the threshold are discarded.
4. A **relevance key** `<filename>_p<page>` is built for each page covered by each returned chunk. When a chunk spans multiple pages, all of them are registered with the same score so that a match on any page counts.
5. The ground-truth relevant document is `<filename>_p<page>` from the QA pair (binary relevance = 1).
6. `ranx` computes the final metrics by comparing the ranked run against the ground-truth qrels.

**Reported metrics** (via `ranx` at `@5`): Hit Rate, MRR, NDCG, MAP, Precision, Recall.

### Customising configurations

Edit `BENCHMARK_COMPARISON_CONFIGS` in `config.py` to add, remove, or modify configurations. Each entry accepts:

| Key | Description |
| --- | --- |
| `name` | Label shown in the output table |
| `embedding_model` | HuggingFace model name for query embedding |
| `collection_name` | ChromaDB collection to query (must be pre-indexed with the right model) |
| `reranker_model` | Cross-encoder model name, or `null` to skip reranking |

Threshold sweep parameters are in `BENCHMARK_THRESHOLD_SWEEP` (`start`, `stop`, `step`, `primary_metric`).