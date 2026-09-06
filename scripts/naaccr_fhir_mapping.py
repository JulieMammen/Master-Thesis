"""NAACCR to FHIR implementation mapping for the breast cancer project.

This module provides a field-level mapping dictionary and helper functions that can
be used to build FHIR resources from an NAACCR-style record.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VALID_PATIENT_GENDERS = {"male", "female", "other", "unknown"}
VALID_OBSERVATION_STATUS = {"registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"}


def _is_valid_date(value: Any) -> bool:
    if value in (None, ""):
        return False
    value_str = str(value).strip()
    if len(value_str) == 10 and value_str[4] == "-" and value_str[7] == "-":
        try:
            from datetime import datetime
            datetime.strptime(value_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    return False


def _is_valid_datetime(value: Any) -> bool:
    if value in (None, ""):
        return False
    value_str = str(value).strip()
    if value_str.endswith("Z"):
        value_str = value_str[:-1] + "+00:00"
    try:
        from datetime import datetime
        datetime.fromisoformat(value_str)
        return True
    except ValueError:
        return False


def validate_bundle(bundle: dict[str, Any]) -> list[str]:
    """Return a list of validation errors for a FHIR bundle.

    This is intentionally strict enough for the thesis project: it checks the
    bundle structure, the core patient/condition/observation elements, and the
    essential mCODE/US Core semantics used by the NAACCR mapping.
    """
    errors: list[str] = []

    if not isinstance(bundle, dict):
        return ["Bundle must be a JSON object."]

    if bundle.get("resourceType") != "Bundle":
        errors.append("Bundle.resourceType must be 'Bundle'.")

    if bundle.get("type") not in {"collection", "searchset", "batch", "transaction", "history", "document"}:
        errors.append("Bundle.type must be a valid FHIR bundle type.")

    entries = bundle.get("entry") or []
    if not isinstance(entries, list) or not entries:
        errors.append("Bundle.entry must be a non-empty list.")

    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"Bundle.entry[{index}] must be an object.")
            continue

        resource = entry.get("resource")
        if not isinstance(resource, dict):
            errors.append(f"Bundle.entry[{index}].resource is missing.")
            continue

        rtype = resource.get("resourceType")
        if rtype == "Patient":
            if not resource.get("identifier"):
                errors.append(f"Patient {resource.get('id', index)} is missing identifier.")
            else:
                ident = resource["identifier"][0]
                if not ident.get("system"):
                    errors.append(f"Patient {resource.get('id', index)} identifier.system is required.")
                if not ident.get("value"):
                    errors.append(f"Patient {resource.get('id', index)} identifier.value is required.")
            gender = resource.get("gender")
            if gender is not None and gender not in VALID_PATIENT_GENDERS:
                errors.append(f"Patient {resource.get('id', index)} has invalid gender: {gender}")
            birth_date = resource.get("birthDate")
            if birth_date is not None and not _is_valid_date(birth_date):
                errors.append(f"Patient {resource.get('id', index)} birthDate is not valid: {birth_date}")
            if resource.get("deceasedBoolean") is True and resource.get("deceasedDateTime") is None:
                errors.append(f"Patient {resource.get('id', index)} is marked deceased but has no deceasedDateTime.")

        elif rtype == "Condition":
            if not resource.get("subject") or not resource["subject"].get("reference"):
                errors.append(f"Condition {resource.get('id', index)} is missing subject.reference.")
            code = resource.get("code")
            if not code:
                errors.append(f"Condition {resource.get('id', index)} is missing code.")
            else:
                coding = code.get("coding") or []
                text = code.get("text")
                if not coding and not text:
                    errors.append(f"Condition {resource.get('id', index)} code must include coding or text.")
            onset = resource.get("onsetDateTime")
            if onset is not None and not _is_valid_datetime(onset):
                errors.append(f"Condition {resource.get('id', index)} onsetDateTime is invalid: {onset}")

        elif rtype == "Observation":
            status = resource.get("status")
            if status not in VALID_OBSERVATION_STATUS:
                errors.append(f"Observation {resource.get('id', index)} has invalid status: {status}")
            if not resource.get("code"):
                errors.append(f"Observation {resource.get('id', index)} is missing code.")
            if not resource.get("subject") or not resource["subject"].get("reference"):
                errors.append(f"Observation {resource.get('id', index)} is missing subject.reference.")

            value_present = any(
                key in resource for key in ("valueQuantity", "valueCodeableConcept", "valueString", "valueInteger", "valueBoolean", "valueDateTime", "valueRange")
            )
            if not value_present:
                errors.append(f"Observation {resource.get('id', index)} must include one value field.")

            if "valueQuantity" in resource:
                qty = resource["valueQuantity"]
                if qty.get("value") is None:
                    errors.append(f"Observation {resource.get('id', index)} valueQuantity.value is required.")
                if qty.get("unit") in (None, "") and qty.get("code") in (None, ""):
                    errors.append(f"Observation {resource.get('id', index)} valueQuantity requires unit or code.")

            if "valueCodeableConcept" in resource:
                vcc = resource["valueCodeableConcept"]
                if not (vcc.get("coding") or vcc.get("text")):
                    errors.append(f"Observation {resource.get('id', index)} valueCodeableConcept is incomplete.")

        else:
            # This is intentionally strict for the thesis scope; we allow only the resources we intentionally emit.
            errors.append(f"Unsupported resource type in bundle: {rtype}")

    return errors


def validate_bundle_file(bundle_path: str | Path) -> tuple[bool, list[str]]:
    path = Path(bundle_path)
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False, [f"Bundle file not found: {path}"]
    except json.JSONDecodeError as exc:
        return False, [f"Invalid JSON in {path}: {exc.msg}"]

    errors = validate_bundle(bundle)
    return len(errors) == 0, errors


# Existing helper code continues below.

FIELD_MAPPING = {
    "patientIdNumber": {
        "resource": "Patient",
        "element": "Patient.identifier.value",
        "profile": "US Core Patient or mCODE Cancer Patient",
        "type": "string",
        "transform": "identity",
        "notes": "Use a project-specific identifier system such as urn:naaccr:patient-id.",
    },
    "sexAssignedAtBirth": {
        "resource": "Patient",
        "element": "Patient.gender",
        "profile": "US Core Patient / mCODE Cancer Patient",
        "type": "code",
        "transform": "map_gender",
        "notes": "1 = male, 2 = female; preserve unknown values in extensions when needed.",
    },
    "race1": {
        "resource": "Patient",
        "element": "Patient.extension:race",
        "profile": "US Core Patient",
        "type": "Coding",
        "transform": "map_race",
        "notes": "Map to CDC/US Core race value set with original NAACCR code retained as supplemental coding.",
    },
    "dateOfBirth": {
        "resource": "Patient",
        "element": "Patient.birthDate",
        "profile": "US Core Patient / mCODE Cancer Patient",
        "type": "date",
        "transform": "to_fhir_date",
        "notes": "Convert YYYYMMDD to FHIR date.",
    },
    "vitalStatus": {
        "resource": "Patient",
        "element": "Patient.deceasedBoolean",
        "profile": "US Core Patient / mCODE Cancer Disease Status",
        "type": "boolean",
        "transform": "to_deceased_boolean",
        "notes": "Use deceasedBoolean for a simple status and Observation when longitudinal tracking is needed.",
    },
    "dateOfLastContact": {
        "resource": "Patient",
        "element": "Patient.deceasedDateTime or Observation.effectiveDateTime",
        "profile": "Same as vital status",
        "type": "dateTime",
        "transform": "to_fhir_datetime",
        "notes": "Pair with vital status for interpretation.",
    },
    "tumorRecordNumber": {
        "resource": "Condition",
        "element": "Condition.identifier",
        "profile": "mCODE Primary Cancer Condition",
        "type": "Identifier",
        "transform": "identity",
        "notes": "Use to distinguish multiple primary tumors for the same patient.",
    },
    "primarySite": {
        "resource": "Condition",
        "element": "Condition.code",
        "profile": "mCODE Primary Cancer Condition",
        "type": "CodeableConcept",
        "transform": "map_icdo_topography",
        "notes": "Use ICD-O-3 topography coding such as C50.* for breast.",
    },
    "histologicTypeIcdO3": {
        "resource": "Condition",
        "element": "Condition.extension or morphology coding",
        "profile": "mCODE Primary Cancer Condition",
        "type": "Coding",
        "transform": "identity",
        "notes": "Store as morphology coding with original source code retained.",
    },
    "behaviorCodeIcdO3": {
        "resource": "Condition",
        "element": "Condition.extension or Condition.clinicalStatus",
        "profile": "mCODE Primary Cancer Condition",
        "type": "Coding",
        "transform": "map_behavior_code",
        "notes": "Preserve distinctions such as in situ vs malignant.",
    },
    "ageAtDiagnosis": {
        "resource": "Condition",
        "element": "derived value",
        "profile": "mCODE Primary Cancer Condition",
        "type": "integer",
        "transform": "calculate_age_at_diagnosis",
        "notes": "Prefer computation from Patient.birthDate and dateOfDiagnosis.",
    },
    "dateOfDiagnosis": {
        "resource": "Condition",
        "element": "Condition.onsetDateTime",
        "profile": "mCODE Primary Cancer Condition",
        "type": "dateTime",
        "transform": "to_fhir_datetime",
        "notes": "Convert YYYYMMDD to FHIR dateTime.",
    },
    "summaryStage2018": {
        "resource": "Observation",
        "element": "Observation.valueCodeableConcept",
        "profile": "mCODE Cancer Stage or Observation",
        "type": "CodeableConcept",
        "transform": "map_summary_stage",
        "notes": "Use SEER Summary Stage 2018 and keep original NAACCR code in supplemental coding.",
    },
    "tumorSizeSummary": {
        "resource": "Observation",
        "element": "Observation.valueQuantity",
        "profile": "mCODE Tumor Size",
        "type": "Quantity",
        "transform": "to_mm_quantity",
        "notes": "Represent value in mm with unit mm.",
    },
    "gleasonScoreClinical": {
        "resource": "Observation",
        "element": "Observation.valueInteger",
        "profile": "Observation / future mCODE extension",
        "type": "integer",
        "transform": "identity",
        "notes": "Clinical Gleason score remains an observation tied to the relevant tumor condition.",
    },
    "gleasonScorePathological": {
        "resource": "Observation",
        "element": "Observation.valueInteger",
        "profile": "Observation",
        "type": "integer",
        "transform": "identity",
        "notes": "Model similarly to clinical Gleason score.",
    },
    "psaLabValue": {
        "resource": "Observation",
        "element": "Observation.valueQuantity",
        "profile": "Observation / tumor-marker style profile",
        "type": "Quantity",
        "transform": "to_quantity_with_unit",
        "notes": "Preserve unit and value as reported by the lab.",
    },
    "estrogenReceptorSummary": {
        "resource": "Observation",
        "element": "Observation.valueCodeableConcept",
        "profile": "mCODE Tumor Marker Test",
        "type": "CodeableConcept",
        "transform": "map_biomarker_result",
        "notes": "High-priority breast biomarker. Use coded result with interpretation when available.",
    },
    "progesteroneRecepSummary": {
        "resource": "Observation",
        "element": "Observation.valueCodeableConcept",
        "profile": "mCODE Tumor Marker Test",
        "type": "CodeableConcept",
        "transform": "map_biomarker_result",
        "notes": "Same pattern as estrogen receptor summary.",
    },
    "her2OverallSummary": {
        "resource": "Observation",
        "element": "Observation.valueCodeableConcept",
        "profile": "mCODE Tumor Marker Test",
        "type": "CodeableConcept",
        "transform": "map_biomarker_result",
        "notes": "HER2 overall result is a standard oncology biomarker observation.",
    },
    "ki67": {
        "resource": "Observation",
        "element": "Observation.valueQuantity",
        "profile": "mCODE Tumor Marker Test",
        "type": "Quantity",
        "transform": "to_percentage_quantity",
        "notes": "Usually expressed as a percentage. Include unit % when available.",
    },
    "oncotypeDxRecurrenceScoreInvasiv": {
        "resource": "Observation",
        "element": "Observation.valueQuantity or GenomicVariant",
        "profile": "mCODE Genomic Variant or Tumor Marker Test",
        "type": "Quantity or GenomicVariant",
        "transform": "to_numeric_score",
        "notes": "Retain original Oncotype score and methodology alongside the FHIR value.",
    },
    "breslowTumorThickness": {
        "resource": "Observation",
        "element": "Observation.valueQuantity",
        "profile": "Observation",
        "type": "Quantity",
        "transform": "to_mm_quantity",
        "notes": "Model as numeric mm thickness with explicit clinical context.",
    },
    "figoStage": {
        "resource": "Observation",
        "element": "Observation.valueCodeableConcept",
        "profile": "Observation / Cancer Stage",
        "type": "CodeableConcept",
        "transform": "map_figo_stage",
        "notes": "Use a coded stage value and link to the relevant tumor condition.",
    },
    "mitoticRateMelanoma": {
        "resource": "Observation",
        "element": "Observation.valueQuantity",
        "profile": "Observation",
        "type": "Quantity",
        "transform": "to_quantity_with_unit",
        "notes": "Often reported per square mm; preserve unit and interpretation if available.",
    },
}


def to_fhir_date(value: Any) -> str | None:
    if value in (None, ""):
        return None
    value_str = str(value).strip()
    if len(value_str) == 8 and value_str.isdigit():
        return f"{value_str[0:4]}-{value_str[4:6]}-{value_str[6:8]}"
    return value_str


def to_fhir_datetime(value: Any) -> str | None:
    formatted = to_fhir_date(value)
    if formatted is None:
        return None
    return formatted + "T00:00:00"


def to_deceased_boolean(value: Any) -> bool:
    if value is None:
        return False
    return str(value).strip().upper() not in {"0", "", "ALIVE", "A"}


def map_gender(value: Any) -> str:
    mapping = {"1": "male", "2": "female"}
    return mapping.get(str(value).strip(), "unknown")


def to_mm_quantity(value: Any, unit: str = "mm") -> dict[str, Any]:
    return {
        "value": float(value),
        "unit": unit,
        "system": "http://unitsofmeasure.org",
        "code": unit,
    }


def to_percentage_quantity(value: Any) -> dict[str, Any]:
    return {
        "value": float(value),
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%",
    }


def to_quantity_with_unit(value: Any, unit: str = "") -> dict[str, Any]:
    returned_unit = unit or ""
    return {
        "value": float(value),
        "unit": returned_unit,
        "system": "http://unitsofmeasure.org" if returned_unit else None,
        "code": returned_unit,
    }


def calculate_age_at_diagnosis(date_of_birth: Any, date_of_diagnosis: Any) -> int | None:
    dob = to_fhir_date(date_of_birth)
    dod = to_fhir_date(date_of_diagnosis)
    if dob is None or dod is None:
        return None
    try:
        birth_year = int(dob[0:4])
        diag_year = int(dod[0:4])
        return diag_year - birth_year
    except (TypeError, ValueError):
        return None


def build_patient_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "identifier": [{
            "system": "urn:naaccr:patient-id",
            "value": record.get("patientIdNumber")
        }],
        "gender": map_gender(record.get("sexAssignedAtBirth")),
        "birthDate": to_fhir_date(record.get("dateOfBirth")),
        "deceasedBoolean": to_deceased_boolean(record.get("vitalStatus")),
    }


def build_condition_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "resourceType": "Condition",
        "code": {
            "text": record.get("primarySite")
        },
        "onsetDateTime": to_fhir_datetime(record.get("dateOfDiagnosis")),
    }
