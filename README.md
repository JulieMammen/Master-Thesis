# Master-Thesis
University Of Nebraska Meidical Center- Master of Biomedical Informatics

# Modernizing Cancer Registry Data with FHIR mCODE

## Project Overview
This project evaluates the transformation of NAACCR-based cancer registry data
(Breast and Prostate cancer) into HL7 FHIR mCODE representations to support
longitudinal analytics, semantic interoperability, and extensibility.

## Clinical  Source
NAACCR abstracted cancer registry data.

## Scope
- Breast and Prostate cancer
- Diagnosis + longitudinal treatment and outcomes
- Comparative analysis: Registry vs mCODE

## Status
Crosswalk development (NAACCR → mCODE)

# Phase 1 – Registry-Style Data Analysis (Breast Cancer)

## Objective
Establish a baseline “traditional cancer registry” analytic dataset to evaluate
limitations in longitudinal analysis, disease status tracking, and interoperability,
prior to transforming the same data into FHIR mCODE.

## Environment
- Database: PostgreSQL
- Access: pgAdmin
- Port: 5434
- Database name: thesis_registry

## Dataset
- Synthetic breast cancer registry-style dataset
- 1000 patients
- Schema aligned to NAACCR-style abstractions (C50.*)
- Used for analytic comparison only (no PHI)

## Table: breast_registry
Key elements include:
- Demographics, diagnosis, stage, grade
- ER / PR / HER2 biomarkers
- Treatment summaries (surgery, radiation, systemic)
- Neoadjuvant response and residual cancer burden

### Design Decisions
- `targeted_therapy` renamed to `immuno_therapy` to better reflect modern oncology
  treatment distinctions and align with mCODE medication modeling.
- `disease_status` added to represent inferred clinical status (e.g., NED, persistent,
  progressive), highlighting a known limitation of registry data.
- `subtype_simulated` retained as a synthetic ground-truth field for validation only;
  not considered a registry-derived element.

## Current Status
- PostgreSQL service running and connected
- Table created successfully
- 1000 rows loaded via COPY
- Schema updated successfully
- Ready for Phase 1 analytic queries
  # Phase 1 – Registry-Style Data Analysis (Breast Cancer)

## Purpose
This phase establishes a **baseline analytic assessment** of traditional cancer registry–style data using a flat relational table. The goal is to evaluate **what registry data supports well** and **where analytic limitations emerge**, prior to transforming the same data into FHIR mCODE for comparison.

This phase intentionally mirrors how cancer registry data is typically queried today.

---

## Data Source
- **Dataset**: Synthetic breast cancer registry-style dataset
- **Cohort size**: 1,000 patients
- **Cancer site**: Breast (ICD-10 C50.*)
- **Data type**: Synthetic (no PHI)
- **Storage**: PostgreSQL (`thesis_registry.breast_registry`)

The dataset includes demographics, diagnosis, staging, biomarkers, treatment summaries, and inferred disease status.

---

## Table: `breast_registry`

The table represents a traditional registry abstraction model with summary-level fields:

- Demographics (age, sex, race)
- Diagnosis and stage at presentation
- Biomarkers (ER, PR, HER2)
- Treatment summaries (surgery, radiation, systemic)
- Neoadjuvant response and residual cancer burden
- Inferred disease status (added for analytic exploration)

### Design Notes
- Breast cancer subtype is **not explicitly stored** and must be derived from biomarker combinations.
- Disease status is inferred and static, reflecting known registry limitations.
- The table is **non-longitudinal** and episode-based.

---

## Analysis 1 – Stage Distribution at Diagnosis

### Question
What is the distribution of breast cancer stage at diagnosis?

### Rationale
Cancer registries are optimized for **population-level surveillance** and descriptive epidemiology. Stage distribution is a core strength of registry data and serves as a baseline validation check.

### SQL
```
SELECT
  stage_group,
  COUNT(*) AS patient_count
FROM breast_registry
GROUP BY stage_group
ORDER BY patient_count DESC;

```

### Observation

Registry data supports cross-sectional summaries such as stage distribution effectively. However, stage is captured as a single snapshot and does not reflect longitudinal changes
### Analysis 2 – Breast Cancer Subtype Derivation from Biomarkers
Question

How many patients fall into common breast cancer subtypes based on ER, PR, and HER2 status?

Rationale

Breast cancer subtype is clinically meaningful but is not a first-class concept in traditional registry data. It must be derived repeatedly using biomarker logic
```
SELECT
  CASE
    WHEN er_status = 'Positive'
         AND pr_status = 'Positive'
         AND her2_status = 'Negative'
      THEN 'HR+/HER2-'
    WHEN her2_status = 'Positive'
      THEN 'HER2+'
    WHEN er_status = 'Negative'
         AND pr_status = 'Negative'
         AND her2_status = 'Negative'
      THEN 'TNBC'
    ELSE 'Other / Unknown'
  END AS derived_subtype,
  COUNT(*) AS patient_count
FROM breast_registry
GROUP BY derived_subtype
ORDER BY patient_count DESC;
```
### Observation

Subtype classification requires indirect inference from multiple fields, increasing analytic complexity and the risk of inconsistency across studies. Subtype is not versioned or time-aware

### Analysis 3 – Treatment Patterns by Stage
Question

How do treatment patterns vary by stage at diagnosis?

Rationale

Registry data captures whether treatments occurred but does not reliably encode treatment intent, sequencing, or line of therapy.
```
SELECT
  stage_group,
  rx_summ_surg_prim_site,
  rx_summ_radiation,
  rx_summ_systemic_surg_seq,
  COUNT(*) AS patient_count
FROM breast_registry
GROUP BY
  stage_group,
  rx_summ_surg_prim_site,
  rx_summ_radiation,
  rx_summ_systemic_surg_seq
ORDER BY
  stage_group,
  patient_count DESC;

```
### Observation

Treatment data is summary-based and non-longitudinal. While treatment occurrence can be counted, clinical context such as intent (curative vs palliative) and temporal sequencing is difficult to reconstruct.


### Analysis 4
Question

How well does registry-style data represent a patient’s disease status over time?
Disease status by stage
```
SELECT
  stage_group,
  disease_status,
  COUNT(*) AS patient_count
FROM breast_registry
GROUP BY stage_group, disease_status
ORDER BY stage_group, patient_count DESC;
```

### Key observation 

Disease status in registry-style data is static and inferred. It does not support longitudinal tracking of remission, recurrence, or progression without additional abstraction or complex workarounds. Captures status once, usually at last contact or abstraction.Most patients fall into “Unknown” or broad categories

### What registries actually capture (precisely)

Under NAACCR standards, registries commonly capture:

Date of Diagnosis

Date of First Course of Treatment

Defined as the earliest treatment given

Could be surgery or systemic therapy or radiation

### Analysis 5 – Time-to-Treatment Limitations
```
SELECT
  stage_group,
  rx_summ_surg_prim_site,
  rx_summ_systemic_surg_seq,
  COUNT(*) AS patient_count
FROM breast_registry
GROUP BY stage_group, rx_summ_surg_prim_site, rx_summ_systemic_surg_seq
ORDER BY stage_group, patient_count DESC;

```

This supports questions like:

“Was treatment initiated within X days of diagnosis?”

So yes — a single time-to-first-treatment metric is possible

### Key Observation
Registry data includes a date of first course of treatment, enabling calculation of time from diagnosis to treatment initiation. However, registry abstractions do not consistently capture individual treatment start dates or longitudinal sequencing, limiting more granular time-to-treatment and pathway analyses

### Phase 1 Conclusion

Traditional registry data performs well for retrospective descriptive analysis, but struggles with:

Longitudinal disease tracking

Explicit subtype representation

Treatment intent and sequencing

Reusability across analytic contexts

These limitations motivate the transformation of the same clinical facts into FHIR mCODE, which is explored in subsequent phases

## Phase 2
```
phase-2/
  fhir/
    patient-0985.bundle.json
  validation/
    patient-0985.validator.r4.txt
    README.md
patient-0985.bundle.json = your working bundle
```



#### Validator Code
```
& "C:\Users\julie\AppData\Local\Programs\Eclipse Adoptium\jdk-25.0.2.10-hotspot\bin\java.exe" -jar tools/validator_cli.jar phase-2\fhir\patient-0985.bundle.json -version 4.0.1 > phase-2\validation\patient-0985.validator.r4.txt

```

#### Result summary

Errors: 0

Warnings: 7

Notes: 2

#### Interpretation 

0 errors indicates the bundle is syntactically valid FHIR R4 and meets required constraints for the profiles used.

Warnings are expected in real-world FHIR pipelines and commonly reflect best-practice guidance (e.g., missing narrative, recommended value-set membership, optional terminology bindings).

For this project, Phase 2 emphasizes structural mCODE alignment rather than complete terminology binding. Terminology completeness is addressed as a limitation and discussion point.

 # Phase 2 — Registry → mCODE FHIR Generation & Validation

## Overview
This phase operationalizes registry-to-mCODE transformation at scale.

Using a synthetic NAACCR-style breast cancer dataset (`breast_registry_synth_1000.csv`), patient-level FHIR Bundles were generated using a Python script and validated using the HL7 FHIR Validator CLI against the HL7 US mCODE Implementation Guide.

## Inputs
- Source dataset: `breast_registry_synth_1000.csv`
- Data dictionary: `breast_registry_synth_1000_data_dictionary.md`

## Bundle Generation

### Script

```

phase-2/scripts/generate_mcode_bundles.py

```

### Command (example)
```
& C:/Python313/python.exe phase-2/scripts/generate_mcode_bundles.py

```

Output

Generated bundles directory: phase-2/fhir_generated/

Naming convention: patient-0001.bundle.json, patient-0002.bundle.json, ...

```

```
mCODE IG Validation
Validator


### : HL7 FHIR Validator CLI (tools/validator_cli.jar)

FHIR version: 4.0.1 (R4)

IG: hl7.fhir.us.mcode#4.0.0
```
& "C:\Users\julie\AppData\Local\Programs\Eclipse Adoptium\jdk-25.0.2.10-hotspot\bin\java.exe" `
  -jar tools/validator_cli.jar `
  phase-2\fhir_generated\patient-0001.bundle.json `
  -version 4.0.1 `
  -ig hl7.fhir.us.mcode#4.0.0

```

#### Validate a batch of 25
```
New-Item -ItemType Directory -Force phase-2\validation\mcode_ig\logs2 | Out-Null

```

```
foreach ($n in 1..25) {
  $id = $n.ToString("0000")
  $in = "phase-2\fhir_generated\patient-$id.bundle.json"
 ls
  $log = "phase-2\validation\mcode_ig\logs2\patient-$id.mcode-ig.txt"

  & "C:\Users\julie\AppData\Local\Programs\Eclipse Adoptium\jdk-25.0.2.10-hotspot\bin\java.exe" `
    -jar tools/validator_cli.jar $in `
    -version 4.0.1 `
    -ig hl7.fhir.us.mcode#4.0.0 `
    | Out-File -Encoding utf8 $log
}

```


# A summary CSV was generated from validation logs:

```
phase-2/validation/mcode_ig/mcode_ig_validation_summary_25.csv

```

- Observed results (patients 0001–0017):

- Errors: 0

- Warnings: ~18–20 per bundle

- Notes: 0

#### Warnings were primarily best-practice recommendations (e.g., narrative text not present) and did not represent structural or mCODE IG conformance failures.

# Interpretation

This phase demonstrates that registry-style cancer abstract data can be transformed into syntactically valid, mCODE IG–validated FHIR Bundles at scale, supporting downstream interoperability and analytic use cases.

#### Phase 2 IN A NUTSHELL

- Generated 1000 bundles

- Validated against base FHIR

- Validated first 25 against mCODE IG

- Got 0 errors (only best-practice warning)

### Phase 3- Analytics Comparison

A) Registry-style SQL analytics

vs

B) FHIR-based resource analytics

##### Phase 3 – FHIR-Based Biomarker Analytics [Checking FHIR mCode mapping works same as Registry based analytics]

- Dataset: 1000 synthetic breast cancer patients
- Source: phase-2/fhir_generated/

```
ER Status:
Positive: 739 (73.9%)
Negative: 237 (23.7%)
Unknown:  24 (2.4%)

PR Status:
Positive: 615 (61.5%)
Negative: 344 (34.4%)
Unknown:  41 (4.1%)

HER2 Status:
Positive: 152 (15.2%)
Negative: 797 (79.7%)
Unknown:    5 (0.5%)
```
#### Result:
FHIR-derived analytics match registry-level SQL distributions, demonstrating preservation of analytic integrity after mCODE transformation

#### Phase 3 — Longitudinal Disease Status (FHIR/mCODE Demonstration)

## Goal
Demonstrate how FHIR/mCODE supports longitudinal oncology analytics by representing **multiple time-stamped disease status observations** per patient (time-series data). This enables analyses such as status transitions and time-to-progression, which are difficult or infeasible using flat registry-style abstractions without redesign.

## Environment
- HAPI FHIR server running locally (Docker)
- FHIR base URL used in this project: `http://localhost:8085/fhir/`

## Patient / Condition
- Patient: `Patient/pat-0001`
- Primary cancer condition: `Condition/condition-0001`

## What was added
Three disease status Observations for the same patient, all using LOINC `69233-9` ("Disease status"):

| Observation ID | Effective Date | Value |
|---|---:|---|
| `obs-ds-2020` | 2020-01-15 | Stable disease |
| `obs-ds-2021` | 2021-07-30 | No evidence of disease |
| `obs-ds-2022` | 2022-07-30 | Progressive disease |

These Observations are linked to the primary cancer condition using `focus: Condition/condition-0001`.

## Files
```
- `phase-3/fhir/longitudinal/pat-0001-cancer-disease-status.bundle.json`
- `phase-3/fhir/longitudinal/pat-0001-add-2-more-status.bundle.json`
 ```
 

## Load into HAPI (transactions)
```
curl -X POST "http://localhost:8085/fhir/" \
  -H "Content-Type: application/fhir+json" \
  --data-binary "@./phase-3/fhir/longitudinal/pat-0001-cancer-disease-status.bundle.json"
```
```
curl -X POST "http://localhost:8085/fhir/" \
  -H "Content-Type: application/fhir+json" \
  --data-binary "@./phase-3/fhir/longitudinal/pat-0001-add-2-more-status.bundle.json"
```
```
phase-3\scripts\analyze_biomarkers_from_fhir.py
```

```
import json
from pathlib import Path
from collections import Counter

FHIR_DIR = Path("phase-2/fhir_generated")

MARKERS = {
    "ER": ("ER status", "Estrogen receptor status"),
    "PR": ("PR status", "Progesterone receptor status"),
    "HER2": ("HER2 status",),
}

def norm(v: str) -> str:
    if not v:
        return "Unknown"
    x = v.strip().lower()
    if x in ("positive", "pos", "+", "present", "true", "yes", "y", "1"):
        return "Positive"
    if x in ("negative", "neg", "-", "absent", "false", "no", "n", "0"):
        return "Negative"
    if x in ("unknown", "unk", "na", "n/a", ""):
        return "Unknown"
    return v.strip()

def analyze(marker_labels):
    c = Counter()
    total = 0
    missing = 0

    for file in sorted(FHIR_DIR.glob("patient-*.bundle.json")):
        bundle = json.loads(file.read_text(encoding="utf-8-sig"))
        total += 1
        found = False

        for entry in bundle.get("entry", []):
            res = entry.get("resource", {})
            if res.get("resourceType") != "Observation":
                continue

            if res.get("code", {}).get("text") in marker_labels:
                found = True
                val = res.get("valueCodeableConcept", {}).get("text", "Unknown")
                c[norm(val)] += 1

        if not found:
            missing += 1
            c["Unknown"] += 1

    return total, missing, c

for name, labels in MARKERS.items():
    total, missing, c = analyze(labels)
    print(f"\nFHIR {name} Status Distribution")
    print("---------------------------------")
    print(f"Total bundles read: {total}")
    print(f"Bundles missing {name}: {missing}\n")
    for s in ["Positive", "Negative", "Unknown"]:
        count = c.get(s, 0)
        pct = round((count / total) * 100, 2) if total else 0
        print(f"{s:8}  {count:4}  ({pct}%)")
```


```
 phase-3\scripts\analyze_biomarkers_from_fhir.py
 ```

```
curl -s "http://localhost:8085/fhir/Observation?_id=obs-ds-2020,obs-ds-2021,obs-ds-2022"
```

```
curl -s "http://localhost:8085/fhir/Observation?subject=Patient/pat-0001&code=http://loinc.org|69233-9&_sort=date&_count=50"
```

## Commit + push to GitH

```
curl.exe -s "http://localhost:8085/fhir/Observation?subject=Patient/pat-0001&code=97509-4&_count=50"
```
### Results
Patient = pat-0001

Disease status Observation

Date = 2021-07-30

Value = “No evidence of disease”

Code includes LOINC 69233-9 (great for searching)


### Step 1  Create a new transaction bundle file with 2 more status observations

```
phase-3\fhir\longitudinal\pat-0001-add-2-more-status.bundle.json  

```

```
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "resource": {
        "resourceType": "Observation",
        "id": "obs-ds-2020",
        "status": "final",
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "69233-9",
              "display": "Disease status"
            }
          ],
          "text": "Cancer disease status"
        },
        "subject": {
          "reference": "Patient/pat-0001"
        },
        "focus": [
          {
            "reference": "Condition/condition-0001"
          }
        ],
        "effectiveDateTime": "2020-01-15T00:00:00+00:00",
        "valueCodeableConcept": {
          "text": "Stable disease"
        }
      },
      "request": {
        "method": "PUT",
        "url": "Observation/obs-ds-2020"
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "id": "obs-ds-2022",
        "status": "final",
        "code": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "69233-9",
              "display": "Disease status"
            }
          ],
          "text": "Cancer disease status"
        },
        "subject": {
          "reference": "Patient/pat-0001"
        },
        "focus": [
          {
            "reference": "Condition/condition-0001"
          }
        ],
        "effectiveDateTime": "2022-07-30T00:00:00+00:00",
        "valueCodeableConcept": {
          "text": "Progressive disease"
        }
      },
      "request": {
        "method": "PUT",
        "url": "Observation/obs-ds-2022"
      }
    }
  ]
}
```
### Step 2- Upload that new bundle to HAPI
```
curl.exe -X POST "http://localhost:8085/fhir/" -H "Content-Type: application/fhir+json" --data-binary "@.\phase-3\fhir\longitudinal\pat-0001-add-2-more-status.bundle.json"
```
### Three longitudinal disease-status events for the same patient:
obs-ds-2020 (Stable disease)

obs-ds-2021 (No evidence of disease)

obs-ds-2022 (Progressive disease)

#### Step 3 : Run the thesis “longitudinal proof” search

```
curl.exe -s "http://localhost:8085/fhir/Observation?subject=Patient/pat-0001&code=http://loinc.org|69233-9&_sort=date&_count=50"

```
##### True longitudinal disease-status timeline in HAPI for the same patient, with multiple dated Observations under the same LOINC code 69233-9. This is exactly the “mCODE/FHIR enables longitudinal analytics” proof that your Phase 1 thesis framing calls for
What you have for Patient/pat-0001 (the clean 3-point storyline)

2020-01-15 → Stable disease (obs-ds-2020)

2021-07-30 → No evidence of disease (obs-ds-2021)

2022-07-30 → Progressive disease (obs-ds-2022)

### Phase 3b

```
phase-3/
│
├── data/
│   ├── phase3_disease_status.json
│   └── phase3_medreq.json
│
├── scripts/
│   └── phase3_analysis.py
│
└── results/
    └── phase3_results.txt
    
```   
``
mkdir .\phase-3\results -Force

```

```
import json
from collections import defaultdict
from pathlib import Path

# ---------------------------
# Load JSON safely (handles BOM if present)
# ---------------------------
def load_json(path):
    b = path.read_bytes()
    if b.startswith(b'\xef\xbb\xbf'):  # strip UTF-8 BOM
        b = b[3:]
    return json.loads(b.decode('utf-8'))

base_dir = Path(__file__).resolve().parent.parent

ds_path = base_dir / "data" / "phase3_disease_status.json"
mr_path = base_dir / "data" / "phase3_medreq.json"

ds_bundle = load_json(ds_path)
mr_bundle = load_json(mr_path)

# ---------------------------
# Build longitudinal timelines
# ---------------------------
patient_status = defaultdict(list)

for entry in ds_bundle.get("entry", []):
    obs = entry.get("resource", {})
    if obs.get("resourceType") != "Observation":
        continue

    subject = obs.get("subject", {}).get("reference", "")
    if not subject.startswith("Patient/"):
        continue

    patient_id = subject.split("/")[-1]
    date = obs.get("effectiveDateTime")
    status = obs.get("valueCodeableConcept", {}).get("text")

    if date and status:
        patient_status[patient_id].append((date, status))

for pid in patient_status:
    patient_status[pid].sort()

# ---------------------------
# Treatment Exposure
# ---------------------------
has_immuno = defaultdict(bool)

for entry in mr_bundle.get("entry", []):
    mr = entry.get("resource", {})
    if mr.get("resourceType") != "MedicationRequest":
        continue

    subject = mr.get("subject", {}).get("reference", "")
    if not subject.startswith("Patient/"):
        continue

    patient_id = subject.split("/")[-1]
    med_text = mr.get("medicationCodeableConcept", {}).get("text", "").lower()

    if "immunotherapy" in med_text:
        has_immuno[patient_id] = True

# ---------------------------
# Recurrence Computation
# ---------------------------
total_patients = len(patient_status)
overall_recur = 0

group_counts = {
    "chemo_only": {"n": 0, "recur": 0},
    "chemo_plus_immuno": {"n": 0, "recur": 0}
}

for pid, timeline in patient_status.items():
    statuses = [s for d, s in timeline]
    recurred = ("Recurrent disease" in statuses)

    if recurred:
        overall_recur += 1

    if has_immuno[pid]:
        grp = "chemo_plus_immuno"
    else:
        grp = "chemo_only"

    group_counts[grp]["n"] += 1
    if recurred:
        group_counts[grp]["recur"] += 1

overall_rate = overall_recur / total_patients * 100


Output Results

results = []

results.append("=== Phase 3 Longitudinal mCODE Analysis ===")
results.append("")
results.append("Overall Cohort:")
results.append(f"Total Patients: {total_patients}")
results.append(f"Patients with Recurrence: {overall_recur}")
results.append(f"Recurrence Rate (%): {round(overall_rate, 2)}")
results.append("")
results.append("By Treatment Exposure (Structural Demonstration):")

for grp in ["chemo_only", "chemo_plus_immuno"]:
    n = group_counts[grp]["n"]
    r = group_counts[grp]["recur"]
    rate = (r / n * 100) if n else 0
    results.append(f"{grp}: n={n}, recurrences={r}, recurrence_rate={rate:.2f}%")

results_path = base_dir / "results" / "phase3_results.txt"
results_path.parent.mkdir(exist_ok=True)

with open(results_path, "w", encoding="utf-8") as f:
    for line in results:
        f.write(line + "\n")

for line in results:
    print(line)

```

```
python .\phase-3\scripts\phase3_analysis.py

```
### Longitudinal Outcome Analysis Using mCODE

#### Objective

- Demonstrate computable longitudinal recurrence analysis using mCODE-aligned FHIR resources.

- Cohort

200 simulated breast cancer patients

3 time-indexed CancerDiseaseStatus Observations per patient

Treatment exposure captured via MedicationRequest resources

Computed Endpoint

#### Recurrence defined as presence of "Recurrent disease" following prior "No evidence of disease" status

### Results

Total Patients: 200

Recurrence: 60

Recurrence Rate: 30%

Treatment stratification (structural demonstration):

Chemo-only: n=100

Chemo + Immunotherapy: n=100

#### Group differences reflect deterministic simulation design and are not intended to model therapeutic efficacy. This experiment demonstrates that longitudinal, exposure-stratified outcome analysis is computable directly from mCODE FHIR resources without schema redesign

- mCODE supports longitudinal modeling

- Recurrence is computable from time-based Observations

- Exposure-outcome stratification is possible

- No additional analytic schema required

#### Registry vs mCODE Longitudinal Comparison Argument

Comparative Evaluation: Traditional Cancer Registry Data vs. mCODE FHIR for Longitudinal Outcome Analysis

### 1. Structural Design Differences

Traditional cancer registry datasets (e.g., NAACCR-based flat files) are primarily designed for standardized reporting, surveillance, and population-level epidemiologic monitoring. Data elements are stored as discrete coded variables in a tabular structure, typically representing:

- Primary diagnosis

- Tumor characteristics at diagnosis

- First course of treatment

- Vital status

- Limited follow-up indicators

These datasets are fundamentally cross-sectional with limited longitudinal granularity. While follow-up fields exist (e.g., recurrence indicators, last contact date), they are not inherently structured as time-indexed clinical events.

In contrast, mCODE implemented via HL7 FHIR represents cancer-related information as modular, time-stamped resources:

-Condition (primary cancer)

- Observation (CancerDiseaseStatus, tumor markers, staging)

- MedicationRequest (systemic therapy)

- Procedure (surgical interventions)

Each resource is independently timestamped and linked via references, enabling true longitudinal modeling of disease trajectories.

### 2. Recurrence Detection: Static Field vs Computable Trajectory

In traditional registry datasets:

Recurrence is often captured as a binary variable or abstracted follow-up field.

Time-to-recurrence must be reconstructed using manually curated dates.

Sequential disease states (e.g., stable → NED → recurrence) are not inherently modeled as discrete events.

In the mCODE FHIR implementation:

Recurrence is derived programmatically from sequential CancerDiseaseStatus Observations.

Disease states are represented as time-indexed resources.

Longitudinal transitions are computable without altering schema design.

This enables:

Automated recurrence detection

Time-ordered disease state analysis

Reproducible analytic pipelines

The analysis conducted in Phase 3 demonstrated that recurrence could be identified by detecting a transition to “Recurrent disease” following “No evidence of disease” across 200 patients, yielding a 30% recurrence rate.

This recurrence was not stored as a static variable; it was computed from structured longitudinal data.

### 3. Treatment Exposure Stratification

#### In registry-based data:

First course of treatment is typically captured in summary form.

Subsequent treatment exposures are inconsistently structured.

Linking treatment timing to outcome transitions requires complex preprocessing.

#### In mCODE:

Treatment exposure is represented via MedicationRequest resources.

Each exposure includes a timestamp.

Exposure-outcome relationships are computable using resource references.

In the simulated cohort, patients were stratified into:

#### Chemotherapy only

Chemotherapy plus immunotherapy

Recurrence stratification was computed directly from linked FHIR resources without database restructuring.

This demonstrates that exposure-based longitudinal analysis is natively supported by the mCODE model.

### 4. Schema Flexibility and Extensibility

Traditional registry schema:

Flat and version-dependent

Adding new longitudinal variables requires schema modification

Genomic data integration is limited or external

#### mCODE FHIR model:

Modular resource-based architecture

Extensible via profiles

Natively supports genomic Observations, biomarkers, and repeated measurements

Thus, the FHIR model accommodates evolving oncology research needs without redesigning core infrastructure.

### 5. Analytic Implications

The key distinction is not data availability but data architecture.

Traditional registry data:

Designed for surveillance and reporting

Optimized for standardized aggregation

Limited native support for dynamic, time-dependent modeling

##### mCODE FHIR:

Designed for interoperability and computability

Supports repeated, time-indexed events

Enables automated derivation of endpoints

Integrates exposure and outcome modeling natively

The Phase 3 experiment demonstrates that recurrence detection and treatment stratification are computable directly from FHIR resources without constructing secondary analytic tables

### While registry datasets remain essential for population-level surveillance, their structural design limits dynamic longitudinal modeling. The mCODE FHIR architecture enables event-based, time-indexed computability, which aligns more closely with modern real-world evidence and precision oncology research workflows. This architectural distinction suggests that mCODE enhances analytic capability beyond what is achievable with traditional registry data elements alone


#### For the final paper  What would this analysis look like in a NAACCR-style flat registry?

In a NAACCR-like table, your dataset is typically one row per tumor (or per patient-tumor) with columns for diagnosis, stage, biomarkers, first-course treatment, and limited follow-up. To replicate what you just did with mCODE longitudinal Observations, you’d need to manufacture longitudinal structure from fields that are usually not event-based.

### Implementation pattern in registry SQL (conceptually):

One row = baseline snapshot

Recurrence is either:

not present, or

present as a single indicator/date (often incomplete), or

embedded in “subsequent therapy”/follow-up notes that aren’t standardized

#### So the registry version of your Phase 3 logic becomes:

Define “NED” using proxy fields (often not explicitly available)

Define recurrence using a single recurrence indicator/date (if present)

Calculate time-to-recurrence using one date subtraction

Stratify by treatment based on first-course treatment summary columns

#### Key limitation: you cannot model trajectories (stable → NED → recur) because the registry row does not store repeated disease-status states with timestamps.

#### Could recurrence after “NED” be derived in registry data?

Usually not directly—and if it can be done, it’s typically inferred.

To compute “recurrence after NED,” you need two things:

1) evidence of a “disease-free” state at some timepoint

2) a later recurrence event with a date

Most NAACCR-style datasets do not store a dated “NED” state as a structured data element. Even when recurrence is captured, “NED date” is rarely present as a computable event.

So you end up with proxy definitions like:

- assume post-treatment implies NED (not always true)

- use “no evidence of disease” from follow-up text (often not standardized)

- use “disease status” fields if present (often not repeated over time)

##### Bottom line: recurrence after NED is often under-reported, inconsistently recorded, or not computable without additional clinical data sources.(mCODE/FHIR wins: you can represent and query multiple dated disease-status Observations per patient)
#### Would time-to-event require redesign in registry format?

##### Yes, for anything beyond a single event date.

If the registry has a single “recurrence date,” you can calculate:

- time from diagnosis → recurrence

But for what you’re aiming to show (and what mCODE supports):

- time from NED → recurrence

- time from treatment start → progression

- multiple episodes (recur, respond, progress again)

 Would need to redesign the registry structure into an event table, e.g.:

patient_id

event_type (NED, recurrence, progression, response)

event_date

source (abstracted, imaging, clinical note)

related_treatment_episode_id
#### That is essentially recreating what FHIR already provides natively: multiple time-stamped resources per patient.
##### “Registry data can support some time-to-event endpoints only when event dates exist as single fields. For longitudinal endpoints requiring multiple intermediate states (e.g., NED → recurrence), the flat registry model must be restructured into an event-based design—whereas mCODE/FHIR supports this natively through repeated time-indexed Observations.”

#### Phase 3c
Phase 3 : time-to-recurrence in months (mCODE)

````
import json
from collections import defaultdict
from pathlib import Path

# Resolve data files relative to this script so the script can be run from any cwd
here = Path(__file__).resolve().parent
root = here.parent
ds_path = here / "data" / "phase3_disease_status.json"

# ---------- Load Disease Status Observations ----------
def load_json(path: Path):
    """Read a JSON file and handle common BOM/UTF-16/UTF-8 variants robustly."""
    b = path.read_bytes()
    # BOM-aware decoding
    if b.startswith(b"\xEF\xBB\xBF"):
        text = b.decode("utf-8-sig")
    elif b.startswith(b"\xFF\xFE") or b.startswith(b"\xFE\xFF"):
        # likely UTF-16 LE/BE
        text = b.decode("utf-16")
    else:
        # try utf-8, fall back to latin-1 to avoid crashes
        try:
            text = b.decode("utf-8")
        except Exception:
            text = b.decode("latin-1")
    return json.loads(text)


ds_bundle = load_json(ds_path)

patient_status = defaultdict(list)

for entry in ds_bundle.get("entry", []):
    obs = entry.get("resource", {})
    if obs.get("resourceType") != "Observation":
        continue

    subject = obs.get("subject", {}).get("reference", "")
    if not subject.startswith("Patient/"):
        continue

    patient_id = subject.split("/")[-1]
    date = obs.get("effectiveDateTime")
    status = obs.get("valueCodeableConcept", {}).get("text")

    if date and status:
        patient_status[patient_id].append((date, status))

# Sort each patient's timeline
for pid in patient_status:
    patient_status[pid].sort()

from datetime import datetime

def parse_dt(s):
    # works for "2022-07-30T00:00:00+00:00"
    return datetime.fromisoformat(s.replace("Z", "+00:00"))

ttr_months = []
for pid, timeline in patient_status.items():
    # find first NED and first recurrence after it
    ned_dates = [parse_dt(d) for d, s in timeline if s == "No evidence of disease"]
    rec_dates = [parse_dt(d) for d, s in timeline if s == "Recurrent disease"]
    if not ned_dates or not rec_dates:
        continue
    ned = min(ned_dates)
    rec_after = [r for r in rec_dates if r > ned]
    if not rec_after:
        continue
    rec = min(rec_after)
    months = (rec - ned).days / 30.44
    ttr_months.append(months)

if ttr_months:
    avg_ttr = sum(ttr_months) / len(ttr_months)
    results_append_marker = True
    # We'll append into results later after results list exists; store values in variables
    _ttr_summary = ["", "Time-to-Recurrence (from first NED):", f"Patients with computable TTR: {len(ttr_months)}", f"Mean TTR (months): {avg_ttr:.2f}", f"Median TTR (months): {sorted(ttr_months)[len(ttr_months)//2]:.2f}"]
else:
    _ttr_summary = []

# ---------- Load MedicationRequests (Treatment Exposure) ----------
mr_path = here / "data" / "phase3_medreq.json"
mr_bundle = load_json(mr_path)

has_immuno = defaultdict(bool)

for entry in mr_bundle.get("entry", []):
    mr = entry.get("resource", {})
    if mr.get("resourceType") != "MedicationRequest":
        continue

    subject = mr.get("subject", {}).get("reference", "")
    if not subject.startswith("Patient/"):
        continue

    patient_id = subject.split("/")[-1]
    med_text = mr.get("medicationCodeableConcept", {}).get("text", "").lower()

    if "immunotherapy" in med_text:
        has_immuno[patient_id] = True

# ---------- Compute recurrence + stratify ----------
total_patients = len(patient_status)

group_counts = {
    "chemo_only": {"n": 0, "recur": 0},
    "chemo_plus_immuno": {"n": 0, "recur": 0}
}

for pid, timeline in patient_status.items():
    statuses = [s for d, s in timeline]
    recurred = ("Recurrent disease" in statuses)

    if has_immuno[pid]:
        grp = "chemo_plus_immuno"
    else:
        grp = "chemo_only"

    group_counts[grp]["n"] += 1
    if recurred:
        group_counts[grp]["recur"] += 1

# ---------- Print results ----------
overall_recur = sum(1 for pid, tl in patient_status.items() if "Recurrent disease" in [s for d, s in tl])
overall_rate = (overall_recur / total_patients * 100) if total_patients else 0

results = []

results.append("=== Overall ===")
results.append(f"Total Patients: {total_patients}")
results.append(f"Patients with Recurrence: {overall_recur}")
results.append(f"Recurrence Rate (%): {round(overall_rate, 2)}")
results.append("")
results.append("=== By Treatment Exposure (structural demo) ===")

for grp in ["chemo_only", "chemo_plus_immuno"]:
    n = group_counts[grp]["n"]
    r = group_counts[grp]["recur"]
    rate = (r / n * 100) if n else 0
    results.append(f"{grp}: n={n}, recurrences={r}, recurrence_rate={rate:.2f}%")

# If we computed TTR, append its summary now
if '_ttr_summary' in globals() and _ttr_summary:
    results.extend(_ttr_summary)

# Write to file
with open("phase3_results.txt", "w", encoding="utf-8") as f:
    for line in results:
        f.write(line + "\n")

# Also print to console
for line in results:
    print(line)

```
##### Time-to-Recurrence (TTR)

Time-to-recurrence was computed as the interval between first documented “No evidence of disease” and subsequent “Recurrent disease” Observation.


Phase 3 – Longitudinal Outcome Analysis Using mCODE FHIR

#### Cohort Description

A simulated cohort of 200 breast cancer patients was generated using mCODE-aligned FHIR transaction bundles. Each patient included:

One Patient resource

Three time-indexed CancerDiseaseStatus Observations

Treatment exposure captured via MedicationRequest resources

Disease states were modeled longitudinally as:

Stable disease (baseline)

No evidence of disease (post-treatment)

Follow-up disease status (recurrent or persistent NED)

#### Recurrence Detection

Recurrence was programmatically identified by detecting the presence of a "Recurrent disease" Observation occurring after a documented "No evidence of disease" state.

Results:

Total Patients: 200

Patients with Recurrence: 60

Recurrence Rate: 30.0%

This endpoint was not stored as a static registry field but derived from sequential, time-indexed Observations.

#### Treatment Exposure Stratification

Patients were stratified based on MedicationRequest resources into:

Chemotherapy only (n = 100)

Chemotherapy plus immunotherapy (n = 100)

Recurrence stratification demonstrated that exposure-based outcome analysis can be computed directly from linked FHIR resources without schema redesign.

Observed group recurrence rates:

Chemo-only: 60.0%

Chemo + immunotherapy: 0.0%

Group differences reflect deterministic simulation logic and are not intended to model therapeutic efficacy. This experiment demonstrates analytic capability rather than treatment effect estimation.

#### Time-to-recurrence

##### Results:

Patients with computable TTR: 60

Mean TTR: 11.99 months

Median TTR: 11.99 months

This computation required:

Multiple time-stamped disease state Observations

Ordered event sequencing

Exposure-outcome linkage

Such event-based modeling is natively supported by mCODE’s FHIR resource architecture

#### Phase 3 Summary
##### Three levels of computability:

- Recurrence detection (derived endpoint)

- Exposure stratification (linked resources)

- Time-to-recurrence (true longitudinal event modeling)
