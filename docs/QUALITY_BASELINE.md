# HydraSim Quality Baseline

HydraSim now uses a local quality gate:

```bash
python -m pip install -e ".[dev,modbus]"
python tools/check_project_quality.py
python -m black --check src/wt_simulator/scenarios src/wt_simulator/ics src/wt_simulator/hydraulics tests tools
python -m unittest discover -s tests -v
```

The gate enforces:

- built-in scenario validation;
- built-in scenario documentation coverage;
- local Markdown link resolution;
- folder-density limits;
- a 500-line limit for new Python modules;
- formatting on the new scenario runtime, its tests, and local quality tools;
- Reference Water Plant profile validation and documentation coverage;
- Reference Water Plant deterministic transcript and PCAP checks;
- CFD/digital-twin roadmap documentation coverage;
- CFD reference area profile validation;
- CFD unit-process catalog validation and documentation coverage;
- CFD boundary-condition catalog validation and documentation coverage;
- CFD performance preset validation and documentation coverage;
- CFD device-coupling catalog validation and documentation coverage;
- CFD controller-coupling catalog validation and documentation coverage;
- CFD supervisory profile and record validation with unknown site identity;
- CFD operator/historian semantic bundle validation with synthetic action,
  alarm, trend, maintenance, and engineering-event caveats;
- CFD digital-twin validation gate checks with implementation evidence
  separated from real-plant validation;
- CFD external review and calibration evidence gate checks with no automatic
  model-status upgrade;
- deterministic CFD summary export checks;
- required `pymodbus` availability for live Modbus end-to-end tests;
- an explicit legacy exception list for oversized modules that existed before
  the scenario runtime work.

## Legacy Oversized Modules

The quality checker allows the existing physics, sensor, maintenance, Modbus,
and runtime orchestration modules to exceed 500 lines as known technical debt.
The CI formatting gate also avoids mass-formatting those legacy scientific
modules until they are refactored intentionally. New scenario-runtime code is
below the line limit and Black-formatted. Future refactors should reduce the
legacy exception list instead of adding to it.

## Industrial Simulator Roadmap Gate

HS-8 through HS-20 add the industrial-simulator roadmap. The local quality gate
now validates built-in plant profiles, staged scenarios, documentation coverage,
and deterministic Reference Water Plant transcript/PCAP output. CI formats the
new `src/wt_simulator/ics` package and its tests.

## CFD/Digital-Twin Foundation Gate

HS-21 begins the CFD/digital-twin foundation. The local quality gate now checks
that every reference water-treatment CFD area is documented, validates its
area-model metadata, validates HS-26A unit-process contracts, validates HS-26B
boundary-condition contracts, validates HS-26C performance presets, and
validates HS-27 device-coupling contracts, and validates HS-28
controller-coupling contracts. HS-29 adds validation for supervisory profiles
and reference records, including the requirement that site identity remains
unknown. HS-29A adds validation for operator/historian semantic bundles,
including synthetic trend tags, advisory alarm states, maintenance windows,
operator actions, and engineering-workstation events. The gate also confirms
HS-30 calibration and uncertainty assessment contracts: default area models
remain `uncalibrated`, accepted synthetic evidence can only become
`synthetic_calibrated`, non-synthetic evidence requires source references, and
even `evidence_calibrated` status is not real-plant validation. The gate also
confirms HS-30B calibration evidence fitting behavior: fitting is
`fitted_not_validated`, rejected data is preserved, accepted non-synthetic
residual evidence remains `calibration_ready` unless an explicit calibration
record is present, and uncertainty updates come from the residual envelope. The
gate also confirms HS-30A numerical verification suite coverage for constant-scalar
conservation, flow residuals, mesh refinement, boundary response, and long-run
drift. These results use `synthetic_numerical_verification` evidence and remain
not real-plant validation. The gate also confirms HS-31 scenario-level
`synthetic_cfd_process_truth` records, deterministic `process-evolution.csv`
export, and process-truth documentation for every built-in reference plant
scenario. The gate also confirms HS-31A scenario process-truth review records,
`synthetic_scenario_process_review` evidence, deterministic `process-review.csv`
export, and explicit must-not-claim text for every built-in reference plant
scenario. The gate also confirms HS-32 CFD Lab Bundle v2 artifacts with
`synthetic_cfd_lab_bundle_v2` evidence in `cfd-mesh-geometry.json`,
`cfd-state-timeline.csv`, `cfd-scalar-fields.csv`, and
`cfd-flow-snapshots.csv`. The gate also confirms HS-33 Runtime Performance Gate
records with `synthetic_runtime_performance_gate` evidence, bounded wall-time
budgets, memory estimates, output-size budgets, stability, CFL, mass residual,
long-run drift, and deterministic exports. This is not hardware qualification.
The gate also confirms HS-34 Digital-Twin Validation Gate records with
`synthetic_digital_twin_validation_gate` evidence and the
`blocked_missing_real_calibration_and_external_validation` status. This proves
current implementation checks are wired together, but it is not real-plant
validation.
The gate also confirms HS-34A External Review And Calibration Evidence Gate
records with `synthetic_external_review_calibration_gate` evidence,
`pending_external_review` default disposition, deterministic export, and no
automatic model-status upgrade.
The gate also confirms HS-35 Reference Water Plant CFD Release Candidate
records with `synthetic_reference_water_plant_cfd_release_candidate` evidence,
full-plant offline output, selected-area full-cell output, selected-area live
plan, expected bundle artifacts, and deterministic JSON output.
The gate also confirms deterministic CFD summary export and requires the
model-scope and roadmap documents to keep the no-overclaim boundary visible:
CFD evidence is not certification, commissioning authority, real-plant
validation, safety-system protection, or unrestricted design authority.

## Dependency Boundary

`pymodbus` remains optional for transcript, PCAP, validation, and bundle
generation. It is mandatory for the full project quality gate because the live
Modbus end-to-end tests must run. Local development and CI install
`.[dev,modbus]` before running the gate. HydraSim currently supports the
`pymodbus >=3.11,<3.13` server-adapter line; a future migration to the newer
`SimDevice` API must be its own compatibility slice.
