"""
Generate FHIR R4 Bundles from the synthetic breast cancer registry CSV.

This script reads breast_registry_synth_1000.csv and writes one patient-level
Bundle per row. It fully supports the fields that actually exist in the CSV
(patient demographics, diagnosis, stage, tumor size, and the main breast
biomarkers). Fields that only appear in the broader 25-field NAACCR extract
are intentionally left out.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def safe_str(value: Any) -> str | None:
    """Return a cleaned string or None if the value is missing."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text if text else None


def map_gender(sex: Any) -> str:
    """Map the CSV sex values to FHIR gender codes."""
    text = safe_str(sex)
    if not text:
        return "unknown"
    text = text.lower()
    if text in {"female", "f"}:
        return "female"
    if text in {"male", "m"}:
        return "male"
    return "unknown"


def to_fhir_date(value: Any) -> str | None:
    """
    Accept either YYYY-MM-DD (already in the CSV) or YYYYMMDD.
    Return a FHIR date string or None.
    """
    text = safe_str(value)
    if not text:
        return None
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        return text
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return None


def cm_to_mm(value: Any) -> float | None:
    """Convert tumor size from cm to mm."""
    try:
        return float(value) * 10.0
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Resource builders
# ---------------------------------------------------------------------------

def build_patient(row: pd.Series) -> dict[str, Any]:
    """Create the Patient resource."""
    patient_id = safe_str(row.get("patient_id")) or "unknown"

    patient: dict[str, Any] = {
        "resourceType": "Patient",
        "id": f"patient-{patient_id}",
        "identifier": [{
            "system": "urn:naaccr:patient-id",
            "value": patient_id,
        }],
        "gender": map_gender(row.get("sex")),
    }

    # Optional race as a simple extension (kept light for the thesis)
    race = safe_str(row.get("race"))
    if race:
        patient["extension"] = [{
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
            "extension": [{
                "url": "text",
                "valueString": race,
            }],
        }]

    return patient


def build_condition(row: pd.Series, patient_id: str) -> dict[str, Any]:
    """Create the primary cancer Condition."""
    icd10 = safe_str(row.get("icd10_code")) or "C50.9"
    onset = to_fhir_date(row.get("date_diagnosed"))

    condition: dict[str, Any] = {
        "resourceType": "Condition",
        "id": f"condition-{patient_id}",
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active",
            }]
        },
        "code": {
            "coding": [{
                "system": "http://hl7.org/fhir/sid/icd-10-cm",
                "code": icd10,
                "display": f"Malignant neoplasm of breast ({icd10})",
            }],
            "text": f"Breast cancer ({icd10})",
        },
        "subject": {"reference": f"Patient/{patient_id}"},
    }

    if onset:
        condition["onsetDateTime"] = onset

    return condition


def build_stage_observation(row: pd.Series, patient_id: str) -> dict[str, Any] | None:
    """Stage group as a simple Observation."""
    stage = safe_str(row.get("stage_group"))
    if not stage:
        return None

    return {
        "resourceType": "Observation",
        "id": f"obs-stage-{patient_id}",
        "status": "final",
        "code": {"text": "Stage Group"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "valueCodeableConcept": {"text": stage},
    }


def build_tumor_size_observation(row: pd.Series, patient_id: str) -> dict[str, Any] | None:
    """Tumor size converted from cm to mm."""
    size_mm = cm_to_mm(row.get("tumor_size_cm"))
    if size_mm is None:
        return None

    return {
        "resourceType": "Observation",
        "id": f"obs-size-{patient_id}",
        "status": "final",
        "code": {"text": "Tumor Size"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "valueQuantity": {
            "value": size_mm,
            "unit": "mm",
            "system": "http://unitsofmeasure.org",
            "code": "mm",
        },
    }


def build_biomarker_observation(
    row: pd.Series,
    patient_id: str,
    csv_column: str,
    display_name: str,
) -> dict[str, Any] | None:
    """Generic helper for ER / PR / HER2 style results."""
    value = safe_str(row.get(csv_column))
    if not value:
        return None

    return {
        "resourceType": "Observation",
        "id": f"obs-{csv_column}-{patient_id}",
        "status": "final",
        "code": {"text": display_name},
        "subject": {"reference": f"Patient/{patient_id}"},
        "valueCodeableConcept": {"text": value},
    }


def build_oncotype_observation(row: pd.Series, patient_id: str) -> dict[str, Any] | None:
    """Oncotype DX score when present."""
    score = row.get("oncotype_dx_score")
    if score is None or (isinstance(score, float) and pd.isna(score)):
        return None

    try:
        numeric = float(score)
    except (TypeError, ValueError):
        return None

    return {
        "resourceType": "Observation",
        "id": f"obs-oncotype-{patient_id}",
        "status": "final",
        "code": {"text": "Oncotype DX Recurrence Score"},
        "subject": {"reference": f"Patient/{patient_id}"},
        "valueQuantity": {
            "value": numeric,
            "unit": "score",
        },
    }


# ---------------------------------------------------------------------------
# Bundle assembly
# ---------------------------------------------------------------------------

def create_bundle(row: pd.Series) -> dict[str, Any]:
    """Build a complete Bundle for one patient row."""
    patient_id = safe_str(row.get("patient_id")) or "unknown"

    resources: list[dict[str, Any]] = []

    # Patient
    resources.append(build_patient(row))

    # Condition
    resources.append(build_condition(row, patient_id))

    # Stage
    stage_obs = build_stage_observation(row, patient_id)
    if stage_obs:
        resources.append(stage_obs)

    # Tumor size
    size_obs = build_tumor_size_observation(row, patient_id)
    if size_obs:
        resources.append(size_obs)

    # Breast biomarkers
    for col, display in [
        ("er_status", "Estrogen Receptor Status"),
        ("pr_status", "Progesterone Receptor Status"),
        ("her2_status", "HER2 Status"),
    ]:
        obs = build_biomarker_observation(row, patient_id, col, display)
        if obs:
            resources.append(obs)

    # Oncotype
    onco = build_oncotype_observation(row, patient_id)
    if onco:
        resources.append(onco)

    return {
        "resourceType": "Bundle",
        "id": f"bundle-{patient_id}",
        "type": "collection",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "entry": [{"resource": r} for r in resources],
    }


# ---------------------------------------------------------------------------
# Simple internal validation
# ---------------------------------------------------------------------------

def validate_bundle(bundle: dict[str, Any]) -> list[str]:
    """Lightweight checks so we catch obvious problems early."""
    errors: list[str] = []

    if bundle.get("resourceType") != "Bundle":
        errors.append("resourceType must be Bundle")
    if not bundle.get("entry"):
        errors.append("Bundle has no entries")

    for i, entry in enumerate(bundle.get("entry", [])):
        resource = entry.get("resource") or {}
        rtype = resource.get("resourceType")

        if rtype == "Patient":
            if not resource.get("identifier"):
                errors.append(f"Patient entry {i} missing identifier")
        elif rtype == "Condition":
            if not resource.get("code"):
                errors.append(f"Condition entry {i} missing code")
            if not resource.get("subject"):
                errors.append(f"Condition entry {i} missing subject")
        elif rtype == "Observation":
            if not resource.get("code"):
                errors.append(f"Observation entry {i} missing code")
            if not resource.get("subject"):
                errors.append(f"Observation entry {i} missing subject")

    return errors


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate FHIR Bundles from the breast registry CSV"
    )
    parser.add_argument(
        "--input",
        default="breast_registry_synth_1000.csv",
        help="Path to the source CSV",
    )
    parser.add_argument(
        "--output",
        default="phase-2/fhir_generated",
        help="Directory where bundles will be written",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional limit on number of patients to process",
    )
    parser.add_argument(
        "--validate",
        metavar="BUNDLE_JSON",
        help="Validate an existing bundle file and exit",
    )
    args = parser.parse_args()

    # Validation-only mode
    if args.validate:
        path = Path(args.validate)
        bundle = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_bundle(bundle)
        if errors:
            print("Validation failed:")
            for e in errors:
                print(f"  - {e}")
        else:
            print("Validation passed.")
        return

    # Normal generation mode
    print(f"Reading {args.input} ...")
    df = pd.read_csv(args.input)

    if args.limit:
        df = df.head(args.limit)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating bundles for {len(df)} patients ...")
    success = 0

    for _, row in df.iterrows():
        bundle = create_bundle(row)
        errors = validate_bundle(bundle)

        patient_id = safe_str(row.get("patient_id")) or "unknown"
        out_file = output_dir / f"patient-{patient_id}.bundle.json"

        if errors:
            print(f"  Skipping {patient_id}: {errors}")
            continue

        out_file.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        success += 1

    print(f"Finished. {success} bundles written to {output_dir}")


if __name__ == "__main__":
    main()