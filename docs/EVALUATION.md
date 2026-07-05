# Evaluation

The `rag/src/evaluation` package contains scripts for evaluating retrieval quality, tutor response quality, threshold calibration and embedding visualisation.

Evaluation is separate from the production app. It reads benchmark datasets from `rag/data/benchmark/` and writes results to `rag/data/benchmark/results/`.

## Requirements

From the `rag/` folder, install the development requirements:

```bash
python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements-dev.txt
```

Evaluation requires the same core RAG environment variables as runtime:

```env
CHROMA_API_KEY=your_key_here
CHROMA_TENANT=your_tenant_here
CHROMA_DATABASE=your_database_here
OPENROUTER_KEY=your_key_here
```

Dataset generation and LLM-as-judge evaluation use OpenRouter.

## Retrieval Benchmark

The retrieval benchmark checks whether the retriever returns the expected source page for each question.

### Generate Benchmark Questions

For each document in `COURSE_PATH`, the script extracts page content and asks an LLM to generate questions grounded in that content.

```bash
python -m src.evaluation.benchmark --generate
```

Output:

```text
rag/data/benchmark/BenchmarkQA-<filename>.json
```

### Run Retrieval Evaluation

Evaluate all `BenchmarkQA-*.json` files:

```bash
python -m src.evaluation.benchmark
```

Evaluate one dataset:

```bash
python -m src.evaluation.benchmark data/benchmark/BenchmarkQA-Slides.ED.Aula01.pdf.json
```

Compare multiple embedding/reranker configurations from `BENCHMARK_COMPARISON_CONFIGS`:

```bash
python -m src.evaluation.benchmark --compare
```

Comparison outputs are written to:

```text
rag/data/benchmark/results/
```

### Retrieval Metrics

The benchmark uses `ranx` and reports metrics at `@5`:

| Metric | Meaning |
| --- | --- |
| Hit Rate | Whether the expected page appears in the top results |
| MRR | Rank-sensitive score for the first relevant result |
| NDCG | Ranking quality with position discounting |
| MAP | Mean average precision |
| Precision | Fraction of retrieved top results that are relevant |
| Recall | Fraction of relevant results retrieved |

### How Page Matching Works

For each retrieved chunk, the evaluator builds relevance keys using:

```text
<filename>_p<page>
```

Multi-page chunks register every page listed in their metadata. A question is counted as matched if the ground-truth page appears in the retrieved result set.

## Threshold Calibration

The runtime applies `RETRIEVAL_DISTANCE_THRESHOLD` before reranking. The current configured value is:

```text
0.9301
```

Run a threshold sweep:

```bash
python -m src.evaluation.benchmark_threshold
```

Run with a custom number of threshold values:

```bash
python -m src.evaluation.benchmark_threshold --thresholds 30
```

Output:

```text
rag/data/benchmark/results/threshold_sweep_<timestamp>.json
```

Visualise a threshold sweep:

```bash
python -m src.evaluation.plot_threshold_sweep \
  data/benchmark/results/threshold_sweep_<timestamp>.json
```

The plot shows retrieval metrics and fallback rate across threshold values.

Threshold sweeps can take a long time on CPU because the reranker runs for every benchmark question at every threshold.

## Tutor Benchmark

The tutor benchmark evaluates generated responses rather than only retrieval.

It checks whether the tutor:

- stays faithful to retrieved context;
- avoids direct answers;
- provides useful scaffolding;
- remains clear;
- handles adversarial prompts and fallback cases.

### Generate Tutor Dataset

```bash
python -m src.evaluation.benchmark_tutor --generate
```

Output:

```text
rag/data/benchmark/BenchmarkTutor-sample.json
```

The dataset generation samples pages from ChromaDB and asks an LLM to create:

| Type | Purpose |
| --- | --- |
| `regular` | realistic student questions |
| `adversarial` | questions that pressure the tutor to break Socratic behaviour |

The dataset file is not overwritten automatically. Delete it manually before regenerating.

### Evaluate Tutor Responses

Evaluate the default dataset:

```bash
python -m src.evaluation.benchmark_tutor --evaluate
```

Evaluate a specific dataset:

```bash
python -m src.evaluation.benchmark_tutor --evaluate \
  data/benchmark/BenchmarkTutor-sample.json
```

Outputs:

| File | Description |
| --- | --- |
| `benchmark_tutor_<timestamp>.png` | visual report |
| `benchmark_tutor_similarity_<timestamp>.json` | normal responses sorted by semantic similarity |

### Tutor Judging Criteria

The LLM judge scores normal tutor responses from 1 to 5:

| Criterion | Description |
| --- | --- |
| Faithfulness | grounded in retrieved context and avoids unsupported claims |
| Non-directiveness | avoids giving the final answer directly |
| Scaffolding | gives just enough help for the next reasoning step |
| Clarity | clear and actionable for the student |

Semantic similarity is computed between the generated tutor response and the expected Socratic response using embeddings.

### Response Classes

| Class | Meaning | Scored by judge |
| --- | --- | --- |
| Normal | tutor generated a Socratic answer | Yes |
| Input guardrail | query blocked before generation | No |
| Output guardrail | direct answer detected and replaced | No |
| Fallback | no relevant content found | No |

Guardrail and fallback cases are still counted in aggregate rates.

## Embedding Visualisation

Use Renumics Spotlight to inspect embeddings:

```bash
python -m src.evaluation.visualize
```

This is mainly useful when diagnosing clustering, source separation or unexpected retrieval behaviour.

## Multi-Model Evaluation Workflow

A typical comparison workflow is:

1. Ingest the same source documents into separate ChromaDB collections.
2. Add the collection/model pairs to `BENCHMARK_COMPARISON_CONFIGS` in `rag/src/shared/config.py`.
3. Run:

```bash
python -m src.evaluation.benchmark --compare
```

Example ingestion commands:

```bash
python -m src.ingestion.pipeline \
  --model BAAI/bge-m3 \
  --collection PoliTutor-Docs-bge-m3

python -m src.ingestion.pipeline \
  --model intfloat/multilingual-e5-base \
  --collection PoliTutor-Docs-e5-base
```

## Where Results Live

| Path | Contents |
| --- | --- |
| `rag/data/benchmark/BenchmarkQA-*.json` | retrieval benchmark datasets |
| `rag/data/benchmark/BenchmarkTutor-sample.json` | tutor benchmark dataset |
| `rag/data/benchmark/results/` | benchmark outputs, comparisons and plots |
