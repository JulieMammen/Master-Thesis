# NAACCR → FHIR / mCODE Crosswalk

**Project:** Modernizing Cancer Registry Data with FHIR mCODE  
**Source extract:** `NAACCR_core_fields_1000_tumors.xlsx` (25 fields)  
**Version:** 1.1  
**Date:** 2026-09-06  
**Target standards:** HL7 FHIR R4, mCODE STU4, US Core

---

## Overview

This crosswalk translates the current NAACCR synthetic extract into a FHIR R4 representation aligned with mCODE STU4 and US Core. The intent is to keep the mapping clinically meaningful, traceable to the source registry field, and implementable in a breast-cancer-focused pipeline without overusing unsupported or non-standard structures.

The mapping strategy is:
- use US Core and mCODE profiles where they already exist for patient, condition, and tumor marker concepts
- model site-specific or non-standard cancer variables as `Observation` resources when a dedicated profile does not exist
- keep raw NAACCR codes as supplemental coding when needed to preserve source fidelity

---

## Crosswalk Table

| # | NAACCR Field | Level | Suggested FHIR Resource / Element | Recommended Profile | Mapping Guidance |
|---|--------------|-------|-----------------------------------|---------------------|------------------|
| 1 | `patientIdNumber` | Patient | `Patient.identifier` | US Core Patient or mCODE Cancer Patient | Use a project-specific identifier system such as `urn:naaccr:patient-id` or an institutional OID. |
| 2 | `sexAssignedAtBirth` | Patient | `Patient.gender` and/or US Core sex extension | US Core Patient / mCODE Cancer Patient | NAACCR values are typically 1 = male, 2 = female. If the source has nonbinary/unknown values, retain them in an extension or additional coding rather than forcing a value. |
| 3 | `race1` | Patient | `Patient.extension` (US Core Race) | US Core Patient | Map NAACCR race categories to CDC/US Core race concepts; retain the original code as additional coding if needed. |
| 4 | `dateOfBirth` | Patient | `Patient.birthDate` | US Core Patient / mCODE Cancer Patient | Convert `YYYYMMDD` to FHIR `date`. |
| 5 | `vitalStatus` | Patient | `Patient.deceasedBoolean` and optional `Observation` | mCODE Cancer Disease Status when longitudinal tracking is needed | Use `deceasedBoolean = false` for alive and `true` for deceased/other non-alive status. Prefer `Observation` for detailed status tracking over time. |
| 6 | `dateOfLastContact` | Patient | `Patient.deceasedDateTime` or `Observation.effectiveDateTime` | Same as vital status | Pair with `vitalStatus` to interpret the meaning of last contact accurately. |
| 7 | `tumorRecordNumber` | Tumor | `Condition.identifier` or a custom linking extension | mCODE Primary Cancer Condition | This distinguishes multiple primary tumors for the same patient. It is not a patient-level identifier alone. |
| 8 | `primarySite` | Tumor | `Condition.code` | mCODE Primary Cancer Condition | Use ICD-O-3 topography coding (for example C50.* for breast, C61.9 for prostate). |
| 9 | `histologicTypeIcdO3` | Tumor | `Condition.extension` or additional morphology coding within the condition | mCODE Primary Cancer Condition | Store as ICD-O-3 morphology; if the profile permits, include it in an extension or supplemental coding. |
| 10 | `behaviorCodeIcdO3` | Tumor | `Condition.extension` or `Condition.clinicalStatus` as appropriate | mCODE Primary Cancer Condition | Values such as 2 = in situ, 3 = malignant should be preserved with explicit terminology, not inferred only from the condition. |
| 11 | `ageAtDiagnosis` | Tumor | Derived value; not usually a primary FHIR field | mCODE Primary Cancer Condition | Prefer calculating age from `Patient.birthDate` and `dateOfDiagnosis` rather than storing a redundant field. |
| 12 | `dateOfDiagnosis` | Tumor | `Condition.onsetDateTime` | mCODE Primary Cancer Condition | Convert `YYYYMMDD` to FHIR `dateTime`. |
| 13 | `summaryStage2018` | Tumor | `Observation` or `CancerStageGroup`-style staging profile | mCODE Cancer Stage / Observation | Use a coded stage concept tied to SEER Summary Stage 2018; preserve original code in a secondary coding element. |
| 14 | `tumorSizeSummary` | Tumor | `Observation` with `valueQuantity` | mCODE Tumor Size | Represent size in mm with a unit of `mm`; retain original summary text if present and not fully codified. |
| 15 | `gleasonScoreClinical` | Prostate | `Observation` | Observation / future mCODE extension | Clinical Gleason score should remain a coded or numeric observation, not a patient attribute. |
| 16 | `gleasonScorePathological` | Prostate | `Observation` | Observation | Same pattern as clinical Gleason score, with a clear observational context. |
| 17 | `psaLabValue` | Prostate | `Observation` with `valueQuantity` | Observation / tumor-marker style profile | Record PSA value and unit (for example ng/mL or `mg/L`, depending on source). |
| 18 | `estrogenReceptorSummary` | Breast | `Observation` | mCODE Tumor Marker Test | ER summary is a high-priority biomarker and should be modeled as a structured tumor marker test. |
| 19 | `progesteroneRecepSummary` | Breast | `Observation` | mCODE Tumor Marker Test | Same pattern as ER; preserve result status and interpretation. |
| 20 | `her2OverallSummary` | Breast | `Observation` | mCODE Tumor Marker Test | HER2 overall result is a standard mCODE tumor marker use case. |
| 21 | `ki67` | Breast | `Observation` with `valueQuantity` or coded result | mCODE Tumor Marker Test | Usually expressed as a percentage; include unit `%` and interpretation when available. |
| 22 | `oncotypeDxRecurrenceScoreInvasiv` | Breast | `Observation` or Genomic Variant / genomic assessment object | mCODE Genomic Variant or Tumor Marker Test | Best modeled as a genomic or biomarker assessment. Preserve the original Oncotype score and methodology. |
| 23 | `breslowTumorThickness` | Melanoma | `Observation` with `valueQuantity` | Observation | Model as numeric `mm` thickness with explicit clinical context. |
| 24 | `figoStage` | Gynecologic | `Observation` or staging profile | Observation / Cancer Stage | FIGO stage is typically represented as a coded stage value and should be linked to the relevant tumor condition. |
| 25 | `mitoticRateMelanoma` | Melanoma | `Observation` | Observation | Record as a numeric value plus units when available; often reported per square mm. |

---

## Prioritization for Implementation

### Breast-focused priority order
These fields are the strongest candidates for initial implementation in the current project:
1. `estrogenReceptorSummary`
2. `progesteroneRecepSummary`
3. `her2OverallSummary`
4. `ki67`
5. `oncotypeDxRecurrenceScoreInvasiv`
6. `primarySite`
7. `dateOfDiagnosis`
8. `tumorSizeSummary`
9. `summaryStage2018`

### Site-specific fields
Fields 15–17 (prostate), 23 and 25 (melanoma), and 24 (gynecologic) are only populated when the corresponding primary site applies. For this project, they should be modeled as generic `Observation` resources unless a site-specific profile is added later.

---

## Mapping Principles

### 1. Preserve source meaning
NAACCR codes should not be discarded if they carry diagnostic semantics that are not fully represented in a standard FHIR code system.

### 2. Prefer standard oncology semantics
Use the most specific clinically meaningful structure available in mCODE or US Core before falling back to generic `Observation`.

### 3. Separate patient, tumor, and biomarker facts
Patient demographics belong on `Patient`; cancer facts belong on `Condition` or staging/marker `Observation`s; laboratory and assay values belong on `Observation` with an appropriate code and unit.

### 4. Keep the mapping auditable
Every translated field should retain traceability back to the original NAACCR variable name and source code when possible.

---

## Detailed Implementation Matrix

This matrix is intended to be the technical specification for the Python conversion layer. It is more explicit than the quick crosswalk and can be used as the source of truth for a generator that reads each NAACCR field and emits the corresponding FHIR element.

| NAACCR field | Resource | FHIR element path | Profile | FHIR type | Transform rule | Notes |
|--------------|----------|------------------|---------|-----------|----------------|-------|
| `patientIdNumber` | `Patient` | `Patient.identifier[0].value` | US Core Patient / mCODE Cancer Patient | `string` | Set identifier value directly | Use a project-specific identifier system, for example `urn:naaccr:patient-id` |
| `sexAssignedAtBirth` | `Patient` | `Patient.gender` | US Core Patient / mCODE Cancer Patient | `code` | `1 -> male`, `2 -> female`; unknown remains `unknown` | Preserve source value as additional coding if needed |
| `race1` | `Patient` | `Patient.extension:race` | US Core Patient | `Coding` | Map to CDC/US Core race code | Keep original NAACCR race code as supplemental information |
| `dateOfBirth` | `Patient` | `Patient.birthDate` | US Core Patient / mCODE Cancer Patient | `date` | `YYYYMMDD -> YYYY-MM-DD` | Required for age derivation |
| `vitalStatus` | `Patient` | `Patient.deceasedBoolean` | US Core Patient / mCODE Cancer Disease Status | `boolean` | `alive -> false`, other statuses -> `true` | Use longitudinal `Observation` when detailed status is needed |
| `dateOfLastContact` | `Patient` or `Observation` | `Patient.deceasedDateTime` or `Observation.effectiveDateTime` | Same as vital status | `dateTime` | Convert to FHIR dateTime | Pair with `vitalStatus` for interpretation |
| `tumorRecordNumber` | `Condition` | `Condition.identifier[0].value` | mCODE Primary Cancer Condition | `string` | Copy directly | Useful for multiple primaries in the same patient |
| `primarySite` | `Condition` | `Condition.code` | mCODE Primary Cancer Condition | `CodeableConcept` | Map ICD-O-3 topography code | For example: `C50.*` breast, `C61.9` prostate |
| `histologicTypeIcdO3` | `Condition` | `Condition.extension` or `Condition.code` additional coding | mCODE Primary Cancer Condition | `Coding` | Preserve morphology coding | Keep original ICD-O-3 value if not represented in standard profile fields |
| `behaviorCodeIcdO3` | `Condition` | `Condition.extension` or `Condition.clinicalStatus` | mCODE Primary Cancer Condition | `Coding` | Map in situ / malignant states explicitly | Value 2 and 3 deserve explicit display text |
| `ageAtDiagnosis` | `Condition` | derived value | mCODE Primary Cancer Condition | `integer` | `year(diagnosis) - year(birth)` | Prefer derivation rather than storing redundant data |
| `dateOfDiagnosis` | `Condition` | `Condition.onsetDateTime` | mCODE Primary Cancer Condition | `dateTime` | `YYYYMMDD -> YYYY-MM-DDT00:00:00` | This is the canonical diagnosis date |
| `summaryStage2018` | `Observation` | `Observation.valueCodeableConcept` | mCODE Cancer Stage / Observation | `CodeableConcept` | Map to SEER Summary Stage 2018 coding | Preserve original registry code in supplemental coding |
| `tumorSizeSummary` | `Observation` | `Observation.valueQuantity` | mCODE Tumor Size | `Quantity` | Convert to `mm` quantity | Use unit `mm` and retain original text if necessary |
| `gleasonScoreClinical` | `Observation` | `Observation.valueInteger` | Observation / future mCODE extension | `integer` | Copy numerical value | Tie to the relevant prostate condition |
| `gleasonScorePathological` | `Observation` | `Observation.valueInteger` | Observation | `integer` | Copy numerical value | Same pattern as clinical Gleason |
| `psaLabValue` | `Observation` | `Observation.valueQuantity` | Observation / tumor-marker style profile | `Quantity` | Copy value and unit | Preserve source units as reported by the lab |
| `estrogenReceptorSummary` | `Observation` | `Observation.valueCodeableConcept` | mCODE Tumor Marker Test | `CodeableConcept` | Map to positive/negative/indeterminate categories | High-priority breast biomarker |
| `progesteroneRecepSummary` | `Observation` | `Observation.valueCodeableConcept` | mCODE Tumor Marker Test | `CodeableConcept` | Map to positive/negative/indeterminate categories | High-priority breast biomarker |
| `her2OverallSummary` | `Observation` | `Observation.valueCodeableConcept` | mCODE Tumor Marker Test | `CodeableConcept` | Map to positive/negative/indeterminate categories | High-priority breast biomarker |
| `ki67` | `Observation` | `Observation.valueQuantity` | mCODE Tumor Marker Test | `Quantity` | Convert to percentage quantity | Use `%` unit when available |
| `oncotypeDxRecurrenceScoreInvasiv` | `Observation` or `GenomicVariant` | `Observation.valueQuantity` or `GenomicVariant` | mCODE Genomic Variant or Tumor Marker Test | `Quantity` | Copy score and preserve methodology metadata | Retain the original assay name and score |
| `breslowTumorThickness` | `Observation` | `Observation.valueQuantity` | Observation | `Quantity` | Convert to `mm` quantity | Link to melanoma condition |
| `figoStage` | `Observation` | `Observation.valueCodeableConcept` | Observation / Cancer Stage | `CodeableConcept` | Map to coded FIGO stage | Link to gynecologic tumor condition |
| `mitoticRateMelanoma` | `Observation` | `Observation.valueQuantity` | Observation | `Quantity` | Capture numeric value and unit | Use explicit unit when available |

### Conversion responsibilities for the generator
- Convert all date fields from `YYYYMMDD` to FHIR date/dateTime formats.
- Preserve raw source values in extension or supplemental coding when the standard code set does not capture the exact NAACCR meaning.
- Keep observation `code`, `subject`, and `focus` linked to the same patient and tumor condition.
- Use `Observation` for any biomarker, stage, or site-specific variable not modeled directly by a more specific mCODE profile.

---

## Open Items / Future Work

- finalize exact value-set mappings for race, stage, and biomarker summaries
- decide whether `vitalStatus` should be represented only on `Patient` or alongside a longitudinal `Observation` or condition-based disease status profile
- add treatment-related resources in a later iteration when the extract expands beyond the current 25-field dataset
- validate the final mapping against real NAACCR coding conventions and the exact field definitions in the source spreadsheet

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-09-06 | Refined mapping language, clarified implementation priorities, and tightened FHIR/mCODE recommendations for breast cancer fields |
| 1.0 | 2026-09-06 | Initial crosswalk for all 25 fields |
