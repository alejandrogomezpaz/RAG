"""Build benchmark_golden_pairs_1.jsonl from corpus_1 (RAD-AI RAG).

Same design + schema as benchmark_golden_pairs_0, regenerated against corpus_1 (41 chunks).
Queries paraphrase the source (retrieval, not string-match). expected_answer_keys are lowercase
substrings that appear verbatim in the union of the golden chunk texts (grounding / hallucination check).
Refusal pairs have empty golden_chunk_ids + should_refuse=true; several are NEAR-MISS refusals whose
topic is adjacent to in-corpus content but whose specific fact is absent (e.g. KI mg dose, Cs-137
half-life) — these exercise the similarity-threshold trigger hardest.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
CORPUS = HERE / "corpus_1.jsonl"
if not CORPUS.exists():
    CORPUS = Path("/sessions/serene-quirky-ride/mnt/RAG/corpus_v1/corpus_1.jsonl")
OUT = HERE / "benchmark_golden_pairs_1.jsonl"

chunks = {r["chunk_id"]: r for r in (json.loads(l) for l in CORPUS.read_text().splitlines() if l.strip())
          if r["record_type"] == "chunk"}

# (pair_id, query, [golden_ids], should_refuse, query_type, origin, [keys], note)
P = [
 # ---- ASN / DOE / IAEA (carried & refreshed from golden_pairs_0) ----
 ("p01","We're on scene and can't yet rule out a chemical agent — what protective gear go on first?",
   ["asn2023_sheet06"],False,"procedural","paraphrase",["cbrn mask","filter cartridge","permeable to air"],""),
 ("p02","Once responders confirm there's no chemical component and it's purely radiological, what lighter gear can they change into?",
   ["asn2023_sheet06"],False,"procedural","paraphrase",["non-woven coverall","ffp3","overboots","gloves"],""),
 ("p03","In the French framework, which units make up the medical team sent to a radiological event?",
   ["asn2023_sheet02"],False,"lookup","paraphrase",["smur","rrhu","radiation protection expert"],""),
 ("p04","After a mass-casualty radiological event, how are affected people categorized and where are the uninjured taken?",
   ["asn2023_sheet04"],False,"procedural","paraphrase",["absolute urgencies","relative urgencies","rcup"],""),
 ("p05","Define LD50/30 for acute whole-body radiation exposure.",
   ["doe_au22_ars"],False,"lookup","paraphrase",["ld50/30","50%","30 days"],"term of art is the lookup target"),
 ("p06","At roughly what acute dose does transient skin reddening appear, and how soon?",
   ["doe_au22_ars"],False,"numeric","paraphrase",["200 rem","2-24 hours","erythema"],""),
 ("p07","In the DOE brief, which federal agencies are listed as holding regulatory authority over US radiation exposure standards?",
   ["doe_au22_regs"],False,"lookup","paraphrase",["regulatory authority","dod","dot"],"DOD/DOT uniquely disambiguate this chunk's agency list"),
 ("p08","On average, how much natural background radiation does a US resident get per year, and what contributes most?",
   ["doe_au22_background"],False,"numeric","paraphrase",["310 mrem","3.1 msv","radon","73%"],""),
 ("p09","I'm near suspected airborne radioactive dust with no respirator — what precautions should I take?",
   ["iaea_pda_ti2"],False,"procedural","paraphrase",["handkerchief","do not smoke, eat or drink","wash hands"],""),

 # ---- OSHA response page ----
 ("p10","Besides ionizing radiation itself, what other hazards should responders at a radiation emergency expect?",
   ["osha_rep_hazards"],False,"lookup","paraphrase",["confined spaces","hazardous energy","noise"],""),
 ("p11","How does distance from a radiation source affect exposure, and what principle governs minimizing dose?",
   ["osha_rep_alara"],False,"lookup","paraphrase",["as low as reasonably achievable","inversely proportional to the square"],""),
 ("p12","What is the standard quarterly whole-body dose limit, and the limit for hands and forearms?",
   ["osha_rep_doselimits_quarterly"],False,"numeric","paraphrase",["1 1/4 rem","18 3/4 rem"],""),
 ("p13","What radiation dose rate helps mark the boundary of an area of concern, and what dosimeter type is required?",
   ["osha_rep_monitoring"],False,"numeric","paraphrase",["10 milliroentgens","alarming electronic dosimeters"],""),
 ("p14","Will wearing PPE protect a responder from direct external gamma radiation?",
   ["osha_rep_ppe"],False,"lookup","paraphrase",["will not protect","internal exposures"],""),
 ("p15","Crew are exiting the contaminated zone — what are the essential steps to get radioactive material off them?",
   ["osha_rep_decon"],False,"procedural","paraphrase",["outer clothing","shower","clean clothes"],""),
 ("p16","A responder vomited for a day, felt fine for a while, and now has infections and bleeding — which ARS phases are these?",
   ["osha_rep_ars_phases"],False,"lookup","paraphrase",["prodromal","latent","overt illness"],""),
 ("p17","What is the lowest absorbed dose at which mild acute radiation symptoms may appear?",
   ["osha_rep_ars_phases"],False,"numeric","paraphrase",["30 rad","0.3 gy"],""),
 ("p18","Name the four ARS subsyndromes and a hallmark sign of the nerve/blood-vessel one.",
   ["osha_rep_ars_subsyndromes"],False,"lookup","paraphrase",["hematopoietic","cutaneous","gastrointestinal","neurovascular","cerebral edema"],"cerebral edema distinguishes this chunk from the RC chunk"),
 ("p19","At a whole-body dose of 6-8 Gy, how soon does vomiting start and what is the latent period?",
   ["osha_rep_wholebody_table"],False,"numeric","paraphrase",["10-60 min","latent period under 7 days"],""),
 ("p20","Which agent is proven effective for internal contamination with cesium-137?",
   ["osha_rep_countermeasures"],False,"lookup","paraphrase",["prussian blue"],""),
 ("p21","A responder is seriously injured and also contaminated — do we decontaminate first or treat the injury first?",
   ["osha_rep_treatment_injured"],False,"procedural","paraphrase",["prioritized over decontamination","blanket"],""),
 ("p22","How much radiation per month does NCRP recommend as the ceiling for a pregnant responder's unborn child?",
   ["osha_rep_pregnant"],False,"numeric","paraphrase",["50 millirem","0.5 msv","gestation"],""),
 ("p23","How often must medical exams be made available to HAZWOPER-covered emergency response workers?",
   ["osha_rep_medsurveillance"],False,"lookup","paraphrase",["once every 12 months","pre-placement"],""),
 ("p24","Within what timeframes must an employer report a work-related fatality versus an inpatient hospitalization?",
   ["osha_rep_recordkeeping"],False,"numeric","paraphrase",["8 hours","24 hours"],""),
 ("p25","In the first hours after a radiological incident, does OSHA usually write up violations or act in a supporting role?",
   ["osha_rep_enforcement_posture"],False,"lookup","paraphrase",["technical assistance and support mode","national response framework"],""),
 ("p26","Does OSHA's guidance set a single maximum turnback dose for responders?",
   ["osha_rep_turnback_decision"],False,"lookup","paraphrase",["does not provide a maximum exposure dose","decision points"],""),
 ("p27","Which ICRP publication underlies OSHA's 1971 standards, and when is following 10 CFR Part 20 treated as a de minimis condition?",
   ["osha_rep_regulatory_basis"],False,"lookup","paraphrase",["publication no. 2","de minimis"],""),

 # ---- EPA PAG / REMM ----
 ("p28","Are PAGs strict legal limits or something else?",
   ["pag_general_concepts"],False,"lookup","paraphrase",["not legally binding","strict numeric criteria"],""),
 ("p29","At what projected dose should evacuation or sheltering of the public be initiated in the early phase?",
   ["pag_early_phase"],False,"numeric","paraphrase",["1 rem","10 msv"],""),
 ("p30","How much dose is allowed for a worker safeguarding vital infrastructure like a power plant?",
   ["pag_worker_guidelines"],False,"numeric","paraphrase",["10 rem","100 msv"],""),
 ("p31","What projected first-year dose triggers relocation of the public in the intermediate phase?",
   ["pag_intermediate_relocation"],False,"numeric","paraphrase",["2 rem","20 msv","first year"],""),
 ("p32","Which federal regulation governs DOE's radiation protection program for its workers?",
   ["pag_worker_regs"],False,"lookup","paraphrase",["10 cfr 835"],"was a refusal in v0; now in-corpus"),
 ("p33","What is the difference between primary and secondary protective actions?",
   ["remm_protective_actions_overview"],False,"lookup","paraphrase",["sheltering-in-place","relocation","access control"],""),
 ("p34","What marks the start of the intermediate phase of a radiological incident?",
   ["remm_incident_phases"],False,"lookup","paraphrase",["brought under control","deposited"],""),
 ("p35","What dose rate defines the dangerous-radiation zone, and at what level should responders turn back entirely?",
   ["remm_responder_reference_values"],False,"numeric","paraphrase",["10 r/h","200 r/h"],""),
 ("p36","How is a patient's ARS Response Category determined from the four subsyndromes?",
   ["remm_ars_response_category"],False,"lookup","paraphrase",["highest degree of severity","rc4"],""),
 ("p37","Which radioactive metals is DTPA approved to chelate, and which should it not be used for?",
   ["remm_dtpa_indications"],False,"lookup","paraphrase",["plutonium","americium","curium","uranium"],""),
 ("p38","What is the intravenous DTPA dose for a child under 12?",
   ["remm_dtpa_dosing"],False,"numeric","paraphrase",["14 mg","per kg","1 g"],""),
 ("p39","What is the PAG Manual, and does it change environmental standards?",
   ["epa_pag_scope"],False,"lookup","paraphrase",["planning guide","does not change"],""),
 ("p40","What did the 2017 PAG Manual add compared with the 1992 version?",
   ["epa_pag_changes_2017"],False,"lookup","paraphrase",["fukushima","drinking water","reentry"],""),
 ("p41","During which phase does the drinking water PAG apply, and what is its purpose?",
   ["epa_pag_drinking_water"],False,"lookup","paraphrase",["intermediate phase","alternative drinking water"],""),
 ("p42","What are the main precautions and side effects when giving DTPA?",
   ["remm_dtpa_precautions"],False,"lookup","paraphrase",["diminished renal function","hemochromatosis","zinc"],""),

 # ---- designed MULTI-CHUNK overlaps ----
 ("p43","During a catastrophic incident, how much radiation exposure is permitted for a life-saving mission?",
   ["osha_rep_doselimits_earlyphase","pag_worker_guidelines","doe_au22_fig5"],False,"multi_chunk","paraphrase",
   ["25 rem","save a life"],"25 rem lifesaving guideline appears independently in all three chunks; 'save a life' is unique to Fig 5"),
 ("p44","At what projected dose should the public be relocated, per both EPA PAG and the DOE emergency guidelines?",
   ["pag_intermediate_relocation","doe_au22_fig5"],False,"multi_chunk","paraphrase",
   ["20 msv","relocation"],"relocation at 2 rem/20 mSv stated in both PAG (>=2 rem) and DOE Fig 5 (2 rem/y)"),
 ("p45","Under DOE and NRC rules, what yearly dose is allowed for the general public compared with occupational workers?",
   ["doe_au22_fig5"],False,"numeric","paraphrase",["100 mrem/y","5 rem/y"],""),
 ("p46","For radioactive iodine exposure, what drug is used and at what projected child thyroid dose is it advised?",
   ["osha_rep_countermeasures","pag_early_phase"],False,"multi_chunk","paraphrase",
   ["potassium iodide","iodine-131","5 rem"],"KI covered by OSHA countermeasures + EPA early-phase PAG"),

 # ---- REFUSALS (verified absent / near-miss; KI & 10 CFR 835 are NO LONGER refusals) ----
 ("r01","What is the half-life of cesium-137?",[],True,"refusal","near_miss",[],
   "Cs-137 named for Prussian blue but its half-life is absent from the corpus"),
 ("r02","How many half-value layers of lead are needed to cut a gamma dose rate in half?",[],True,"refusal","absent_topic",[],
   "no half-value-layer / shielding-thickness data in corpus"),
 ("r03","What is the half-life of iodine-131?",[],True,"refusal","near_miss",[],
   "I-131 described as 'short-lived' but no numeric half-life in corpus"),
 ("r04","What milligram dose of potassium iodide should a 5-year-old child take?",[],True,"refusal","near_miss",[],
   "KI indications present but no KI mg dosing (DTPA has mg dosing — must not be borrowed)"),
 ("r05","How do I calibrate a Geiger-Müller survey meter before a shift?",[],True,"refusal","absent_topic",[],
   "no instrument calibration content in corpus"),
 ("r06","What is the half-life of plutonium-239?",[],True,"refusal","near_miss",[],
   "plutonium named as a DTPA chelation target but no half-life in corpus"),
]

records = []
records.append({"record_type":"meta","name":"benchmark_golden_pairs_1","version":1,"created":"2026-07-10",
  "derived_from":"corpus_1.jsonl (41 chunks)","supersedes":"benchmark_golden_pairs_0",
  "id_convention":"corpus_1 chunk_ids",
  "counts":{"answerable":sum(1 for p in P if not p[3]),"refusal":sum(1 for p in P if p[3]),"chunks_referenced":None},
  "notes":("Same schema/design as benchmark_golden_pairs_0, regenerated for corpus_1. Queries paraphrase "
           "the source. expected_answer_keys are verbatim lowercase substrings of the golden chunk union. "
           "KI and 10 CFR 835 are now ANSWERABLE (were refusals r03/r05 in v0); refusal set refreshed with "
           "half-life / calibration / KI-mg-dose near-misses that are verified absent.")})

# chunk manifest (mirror v0: list chunks used, with source/section)
used = sorted({c for p in P for c in p[2]})
for cid in used:
    ch = chunks[cid]
    records.append({"record_type":"chunk","chunk_id":cid,"source":ch["source"],"section":ch["section"]})

for pid,q,g,refuse,qt,origin,keys,note in P:
    rec={"record_type":"golden_pair","pair_id":pid,"query":q,"golden_chunk_ids":g,
         "should_refuse":refuse,"query_type":qt,"origin":origin,"expected_answer_keys":keys}
    if note: rec["notes"]=note
    records.append(rec)

records[0]["counts"]["chunks_referenced"]=len(used)
with OUT.open("w") as f:
    for r in records:
        f.write(json.dumps(r)+"\n")
print(f"wrote {OUT.name}: {sum(1 for p in P if not p[3])} answerable + {sum(1 for p in P if p[3])} refusal, "
      f"{len(used)}/{len(chunks)} chunks referenced")
