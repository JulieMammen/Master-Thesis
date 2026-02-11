# Phase 2 — mCODE FHIR Patient Bundles 

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
# Phase 2 — Registry → mCODE FHIR Generation & Validation

## Overview
This phase operationalizes registry-to-mCODE transformation at scale.

Using a synthetic NAACCR-style breast cancer dataset (`breast_registry_synth_1000.csv`), patient-level FHIR Bundles were generated using a Python script and validated using the HL7 FHIR Validator CLI against the HL7 US mCODE Implementation Guide.

## Inputs
- Source dataset: `breast_registry_synth_1000.csv`
- Data dictionary: `breast_registry_synth_1000_data_dictionary.md`

## Bundle Generation

### Script
- `phase-2/scripts/generate_mcode_bundles.py`

### Validate one Bundle
```
"C:\Users\julie\AppData\Local\Programs\Eclipse Adoptium\jdk-25.0.2.10-hotspot\bin\java.exe" `
  -jar tools/validator_cli.jar `
  phase-2\fhir_generated\patient-0001.bundle.json `
  -version 4.0.1 `
  -ig hl7.fhir.us.mcode#4.0.0
  ```
  ### Validate a batch of 25
  ```

New-Item -ItemType Directory -Force phase-2\validation\mcode_ig\logs2 | Out-Null

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

