"""benchmark_v3.py — the benchmark_v0 algorithm, wired to corpus_v3.

This is a faithful port of benchmarks/benchmark_v0.ipynb: the metric functions (COP, COPG,
REC, NDCG, CIF1, AC, RR, HR, RT, CTX_TOK and the weighted `quality` composite) are copied
verbatim. Only the data wiring is repointed:

    corpus_1.jsonl                -> corpus_3.jsonl                  (this folder)
    benchmark_golden_pairs_1      -> benchmark_golden_pairs_3        (this folder)

Retrieval is self-contained (SentenceTransformer all-MiniLM-L6-v2 + FAISS IndexFlatIP, the
same recipe as old_RAG.ipynb) so this runner does NOT depend on old_RAG.ipynb, which hardcodes
corpus_1. If sentence-transformers/faiss are unavailable or the model can't be downloaded, it
falls back to a dependency-free hashing embedder (lower quality — for plumbing/smoke tests).

corpus_v3 is read-only; this script only reads corpus_3.jsonl (built by build_corpus_3.py).

Generation-dependent metrics (AC, CIF1, HR, RR) require a RAG *answer* function that generates
over corpus_3. Provide one with `configure_generator(fn)` where fn(question, k) -> dict/str.
Without it, the runner reports retrieval-only metrics (COP, COPG, REC, NDCG, CTX_TOK, RT).
The independent hallucination judge (HR) additionally needs GROQ_API_KEY + the `groq` package.

Run:
    python benchmark_v3.py           # -> benchmark_results_v3.csv
"""
import csv, json, math, os, re, statistics, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS_PATH = str(HERE / "corpus_3.jsonl")
RESULTS_PATH = str(HERE / "benchmark_results_v3.csv")

from benchmark_golden_pairs_3 import golden_pairs, should_refuse_map, answer_keys  # noqa: E402

REFUSAL = "don't have enough information"
DEFAULT_K = 3
N_RUNS = 1
JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "llama-3.3-70b-versatile")
QUALITY_WEIGHTS = {'AC': 0.30, 'CIF1': 0.20, 'REC': 0.15, 'COPG': 0.10, 'RR': 0.15, 'HR': 0.10}

# ---- corpus metadata (identical shape to benchmark_v0: page := chunk "section") ----
_corpus = [json.loads(l) for l in open(CORPUS_PATH, encoding="utf-8") if l.strip()]
metas = [
    {"source": r["source"], "page": r["section"], "chunk_id": r["chunk_id"], "text": r["text"]}
    for r in _corpus if r.get("record_type") == "chunk"
]
cid2sp = {m["chunk_id"]: f'{m["source"]} | page {m["page"]}' for m in metas}
golden_sp = {q: {cid2sp[c] for c in ids} for q, ids in golden_pairs.items()}

# =====================================================================================
# Retrieval — self-contained MiniLM + FAISS (old_RAG recipe), with a dependency-free
# hashing fallback so the harness always runs.
# =====================================================================================
_INDEX = {"ready": False, "mode": None, "embed": None, "matrix": None}


def _minilm_embedder():
    import numpy as np
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    def embed(texts):
        return model.encode(texts, normalize_embeddings=True).astype(np.float32)
    return embed


def _hash_embedder(dim=512):
    """Dependency-free bag-of-words hashing embedder (cosine via L2-normalized vectors)."""
    import numpy as np
    tok = re.compile(r"[a-z0-9]+")

    def embed(texts):
        out = np.zeros((len(texts), dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in tok.findall(t.lower()):
                out[i, hash(w) % dim] += 1.0
        n = np.linalg.norm(out, axis=1, keepdims=True)
        n[n == 0] = 1.0
        return out / n
    return embed


def build_index():
    import numpy as np
    try:
        embed = _minilm_embedder()
        mode = "minilm"
    except Exception as e:
        print(f"[benchmark_v3] MiniLM unavailable ({type(e).__name__}); using hashing embedder.")
        embed = _hash_embedder()
        mode = "hash"
    mat = embed([m["text"] for m in metas])
    try:
        import faiss
        idx = faiss.IndexFlatIP(mat.shape[1])
        idx.add(mat)
        _INDEX.update(ready=True, mode=mode, embed=embed, matrix=idx, backend="faiss")
    except Exception:
        _INDEX.update(ready=True, mode=mode, embed=embed, matrix=np.asarray(mat), backend="numpy")
    print(f"[benchmark_v3] index built: {len(metas)} chunks, embedder={mode}, backend={_INDEX['backend']}")


def retrieve(question, k=DEFAULT_K):
    """Return list of (score, text, meta) — meta carries source/page/chunk_id (benchmark_v0 shape)."""
    if not _INDEX["ready"]:
        build_index()
    import numpy as np
    qv = _INDEX["embed"]([question])
    if _INDEX["backend"] == "faiss":
        scores, ids = _INDEX["matrix"].search(qv, k)
        pairs = list(zip(scores[0], ids[0]))
    else:
        sims = (_INDEX["matrix"] @ qv[0])
        ids = np.argsort(-sims)[:k]
        pairs = [(float(sims[i]), int(i)) for i in ids]
    out = []
    for score, i in pairs:
        m = metas[int(i)]
        out.append((float(score), m["text"],
                    {"source": m["source"], "page": m["page"], "chunk_id": m["chunk_id"]}))
    return out


# ---- generation hook (optional): fn(question, k) -> {"answer": str, "refused": bool} or str
_GENERATOR = {"fn": None}


def configure_generator(fn):
    """Register a RAG answer function that generates over corpus_3 (for AC/CIF1/HR/RR)."""
    _GENERATOR["fn"] = fn


def rag_answer(question, k=DEFAULT_K, max_new_tokens=300):
    if _GENERATOR["fn"] is None:
        return None
    return _GENERATOR["fn"](question, k)


# =====================================================================================
# Metric functions — copied VERBATIM from benchmark_v0.ipynb
# =====================================================================================
def get_citation(hit):
    """Comparable source|page string for a retrieved hit."""
    return f'{hit["source"]} | page {hit["page"]}'


def context_precision(q, hits):
    """Fraction of retrieved chunks that are golden."""
    if not hits:
        return 0.0
    g = golden_sp.get(q, set())
    return sum(1 for h in hits if get_citation(h) in g) / len(hits)


def context_precision_at_g(q, hits):
    """Correct retrieved / min(k, #golden); removes the single-golden precision cap."""
    g = golden_sp.get(q, set())
    if not g:
        return None
    got = {get_citation(h) for h in hits}
    denom = min(len(hits), len(g))
    return len(got & g) / denom if denom else 0.0


def context_recall(q, hits):
    """Fraction of golden chunks that were retrieved (Hit@k)."""
    g = golden_sp.get(q, set())
    if not g:
        return None
    got = {get_citation(h) for h in hits}
    return len(got & g) / len(g)


def ndcg(q, hits):
    """Rank-aware retrieval quality over binary golden relevance."""
    g = golden_sp.get(q, set())
    if not g:
        return None
    dcg, seen = 0.0, set()
    for i, h in enumerate(hits):
        c = get_citation(h)
        if c in g and c not in seen:
            seen.add(c)
            dcg += 1 / math.log2(i + 2)
    idcg = sum(1 / math.log2(i + 2) for i in range(min(len(g), len(hits))))
    return dcg / idcg if idcg else 0.0


def citation_f1(cited, golden):
    """Harmonic mean of citation precision and citation recall."""
    if not golden:
        return None
    p = sum(1 for c in cited if c in golden) / len(cited) if cited else 0.0
    r = sum(1 for c in golden if c in set(cited)) / len(golden)
    return 2 * p * r / (p + r) if (p + r) else 0.0


def answer_correctness(answer, key):
    """Fraction of required phrases present, or token-F1 vs a gold answer string."""
    if key is None or refused(answer):
        return None if key is None else 0.0
    ans = (answer.get("answer", "") if isinstance(answer, dict) else str(answer)).lower()
    if isinstance(key, dict):
        key = key.get("must_include") or key.get("keywords") or key.get("answer")
    if isinstance(key, (list, tuple, set)):
        return sum(1 for p in key if str(p).lower() in ans) / len(key) if key else None
    gold, got = set(re.findall(r"[a-z0-9]+", str(key).lower())), set(re.findall(r"[a-z0-9]+", ans))
    o = len(gold & got)
    return 2 * o / (len(gold) + len(got)) if o else 0.0


def refused(answer):
    """True if the pipeline abstained (structured flag or refusal phrase)."""
    if isinstance(answer, dict) and "refused" in answer:
        return bool(answer["refused"])
    text = answer.get("answer", "") if isinstance(answer, dict) else str(answer)
    return REFUSAL in text.lower()


def refusal_score(did, should):
    """Fraction of correct refuse/answer decisions."""
    return sum(1 for d, s in zip(did, should) if d == s) / len(should)


def judge_hallucination(q, answer, chunks, retries=2):
    """Independent LLM judge (Groq, not the local generator).
    True = answer has a claim unsupported by the chunks, False = grounded,
    None = judge unreachable (excluded from HR rather than scored as clean)."""
    if refused(answer):
        return False
    ans = answer.get("answer", "") if isinstance(answer, dict) else str(answer)
    if not ans.strip():
        return None
    ctx = "\n\n".join(f"[{i+1}] {h['text']}" for i, h in enumerate(chunks)) or "(none)"

    system = (
        "You are a strict factuality judge for a retrieval-augmented QA system. "
        "Decide whether the ANSWER contains a hallucination: any factual claim not "
        "supported by the CONTEXT. Judge only against the CONTEXT, not outside knowledge. "
        "A refusal is NOT a hallucination. List unsupported claims first, then the verdict. "
        'Respond ONLY as JSON: {"unsupported": ["..."], "hallucinated": true|false}'
    )
    user = f"QUESTION:\n{q}\n\nCONTEXT:\n{ctx}\n\nANSWER:\n{ans}"

    try:
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])
    except Exception:
        return None
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=JUDGE_MODEL, temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
            )
            raw = resp.choices[0].message.content
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                return bool(json.loads(m.group(0)).get("hallucinated", False))
        except Exception:
            if attempt < retries:
                time.sleep(2 ** attempt)
    return None


def context_tokens(hits):
    """Estimated context tokens sent to the LLM (~4 chars/token)."""
    return sum(len(h["text"]) for h in hits) // 4


def quality_score(s):
    """Weighted composite of the quality metrics; HR inverted, weights normalized."""
    parts = {'AC': s['AC'], 'CIF1': s['CIF1'], 'REC': s['REC'],
             'COPG': s['COPG'], 'RR': s['RR'], 'HR': 1 - s['HR']}
    num = sum(QUALITY_WEIGHTS[k] * v for k, v in parts.items() if v is not None)
    wsum = sum(QUALITY_WEIGHTS[k] for k, v in parts.items() if v is not None)
    return num / wsum if wsum else 0.0


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0


def run_once(k=DEFAULT_K):
    """One full pass over the eval set; returns (quality, scores dict).

    Generation-dependent metrics (CIF1, AC, HR) are only computed when a generator is
    configured; RR is computed only then too (a refusal decision needs an answer)."""
    have_gen = _GENERATOR["fn"] is not None
    lat, cop, copg, rec, nd, cif, ac, tok = [], [], [], [], [], [], [], []
    did, should, hall = [], [], []
    for q, sr in should_refuse_map.items():
        t0 = time.time()
        hits = [{"source": m["source"], "page": m["page"], "chunk_id": m["chunk_id"], "text": txt}
                for _, txt, m in retrieve(q, k=k)]
        answer = rag_answer(q, k=k) if have_gen else None
        lat.append(time.time() - t0)
        tok.append(context_tokens(hits))

        cop.append(context_precision(q, hits))
        for lst, fn in ((copg, context_precision_at_g), (rec, context_recall), (nd, ndcg)):
            v = fn(q, hits)
            if v is not None:
                lst.append(v)

        if have_gen and not sr:
            ans = answer.get("answer", answer) if isinstance(answer, dict) else answer
            cited = [get_citation(h) for h in hits if h["source"].lower() in str(ans).lower()]
            f = citation_f1(cited, golden_sp.get(q, set()))
            if f is not None:
                cif.append(f)
            a = answer_correctness(answer, answer_keys.get(q))
            if a is not None:
                ac.append(a)
            hall.append(judge_hallucination(q, answer, hits))

        if have_gen:
            did.append(refused(answer))
            should.append(sr)

    scores = {'COP': _mean(cop), 'COPG': _mean(copg), 'REC': _mean(rec), 'NDCG': _mean(nd),
              'CIF1': _mean(cif), 'AC': _mean(ac),
              'RR': refusal_score(did, should) if did else None,
              'HR': _mean(hall), 'RT': _mean(lat), 'CTX_TOK': _mean(tok)}
    # quality_score needs the generation metrics; report it only when available
    q_scores = dict(scores)
    for key_ in ('CIF1', 'AC', 'RR', 'HR'):
        if q_scores[key_] is None:
            q_scores[key_] = 0.0
    return (quality_score(q_scores) if have_gen else None), scores


def benchmark(k=DEFAULT_K, n_runs=N_RUNS):
    """Run n_runs times; returns (quality, scores) each as mean ± 95% CI half-width."""
    def ci(xs):
        xs = [x for x in xs if x is not None]
        if not xs:
            return None, 0.0
        m = statistics.mean(xs)
        return m, (1.96 * statistics.stdev(xs) / math.sqrt(len(xs)) if len(xs) > 1 else 0.0)
    runs = [run_once(k) for _ in range(n_runs)]
    quals, scores = [q for q, _ in runs], [s for _, s in runs]
    return ci(quals), {m: ci([s[m] for s in scores]) for m in scores[0]}


# =====================================================================================
# CSV writer — copied from benchmark_v0.ipynb (cell 2), repointed output path
# =====================================================================================
METRIC_DOCS = {
    'COP':     "Context Precision: fraction of retrieved chunks that are golden.",
    'COPG':    "Context Precision @ golden-count: correct / min(k, #golden).",
    'REC':     "Context Recall (Hit@k): fraction of golden chunks retrieved.",
    'NDCG':    "Normalized DCG@k: rank-aware retrieval quality, golden nearer top scores higher.",
    'CIF1':    "Citation F1: harmonic mean of citation precision and recall.",
    'AC':      "Answer Correctness: required phrases present / token-F1 vs gold answer.",
    'RR':      "Refusal accuracy: fraction of correct refuse/answer decisions.",
    'HR':      "Hallucination Rate: fraction of answers unsupported by context (lower better).",
    'RT':      "Latency: mean retrieval + generation time per query (seconds).",
    'CTX_TOK': "Mean estimated context tokens sent to the LLM (~4 chars/token).",
}


def write_csv(path, quality, agg):
    """Write one row per metric (value, 95% CI, explanation) plus the composite quality."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value", "ci95_halfwidth", "explanation"])
        for m, (v, c) in agg.items():
            w.writerow([m, ("" if v is None else round(v, 4)), round(c, 4), METRIC_DOCS.get(m, "")])
        qv, qc = quality
        w.writerow(["quality", ("" if qv is None else round(qv, 4)), round(qc, 4),
                    "Weighted composite of AC, CIF1, REC, COPG, RR, (1-HR); mean +/- 95% CI over N_RUNS "
                    "(blank unless a generator is configured)."])
    print("saved:", path)


if __name__ == "__main__":
    (q_mean, q_ci), agg = benchmark()
    write_csv(RESULTS_PATH, (q_mean, q_ci), agg)
    if _GENERATOR["fn"] is None:
        print("\nNote: no generator configured — retrieval metrics only "
              "(COP/COPG/REC/NDCG/CTX_TOK/RT). Register one with configure_generator(fn) "
              "to also score CIF1/AC/RR/HR and the composite quality.")
