"""Assemble corpus_1.jsonl for RAD-AI RAG.

Sources (all official / authoritative, retrieved 2026-07-10):
- OSHA — Radiation Emergency Preparedness and Response (full response page)
- EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017), via HHS REMM
- HHS REMM — protective actions, incident phases, responder reference values, ARS, DTPA
- Existing validated mini-corpus excerpts (ASN, DOE, IAEA PDA) carried forward verbatim

Chunk texts below are lightly cleaned (footnote markers / hyperlinks stripped,
whitespace normalized) but otherwise faithful to the source wording, so every
factual key remains verbatim-groundable.
"""
import json, re, sys
from pathlib import Path

OUT = Path(__file__).parent / "corpus_1.jsonl"
DOCS = Path("/sessions/serene-quirky-ride/mnt/.projects/019f4436-5d3d-72d1-b9a2-2e0ec05f4db1/docs")
# fallback for file-tool path
if not DOCS.exists():
    DOCS = Path("/Users/alejandrogomez-paz/Library/Application Support/Claude/local-agent-mode-sessions/4822f1e3-e5e4-4a11-996a-c39843000ab4/3127b091-3154-441b-a88c-1454d41ca0e6/.project-cache/019f4436-5d3d-72d1-b9a2-2e0ec05f4db1/docs")

OSHA_URL = "https://www.osha.gov/emergency-preparedness/radiation/response"
PAG_URL  = "https://remm.hhs.gov/pag.htm"
REMM_ARS = "https://remm.hhs.gov/ars.htm"
REMM_DTPA = "https://remm.hhs.gov/dtpa.htm"

# ---------------------------------------------------------------- new chunks
new = []
def add(cid, source, section, url, text):
    new.append({
        "record_type": "chunk", "chunk_id": cid, "source": source,
        "section": section, "url": url, "retrieved": "2026-07-10",
        "text": re.sub(r"\s+", " ", text).strip(),
    })

# ---- OSHA: Radiation Emergency Preparedness and Response ----
add("osha_rep_hazards", "OSHA — Radiation Emergency Preparedness and Response",
    "Health and Safety Hazards during Radiation Emergencies", OSHA_URL, """
During and after radiation emergencies, including during response operations and evacuation or
sheltering-in-place periods, workers and employers should be aware of the hazards. Ionizing radiation
may be the primary hazard; high doses, even for short durations, can cause short- and long-term health
impacts. Other hazards to which workers may be exposed include: hazardous substances, including
releases of chemical and biological agents resulting from the initial explosion, structural
damage/collapse, and fires; entry into confined spaces; heavy equipment and vehicular traffic; hazardous
energy (electrical, mechanical, hydraulic, pneumatic, chemical, or thermal); slips, trips, and falls on
unstable or collapsed surfaces and falls from heights; fires and explosions resulting from a nuclear
blast or secondary ignition of fuel sources; hazards associated with response tasks such as
welding/cutting, trenching, and excavation; and noise exposure. Employers are always required to protect
workers from these and other recognized health and safety hazards.""")

add("osha_rep_alara", "OSHA — Radiation Emergency Preparedness and Response",
    "Basic Protective Actions for Radiation (ALARA)", OSHA_URL, """
Radiation doses should be kept to a level that is As Low As Reasonably Achievable (ALARA). Minimizing
doses consistent with the ALARA concept can be done by: minimizing time spent in areas where radiation
exposure may occur, planning missions so that first responders enter and leave areas as few times as
possible and spend as little time as possible in them; maximizing distance between a worker and a source
of radiation exposure, since radiation intensity decreases rapidly with distance and intensity is
inversely proportional to the square of the distance from the source; and using proper hazard controls,
including shielding workers from a radiation source and contamination. Shielding may include the use of
personal protective equipment (PPE) — for example, shielding your body by staying on the opposite side
of a cinder block wall from a radiation source.""")

add("osha_rep_doselimits_quarterly", "OSHA — Radiation Emergency Preparedness and Response",
    "Dose Limits — Table G-18 (quarterly occupational limits)", OSHA_URL, """
For workers engaged in response operations covered by OSHA's ionizing radiation standards for general
industry (29 CFR 1910.1096) and construction (29 CFR 1926.53), dose limits to certain parts of the body
from external exposures are described by Table G-18 of the general industry standard: whole body (head
and trunk; active blood-forming organs; lens of eyes; or gonads), 1 1/4 rem per calendar quarter; hands
and forearms, feet and ankles, 18 3/4 rem per calendar quarter; skin of whole body, 7 1/2 rem per
calendar quarter. The Ionizing Radiation standards generally limit whole-body occupational ionizing
radiation dose to 1.25 rem per calendar quarter. Responders generally must not exceed a 5-rem (0.05 Sv)
annual whole-body dose of ionizing radiation.""")

add("osha_rep_doselimits_earlyphase", "OSHA — Radiation Emergency Preparedness and Response",
    "Dose Limits for Emergency Response Situations — early phase of a catastrophic emergency", OSHA_URL, """
The following guidelines apply during the early phase of a catastrophic radiation emergency response,
such as a nuclear detonation, expressed as Total Effective Dose Equivalent (TEDE): 5 rem (0.05 Sv) —
annual limit for all occupational exposures, including for radiation workers; all reasonably achievable
actions must be taken to minimize dose. 10 rem (0.10 Sv) — infrastructure protection and restoration in
lower-hazard areas such as the Light Damage zone and fallout areas around a nuclear detonation site,
excluding the Dangerous Fallout zone; exceeding 5 rem is unavoidable; appropriate respiratory protection
and other personal protection provided and used; monitoring available. 25 rem (0.25 Sv) — life-saving,
medical response, infrastructure restoration, or protection of populations in medium-hazard areas such
as the Moderate Damage zone; same conditions. Greater than 25 rem (>0.25 Sv) — life-saving and critical
infrastructure missions in high-hazard zones including the Dangerous Fallout zone; if lifesaving
responder doses approach or exceed 50 rem (0.5 Sv), responders must be made fully aware of both the acute
and the chronic (cancer) risks. Each responder should make an informed decision as to how much radiation
risk he or she is willing to accept to save lives. These limits are only for the early phase; in later
phases the standard 1.25-rem/quarter occupational dose limit normally applies.""")

add("osha_rep_monitoring", "OSHA — Radiation Emergency Preparedness and Response",
    "Dose Monitoring", OSHA_URL, """
It is important to conduct a hazard assessment for workers conducting emergency response operations and
to monitor workers' radiation doses. Detecting a radiation dose rate of 10 milliroentgens (mR) per hour
(approximately 0.0001 Gy/h) may help employers and workers identify the boundaries of areas with
radiation levels of concern. In areas where there is radiation above background, response workers should
be equipped with appropriate radiation monitoring equipment; if possible, use equipment that provides
unambiguous alarms based on predefined levels (turn-back doses set by an Incident Commander, ideally well
below OSHA dose limits) that indicate when workers should leave an area. Only alarming electronic
dosimeters meet these criteria. Since it is assumed there is no radiation dose threshold below which
there is no associated risk, responders who are reasonably expected to receive more than 25 percent of
the occupational dose limit should be appropriately trained and monitored.""")

add("osha_rep_ppe", "OSHA — Radiation Emergency Preparedness and Response",
    "Personal Protective Equipment", OSHA_URL, """
PPE is equipment worn to minimize exposure to hazards that other workplace controls cannot control.
During a radiation emergency, PPE will not protect workers against most types of direct, external
radiation exposure. However, correctly using proper PPE will help prevent or minimize any internal
exposures by preventing ingestion, inhalation, or skin absorption of radioactive materials. Direct
external exposure can be a persistent hazard during radiation emergencies. Typically, the type of PPE
required and guidelines for its use are based on contamination levels. Depending on the nature of the
response operations, a worker may need different types of PPE to protect against hazards other than
radiation contamination. OSHA requires employers to select and provide appropriate PPE for their workers
and ensure its proper use.""")

add("osha_rep_decon", "OSHA — Radiation Emergency Preparedness and Response",
    "Decontamination", OSHA_URL, """
Getting radioactive material off the body as soon as possible can lower a worker's radiation dose from
external contamination. Removing outer clothing and showering or, at a minimum, washing the face, hands,
and any other exposed skin are essential decontamination steps. Incident commanders may also implement
worker decontamination (or "decon") procedures that include decon lines for responders exiting
contaminated areas. Employers whose workers may be contaminated should establish procedures for
radiological monitoring or surveying workers to identify which, if any, are contaminated, and to what
extent. If workers need to be decontaminated, employers should establish on-scene decontamination
facilities with the ability to: provide an area for workers to remove contaminated clothing; provide
showers for each contaminated worker to shampoo hair, wash skin, and put on clean clothes; and store
contaminated waste (including worker clothing and equipment) at a safe distance from people and
animals.""")

add("osha_rep_ars_phases", "OSHA — Radiation Emergency Preparedness and Response",
    "Medical Management — Acute Radiation Syndrome: four phases", OSHA_URL, """
In the immediate minutes, hours, and days following exposure to radiation, healthcare providers should
monitor victims for signs and symptoms of acute radiation syndrome (ARS). ARS is characterized by four
distinct phases: a prodromal period during which victims may experience loss of appetite, nausea,
vomiting, fatigue, and diarrhea (after extremely high doses, additional symptoms such as fever,
prostration, respiratory distress, and hyper-excitability can occur); in cases where the dose is not
sufficient to cause rapid death, these symptoms usually disappear within 1-2 days. A symptom-free latent
period follows, varying in length depending on the effective radiation dose. Following the latent period,
a period of overt illness manifests as infection, electrolyte imbalance, diarrhea, bleeding,
cardiovascular collapse, and sometimes short periods of unconsciousness. Death or a period of recovery
follows the period of overt illness. While ARS typically would be expected at absorbed doses around 70
rad (0.7 Gy), mild symptoms may be observed with doses as low as 30 rad (0.3 Gy). Doses greater than or
equal to 100 rad (1 Gy) are the doses at which elevated risk of acute death becomes a concern.""")

add("osha_rep_ars_subsyndromes", "OSHA — Radiation Emergency Preparedness and Response",
    "Medical Management — Acute Radiation Syndrome: four subsyndromes", OSHA_URL, """
ARS is also associated with four subsyndromes manifesting over a period of hours to weeks. The
hematopoietic subsyndrome is characterized by deficiencies of white blood cells and platelets, immune
system impairment, infectious complications, bleeding, anemia, and impaired wound healing. The cutaneous
subsyndrome is characterized by progressively worsening skin reactions depending on radiation dose,
including redness, itching, swelling, blistering, radiation burns, ulcers, and hair loss. The
gastrointestinal subsyndrome is characterized by loss of cells lining the gastrointestinal tract that
can lead to vomiting, diarrhea, fluid loss, abdominal pain, bleeding, and infections. The neurovascular
subsyndrome is characterized by vomiting and diarrhea, which can occur within minutes of exposure, along
with confusion, disorientation, cerebral edema (brain swelling), drop in blood pressure, and elevated
body temperature; death may quickly follow.""")

add("osha_rep_wholebody_table", "OSHA — Radiation Emergency Preparedness and Response",
    "Effects of Whole-Body Irradiation (by absorbed dose)", OSHA_URL, """
Effects of whole-body irradiation from external radiation or internal absorption, by whole-body absorbed
dose. 100-200 rad (1-2 Gy): nausea and vomiting in 5-50% (onset 2-6 h, duration under 24 h); no diarrhea;
latent period 28-31 days; illness is mild to moderate leukopenia, fatigue, weakness; mortality without
care 0-5%. 200-600 rad (2-6 Gy): nausea and vomiting 50-100% (onset 1-2 h); diarrhea none to mild; latent
period 7-28 days; moderate to severe leukopenia, purpura, hemorrhage, infections, epilation (hair loss)
after 300 rad (3 Gy); mortality 5-100% without care and 5-50% with care; death in 4-6 weeks. 600-800 rad
(6-8 Gy): nausea and vomiting 75-100% (onset 10-60 min); heavy diarrhea; latent period under 7 days;
severe leukopenia, high fever, diarrhea, hypotension, electrolyte disturbance; mortality 95-100% without
care and 50-100% with care; death in 2-4 weeks. 800-3,000 rad (8-30 Gy): nausea and vomiting 90-100%
(onset under 10 min); heavy diarrhea; no latent period; rapid incapacitation; mortality 100%; death 2
days to 2 weeks. Greater than 3,000 rad (>30 Gy): nausea and vomiting 100% (onset in minutes); patients
die in under 48 hours; seizures, tremor, ataxia, lethargy; mortality 100%; death in 1-2 days.""")

add("osha_rep_countermeasures", "OSHA — Radiation Emergency Preparedness and Response",
    "Medical Management — medical countermeasures", OSHA_URL, """
There are no reliable antidotes once exposure to radiation has occurred or radioactive material has been
inhaled or ingested. However, there are some chemicals that help cleanse the body of specific radioactive
materials or block uptake of radionuclides within the body. Prussian blue has been proven effective for
cesium-137 ingestion. Potassium iodide (KI) tablets are sometimes recommended for exposure to iodine-131
(I-131), a short-lived radioactive element produced by certain types of nuclear reactions. Chelation and
sodium bicarbonate may also be used for certain radionuclides. Healthcare providers will determine how to
treat symptoms and whether or not medical countermeasures (MCM) are appropriate for each patient.
Long-term health effects, if they occur, will likely develop decades after exposure.""")

add("osha_rep_treatment_injured", "OSHA — Radiation Emergency Preparedness and Response",
    "Treatment of Injured/Ill Response Workers", OSHA_URL, """
Emergency response workers who sustain injuries or become ill (e.g., due to radiation exposure) should be
monitored for contamination and decontaminated, if needed, in a safe manner before transportation to
medical facilities. When a worker needs to be transported to a medical facility, the employer should
inform the receiving facility of the worker's known or potential contamination with radioactive material.
Treatment of injured or ill response workers should be prioritized over decontamination of the worker if
decontamination procedures (such as removal of clothing, showering) would aggravate the worker's
condition. Removal of outer clothing and shoes can greatly reduce levels of external contamination.
Workers whose clothing cannot be removed or whose bodies cannot be properly decontaminated can be covered
with a blanket during transport to minimize the spread of radioactive material.""")

add("osha_rep_pregnant", "OSHA — Radiation Emergency Preparedness and Response",
    "Dose limits — pregnant workers and the fetus", OSHA_URL, """
OSHA's dose limits are not different for pregnant workers compared to other workers. However, NCRP, ICRP,
and the Conference of Radiation Control Program Directors (CRCPD) have each recommended lower doses for
the fetus of an occupationally exposed worker: NCRP recommends a limit of 50 millirem (0.5 mSv) per month
during the gestation period (Report No. 116); ICRP recommends a limit for the fetus of an occupationally
exposed individual of 200 mrem (2 mSv) during the gestation period, and a limit for a member of the
general public of 100 mrem (1 mSv) per year (Publication 60); CRCPD suggests keeping the fetal dose below
500 mrem (5 mSv) during the gestation period. The NRC requires licensees to maintain exposure to the
fetus of a declared pregnant worker to 500 mrem (5 mSv) or less during the gestation period. CDC
identifies a practical threshold for birth defects in the human embryo or fetus between 10 and 20 rads
(0.10-0.20 Gy). Employers should consider reassigning declared pregnant workers to duties that minimize
radiation exposure to the worker and fetus.""")

add("osha_rep_medsurveillance", "OSHA — Radiation Emergency Preparedness and Response",
    "Medical Surveillance (HAZWOPER)", OSHA_URL, """
OSHA's Hazardous Waste Operations and Emergency Response (HAZWOPER) standards require that employers make
medical exams available to covered emergency response workers at a reasonable time and place prior to
employment, periodically (at least once every 12 months), and at the termination of employment or
reassignment to a non-covered position. Covered workers include those who are or may be exposed to
hazardous substances or health hazards at or above the permissible exposure limit for 30 days or more a
year; all employees who wear a respirator for 30 days or more a year; all employees who are injured,
become ill, or develop symptoms due to possible over-exposure during an emergency response or hazardous
waste operation; and members of HAZMAT teams. Required provisions under 29 CFR 1910.120(f) include a
pre-placement exam, a periodic exam (annually or at physician's discretion), an emergency/exposure
examination, a termination exam, evaluation of the ability to wear a respirator, and a written medical
opinion from the physician to the employer.""")

add("osha_rep_recordkeeping", "OSHA — Radiation Emergency Preparedness and Response",
    "Recordkeeping", OSHA_URL, """
Under OSHA recordkeeping requirements, all employers must report all work-related fatalities within 8
hours and all work-related inpatient hospitalizations, all amputations, and all losses of an eye within
24 hours. Under the OSHA Recordkeeping requirements (29 CFR 1904), covered employers must prepare and
maintain records of serious occupational injuries and illnesses using the OSHA 300 Log. Employers must
also record any injuries incurred during emergency response operations, as well as the results of on-site
medical treatment or monitoring (e.g., for radiation exposure, heat stress, or other hazards). Accurate,
readily available records enable an incident commander to assign workers to response and recovery
activities based on their level of training and medical clearance.""")

# ---- EPA PAG Manual (2017), via HHS REMM ----
add("pag_general_concepts", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "General concepts about PAGs (page 1)", PAG_URL, """
Protective Action Guides (PAGs) are guides to help officials select protective actions under emergency
conditions during which exposures would occur for relatively short time periods. They are not meant to be
applied as strict numeric criteria, but rather as guidelines to be considered in the context of
incident-specific factors. PAGs do not establish an acceptable level of risk for normal, non-emergency
conditions, nor do they represent the boundary between safe and unsafe conditions. The PAGs are not
legally binding regulations or standards and do not supersede any environmental laws. The PAG guidelines
are only for use during a large-scale emergency, when radiation levels could be high enough to cause
health effects unless public safety measures are taken.""")

add("pag_early_phase", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "Table 2-1 — PAGs and Protective Actions for the Early Phase", PAG_URL, """
PAGs and Protective Actions for the Early Phase of a Radiological Incident. Sheltering-in-place or
evacuation of the public: PAG of 1 to 5 rem (10 mSv to 50 mSv) projected dose over four days; evacuation
(or, for some situations, sheltering-in-place) should be initiated when the projected dose is 1 rem (10
mSv); take whichever action, or combination of actions, that results in the lowest exposure for the
majority of the population. Supplementary administration of prophylactic drugs, potassium iodide (KI):
PAG of 5 rem (50 mSv) projected child thyroid dose from exposure to radioactive iodine; KI is most
effective if taken prior to exposure and may require approval of state medical officials. KI provides
thyroid protection from radioactive iodines only. The one-year-old age group is expected to receive the
largest dose to the thyroid from radioactive iodine, and is the group considered when deciding on the
administration of prophylactic KI.""")

add("pag_worker_guidelines", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "Table 3-1 — EPA emergency worker exposure guidelines", PAG_URL, """
EPA emergency worker exposure guidelines, based on cumulative dose incurred over the duration of an
emergency and assumed to be once-in-a-lifetime doses: 5 rem (50 mSv) for all occupational exposures; 10
rem (100 mSv) for protecting critical infrastructure necessary for public welfare, such as a power plant
(for potential doses above 5 rem, medical monitoring programs should be considered); 25 rem (250 mSv) for
lifesaving or protection of large populations, which provides assurance that exposures will not result in
detrimental deterministic (prompt or acute) health effects but could increase the risk of stochastic
(chronic) effects such as cancer; and greater than 25 rem (250 mSv) for lifesaving or protection of large
populations, where in a very large incident such as an improvised nuclear device (IND) incident
commanders may need to consider raising the property and lifesaving guidelines. NCRP recommends that when
the cumulative absorbed dose to an emergency responder reaches 50 rad (0.5 Gy), a decision be made on
whether to withdraw the responder from the Hot Zone; the 50 rad value is a decision dose, not a dose
limit.""")

add("pag_intermediate_relocation", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "Table 4-1 — Intermediate Phase: relocation and dose reduction", PAG_URL, """
PAGs and Protective Actions for exposure to deposited radioactivity during the Intermediate Phase.
Relocation of the public: PAG of greater than or equal to 2 rem (20 mSv) projected dose in the first
year, and 0.5 rem (5 mSv) per year projected dose in the second and subsequent years. Apply simple dose
reduction techniques: guideline of less than 2 rem (20 mSv) projected dose in the first year; simple
techniques include scrubbing or flushing hard surfaces, minor removal of soil where radioactive materials
have concentrated, and spending more time than usual indoors or in low exposure-rate areas. Food
interdiction: PAG of 0.5 rem (5 mSv) per year projected whole body dose, or 5 rem (50 mSv) per year to
any individual organ or tissue, whichever is limiting. Drinking water: 100 mrem (1 mSv) projected dose,
for one year, to the most sensitive populations (infants, children, pregnant and nursing women), and 500
mrem (5 mSv) to the general population.""")

add("pag_worker_regs", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "Table 3-3 — Regulations for worker protection (US agencies)", PAG_URL, """
US government agency regulations for worker protection during radiation incidents: the Occupational
Safety and Health Administration (OSHA) — 29 CFR 1910.120 (Safety and Health, HAZWOPER) and 29 CFR
1910.1096 (Ionizing Radiation); the Environmental Protection Agency (EPA) — 40 CFR 311 (Occupational
Radiation Protection); the Nuclear Regulatory Commission (NRC) — 10 CFR 20 (Standards for Protection
Against Radiation); and the Department of Energy (DOE) — 10 CFR 835 (Radiation Protection regulations),
which apply to all DOE employees and contractors who may be exposed to ionizing radiation as a result of
their work for DOE. Worker safety and health is regulated in all states by federal OSHA or by respective
state regulations under an OSHA-approved state plan; 40 CFR Part 311 applies the OSHA HAZWOPER standard
(29 CFR 1910.120) to public-sector workers in states that do not operate their own occupational safety
and health programs.""")

# ---- HHS REMM ----
add("remm_protective_actions_overview", "HHS Radiation Emergency Medical Management (REMM)",
    "Protective Actions — overview", PAG_URL, """
Protective actions (protective action recommendations) are designed to be taken before an anticipated
Protective Action Guide (PAG) dose is reached, to reduce or eliminate the public's exposure to radiation
or other hazards following a radiation incident. In the early and intermediate phases of RDD/IND
incidents there may be inadequate information to determine radiation levels precisely or make dose
projections, so initial protective actions may be undertaken based on models rather than actual measured
radiation levels, and protective action recommendations may change over the course of an incident as new
information is obtained. Primary protective actions include sheltering-in-place, evacuation, relocation,
and interdiction of food and water. Secondary protective actions include medical countermeasure
administration, decontamination of people and places, restrictions of food and/or water, access control,
and victim extraction.""")

add("remm_incident_phases", "HHS Radiation Emergency Medical Management (REMM)",
    "Phases of a radiological incident", PAG_URL, """
A radiological incident is divided into phases. The Early Phase is the period at the beginning of the
incident when immediate decisions for effective protective actions are required; there may be little or
no information available on actual releases or field measurement data, and protective actions in the
early phase are aimed at avoiding inhalation of gases or particulates in a plume and minimizing external
exposure. The Intermediate Phase may overlap with and/or follow the early phase within as little as a few
hours and can last for weeks or months; it is assumed to begin after the incident source and releases
have been brought under control and protective action decisions can be made based on measurements of
deposited radioactive materials, with actions intended to reduce or avoid dose to the public, control
worker exposures and the spread of contamination, and prepare for late-phase cleanup. The Late Phase is
the period when actions designed to reduce radiation levels in the environment to acceptable levels are
conducted, entailing final clean-up decisions and implementation of remediation strategies.""")

add("remm_responder_reference_values", "HHS REMM / NCRP Report No. 179 (2017), Table 4.1",
    "Reference values for emergency responder radiation safety", PAG_URL, """
Reference values for emergency responder radiation safety. Response worker guideline: 5 rem accumulated
dose for all occupational exposures (EPA PAG Manual, 2017). Decision dose: 50 rad accumulated — used to
decide whether to remove the responder or continue the mission, based on operational awareness and
mission priorities. Turn-back dose guidance: 50 rem accumulated — to prevent severe health effects or
injuries (Manual for First Responders to a Radiological Emergency, IAEA, 2006). Cold zone: dose rate less
than or equal to 0.01 R/h — alarm threshold. Hot zone: dose rate greater than 0.01 R/h — routine response
activities performed with personal protective equipment, including active radiation monitoring.
Dangerous-radiation zone: dose rate greater than or equal to 10 R/h — restrict actions to time-sensitive,
mission-critical tasks such as lifesaving. Turn back at 200 R/h — responders should turn back, even when
working on lifesaving missions.""")

add("remm_ars_response_category", "HHS Radiation Emergency Medical Management (REMM)",
    "Managing ARS — Response Category (RC)", REMM_ARS, """
Response Categories (RC) for acute radiation syndrome correlate the severity of damage with the
likelihood of autologous (self) recovery, and are auto-calculated using the highest degree of severity
(1 least to 4 most) checked for any parameter across the four subsyndromes of ARS (hematopoietic,
gastrointestinal, cutaneous, and neurovascular). For example, severity inputs of H4, C2, G3, N1 yield
RC4. RC1 corresponds to mild damage, RC2 to moderate, RC3 to severe, and RC4 to serious damage. The
requirements for the institution where patients should be hospitalized are highly dependent on the
patient's RC, which in turn requires specific therapeutic interventions, and the complexity of clinical
care required increases at higher RC. In a very large mass-casualty incident with austere conditions,
referral decisions may need to change.""")

add("remm_dtpa_indications", "HHS Radiation Emergency Medical Management (REMM)",
    "Ca-DTPA / Zn-DTPA — indications and timing", REMM_DTPA, """
The chelating agents Ca-DTPA and Zn-DTPA, salts of diethylenetriamine pentaacetate (DTPA), are FDA
approved for the elimination of known or suspected internal contamination with the transuranic (Z greater
than 92) metals plutonium, americium, and curium. DTPA should not be used to chelate internal
contamination with uranium or neptunium, and is most effective when the metals to be chelated are in
soluble form. Ca-DTPA and Zn-DTPA should not be administered simultaneously; if both are available,
Ca-DTPA should be given as the first dose because it is more effective than Zn-DTPA during the first 24
hours after internal contamination, and treatment should then switch to Zn-DTPA, which is preferred for
maintenance therapy because Ca-DTPA causes more loss of essential metals such as zinc. To reduce the risk
of future biological effects, DTPA should be given as soon as possible after internal contamination,
following or concurrent with distancing the individual from the source and appropriate external
decontamination; it remains effective even after time has elapsed, though effectiveness decreases once
the elements are trapped in bone. Zn-DTPA is the preferred treatment for a pregnant woman with internal
contamination.""")

add("remm_dtpa_dosing", "HHS Radiation Emergency Medical Management (REMM)",
    "Ca-DTPA / Zn-DTPA — dosing", REMM_DTPA, """
DTPA intravenous dosing for healthy, non-pregnant adults with normal bone marrow and renal function: 1 g
in 5 cc of 5% dextrose in water (D5W) or 0.9% sodium chloride (normal saline) by slow IV push over 3-4
minutes, or 1 g in 100-250 cc of D5W or normal saline as an infusion over 30 minutes. For children under
12 years old: 14 mg DTPA per kg of body weight per day by slow IV push, not to exceed 1 g per day. The
DTPA dose should not be fractionated and should be given only as a single dose once per day. Nebulizer
dosing is 1 g in a 1:1 dilution with sterile water or normal saline, inhaled over 15-20 minutes; FDA
recommends nebulized Zn-DTPA for adults whose internal contamination is only by inhalation. Because
radioactive materials chelated to DTPA are excreted in urine, DTPA must be used carefully in people with
diminished renal function; toxicity, due to chelation of essential metals such as zinc and manganese,
includes nausea, vomiting, chills, diarrhea, fever, pruritus, and muscle cramps.""")

add("osha_rep_enforcement_posture", "OSHA — Radiation Emergency Preparedness and Response",
    "Dose Limits — OSHA applicability and enforcement posture", OSHA_URL, """
Even during emergency response operations, OSHA standards always apply, covering most private sector and
civilian federal employees in all U.S. states and territories; public-sector emergency responders in
states with OSHA-approved State Plans are covered by state OSHA requirements. However, during the initial
emergency response to a radiation emergency, OSHA will likely operate in a technical assistance and
support mode, pursuant to the National Response Framework, rather than issuing citations for workplace
violations, though it retains its enforcement authority under the OSH Act. The guidance assumes that
hazards associated with a radiation emergency, including ionizing radiation, are likely to be extreme
compared to those associated with non-emergency conditions, and that employers may not be able to control
extreme hazards to the degree ordinarily required by the OSH Act and OSHA standards.""")

add("osha_rep_turnback_decision", "OSHA — Radiation Emergency Preparedness and Response",
    "Dose Limits — no maximum turnback dose; guidelines as decision points", OSHA_URL, """
This guidance does not provide a maximum exposure dose (i.e., turnback level). It is not possible to
predict, for extreme events, all of the factors necessary to establish a single maximum dose that could
apply to all responders for all missions. The 5, 10, and 25 rem (0.05, 0.1, and 0.25 Sv) guidelines
should be viewed as flexible limits applicable to the range of early-phase emergency response actions,
and should serve as decision points for planning the protection of responders during response to a
nuclear detonation. Incident Commanders need to understand and consider the risks associated with various
doses of ionizing radiation and establish protocols, as part of the planning process, for determining
when to stop, or not initiate, actions. Since there is assumed to be no risk-free radiation dose,
responders who are reasonably expected to receive more than 25 percent of the occupational dose limit
should be appropriately trained and monitored.""")

add("osha_rep_regulatory_basis", "OSHA — Radiation Emergency Preparedness and Response",
    "Dose Limits — regulatory basis and comparison (OSHA vs DOE vs NRC)", OSHA_URL, """
OSHA's ionizing radiation standards, issued in 1971, are based on International Commission on
Radiological Protection (ICRP) Publication No. 2 and set maximum allowable doses by limiting the dose to
the most critically exposed body part, using maximum permissible concentrations (MPCs) of radionuclides.
OSHA's dose limits are often compared to the more updated requirements of the U.S. Department of Energy
(10 CFR part 835), for workers in its facilities, and the U.S. Nuclear Regulatory Commission (10 CFR part
20), for NRC-licensed facilities. DOE standards are based on ICRP Publication 60; current NRC regulations
are based on ICRP Publications 26 and 30. OSHA has issued a letter of interpretation explaining that it
would be considered a de minimis condition if an employer complied with the more current regulation at 10
CFR Part 20, because the more current standard generally is considered as protective as, or more
protective than, the older OSHA standard.""")

add("epa_pag_scope", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "PAG Manual — purpose and scope", "https://www.epa.gov/radiation/protective-action-guides-pags", """
The Protective Action Guide (PAG) Manual contains advice, planning considerations, best practices, and
radiation dose guidelines that would trigger public safety measures such as evacuation or staying indoors
to minimize or prevent radiation exposure during an emergency. EPA developed Protective Action Guides to
help responders plan for radiation emergencies. The PAG Manual is a planning guide for emergency
responders and does not change federal, state, or local environmental standards. The PAG guidelines are
only for use during a large-scale emergency, when radiation levels could be high enough to cause health
effects unless public safety measures are taken. Section 2.2.2 of the PAG Manual discusses the benefits
and risks of sheltering in place versus evacuation in planning protective actions.""")

add("epa_pag_changes_2017", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "Significant changes from the 1992 PAG Manual", "https://www.epa.gov/radiation/protective-action-guides-pags", """
Significant changes in the 2017 PAG Manual from the 1992 PAG Manual include: applying the PAG Manual to
incidents other than just nuclear power plant accidents; referring users to current food guidance from
the Food and Drug Administration (FDA); providing guidance for potassium iodide (KI) based on the latest
FDA guidance; providing basic planning guidance on reentry, cleanup, and waste disposal; incorporating
late-phase (cleanup) guidance from the Department of Homeland Security's Radiological Dispersal
Device/Improvised Nuclear Device Planning Guidance; and adding a two-tiered drinking water guidance
addressing the people at the most sensitive life stages and the general population. The manual
incorporates lessons learned from actual radiological emergencies, particularly from the Fukushima
nuclear power plant accident.""")

add("epa_pag_drinking_water", "EPA Protective Action Guides (PAG) Manual, EPA-400/R-17/001 (2017)",
    "Drinking water PAG", "https://www.epa.gov/radiation/protective-action-guides-pags", """
In January 2017, EPA incorporated non-regulatory guidance into Chapter 4 of the PAG Manual that
authorities can use to protect residents from experiencing the harmful effects of radiation in drinking
water after a nationally significant radiological emergency. The drinking water PAG is a level that can
be used to determine when alternative drinking water should be provided and the use of contaminated water
supplies restricted; it identifies doses of radiation that should be avoided during an emergency event
and does not represent acceptable routine exposures. The drinking water PAGs apply during the
intermediate phase of an incident, which may last weeks to months but not longer than one year. The
guidance is two-tiered, addressing the people at the most sensitive life stages and the general
population, and is for use only during an emergency; it is not a substitute for compliance with EPA's
National Primary Drinking Water Regulations for Radionuclides.""")

add("remm_dtpa_precautions", "HHS Radiation Emergency Medical Management (REMM)",
    "Ca-DTPA / Zn-DTPA — precautions and side effects", REMM_DTPA, """
Because radioactive materials chelated to DTPA are excreted in urine, DTPA must be used carefully in
people with diminished renal function. The safety and effectiveness of the intramuscular route of Ca-DTPA
or Zn-DTPA administration have not been established. Toxicity is due to chelation of essential metals such
as zinc and manganese, and includes nausea, vomiting, chills, diarrhea, fever, pruritus, and muscle
cramps. Ca-DTPA should be used with caution in patients with hemochromatosis, a genetic disease that
causes the body to absorb too much iron from the diet. The main side effect of Ca-DTPA is loss of certain
essential nutritional metals, such as zinc, from the body, which can be replaced by taking oral zinc
supplements; Zn-DTPA may also decrease levels of certain nutritional metals, but the effect is less than
with Ca-DTPA. Chelation therapy administered by nebulized inhalation may cause breathing difficulties in
some individuals.""")

# ---------------------------------------------------------------- carry-forward existing chunks
# Pull the ORIGINAL validated context blocks straight from the mini-corpus (longest variant),
# except OSHA sections which are superseded by the fuller live-page chunks above.
sec2id = {
    "Sheet 02 — General Conditions of Response": ("asn2023_sheet02",
        "ASN National Guide — Medical Response in a Nuclear or Radiological Emergency, June 2023"),
    "Sheet 04 — The 3 Types of Victim": ("asn2023_sheet04",
        "ASN National Guide — Medical Response in a Nuclear or Radiological Emergency, June 2023"),
    "Sheet 06 — Responders' Equipment and Means of Protection": ("asn2023_sheet06",
        "ASN National Guide — Medical Response in a Nuclear or Radiological Emergency, June 2023"),
    "Acute Radiation Syndromes": ("doe_au22_ars",
        "DOE Ionizing Radiation Dose Ranges Chart Information Brief, AU-22 001-2018"),
    "Regulations and Guidelines": ("doe_au22_regs",
        "DOE Ionizing Radiation Dose Ranges Chart Information Brief, AU-22 001-2018"),
    "DOE Ionizing Radiation Dose Ranges Chart, Figure 5": ("doe_au22_fig5",
        "DOE Ionizing Radiation Dose Ranges Chart"),
    "Natural Background Radiation": ("doe_au22_background",
        "DOE Ionizing Radiation Dose Ranges Chart Information Brief, AU-22 001-2018"),
    "TI.2 — Personnel Protection Guidelines": ("iaea_pda_ti2",
        "IAEA Portable Digital Assistant for First Responders"),
}
carry_text = {}
for fn in ["train.jsonl", "val.jsonl"]:
    for line in (DOCS / fn).read_text().splitlines():
        if not line.strip():
            continue
        u = [m for m in json.loads(line)["messages"] if m["role"] == "user"][0]["content"]
        if "[SOURCE:" not in u:
            continue
        body = u.split("CONTEXT:")[1].split("QUESTION:")[0]
        for blk in re.split(r"(?=\[SOURCE:)", body):
            m = re.match(r"\[SOURCE: ([^\]]+)\]\s*(.*)", blk.strip(), re.S)
            if not m:
                continue
            head, txt = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
            sec = head.split("|")[-1].strip() if "|" in head else head.strip()
            if sec in sec2id:
                cid, src = sec2id[sec]
                if len(txt) > len(carry_text.get(cid, ("", "", ""))[2] if cid in carry_text else ""):
                    carry_text[cid] = (cid, src, txt, sec)

carried = []
for cid, (cid_, src, txt, sec) in carry_text.items():
    carried.append({
        "record_type": "chunk", "chunk_id": cid, "source": src, "section": sec,
        "url": "", "retrieved": "carried_from_mini_corpus", "text": txt,
    })

# ---------------------------------------------------------------- write
all_chunks = new + carried
ids = [c["chunk_id"] for c in all_chunks]
assert len(ids) == len(set(ids)), f"duplicate id: {[i for i in ids if ids.count(i) > 1]}"

def toks(t): return max(1, round(len(t) / 4))
meta = {
    "record_type": "meta", "name": "corpus_1", "version": 1, "created": "2026-07-10",
    "prev": "mini-corpus (train.jsonl/val.jsonl)",
    "sources": sorted({c["source"] for c in all_chunks}),
    "counts": {"chunks": len(all_chunks), "new": len(new), "carried": len(carried),
               "tokens_est": sum(toks(c["text"]) for c in all_chunks)},
    "id_convention": "docslug_sectionslug",
    "notes": ("Chunk texts lightly cleaned from official sources (footnote markers/links stripped, "
              "whitespace normalized), faithful to source wording. OSHA excerpts from the mini-corpus "
              "were superseded by fuller live-page sections. IAEA EPR-First Responders full manual was "
              "not retrievable via fetch; IAEA is represented by the carried PDA excerpt plus the IAEA "
              "2006 turn-back value in remm_responder_reference_values. New content makes former refusal "
              "topics (KI, 10 CFR 835) answerable — regenerate golden pairs as v1."),
}
with OUT.open("w") as f:
    f.write(json.dumps(meta) + "\n")
    for c in all_chunks:
        f.write(json.dumps(c) + "\n")

# ---------------------------------------------------------------- report
from collections import Counter
bysrc = Counter(c["source"].split(",")[0].split(" — ")[0].split(" (")[0][:34] for c in all_chunks)
tk = [toks(c["text"]) for c in all_chunks]
print(f"WROTE {OUT.name}: {len(all_chunks)} chunks ({len(new)} new + {len(carried)} carried)")
print(f"tokens est: total {sum(tk)}  |  per-chunk min {min(tk)} / median {sorted(tk)[len(tk)//2]} / max {max(tk)}")
print(f"vs mini-corpus ~2356 tok / 11 chunks  ->  {sum(tk)/2356:.1f}x tokens, {len(all_chunks)/11:.1f}x chunks")
print("per source:")
for s, n in bysrc.most_common():
    print(f"  {n:2d}  {s}")
