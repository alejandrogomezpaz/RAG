"""benchmark_compare.py — one benchmark, four RAG configurations, one readable CSV.

Runs the benchmark_v3 metric suite (which is the benchmark_v0 algorithm, verbatim) across four
systems, holding EVERYTHING constant except the system under test:

    arm         retrieval                                        generation
    ---------   ----------------------------------------------   -----------------------------
    old         MiniLM + FAISS, plain top-k, no rerank           old rad_ai prompt (old_RAG.ipynb)
    new_exact   rag_query.py, embedding strategy = "exact"       new rad_ai prompt (rag_query.py)
    new_mqu     rag_query.py, embedding strategy = "mqu"         new rad_ai prompt
    new_hyde    rag_query.py, embedding strategy = "hyde"        new rad_ai prompt

Constant across all arms: the golden_pairs_3 eval set, the benchmark_v0 metrics, the Groq
hallucination judge, k, and N_RUNS.

FAIRNESS NOTES (why this file exists rather than four ad-hoc runs)
------------------------------------------------------------------
1. Same corpus / id-space. golden_pairs_3 lives in corpus_3's id-space, so every arm must
   retrieve over the same underlying corpus_v3 documents. The "old" arm therefore uses
   old-STYLE retrieval (the old_RAG.ipynb recipe) re-pointed at corpus_3 — NOT the original
   corpus_1 index, which would score ~0 here and mislead. The new arms retrieve over the Chroma
   index that rag_database_initializer.py builds from the same corpus_v3 PDFs.

2. Document-level citation matching. benchmark_v0 matches retrieved hits to golden chunks on a
   "source | page" string. But the new pipeline stores (filename, chunk_index) with NO page
   numbers and a different (semantic) chunker, so its hits have no comparable page label. The
   only common, fair unit across the two chunkers is the SOURCE DOCUMENT. This driver therefore
   scores retrieval/citation metrics at DOCUMENT granularity for ALL arms (so the comparison is
   apples-to-apples). That makes the absolute COP/REC/NDCG here coarser (higher) than the
   page-level numbers benchmark_v3.py reports on its own — expected; only cross-arm deltas matter.

3. Cost shows up. HyDE and MQU add query-time LLM calls, so their RT (latency) and CTX_TOK will
   be higher. That's the tradeoff the benchmark is meant to expose.

SAFETY: this script imports benchmark_v3 and swaps its module-level retrieve()/get_citation()/
golden_sp and its generator hook at runtime. It does NOT modify benchmark_v3.py, anything under
benchmark_v3/, or corpus_v3/.

PREREQUISITES (this script is NOT runnable until these exist — run it explicitly when ready):
  - Chroma index built:            python rag_database_initializer.py   (creates ./index)
  - deps: sentence-transformers, faiss-cpu, langchain-huggingface, langchain-community,
          langchain-experimental, chromadb, transformers, groq
  - the rad_ai local LLM served (Ollama), for generation metrics
  - GROQ_API_KEY set, for the HR hallucination judge

Run:
    python benchmark_compare.py                     # all four arms, full metrics
    python benchmark_compare.py --retrieval-only    # skip generation (no LLM needed)
    python benchmark_compare.py --arms old,new_exact --runs 1
"""
import argparse, csv, os, sys, traceback
from datetime import datetime
from pathlib import Path
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

HERE = Path(__file__).resolve().parent            # .../RAG/benchmarks
RAG_ROOT = HERE.parent                            # .../RAG
V3_DIR = HERE / "benchmark_v3"
sys.path.insert(0, str(V3_DIR))                   # so we can import benchmark_v3 + its loader
sys.path.insert(0, str(RAG_ROOT / "local_LLM"))   # rad_ai.query

import benchmark_v3 as B                          # safe: only loads corpus_3.jsonl; retriever is lazy

# ---- run configuration (all easily overridable via CLI) -----------------------------------
K = 3                 # final chunks fed to the generator (benchmark_v0 DEFAULT_K)
K1_CANDIDATES = 20    # new-RAG candidate pool before rerank (rag_query docstring: ~20 -> 3-5)
MQU_VARIANTS = 3      # multi-query paraphrase count
N_RUNS = 3            # repeats -> 95% CI half-widths (generation is stochastic); lower to cut cost
RESULTS_CSV = HERE / "benchmark_comparison_results.csv"
RUNINFO_CSV = HERE / "benchmark_comparison_runinfo.csv"

# =====================================================================================
# Document-level citation wiring (shared by every arm)
# =====================================================================================
def _load_manifest_titles():
    """corpus_v3 PDF filename stem (== manifest id) -> document title."""
    import csv as _csv
    m = {}
    with open(RAG_ROOT / "corpus_v3" / "corpus_manifest.csv", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            m[row["id"]] = row["title"]
    return m

_TITLES = _load_manifest_titles()

def filename_to_title(filename):
    stem = filename[:-4] if filename.lower().endswith(".pdf") else filename
    return _TITLES.get(stem, stem)

def doc_citation(hit):
    """Document-granularity citation: the source title only (no page)."""
    return hit["source"]

# golden set collapsed to documents: query -> {source titles of its golden chunks}
_CID2SOURCE = {m["chunk_id"]: m["source"] for m in B.metas}
GOLDEN_SP_DOC = {q: {_CID2SOURCE[c] for c in ids} for q, ids in B.golden_pairs.items()}

# =====================================================================================
# Arm builders — each returns (retrieve_fn, answer_fn). Heavy imports are lazy so that
# merely importing this module never triggers model / index loading.
# =====================================================================================
def build_old_arm(retrieval_only):
    """Old RAG: old-style MiniLM+FAISS retrieval over corpus_3 + the old_RAG.ipynb prompt."""
    builtin_retrieve = B._ORIG_RETRIEVE            # captured below, before any patching

    def retrieve_fn(q, k=K):
        return builtin_retrieve(q, k=k)            # (score, text, meta) with source/page

    if retrieval_only:
        return retrieve_fn, None

    from rad_ai import query                        # old + new share the same local LLM

    def answer_fn(q, k=K):
        hits = builtin_retrieve(q, k=k)
        context = "\n\n---\n\n".join(
            f"[SOURCE: {m['source']} | page {m['page']} | score {s:.3f}]\n{txt}"
            for s, txt, m in hits)
        system = ("You are RAD-AI, a radiation safety assistant.\n"
                  "Use ONLY the provided context to answer.\n"
                  "If the answer is not in the context, say: "
                  "'I don't have enough information in the provided files.'\n"
                  "Cite sources as (source, page).")
        ans = query(f"CONTEXT:\n{context}\n\nQUESTION:\n{q}", system=system, temperature=0.0)
        return {"answer": ans, "refused": "don't have enough information" in str(ans).lower()}

    return retrieve_fn, answer_fn

def build_new_arm(strategy, retrieval_only):
    """New RAG (rag_query.py) with a given embedding strategy: 'exact' | 'mqu' | 'hyde'."""
    import rag_query as R                            # module-level: loads Chroma + CrossEncoder

    def _retrieved_docs(q, k):
        """Replicate rag_query's retrieval to expose the surviving chunks (with metadata)."""
        variants = R.query_embedding(q, strategy=strategy, num=MQU_VARIANTS)
        pool = R.top_k_search(variants, R.vectorstore, K1_CANDIDATES)
        return R.rerank_top_k(q, pool, K1_CANDIDATES, k)      # [(doc, rerank_score)]

    def retrieve_fn(q, k=K):
        out = []
        for doc, score in _retrieved_docs(q, k):
            fn = doc.metadata.get("filename")
            ci = doc.metadata.get("chunk_index")
            out.append((float(score), doc.page_content, {
                "source": filename_to_title(fn),                  # -> comparable document title
                "page": f"chunk {ci}",                            # no real page in this pipeline
                "chunk_id": f"{fn}#{ci}",
            }))
        return out

    if retrieval_only:
        return retrieve_fn, None

    def answer_fn(q, k=K):
        prompt = R.retrieve(q, strategy, MQU_VARIANTS, K1_CANDIDATES, k)   # system prompt OR refusal
        refused_pre = "cannot answer this question" in str(prompt).lower()
        ans = R.query(prompt)
        refused = refused_pre or any(p in str(ans).lower() for p in
                                     ("i cannot answer", "not found in the provided sources"))
        return {"answer": ans, "refused": refused}

    return retrieve_fn, answer_fn

ARM_BUILDERS = {
    "old":       lambda ro: build_old_arm(ro),
    "new_exact": lambda ro: build_new_arm("exact", ro),
    "new_mqu":   lambda ro: build_new_arm("mqu", ro),
    "new_hyde":  lambda ro: build_new_arm("hyde", ro),
}
ARM_LABELS = {"old": "Old RAG", "new_exact": "New (exact)",
              "new_mqu": "New (MQU)", "new_hyde": "New (HyDE)"}

# =====================================================================================
# Scoring — patch benchmark_v3's globals for the arm, then run its benchmark() unchanged
# =====================================================================================
def score_arm(name, retrieve_fn, answer_fn, k, n_runs):
    B.retrieve = retrieve_fn                    # run_once() resolves `retrieve` as a module global
    B.get_citation = doc_citation               # document-level matching for every metric
    B.golden_sp = GOLDEN_SP_DOC
    B.configure_generator(answer_fn)            # None -> retrieval-only run
    (q_mean, q_ci), agg = B.benchmark(k=k, n_runs=n_runs)
    return {"quality": (q_mean, q_ci), **agg}

# =====================================================================================
# Human-readable CSV
# =====================================================================================
# metric_key: (pretty label, direction, explanation)
METRIC_ROWS = [
    ("COP",     "Context Precision",      "higher", "fraction of retrieved chunks from a golden document"),
    ("COPG",    "Context Precision @g",   "higher", "correct / min(k, #golden documents)"),
    ("REC",     "Context Recall (Hit@k)", "higher", "fraction of golden documents retrieved"),
    ("NDCG",    "NDCG@k",                 "higher", "rank-aware retrieval quality (golden nearer top = better)"),
    ("CIF1",    "Citation F1",            "higher", "harmonic mean of citation precision & recall"),
    ("AC",      "Answer Correctness",     "higher", "required answer-key phrases present in the answer"),
    ("RR",      "Refusal Accuracy",       "higher", "fraction of correct refuse/answer decisions"),
    ("HR",      "Hallucination Rate",     "lower",  "answers with an unsupported claim (Groq judge)"),
    ("RT",      "Latency (s/query)",      "lower",  "mean retrieval + generation time per query"),
    ("CTX_TOK", "Context Tokens",         "lower",  "mean est. context tokens sent to the LLM"),
    ("quality", "QUALITY (composite)",    "higher", "weighted AC/CIF1/REC/COPG/RR/(1-HR)"),
]

def fmt_cell(pair):
    if pair is None:
        return "n/a"
    mean, ci = pair
    if mean is None:
        return "n/a"
    return f"{mean:.4f} +/- {ci:.4f}"

def write_results_csv(results, arms):
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "better", "explanation"] + [ARM_LABELS[a] for a in arms])
        for key, label, direction, expl in METRIC_ROWS:
            row = [label, direction, expl]
            for a in arms:
                r = results[a]
                row.append("ERROR" if isinstance(r, str) else fmt_cell(r.get(key)))
            w.writerow(row)
        w.writerow([])
        w.writerow(["arm status"] + ["", ""] + [ (results[a] if isinstance(results[a], str) else "ok")
                                                  for a in arms])
    print("saved:", RESULTS_CSV)

def write_runinfo_csv(arms, retrieval_only, n_runs):
    with open(RUNINFO_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["setting", "value"])
        rows = [
            ("generated", datetime.now().isoformat(timespec="seconds")),
            ("eval set", f"benchmark_golden_pairs_3 ({len(B.golden_pairs)} answerable + "
                         f"{sum(B.should_refuse_map.values())} refusal)"),
            ("metric algorithm", "benchmark_v0 (via benchmark_v3.py), unchanged"),
            ("citation matching", "DOCUMENT level (source title) — common unit across chunkers"),
            ("arms", ", ".join(ARM_LABELS[a] for a in arms)),
            ("k (final chunks)", K),
            ("k1 (new-RAG candidate pool)", K1_CANDIDATES),
            ("MQU variants", MQU_VARIANTS),
            ("N_RUNS", n_runs),
            ("mode", "retrieval-only" if retrieval_only else "full (retrieval + generation + judge)"),
            ("judge model (HR)", B.JUDGE_MODEL),
        ]
        for k_, v_ in rows:
            w.writerow([k_, v_])
    print("saved:", RUNINFO_CSV)

# =====================================================================================
def main():
    ap = argparse.ArgumentParser(description="Benchmark old vs new RAG (exact / MQU / HyDE).")
    ap.add_argument("--arms", default="old,new_exact,new_mqu,new_hyde",
                    help="comma list from: old,new_exact,new_mqu,new_hyde")
    ap.add_argument("--runs", type=int, default=N_RUNS, help="N_RUNS (repeats for CI)")
    ap.add_argument("--retrieval-only", action="store_true",
                    help="skip generation metrics (no local LLM / Groq needed)")
    args = ap.parse_args()

    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    bad = [a for a in arms if a not in ARM_BUILDERS]
    if bad:
        sys.exit(f"unknown arm(s): {bad}. choose from {list(ARM_BUILDERS)}")

    # capture benchmark_v3's built-in retriever BEFORE any monkeypatching (old arm reuses it)
    B._ORIG_RETRIEVE = B.retrieve

    print(f"[compare] arms={arms} runs={args.runs} "
          f"mode={'retrieval-only' if args.retrieval_only else 'full'}")
    results = {}
    for name in arms:
        print(f"\n[compare] === {ARM_LABELS[name]} ===")
        try:
            retrieve_fn, answer_fn = ARM_BUILDERS[name](args.retrieval_only)
            results[name] = score_arm(name, retrieve_fn, answer_fn, K, args.runs)
            print(f"[compare] {ARM_LABELS[name]} done.")
        except Exception as e:
            results[name] = f"ERROR: {type(e).__name__}: {e}"
            print(f"[compare] {ARM_LABELS[name]} FAILED:\n{traceback.format_exc()}")

    write_results_csv(results, arms)
    write_runinfo_csv(arms, args.retrieval_onlcy, args.runs)
    print("\nDone. Open benchmark_comparison_results.csv for the side-by-side table.")

if __name__ == "__main__":
    main()
