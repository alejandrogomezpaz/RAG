# benchmark_v3 — Golden Pairs + benchmark harness for corpus_v3

A self-contained evaluation package for the **corpus_v3** RAG corpus, built on the
**benchmark_v0 algorithm** (`benchmarks/benchmark_v0.ipynb`). Everything here is generated from
the `corpus_v3` PDFs, which are treated as **read-only input** — nothing in `corpus_v3/` is
modified.

## What's here

| File | Role | Analogue in v1 |
|---|---|---|
| `build_corpus_3.py` | Extract + chunk every `corpus_v3/corpus/*.pdf` into `corpus_3.jsonl` (+ manifest) | `build_corpus_1.py` |
| `corpus_3.jsonl` | Chunked eval corpus (meta + 5,556 chunk records) the retriever runs over | `corpus_1.jsonl` |
| `corpus_3_manifest.md` | Per-document, human-validation manifest (counts + sample chunks) | `corpus_1_manifest.md` |
| `build_golden_pairs_3.py` | Authors + **verifies** the golden pairs, writes the JSONL | `build_golden_pairs_1.py` |
| `benchmark_golden_pairs_3.jsonl` | The Golden Pairs set (46 answerable + 6 refusal) | `benchmark_golden_pairs_1.jsonl` |
| `benchmark_golden_pairs_3.py` | Loader → `golden_pairs`, `should_refuse_map`, `answer_keys`, `pairs` | `benchmark_golden_pairs_1.py` |
| `benchmark_v3.py` | The benchmark_v0 metrics, verbatim, wired to the v3 data | `benchmark_v0.ipynb` |
| `benchmark_results_v3.csv` | Output (written by `benchmark_v3.py`) | `benchmark_results.csv` |

## The Golden Pairs set

`benchmark_golden_pairs_3.jsonl` follows the exact schema the benchmark_v0 algorithm consumes:

- **`meta`** — provenance + counts.
- **`chunk`** — snapshot (`chunk_id`, `source`, `section`) of every referenced chunk.
- **`golden_pair`** — `query`, `golden_chunk_ids`, `should_refuse`, `query_type`, `origin`,
  `expected_answer_keys` (+ optional `notes`).

**46 answerable + 6 refusal = 52 pairs**, spanning 15 documents (EPA PAG, IAEA EPR / GSR / GSG /
RS-G / SRS, DOE-STD-1098, NRC RG 8.34, Radiacode + GQ GMC detector manuals). Design mirrors v1:

- Queries **paraphrase** the source (so this tests retrieval, not string matching).
- `expected_answer_keys` are **verbatim lowercase substrings** of the golden chunk union —
  `build_golden_pairs_3.py` fails loudly if any key is not present.
- Refusals are **verified absent** from the corpus (near-misses: isotope half-lives, a detector
  mAh rating, retail price, uranium melting point).
- Two topics that were **refusals in v1 are now answerable in v3**, because the corpus_v3 PDFs add
  them: **detector calibration** (GQ GMC manual) and **KI milligram dosing by age** (EPA PAG
  Table 2-2).

## How it maps to benchmark_v0

`benchmark_v3.py` copies the benchmark_v0 metric functions **verbatim** — `COP, COPG, REC, NDCG,
CIF1, AC, RR, HR, RT, CTX_TOK` and the weighted `quality` composite. Only the wiring changes:

```
corpus_1.jsonl            -> corpus_3.jsonl
benchmark_golden_pairs_1  -> benchmark_golden_pairs_3
```

Retrieval is self-contained (SentenceTransformer `all-MiniLM-L6-v2` + FAISS `IndexFlatIP`, the
same recipe as `old_RAG.ipynb`), so it does **not** depend on `old_RAG.ipynb` (which hardcodes
corpus_1). If those libraries or the model aren't available, it falls back to a dependency-free
hashing embedder so the harness still runs (lower quality — for plumbing / smoke tests).

## Run it

```bash
# 1) (re)build the corpus from the corpus_v3 PDFs   — needs: pdftotext (poppler) or pypdf
python build_corpus_3.py

# 2) (re)build + verify the golden pairs
python build_golden_pairs_3.py

# 3) run the benchmark  -> benchmark_results_v3.csv
#    full retrieval quality needs: pip install sentence-transformers faiss-cpu
python benchmark_v3.py
```

### Retrieval-only vs. full

Out of the box `benchmark_v3.py` reports **retrieval** metrics (`COP, COPG, REC, NDCG, CTX_TOK,
RT`) — no LLM required. To also score the **generation** metrics (`CIF1, AC, RR, HR`) and the
composite `quality`, register a RAG answer function that generates over `corpus_3`:

```python
import benchmark_v3
from my_rag import answer          # answer(question, k) -> {"answer": str, "refused": bool} | str
benchmark_v3.configure_generator(answer)
(q, q_ci), agg = benchmark_v3.benchmark()
benchmark_v3.write_csv(benchmark_v3.RESULTS_PATH, (q, q_ci), agg)
```

The independent hallucination judge (`HR`) additionally needs `GROQ_API_KEY` and `pip install
groq` (set `JUDGE_MODEL` to override the default).
