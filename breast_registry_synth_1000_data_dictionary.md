
# Synthetic Breast Cancer Registry-Style Dataset (1000 patients)

**Purpose:** A registry-like, analysis-ready CSV for Phase 1/2 thesis work (NAACCR-style concepts).
**Notes:** Values are *synthetic* and sampled from plausible distributions (not real patients).

## Columns
- patient_id: 4-digit synthetic identifier
- age, sex, race
- date_diagnosed (YYYY-MM-DD)
- icd10_code (C50.*)
- stage_group (0, I, II, III, IV, Unknown)
- grade (1,2,3,9=Unknown)
- tumor_size_cm (0.1–10.0)
- er_status, pr_status, her2_status
- oncotype_dx_score (0–100; only for some HR+/HER2- early-stage)
- multigene_signature_method / risk
- neoadjuvant_therapy (Yes/No), neoadjuvant_response, residual_cancer_burden_rcb
- rx_summ_surg_prim_site, rx_summ_radiation, rx_summ_systemic_surg_seq
- chemo, hormone_therapy, targeted_therapy
- subtype_simulated (HR+/HER2-, HER2+, TNBC, Unknown) – helper field for sanity checks
