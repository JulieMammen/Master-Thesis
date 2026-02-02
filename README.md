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
Week 1: Crosswalk development (NAACCR → mCODE)

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
