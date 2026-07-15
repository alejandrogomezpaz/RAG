RAD-AI RAG Corpus (v2)
32 free/public radiation-safety documents (IAEA, DOE, NRC, EPA, FEMA, detector manuals) in one CSV, plus a single stdlib scraper.
Files: corpus_manifest.csv · scrape_corpus.py · README.md
Run:
bashpython scrape_corpus.py   # → corpus/*.pdf + corpus/pdf_paths.json
Ingest:
pythonlist_of_pdfs = json.load(open("corpus/pdf_paths.json"))
list_of_documents = add_documents(base_corpus, pdf_cleaner(list_of_pdfs))
Grow the corpus by adding CSV rows. ICRP/NCRP excluded (paywalled).