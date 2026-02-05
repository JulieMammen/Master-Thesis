# Phase 2 — mCODE FHIR Patient Bundles (Draft)

This folder contains draft HL7 FHIR R4 JSON Bundles representing registry-style breast cancer data transformed into mCODE-aligned resources.

## Structure
- `fhir/` — one Bundle JSON per patient (e.g., `patient-0985.bundle.json`)

## Notes / Assumptions (initial draft)
- Source dataset includes demographics, diagnosis date, ICD-10-CM site code, stage group, tumor size, grade, ER/PR/HER2, treatment flags (surgery/chemo/hormone/radiation), and disease_status.
- Exact treatment dates and medication agents are not available in the source extract; placeholder dates and free-text medication descriptions are used for Phase 2 and will be refined later.
- Validation using the HL7 FHIR Validator against the mCODE IG will be performed after initial commits.

## Next Steps
- Validate `patient-0985.bundle.json` against the mCODE IG.
- Iterate to resolve errors and document warnings.
- Scale from 1 patient bundle → 10 → 1000.
