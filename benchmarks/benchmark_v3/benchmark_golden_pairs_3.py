"""Loader for benchmark_golden_pairs_3.jsonl -> structures consumed by the benchmark_v0 algorithm.

Usage:
    from benchmark_golden_pairs_3 import golden_pairs, should_refuse_map, answer_keys, pairs
"""
import json
from pathlib import Path

_PATH = Path(__file__).with_suffix(".jsonl")
_records = [json.loads(l) for l in _PATH.read_text(encoding="utf-8").splitlines() if l.strip()]

meta = next(r for r in _records if r["record_type"] == "meta")
chunks = {r["chunk_id"]: r for r in _records if r["record_type"] == "chunk"}
pairs = [r for r in _records if r["record_type"] == "golden_pair"]

# benchmark_v0: golden_pairs = {"query text": {"chunk_id_1", ...}}  (answerable only)
golden_pairs = {p["query"]: set(p["golden_chunk_ids"]) for p in pairs if not p["should_refuse"]}

# refusal evaluation: query -> should_refuse (all pairs)
should_refuse_map = {p["query"]: p["should_refuse"] for p in pairs}

# grounding keys for hallucination/citation judging
answer_keys = {p["query"]: p["expected_answer_keys"] for p in pairs}

if __name__ == "__main__":
    print(f"{meta['name']}: {len(golden_pairs)} answerable, "
          f"{sum(should_refuse_map.values())} refusal, "
          f"{meta['counts']['chunks_referenced']} chunks referenced")
