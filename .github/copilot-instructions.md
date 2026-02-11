<!-- .github/copilot-instructions.md -->
# Copilot instructions — Master-Thesis repository

Purpose: give an AI coding agent the minimum, actionable knowledge to be productive in this repo.

- Big picture
  - This project transforms a synthetic NAACCR-style cancer registry into FHIR mCODE bundles and compares analytic capabilities.
  - Two primary representations live here:
    - Relational/registry-style CSV + Postgres table: `breast_registry_synth_1000.csv`, schema & notes in `breast_registry_synth_1000_data_dictionary.md` and the `breast_registry` table described in `README.md`.
    - mCODE FHIR JSON Bundles: `phase-2/fhir/*.bundle.json` (sample: `phase-2/fhir/patient-0985.bundle.json`).

- Key files / directories (use these as anchors when changing behavior)
  - `README.md` — project overview, Postgres details (DB: `thesis_registry`, port: `5434`).
  - `breast_registry_synth_1000.csv` and `breast_registry_synth_1000_data_dictionary.md` — canonical source CSV + data dictionary.
  - `phase-2/` — mCODE work: `phase-2/fhir/` contains sample patient bundles and resource examples (`obs-er.json`, `obs-her2.json`, `procedure-surgery.json`, etc.).
  - `tools/validator_cli.jar` — local copy of the HL7 FHIR validator used to validate mCODE bundles (see Phase 2 README notes).

- Architectural/flow notes an agent should know
  - Source-of-truth is the flat registry CSV / Postgres `breast_registry` table. Transformation code (not present here) should map row-level fields into an mCODE FHIR Bundle per patient.
  - Phase 2 bundles intentionally use placeholder dates and free-text medications where the original extract lacks structured medication agents or exact dates. Expect validation warnings/errors until placeholders are refined.
  - Some project-specific renames and fields are used in the data model (documented in `README.md`): e.g. `targeted_therapy` renamed to `immuno_therapy`, `disease_status` exists as an inferred analytic field, and `subtype_simulated` is synthetic ground truth (not registry-derived).

- Developer workflows (quick reference)
  - Database: PostgreSQL service (port `5434`), DB name `thesis_registry`. The README describes the table `breast_registry` and example SQL queries — use those for analytic checks.
  - FHIR validation: `tools/validator_cli.jar` is the local validator artifact. The Phase 2 README says validation is performed against the mCODE IG. (Assumption: run via `java -jar tools/validator_cli.jar <bundle.json> -ig <mcode-ig>`; update if your validator wrapper differs.)
  - Samples to exercise changes: edit or create new files under `phase-2/fhir/` for bundle-level work; test with the validator and compare field mappings back to the CSV/dictionary.

- Project-specific patterns to follow (discoverable from the repo)
  - Keep one patient per bundle in `phase-2/fhir/` (file naming uses `patient-<id>.bundle.json`). Use existing files as templates (e.g., `patient-0985.bundle.json`).
  - For biomarker/observation examples, mirror resource structure used in `phase-2/fhir/obs-er.json`, `obs-pr.json`, `obs-her2.json` and `obs-tumor-size.json`.
  - When adding clinical data that the source lacks, prefer explicit comments in the JSON and consistent placeholder dates rather than silent defaults (this makes downstream validation and iteration easier).

- Integration points and external dependencies
  - PostgreSQL (local/dev) — used for analytics in Phase 1.
  - HL7 FHIR Validator (local jar in `tools/`) and the mCODE Implementation Guide (external) — used to validate bundles.

- Quick examples (where to look / edit)
  - To see how stage observations are represented: `phase-2/fhir/obs-ajcc-stage-group.json`.
  - To add a new sample bundle: copy `phase-2/fhir/patient-0985.bundle.json`, update identifiers and mapped fields derived from `breast_registry_synth_1000.csv`.

- Assumptions and notes for contributors
  - There is no transformation code in this repo that maps CSV → FHIR bundles. If you add mapping code, place it in a top-level folder `transform/` and include a README describing inputs/outputs and a small CLI or tests that map 1–10 rows to bundles.
  - Validator usage is assumed to be via the provided jar; if you prefer the online mCODE IG validator or a different validator CLI, document the steps in `phase-2/README.md` or this file.

If any of these assumptions are wrong (validator command, DB host/port, or expected naming), tell me which lines to change and I will update this file. Ready for feedback or to merge further details (example validator command, transformation entrypoint) if you want them included.
