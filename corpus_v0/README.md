# RAD-AI Mini-Corpus (v0)

Curated, validated document set for the **offline LLM assistant for non-expert emergency responders** (radiation / nuclear incidents).

Generated: 2026-07-07. 15 documents, all validated PASS.

## Why these documents

Selected for the responder use case: triage, decontamination, protective actions, population monitoring, public communication, and the international emergency-response framework. Sources are authoritative (CDC, FEMA, EPA, IAEA, ICRP, AFRRI, HHS REMM, NYC DOHMH). Deep-science and occupational-compliance material (UNSCEAR/BEIR, 10 CFR, NRC dockets) was intentionally excluded to keep retrieval precision high and token cost low.

## Contents

| Folder / file | Purpose |
|---|---|
| `docs/` | Source documents (PDF from local corpora; Markdown from web) |
| `text/` | Plain-text extraction of every doc (OCR fallback where needed) |
| `corpus.jsonl` | RAG-ready: one JSON record per doc `{id, title, text, metadata}` |
| `manifest.csv` | Human-readable index + validation results |
| `manifest.json` | Same, machine-readable |
| `_raw_web/` | Original fetched web pages (Markdown) before processing |

## Provenance

- 12 documents copied from the local RAD-AI corpus (`RAD_AI_Local`), from the CDC/FEMA/EPA/REMM, IAEA, ICRP, and state-responder folders.
- 3 documents fetched fresh from the internet (CDC Radiation Emergencies site).

## Validation

Each document was checked for: valid file header, extractable text, and text yield (words/page). One image-only PDF (REMM triage tag) was recovered via OCR. SHA-256 checksums are recorded in the manifest for integrity. Result: **15/15 PASS**.

## Notes / gaps

- Full NCRP reports are paywalled and are not included.
- FEMA/REMM binary PDFs could not be pulled over the web fetcher; the equivalent documents were sourced from the local corpus instead.
