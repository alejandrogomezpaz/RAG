#!/usr/bin/env python3
"""Minimal corpus scraper. Downloads every open/public-domain URL in
corpus_manifest.csv into corpus/, then writes corpus/pdf_paths.json — the list
your RAG instantiator feeds to pdf_cleaner():
    list_of_pdfs = json.load(open("corpus/pdf_paths.json"))
    list_of_documents = add_documents(base_corpus, pdf_cleaner(list_of_pdfs))
Stdlib only; all the richness lives in the CSV."""
import csv, json, os, urllib.request

HERE   = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")
os.makedirs(CORPUS, exist_ok=True)
paths  = []

for r in csv.DictReader(open(os.path.join(HERE, "corpus_manifest.csv"), encoding="utf-8")):
    if r["access"] == "local":                      # local docs: used in place, never fetched
        p = os.path.normpath(os.path.join(HERE, r["url"]))
    else:                                           # open/public-domain: download once
        p = os.path.join(CORPUS, r["id"] + ".pdf")
        if not os.path.exists(p):
            try:
                req  = urllib.request.Request(r["url"], headers={"User-Agent": "RAD-AI/1.0"})
                data = urllib.request.urlopen(req, timeout=60).read()
                assert data[:5] == b"%PDF-", "not a PDF"
                open(p, "wb").write(data); print("+", r["id"])
            except Exception as e:
                print("x", r["id"], e); continue    # skip failures, never break the list
    if os.path.exists(p):
        paths.append(p)

json.dump(paths, open(os.path.join(CORPUS, "pdf_paths.json"), "w"), indent=2)
print(f"\n{len(paths)} PDFs → corpus/pdf_paths.json")