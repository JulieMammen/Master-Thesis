# Phase 2: Registry to mCODE FHIR

Phase 2 operationalizes the transformation of the synthetic breast cancer
registry into patient-level HL7 FHIR R4 Bundles aligned with the mCODE model.

## Inputs

- `breast_registry_synth_1000.csv`: 1,000 synthetic records with no PHI
- `breast_registry_synth_1000_data_dictionary.md`: source field definitions
- `docs/NAACCR_to_mCODE_crosswalk.md`: mapping specification
- `scripts/naaccr_fhir_mapping.py`: generator and internal validator

The generator uses the CSV's actual column names, including `patient_id`,
`sex`, `date_diagnosed`, `icd10_code`, `stage_group`, `tumor_size_cm`,
`er_status`, `pr_status`, `her2_status`, and `oncotype_dx_score`.

## Generated Resources

Each patient Bundle contains:

- `Patient` with a synthetic NAACCR identifier and normalized gender
- `Condition` with ICD-10-CM breast cancer coding and diagnosis date
- `Observation` for stage group when present
- `Observation` for tumor size, converted from centimeters to millimeters
- `Observation` resources for ER, PR, HER2, and Oncotype DX when present

## Generate Bundles

Run these commands from the repository root. Start with 10 records:

```powershell
python scripts/naaccr_fhir_mapping.py `
  --input breast_registry_synth_1000.csv `
  --output phase-2/fhir_generated `
  --limit 10
```

Generate all 1,000 records by omitting `--limit 10`:

```powershell
python scripts/naaccr_fhir_mapping.py `
  --input breast_registry_synth_1000.csv `
  --output phase-2/fhir_generated
```

The output directory is generated build output and is excluded from Git.

## Validate Bundles

Every generated Bundle is checked by `validate_bundle` before it is written.
To validate one existing Bundle directly:

```powershell
python scripts/naaccr_fhir_mapping.py `
  --validate phase-2/fhir_generated/patient-0001.bundle.json
```

The complete synthetic cohort has been generated successfully, and the first
and last generated Bundles pass the internal validation checks. The next
quality step is external validation with the HL7 FHIR Validator and the US
mCODE Implementation Guide.

## Limitations

The source extract does not provide treatment agent names or treatment dates,
so this generator does not create medication or procedure resources. Treatment
flags remain available in the source CSV for later modeling. The generated
stage and biomarker values currently preserve source text; terminology binding
and profile-level mCODE validation are subsequent refinement steps.
