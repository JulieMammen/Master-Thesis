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
```sql
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
### Phase 1 Conclusion

Traditional registry data performs well for retrospective descriptive analysis, but struggles with:

Longitudinal disease tracking

Explicit subtype representation

Treatment intent and sequencing

Reusability across analytic contexts

These limitations motivate the transformation of the same clinical facts into FHIR mCODE, which is explored in subsequent phases
