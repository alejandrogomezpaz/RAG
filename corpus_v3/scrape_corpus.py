#!/usr/bin/env python3
"""Corpus scraper. Downloads every open/public-domain URL in corpus_manifest.csv
into corpus/, then writes corpus/pdf_paths.json for your RAG instantiator:
    list_of_pdfs = json.load(open("corpus/pdf_paths.json"))
    list_of_documents = add_documents(base_corpus, pdf_cleaner(list_of_pdfs))
Stdlib only. Browser UA + retries because gov sites block bots / are slow.
Re-runnable: keeps whatever is already in corpus/, only fetches what's missing."""
import csv, json, os, time, urllib.request, urllib.parse, subprocess, shutil

HERE   = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.join(HERE, "corpus")
HDRS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
        "Accept": "application/pdf,text/html;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"}

def _curl(url, referer):                             # fallback: some gov WAFs (nrc/fema/doe) accept curl's TLS but 403 urllib
    if not shutil.which("curl"): return None
    try:
        r = subprocess.run(["curl", "-fsSL", "--max-time", "90",
                            "-A", HDRS["User-Agent"],
                            "-H", "Accept-Language: " + HDRS["Accept-Language"],
                            "-H", "Referer: " + referer, url],
                           capture_output=True, timeout=120)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None

def fetch(url):                                      # 3 urllib tries + backoff, then curl fallback; 90s timeout
    referer = "{0.scheme}://{0.netloc}/".format(urllib.parse.urlsplit(url))
    hdrs = dict(HDRS, Referer=referer)
    err = None
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=hdrs), timeout=90).read()
            if data[:5] != b"%PDF-": raise ValueError("not a PDF (server returned a block/HTML page)")
            return data
        except Exception as e:
            err = e
            if attempt < 2: time.sleep(2 ** attempt)
    data = _curl(url, referer)                       # last resort for WAF-protected hosts
    if data and data[:5] == b"%PDF-": return data
    raise err

paths = []
for r in csv.DictReader(open(os.path.join(HERE, "corpus_manifest.csv"), encoding="utf-8")):
    if r["access"] == "local":                      # local docs: used in place, never fetched
        p = os.path.normpath(os.path.join(HERE, r["url"]))
    else:
        p = os.path.join(CORPUS, r["id"] + ".pdf")
        if not os.path.exists(p):                   # skip anything already downloaded
            try:
                data = fetch(r["url"])
                os.makedirs(CORPUS, exist_ok=True)  # (re)create before writing — safe if the folder moved
                open(p, "wb").write(data); print("+", r["id"])
            except Exception as e:
                print("x", r["id"], e); continue    # skip failures, never break the list
    if os.path.exists(p):
        paths.append(p)
    elif r["access"] == "local":                    # user-supplied project doc that isn't here yet
        print("x", r["id"], "MISSING local file — expected at", p)

os.makedirs(CORPUS, exist_ok=True)
json.dump(paths, open(os.path.join(CORPUS, "pdf_paths.json"), "w"), indent=2)
print(f"\n{len(paths)} PDFs → corpus/pdf_paths.json")
