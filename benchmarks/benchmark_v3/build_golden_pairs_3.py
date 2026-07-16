"""Build benchmark_golden_pairs_3.jsonl from corpus_3 (RAD-AI RAG, corpus_v3).

Same design + schema as benchmark_golden_pairs_1, regenerated against corpus_3 (the chunked
corpus_v3 PDFs). Queries paraphrase the source (retrieval, not string-match). expected_answer_keys
are lowercase substrings that appear verbatim in the union of the golden chunk texts
(grounding / hallucination check). Refusal pairs have empty golden_chunk_ids + should_refuse=true;
several are NEAR-MISS refusals whose topic is adjacent to in-corpus content but whose specific fact
is verified absent (e.g. isotope half-lives, detector mAh rating) — these exercise the
similarity-threshold trigger hardest.

Two topics that were REFUSALS in golden_pairs_1 are now ANSWERABLE in corpus_3 because the
corpus_v3 PDFs include them: detector calibration (GQ GMC manual) and KI milligram dosing by age
(EPA PAG Table 2-2). The refusal set is refreshed accordingly.

Run:
    python build_golden_pairs_3.py     # verifies keys, then writes the jsonl
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus_3.jsonl"
OUT = HERE / "benchmark_golden_pairs_3.jsonl"

chunks = {r["chunk_id"]: r for r in (json.loads(l) for l in CORPUS.read_text(encoding="utf-8").splitlines() if l.strip())
          if r.get("record_type") == "chunk"}
# whole-corpus lowercase text, for verifying that refusal facts are genuinely absent
CORPUS_TEXT = "\n".join(c["text"] for c in chunks.values()).lower()

# (pair_id, query, [golden_ids], should_refuse, query_type, origin, [keys], note)
P = [
 # ---------- EPA PAG 2017: KI, protective-action thresholds, decorporation ----------
 ("p01", "For radioactive-iodine exposure, at what projected child thyroid dose does the manual now recommend giving KI?",
   ["epa_pag_2017_0019"], False, "numeric", "paraphrase",
   ["5 rem", "50 millisieverts", "projected child thyroid dose"], ""),
 ("p02", "What KI tablet strengths are used when dosing the different age and risk groups?",
   ["epa_pag_2017_0062"], False, "lookup", "paraphrase",
   ["130 mg", "65 mg", "pregnant or lactating women"], "KI mg dosing was a REFUSAL in golden_pairs_1; corpus_v3 EPA PAG Table 2-2 makes it answerable"),
 ("p03", "Which groups does FDA prioritize for KI, and what thyroid risk do the youngest face?",
   ["epa_pag_2017_0060"], False, "lookup", "paraphrase",
   ["neonates", "hypothyroidism", "pregnant or lactating women"], ""),
 ("p04", "At what projected first-year dose should the public be relocated during the intermediate phase?",
   ["epa_pag_2017_0030", "epa_pag_2017_0114"], False, "multi_chunk", "paraphrase",
   ["2 rem", "20 msv", "first year"], "relocation PAG stated independently in two EPA chunks"),
 ("p05", "After the first year, what relocation PAG applies for each subsequent year?",
   ["epa_pag_2017_0030"], False, "numeric", "paraphrase",
   ["0.5 rem", "5 msv", "subsequent year"], ""),
 ("p06", "What projected dose range triggers evacuation or sheltering of the public in the early phase?",
   ["epa_pag_2017_0047", "epa_pag_2017_0022"], False, "multi_chunk", "paraphrase",
   ["1 to 5 rem", "10 to 50 msv"], "early-phase PAG appears in the narrative and in Table 1-1"),
 ("p07", "During a catastrophic incident, how much dose is permitted for a lifesaving mission?",
   ["epa_pag_2017_0101", "epa_pag_2017_0094"], False, "multi_chunk", "paraphrase",
   ["25 rem", "250 msv", "lifesaving"], "25 rem lifesaving guideline appears in the dose table and the narrative"),
 ("p08", "What total-dose guideline covers an emergency worker over an entire response, absent exceptional circumstances?",
   ["epa_pag_2017_0022"], False, "numeric", "paraphrase",
   ["5 rem", "50 msv", "year"], ""),
 ("p09", "What is the PAG for food interdiction after a radiological incident?",
   ["epa_pag_2017_0022"], False, "numeric", "paraphrase",
   ["food interdiction", "0.5 rem"], ""),
 ("p10", "Which decorporation drugs did the 2017 update add references to?",
   ["epa_pag_2017_0020"], False, "lookup", "paraphrase",
   ["calcium-dtpa", "zinc-dtpa", "prussian blue"], ""),
 ("p11", "Which outdated intermediate-phase PAG did the 2017 manual remove to avoid confusion with cleanup?",
   ["epa_pag_2017_0020"], False, "lookup", "paraphrase",
   ["5 rem", "50 years", "relocation"], ""),
 ("p12", "What principle governs keeping radiation doses as low as feasible after an incident?",
   ["doe_std_1098_2017_0009", "epa_pag_2017_0094"], False, "multi_chunk", "paraphrase",
   ["as low as reasonably achievable", "alara"], "ALARA phrasing appears in both DOE and EPA text"),
 ("p13", "Which protective action most effectively cuts public exposure to deposited material, and why is it used sparingly?",
   ["epa_pag_2017_0114"], False, "lookup", "paraphrase",
   ["relocation", "highly disruptive"], ""),

 # ---------- IAEA EPR-Medical 2005: decorporation ----------
 ("p14", "Which agent treats internal cesium contamination, and what is its chemical name?",
   ["iaea_epr_medical_2005_0112", "iaea_epr_medical_2005_0113"], False, "lookup", "paraphrase",
   ["prussian blue", "ferric hexacyanoferrate"], ""),
 ("p15", "What is the adult Prussian blue regimen for internal contamination?",
   ["iaea_epr_medical_2005_0112"], False, "numeric", "paraphrase",
   ["1 g", "3 times daily", "prussian blue"], ""),
 ("p16", "What is the standard Ca-DTPA dose, and roughly how much does Prussian blue reduce the dose?",
   ["iaea_epr_medical_2005_0113"], False, "numeric", "paraphrase",
   ["ca-dtpa", "1 g", "factor of about 2-3"], ""),

 # ---------- IAEA EPR-NPP OILs 2017 ----------
 ("p17", "What is the default OIL1 gamma dose-rate value for ground monitoring, and how does it change over the first ten days?",
   ["iaea_epr_npp_oils_2017_0040", "iaea_epr_npp_oils_2017_0022"], False, "multi_chunk", "paraphrase",
   ["oil1", "1000", "first 10 days after reactor shutdown"], "OIL1 default listed in Table 1 and in the OIL1 detail page"),
 ("p18", "What are the default OIL7 activity concentrations for iodine-131 and caesium-137 in food?",
   ["iaea_epr_npp_oils_2017_0022"], False, "numeric", "paraphrase",
   ["1000 bq/kg", "i-131", "200 bq/kg", "cs-137"], ""),
 ("p19", "Which gamma OIL applies later than ten days after shutdown, and what is OIL3 relative to background?",
   ["iaea_epr_npp_oils_2017_0040"], False, "lookup", "paraphrase",
   ["later than 10 days", "above background"], ""),

 # ---------- IAEA EPR Manual for First Responders ----------
 ("p20", "At what ambient dose rate is the inner-cordon boundary set, and above what rate should only life-saving actions occur?",
   ["iaea_epr_first_responders_0065"], False, "numeric", "paraphrase",
   ["100 msv/h", "life saving", "inner cordoned area", "30 min"], ""),
 ("p21", "What measurement range should responders confirm their gamma dose-rate meter can cover?",
   ["iaea_epr_first_responders_0064"], False, "numeric", "paraphrase",
   ["gamma dose rate", "1000 msv/h", "1 sv/h"], ""),
 ("p22", "What are the most commonly considered urgent protective actions in a radiological emergency?",
   ["iaea_epr_first_responders_0132"], False, "lookup", "paraphrase",
   ["evacuation", "sheltering", "respiratory protection", "iodine prophylaxis"], ""),
 ("p23", "What field decontamination is applied to responders leaving the inner cordoned area?",
   ["iaea_epr_first_responders_0087"], False, "procedural", "paraphrase",
   ["hose down", "inner cordoned area"], ""),
 ("p24", "Can the standard gamma dose-rate instruments carried by emergency services detect every radioactive hazard?",
   ["iaea_epr_first_responders_0017"], False, "lookup", "paraphrase",
   ["cannot detect", "radiological assessor"], ""),

 # ---------- IAEA GSR Part 3: dose limits ----------
 ("p25", "What is the occupational effective-dose limit, and how is it averaged?",
   ["iaea_gsr_part_3_0279"], False, "numeric", "paraphrase",
   ["20 msv per year", "averaged over five consecutive years", "50 msv in any single year"], ""),
 ("p26", "What is the occupational equivalent-dose limit for the lens of the eye, and what was it previously?",
   ["iaea_gsr_part_3_0022"], False, "numeric", "paraphrase",
   ["lens of the eye", "20 msv in a year", "150 msv per year"], ""),
 ("p27", "What reference-level band applies to residual dose after a nuclear or radiological emergency?",
   ["iaea_gsr_part_3_0070"], False, "lookup", "paraphrase",
   ["reference levels", "100 msv"], ""),

 # ---------- IAEA RS-G-1.1: area classification ----------
 ("p28", "What two types of area can be designated in a radiation protection programme?",
   ["iaea_rs_g_1_1_0079"], False, "lookup", "paraphrase",
   ["controlled areas", "supervised areas"], ""),

 # ---------- NRC RG 8.34: dose quantities ----------
 ("p29", "How is total effective dose equivalent defined in the revised guidance?",
   ["nrc_rg_8_34_0008"], False, "lookup", "paraphrase",
   ["total effective dose equivalent", "committed effective dose equivalent"], ""),
 ("p30", "Which dose-equivalent quantities must an airborne-material dose assessment include?",
   ["nrc_rg_8_34_0003"], False, "lookup", "paraphrase",
   ["deep-dose equivalent", "lens dose equivalent", "shallow-dose equivalent"], ""),

 # ---------- DOE-STD-1098-2017: radiological control ----------
 ("p31", "Above what general-area dose rate is hot-spot labeling not required?",
   ["doe_std_1098_2017_0075"], False, "numeric", "paraphrase",
   ["hot spot", "1 rem/hr"], ""),
 ("p32", "What extra monitoring is required for entry into a high or very high radiation area?",
   ["doe_std_1098_2017_0192"], False, "lookup", "paraphrase",
   ["supplemental dosimeter", "high radiation"], ""),

 # ---------- Radiacode detector documentation ----------
 ("p33", "In what forms and units can the Radiacode present its measurements?",
   ["radiacode_docs_0003"], False, "lookup", "paraphrase",
   ["energy spectrum", "counts per second", "accumulated dose"], ""),
 ("p34", "What kind of detector is the Radiacode, and what sensor technology does it use?",
   ["radiacode_docs_0002"], False, "lookup", "paraphrase",
   ["spectrometer", "scintillator", "solid-state photomultiplier"], ""),
 ("p35", "On the Radiacode energy-spectrum histogram, what do the dots, dashes and arrows mark?",
   ["radiacode_docs_0035"], False, "numeric", "paraphrase",
   ["100kev", "500kev", "1000kev"], ""),
 ("p36", "What do the Radiacode's Spectrum and Dose menu screens display?",
   ["radiacode_docs_0007"], False, "lookup", "paraphrase",
   ["energy spectrum", "accumulated dose"], ""),

 # ---------- GQ GMC-320 / GMC-500 Geiger counters ----------
 ("p37", "How many calibration points does the GMC-320 support, and what values does each need?",
   ["gq_gmc_320_0015"], False, "procedural", "paraphrase",
   ["three points", "cpm value", "calibration point"], "instrument calibration was a REFUSAL in golden_pairs_1; the corpus_v3 GQ manual makes it answerable"),
 ("p38", "Which reading units can the GMC-320 toggle between on screen?",
   ["gq_gmc_320_0011"], False, "lookup", "paraphrase",
   ["cpm", "mr/h"], ""),
 ("p39", "How does the GMC-500+ extend its detection range compared with the base model?",
   ["gq_gmc_500_0004"], False, "lookup", "paraphrase",
   ["second high dose sensor tube", "ten times higher"], ""),
 ("p40", "What internal battery does the GMC-500 use, and how is it charged?",
   ["gq_gmc_500_0004"], False, "lookup", "paraphrase",
   ["li-ion", "usb port"], ""),

 # ---------- IAEA GSG-2, SRS-21, EPR-NPP-PPA, GSR Part 7 ----------
 ("p41", "What is the purpose of the generic criteria set out in GSG-2?",
   ["iaea_gsg_2_0026"], False, "lookup", "paraphrase",
   ["generic criteria", "operational criteria", "protective actions"], ""),
 ("p42", "What health consequences did GSG-2's generic criteria address?",
   ["iaea_gsg_2_0030"], False, "lookup", "paraphrase",
   ["external exposure", "internal exposure", "deterministic"], ""),
 ("p43", "In optimization, when is a protection option judged reasonable relative to the value of the man-sievert?",
   ["iaea_srs_21_0107"], False, "lookup", "paraphrase",
   ["man-sievert", "cost effectiveness"], ""),
 ("p44", "On what basis must urgent protective actions at a reactor be initiated to be most effective?",
   ["iaea_epr_npp_ppa_0046"], False, "lookup", "paraphrase",
   ["urgent protective actions", "eals"], ""),
 ("p45", "Under GSR Part 7, which emergency preparedness category covers transport of radioactive material?",
   ["iaea_gsr_part_7_0034"], False, "lookup", "paraphrase",
   ["emergency preparedness category iv", "transport"], ""),
 ("p46", "How does the GMC-500 record radiation data over time?",
   ["gq_gmc_500_0004"], False, "lookup", "paraphrase",
   ["automatic data recording", "internal memory"], ""),

 # ---------- REFUSALS (verified absent / near-miss) ----------
 ("r01", "What is the half-life of cesium-137?", [], True, "refusal", "near_miss", [],
   "Cs-137 is named (OIL7 food criterion, FRC ingestion guidance) but its numeric half-life is absent"),
 ("r02", "What is the half-life of iodine-131?", [], True, "refusal", "near_miss", [],
   "I-131 is named (OIL7, KI context) but no numeric half-life appears in the corpus"),
 ("r03", "What is the half-life of plutonium-239?", [], True, "refusal", "near_miss", [],
   "plutonium appears as a decorporation/DTPA target; 'plutonium-239' and its half-life are absent"),
 ("r04", "What is the battery capacity in mAh of the Radiacode detector?", [], True, "refusal", "near_miss", [],
   "battery charging is discussed in the Radiacode manual, but no mAh rating is given"),
 ("r05", "How much does a Radiacode radiation detector cost to buy?", [], True, "refusal", "absent_topic", [],
   "no purchase price / retail cost for any detector appears in the corpus"),
 ("r06", "What is the melting point of uranium metal?", [], True, "refusal", "absent_topic", [],
   "elemental physical-chemistry data such as melting points are outside the corpus"),
]


def verify():
    """Fail loudly if any golden id is missing, any key is not a verbatim substring of its
    golden-chunk union, or any refusal's distinctive fact is actually present."""
    problems = []
    for pid, q, gids, refuse, qt, origin, keys, note in P:
        for cid in gids:
            if cid not in chunks:
                problems.append(f"{pid}: missing chunk_id {cid}")
        if not refuse:
            union = " ".join(chunks[c]["text"] for c in gids if c in chunks).lower()
            for k in keys:
                if k.lower() not in union:
                    problems.append(f"{pid}: answer key not in golden union -> {k!r}")
        else:
            if gids or keys:
                problems.append(f"{pid}: refusal must have empty golden_chunk_ids and keys")
    # refusal fact-absence spot checks (the specific numeric facts, not the topic word)
    for probe in ["30.1 years", "8.02 days", "8 days", "24,100 years", "melting point"]:
        if probe in CORPUS_TEXT:
            problems.append(f"refusal-absence probe FOUND in corpus: {probe!r}")
    return problems


def main():
    problems = verify()
    if problems:
        print("VERIFICATION FAILED:")
        for p in problems:
            print("  -", p)
        sys.exit(1)

    ans = sum(1 for p in P if not p[3])
    ref = sum(1 for p in P if p[3])
    records = [{
        "record_type": "meta", "name": "benchmark_golden_pairs_3", "version": 3, "created": "2026-07-15",
        "derived_from": f"corpus_3.jsonl ({len(chunks)} chunks)", "supersedes": "benchmark_golden_pairs_1",
        "id_convention": "corpus_3 chunk_ids",
        "counts": {"answerable": ans, "refusal": ref, "chunks_referenced": None},
        "notes": ("Same schema/design as benchmark_golden_pairs_1, regenerated for corpus_3 (the chunked "
                  "corpus_v3 PDFs). Queries paraphrase the source. expected_answer_keys are verbatim "
                  "lowercase substrings of the golden chunk union. Detector calibration and KI mg dosing, "
                  "which were refusals in v1, are now ANSWERABLE (corpus_v3 includes the GQ manual and EPA "
                  "PAG Table 2-2); refusal set refreshed with isotope-half-life / detector-spec near-misses "
                  "that are verified absent."),
    }]
    used = sorted({c for p in P for c in p[2]})
    for cid in used:
        ch = chunks[cid]
        records.append({"record_type": "chunk", "chunk_id": cid, "source": ch["source"], "section": ch["section"]})
    for pid, q, g, refuse, qt, origin, keys, note in P:
        rec = {"record_type": "golden_pair", "pair_id": pid, "query": q, "golden_chunk_ids": g,
               "should_refuse": refuse, "query_type": qt, "origin": origin, "expected_answer_keys": keys}
        if note:
            rec["notes"] = note
        records.append(rec)
    records[0]["counts"]["chunks_referenced"] = len(used)

    with OUT.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.name}: {ans} answerable + {ref} refusal, {len(used)}/{len(chunks)} chunks referenced")


if __name__ == "__main__":
    main()
