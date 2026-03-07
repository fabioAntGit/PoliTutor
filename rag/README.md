# Poli-Tutor

> Python project structured for document processing with **RAG (Retrieval-Augmented Generation)** capabilities, targeted at academic course materials.

---

## Description

Poli-Tutor implements a modular RAG pipeline for ingesting, chunking, embedding and retrieving documents (slides, notes) from polytechnic course units. The system supports PDF, PPTX and Markdown files, multimodal image processing, cross-encoder reranking, an interactive retrieval interface, and a full evaluation benchmark.

**Key features:**
- Multi-format extraction via Unstructured API (PDF, PPTX, MD — hi-res, table and image aware)
- Multimodal image processing: images classified and summarised by an LLM (OpenRouter/Gemini), then embedded alongside text
- Source-type aware chunking strategies (slides vs. notes)
- Multilingual embeddings (`multilingual-e5-large`) stored in ChromaDB Cloud
- Cross-encoder reranking (`mmarco-mMiniLMv2-L12-H384-v1`)
- `retrieve()` function callable by a backend, plus an interactive CLI for local testing
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
    │
    ├── src/
    │   ├── config.py                   # All configuration and constants
    │   ├── utils.py                    # Filename parsing and metadata extraction
    │   ├── extractor.py                # File partitioning and page grouping
    │   ├── chunker.py                  # Text splitting with page tracking
    │   ├── embedding.py                # HuggingFace embedder + image LLM summarisation
    │   ├── database.py                 # ChromaDB Cloud client
    │   ├── reranker.py                 # Cross-encoder reranker
    │   ├── retrieval.py                # retrieve() for backend + interactive CLI
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
# Ingest documents into ChromaDB
python src/pipeline.py

# Interactive retrieval CLI
python src/retrieval.py

# Generate benchmark Q&A datasets
python src/benchmark.py --generate

# Evaluate retrieval against existing benchmark files
python src/benchmark.py                                                   # evaluates all BenchmarkQA-*.json
python src/benchmark.py data/benchmark/BenchmarkQA-slides.ED.CAP1.json   # single file

# Visualise embeddings with Spotlight
python src/visualize.py
```

---

## Pipeline Overview

```
Document Files (PDF / PPTX / MD)
      |
      v
extractor.py    →  Partition via Unstructured API (hi-res, tables, images)
      |
      v
chunker.py      →  Split into chunks, track source pages, attach image paths
      |
      v
embedding.py    →  Summarise images via OpenRouter (Gemini), embed text + image
                   summaries with multilingual-e5-large, upsert into ChromaDB Cloud
```

---

## Retrieval

`retrieval.py` exposes a `retrieve(course, query)` function intended to be called by a backend service:

```python
from retrieval import retrieve

results = retrieve(course="ed", query="O que é uma árvore AVL?")
```

It queries ChromaDB filtered by course unit, then applies cross-encoder reranking before returning results.

For local testing, run `python src/retrieval.py` to launch the interactive CLI.

---

## Benchmark

The benchmark module generates Q&A pairs from page content (via IAEdu API) and evaluates ChromaDB retrieval quality.

**Generate datasets** (requires IAEdu API):
```bash
python src/benchmark.py --generate
```
This creates `BenchmarkQA-<filename>.json` files in `rag/data/benchmark/`.

**Evaluate retrieval:**
```bash
python src/benchmark.py
```

**Reported metrics** (via `ranx` at `@5`): Hit Rate, MRR, NDCG, MAP, Precision, Recall.
