"""Build corpus_3.jsonl from the corpus_v3 PDFs (RAD-AI RAG).

Same schema/design as corpus_1.jsonl, but sourced by extracting + chunking every PDF
under corpus_v3/corpus/*.pdf. corpus_v3 is treated as READ-ONLY input; nothing there is
modified. All output lands in benchmarks/benchmark_v3/.

Chunk record schema (consumed by benchmark_v0's algorithm):
    {record_type:"chunk", chunk_id, source, section, url, retrieved, doc_id,
     page_start, page_end, text}
benchmark_v0 reads r["source"], r["section"], r["chunk_id"] (cid2sp) and h["text"] (retrieval).

Run:
    python build_corpus_3.py            # -> corpus_3.jsonl
"""
import csv, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAG_ROOT = HERE.parents[1]                       # .../RAG
CORPUS_DIR = RAG_ROOT / "corpus_v3" / "corpus"    # read-only PDFs
MANIFEST = RAG_ROOT / "corpus_v3" / "corpus_manifest.csv"
OUT = HERE / "corpus_3.jsonl"
OUT_MANIFEST = HERE / "corpus_3_manifest.md"
RETRIEVED = "2026-07-15"
MANIFEST_SAMPLES = 4     # chunk previews shown per document in the human-validation manifest

TARGET_CHARS = 1100      # ~275 tokens target per chunk
MAX_CHARS = 1700         # hard cap before force-splitting a segment
MIN_CHUNK_CHARS = 200    # drop tiny trailing fragments


def load_manifest():
    """id -> {title, publisher, doc_class, url, access}."""
    m = {}
    with open(MANIFEST, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m[row["id"]] = row
    return m


def pdf_pages(pdf_path):
    """Return list of raw page texts using pdftotext (form-feed separated)."""
    try:
        out = subprocess.run(["pdftotext", "-q", str(pdf_path), "-"],
                             capture_output=True, text=True, timeout=300)
        txt = out.stdout
        if txt.strip():
            return txt.split("\f")
    except Exception as e:
        print(f"  pdftotext failed ({e}); falling back to pypdf", file=sys.stderr)
    import pypdf
    return [p.extract_text() or "" for p in pypdf.PdfReader(str(pdf_path)).pages]


def find_boilerplate(pages):
    """Lines repeated on >=30% of pages are treated as running headers/footers."""
    from collections import Counter
    c = Counter()
    for pg in pages:
        for ln in {l.strip() for l in pg.splitlines() if l.strip()}:
            c[ln] += 1
    n = max(len(pages), 1)
    return {ln for ln, k in c.items() if k >= max(3, 0.30 * n) and len(ln) < 120}


def clean_page(text, boiler):
    """Normalize one page's text: drop boilerplate, de-hyphenate, collapse whitespace."""
    lines = []
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s in boiler:
            continue
        if re.fullmatch(r"[-–—•\.\s]*\d*[-–—•\.\s]*", s):   # page numbers / rule lines
            continue
        s = re.sub(r"\.{3,}", " ", s)                        # TOC dot leaders
        lines.append(s)
    text = "\n".join(lines)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)             # de-hyphenate across line breaks
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    return text.strip()


def segments(text):
    """Paragraph-ish segments; long paragraphs are split on sentence boundaries."""
    segs = []
    for para in re.split(r"\n\s*\n", text):
        para = para.replace("\n", " ").strip()
        if not para:
            continue
        if len(para) <= MAX_CHARS:
            segs.append(para)
        else:
            buf = ""
            for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", para):
                if len(buf) + len(sent) + 1 > MAX_CHARS and buf:
                    segs.append(buf.strip()); buf = sent
                else:
                    buf = f"{buf} {sent}".strip()
            if buf.strip():
                segs.append(buf.strip())
    return segs


def chunk_document(pages, boiler):
    """Yield (text, page_start, page_end) packed to ~TARGET_CHARS, tracking page spans."""
    buf, pstart, pcur = "", None, None
    for i, raw in enumerate(pages, start=1):
        cleaned = clean_page(raw, boiler)
        if not cleaned:
            continue
        for seg in segments(cleaned):
            if pstart is None:
                pstart = i
            pcur = i
            if len(buf) + len(seg) + 1 > TARGET_CHARS and len(buf) >= MIN_CHUNK_CHARS:
                yield buf.strip(), pstart, pcur
                buf, pstart = seg, i
            else:
                buf = f"{buf} {seg}".strip()
    if buf.strip() and len(buf.strip()) >= MIN_CHUNK_CHARS // 2:
        yield buf.strip(), pstart or 1, pcur or 1


def write_manifest(records, per_doc, man, tok_est):
    """Per-document human-validation manifest (summary + sample chunks per doc)."""
    by_doc = {}
    for r in records:
        by_doc.setdefault(r["doc_id"], []).append(r)
    lines = ["# corpus_3 — manifest for human validation", "",
             f"**{len(records)} chunks · ~{tok_est} tokens · {len(by_doc)} documents** — "
             f"v3, built {RETRIEVED}", "",
             "Auto-extracted from the corpus_v3 PDFs (read-only). Chunks are ~275-token "
             "packings of cleaned page text with page spans. Spot-check a sample per document "
             f"against the source PDF; full chunk text lives in `corpus_3.jsonl`. "
             f"Showing {MANIFEST_SAMPLES} sample chunks per document.", "", "---", ""]
    for doc_id in sorted(by_doc):
        chs = by_doc[doc_id]
        meta = man.get(doc_id, {})
        title = meta.get("title", doc_id)
        url = meta.get("url", "")
        dtok = sum(len(c["text"]) // 4 for c in chs)
        lines += [f"## {title}", "", f"<{url}>", "",
                  f"`{doc_id}` · **{len(chs)} chunks** · ~{dtok} tok · "
                  f"ids `{chs[0]['chunk_id']}` … `{chs[-1]['chunk_id']}`", ""]
        step = max(1, len(chs) // MANIFEST_SAMPLES)
        for c in chs[::step][:MANIFEST_SAMPLES]:
            prev = c["text"][:160].replace("\n", " ")
            lines.append(f"- [ ] **`{c['chunk_id']}`** · *{c['section']}* · "
                         f"~{len(c['text'])//4} tok  \n  {prev}…")
        lines += ["", "---", ""]
    OUT_MANIFEST.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT_MANIFEST.name}: {len(by_doc)} documents")


def main():
    man = load_manifest()
    pdfs = sorted(CORPUS_DIR.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs under {CORPUS_DIR}")

    records, sources_seen, tok_est = [], [], 0
    per_doc = {}
    for pdf in pdfs:
        doc_id = pdf.stem
        meta = man.get(doc_id, {})
        title = meta.get("title", doc_id)
        url = meta.get("url", "")
        pages = pdf_pages(pdf)
        boiler = find_boilerplate(pages)
        idx = 0
        for text, ps, pe in chunk_document(pages, boiler):
            idx += 1
            cid = f"{doc_id.replace('-', '_')}_{idx:04d}"
            section = f"p{ps}" if ps == pe else f"p{ps}-{pe}"
            records.append({
                "record_type": "chunk", "chunk_id": cid, "source": title,
                "section": section, "url": url, "retrieved": RETRIEVED,
                "doc_id": doc_id, "page_start": ps, "page_end": pe, "text": text,
            })
            tok_est += len(text) // 4
        per_doc[doc_id] = idx
        if title not in sources_seen:
            sources_seen.append(title)
        print(f"  {doc_id}: {idx} chunks ({len(pages)} pages)")

    meta_rec = {
        "record_type": "meta", "name": "corpus_3", "version": 3, "created": RETRIEVED,
        "source": "corpus_v3/corpus/*.pdf (21 documents)",
        "sources": sources_seen,
        "counts": {"chunks": len(records), "documents": len(pdfs), "tokens_est": tok_est},
        "id_convention": "<doc_id with '-'->'_'>_<0000 index>",
        "notes": ("Built by extracting + chunking every corpus_v3 PDF (pdftotext, "
                  "boilerplate/header removal, de-hyphenation, ~275-token packing with page "
                  "spans). corpus_v3 is read-only input. Consumed by benchmark_v3 "
                  "(benchmark_v0 algorithm)."),
    }
    with OUT.open("w", encoding="utf-8") as f:
        f.write(json.dumps(meta_rec, ensure_ascii=False) + "\n")
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nwrote {OUT.name}: {len(records)} chunks from {len(pdfs)} docs, ~{tok_est} tok")
    write_manifest(records, per_doc, man, tok_est)


if __name__ == "__main__":
    main()
