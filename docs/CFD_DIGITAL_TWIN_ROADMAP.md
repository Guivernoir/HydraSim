# HydraSim CFD/Digital-Twin Roadmap

HydraSim's post-HS-20 direction is a CFD-backed digital-twin simulator
foundation. HS-1 through HS-20 remain the compatibility and regression base:
legacy single-endpoint Modbus behavior, deterministic MVP scenarios, staged
Reference Water Plant profiles, transcript export, PCAP export, and lab bundles
must continue to work while CFD capability grows.

The selected strategy is **in-process finite-volume CFD** using the existing
Python/NumPy/SciPy stack. External CFD tools such as OpenFOAM may later be used
as validation references, but they are not runtime dependencies.

HydraSim does not claim certification, commissioning authority, safety-system
protection, operational validation, calibrated real-plant equivalence, or full
plant-design authority without separate calibration and validation evidence.

## Current Foundation

The repository now includes a bounded CFD/digital-twin foundation under
`src/wt_simulator/hydraulics/cfd`:

- structured finite-volume mesh primitives;
- small-grid incompressible-flow stepping with CFL and mass-residual diagnostics;
- scalar transport stepping for water-quality fields;
- bounded turbulence/mixing helper;
- reference area CFD models for intake, dosing, clarification, filtration,
  disinfection, and storage/pumping;
- digital-twin metadata, calibration status, uncertainty, and residual records;
- simulated device-coupling contracts for spatial sensor sampling and bounded
  actuator source effects;
- simulated controller-to-CFD contracts that map bounded controller decisions
  onto declared actuator/source regions;
- synthetic supervisory records for HMI, historian, and engineering-workstation
  style consumers of CFD state and digital-twin metadata;
- operator/historian semantic bundles with trend tags, advisory alarm states,
  maintenance windows, operator actions, and engineering events;
- deterministic CFD summary export.

These primitives make HS-21 tangible and start HS-22 through HS-26 at foundation
level. They are not yet a full CFD-backed plant runtime.

Current reference CFD area IDs are `intake`, `dosing`, `clarification`,
`filtration`, `disinfection`, and `storage-pumping`.

## HS-26A Unit-Process Catalog

The Reference Water Plant is decomposed into unit-process contracts before
device coupling or CFD-backed scenario truth is allowed. Each unit declares a
purpose, geometry class, area, input/output boundaries, process variables,
instrumentation, and limitations.

| Unit ID | Area | Geometry class | Purpose |
| --- | --- | --- | --- |
| `intake-channel` | `intake` | `open_channel` | Raw-water flow and upstream quality context. |
| `rapid-mix-dosing` | `dosing` | `rapid_mix_basin` | Chemical dosing and rapid-mix context. |
| `flocculation-placeholder` | `clarification` | `flocculation_placeholder` | Reserved flocculation unit without chemistry overclaim. |
| `clarifier` | `clarification` | `settling_basin` | Settling-basin hydraulics and turbidity context. |
| `filter-backwash` | `filtration` | `filter_bed` | Filtration headloss and backwash transition context. |
| `contact-basin` | `disinfection` | `contact_basin` | Spatial disinfectant-residual contact context. |
| `clearwell` | `storage-pumping` | `storage_tank` | Treated-water storage, level, and residual context. |
| `pumping-header` | `storage-pumping` | `pump_header` | Pump/valve boundary effects on downstream flow. |
| `chemical-feed-skid` | `dosing` | `chemical_feed_skid` | Chemical source terms and dosing-equipment context. |
| `waste-backwash-handling` | `filtration` | `waste_handling` | Waste/backwash routing metadata for lab scenarios. |

HS-26A does not certify plant design, hydraulics, process outcomes, or safety
behavior. It is a contract layer that makes later CFD boundary-condition,
device-coupling, scenario, and bundle work testable.

## HS-26B Boundary-Condition Library

Reusable CFD boundary/source contracts are locked before device coupling or
CFD-backed scenario runtime is expanded. Unit processes may reference these
contracts by geometry class and boundary purpose.

| Contract ID | Kind | Primary use |
| --- | --- | --- |
| `bc-inlet-flow` | `inlet_flow` | Upstream flow, temperature, and quality values. |
| `bc-outlet-flow` | `outlet_flow` | Downstream outflow without modeling the full network. |
| `bc-pump-discharge` | `pump_discharge` | Pump setpoint/status to flow and head context. |
| `bc-valve-loss` | `valve_loss` | Valve-position hydraulic loss term. |
| `bc-dosing-injection` | `dosing_injection` | Chemical scalar source terms. |
| `bc-mechanical-mixer` | `mechanical_mixer` | Bounded local mixing energy. |
| `bc-baffle-wall` | `baffle_wall` | Fixed baffle obstacles and directed flow pathing. |
| `bc-porous-filter-media` | `porous_filter_media` | Filter-bed resistance and scalar sink context. |
| `bc-backwash-flow` | `backwash_flow` | Reverse/flush filter flow during backwash scenarios. |
| `bc-drain-flow` | `drain_flow` | Water or waste stream removal. |
| `bc-recirculation-flow` | `recirculation_flow` | Bounded recirculation between declared local regions. |
| `bc-free-surface-level` | `free_surface_level` | Tank/channel level metadata for bounded grid presets. |

Each contract carries required variables, CFD effects, geometry targets, and
limitations. HS-26B does not implement plant-calibrated pump curves, valve
curves, filter fouling, free-surface deformation, air scour, or downstream
network hydraulics. Those require later verification/calibration slices.

## HS-26C Early Performance Envelope

Before sensors, actuators, controllers, and live runtime are coupled to CFD,
HydraSim defines bounded grid presets and a benchmark helper. These presets are
evidence-gathering tools, not performance claims for every machine.

| Preset ID | Cells | Intended use |
| --- | ---: | --- |
| `tiny-grid` | `6 x 3 x 2` | Unit tests and smoke checks. |
| `small-grid` | `10 x 4 x 3` | Selected-area offline scenario checks. |
| `medium-grid` | `16 x 6 x 4` | Pre-coupling benchmark ceiling on developer machines. |

The benchmark records cell count, estimated field memory, iteration count,
wall-clock time, stability, max CFL, and mass residual. Later coupling slices
must use measured presets instead of assuming arbitrary whole-plant CFD grids
will run comfortably.

## HS-27 Device-To-CFD Coupling

HydraSim now includes the first device-to-CFD coupling foundation. Simulated
sensor contracts can sample declared mesh regions such as inlet, outlet,
center, all cells, or explicit cell IDs. Simulated actuator contracts can apply
bounded scalar/source effects to declared mesh regions. The current catalog is
derived from the water-treatment unit-process instrumentation and chemical
source boundaries, and every contract is marked `simulated_metadata`.

HS-27 deliberately keeps the ICS runtime separate from CFD internals. Modbus or
future ICS endpoints may read simulated process values or write setpoints, but
they do not own the solver, mesh, calibration state, or plant-realism claims.
The current coupling foundation does not yet implement calibrated sensor
placement, sample-line hydraulics, actuator curves, controller-to-CFD closed
loop behavior, noisy/stale measurements, or field-validated device behavior.

## HS-28 Controller-To-CFD Coupling

HydraSim now includes the first Controller-To-CFD Coupling foundation. Synthetic
controller contracts bind a controller ID, unit process, actuator tag, routine,
controlled variable, manipulated variable, setpoint, deadband, proportional
gain, and bounded output range. Controller actions are evaluated from a process
value and can apply a bounded source term through the matching simulated
actuator region.

This implements a deterministic coupling contract, not real PLC firmware or
plant-calibrated control. Current actions support monitoring, within-deadband,
increase-source, and withhold-source outcomes. The coupling remains
`simulated_metadata` and does not yet include calibrated actuator curves,
anti-windup, full PID dynamics, closed-loop scenario timelines, interlock
validation, failover dynamics, or safety-system behavior.

## HS-29 Supervisory Digital-Twin Layer

HydraSim now includes the first Supervisory Digital-Twin Layer for consuming
CFD/digital-twin facts in synthetic HMI, historian, and engineering-workstation
style views. Current profiles are:

| Profile ID | Role | Purpose |
| --- | --- | --- |
| `hmi-process-overview` | `hmi` | Show selected-area CFD process context to a synthetic operator view. |
| `historian-process-trend` | `historian` | Store deterministic process trend samples with spatial context. |
| `engineering-model-context` | `engineering_workstation` | Inspect synthetic mesh, geometry, and model-status metadata. |

Supervisory records may summarize CFD scalar values, flow values, mesh metadata,
digital-twin status, and spatial context. Every record keeps `site_identity` as
`unknown` and `evidence_status` as `simulated_metadata`.

HS-29 does not implement vendor HMI, historian, engineering-workstation,
SCADA/DCS/PCS, or OPC-UA behavior. It does not prove operational visibility,
plant identity, equipment identity, customer validation, field readiness, or
real historian evidence.

## HS-29A Operator And Historian Semantics

HydraSim now includes the first Operator And Historian Semantics foundation.
The semantic bundle adds:

- historian trend tags with sampling intervals and synthetic retention class;
- advisory alarm states such as `normal`, `advisory_high`, and `advisory_low`;
- maintenance-window records with manual/maintenance context;
- operator setpoint or mode-change records;
- engineering-workstation events such as profile validation and metadata export.

These records make supervisory output more useful for training and review, but
they remain synthetic. Trend tags are not operational historian evidence.
Advisory alarm states are review prompts only and are not incidents, safety
alarms, or operational alarm evidence. Operator actions are not a real operator action or authorization record. Engineering-workstation events are not real
vendor tool or configuration-change evidence.

## HS-30 Calibration And Uncertainty Framework

HS-30 adds the first Calibration And Uncertainty Framework. The framework
records:

- calibration evidence sources such as `synthetic_reference`,
  `manufactured_solution`, `lab_measurement`, `field_telemetry`, and
  `external_cfd_comparison`;
- calibration parameters with source IDs, units, accepted ranges, and values;
- residual checks with observed values, predicted values, tolerances, absolute
  residuals, and accepted/rejected status;
- uncertainty records with quantity, absolute bound, and basis;
- calibration confidence labels: `unknown`, `low`, `medium`, and `high`;
- calibration status labels: `uncalibrated`, `calibration_ready`,
  `synthetic_calibrated`, `evidence_calibrated`, and `rejected`.

The default reference water-treatment area models remain `uncalibrated` and
`synthetic_unvalidated`. A synthetic reference case can only produce
`synthetic_calibrated` evidence. Non-synthetic lab, field telemetry, or external
CFD comparison sources require explicit source references before they can
support `evidence_calibrated` status.

HS-30 still does not perform parameter fitting, real-plant validation, external
CFD comparison, certification, commissioning, safety validation, or plant design
authority. Even `evidence_calibrated` means a bounded parameter set has accepted
calibration residuals; it is not real-plant validation.

## HS-30A Numerical Verification Suite

HS-30A adds a bounded Numerical Verification Suite for the current CFD
primitives. The suite emits `synthetic_numerical_verification` evidence for:

- a constant-scalar manufactured/simple reference solution;
- a flow mass-residual conservation check;
- a mesh refinement sensitivity check using a constant-field integral;
- an inlet boundary-condition response check;
- a long-run drift check for repeated constant-scalar transport steps.

These checks make numerical regressions visible before the CFD-backed scenario
work expands. They are intentionally small and deterministic so they can run in
CI and on a developer workstation.

HS-30A does not validate a real water-treatment plant, prove calibration,
compare against external CFD tools, certify solver correctness, authorize
commissioning decisions, or prove safety-system behavior. It only says the
current synthetic verification cases pass within their declared tolerances.

## HS-30B Calibration Evidence Model

HS-30B adds the first Calibration Evidence Model. It separates parameter
fitting from validation by storing each fit as `fitted_not_validated` until a
later validation gate accepts stronger evidence.

The HS-30B contract records:

- source evidence through `CalibrationEvidenceSource`;
- accepted calibration samples and rejected data with rejection reasons;
- fitted parameter value, units, and accepted range;
- residuals computed after fitting;
- an uncertainty update derived from the residual envelope;
- an explicit calibration record tied to the evidence source.

`evidence_calibrated` can only be assigned when a non-synthetic source has an
explicit calibration record. Non-synthetic source evidence and accepted
residuals without that record remain `calibration_ready`, not
`evidence_calibrated`.

HS-30B does not perform validation, real-plant equivalence, external CFD
acceptance, commissioning review, safety review, or plant-design authority.
Rejected data remains part of the fit evidence so questionable samples cannot
silently disappear.

## Digital-Twin Status Labels

| Status | Meaning |
| --- | --- |
| `synthetic_unvalidated` | Synthetic model exists but has not passed verification or calibration evidence. |
| `synthetic_verified` | Synthetic model has passed deterministic and numerical verification cases. |
| `calibration_ready` | Model has calibration parameters and can ingest comparison evidence. |
| `evidence_calibrated` | Model has recorded source evidence and residuals supporting a calibrated parameter or area. |

No status implies certification, safety validation, or real-plant design
authority.

## Slice Sequence

| Slice | Name | Primary output | Exit gate |
| ---: | --- | --- | --- |
| HS-21 | CFD/Digital-Twin Architecture Lock | CFD solver scope, mesh model, equations, calibration model, validation vocabulary, and no-overclaim rules. | Docs and contracts replace simplified-physics direction with in-process CFD/digital-twin direction. |
| HS-22 | Mesh And Geometry Kernel | Structured grid support for tanks, channels, basins, pipes/links, inlets, outlets, baffles, and obstacles. | Deterministic mesh generation and geometry validation for each water-treatment area. |
| HS-23 | Incompressible Flow Solver v1 | Finite-volume velocity/pressure solve for water flow with mass-conservation checks. | Stable flow fields for simple tanks/channels with benchmark conservation tests. |
| HS-24 | Scalar Transport CFD | Advection-diffusion-reaction transport for chlorine, pH proxy species, temperature, ammonia, chloramine, and demand precursor. | Scalar fields evolve over the mesh and match conservation/tolerance tests. |
| HS-25 | Turbulence And Mixing Model | RANS-style turbulence/mixing support suitable for small local grids. | Mixing behavior is spatially resolved and benchmarked against controlled reference cases. |
| HS-26 | Area CFD Models | Intake, dosing, clarification, filtration, disinfection, and storage/pumping geometry/flow models. | Each area has CFD geometry, boundary conditions, state outputs, and limitations. |
| HS-26A | Water-Treatment Unit Process Decomposition | Break the reference plant into CFD-backed unit processes: intake channel, rapid-mix/dosing, flocculation-ready placeholder, clarifier, filter/backwash, contact basin, clearwell, pumping, chemical feed skids, and waste/backwash handling metadata. | Every unit has purpose, geometry class, input/output boundaries, process variables, instrumentation, and explicit limitations. |
| HS-26B | CFD Boundary Condition Library | Lock reusable boundary/source models for inlets, outlets, pumps, valves, dosing injection, mixers, baffles, filter media, backwash, drains, recirculation, and tank level surfaces. | Area models stop using ad hoc boundary choices and reference named boundary-condition contracts. |
| HS-26C | Early CFD Performance Envelope | Benchmark tiny/small/medium grids before coupling to devices. | Coupling slices use grid/time-step presets with measured CPU, memory, output-size, stability, and wall-time budgets. |
| HS-27 | Device-To-CFD Coupling | Sensors sample local CFD cells/regions; actuators alter CFD boundary conditions or source terms. | Field-device personas report spatially grounded process values. |
| HS-27A | Sensor/Actuator Spatial Coupling Contract | Define sampling regions, sample-line delay, sensor health, actuator source/boundary effects, stale data, calibration state, and noisy measurement behavior. | Device coupling is testable without assuming one sensor equals one cell or one actuator equals one scalar value. |
| HS-28 | Controller-To-CFD Coupling | PLC/RTU-like routines affect actuator setpoints and CFD source/boundary terms. | Controller writes cause measurable process-field changes visible in traffic and state timelines. |
| HS-29 | Supervisory Digital-Twin Layer | HMI/historian/engineering workstation profiles consume CFD state summaries and metadata. | Historian records include spatial/process context without inventing site identity. |
| HS-29A | Operator And Historian Semantics | Add alarm states, trend tags, historian sampling rates, operator setpoint changes, maintenance windows, engineering-workstation configuration events, and manual/auto context. | Supervisory output becomes useful for training/review while remaining synthetic and caveated. |
| HS-30 | Calibration And Uncertainty Framework | Parameters, calibration records, source evidence, confidence, residuals, and uncertainty bounds. | A model can be marked uncalibrated, synthetic-calibrated, or evidence-calibrated with explicit caveats. |
| HS-30A | Numerical Verification Suite | Manufactured/simple reference cases, conservation checks, mesh-refinement sensitivity, boundary-condition tests, and long-run drift checks. | CFD code can be called numerically verified for bounded cases, not real-plant validated. |
| HS-30B | Calibration Evidence Model | Separate calibration parameter fitting from validation; store source evidence, residuals, accepted ranges, rejected data, and uncertainty updates. | `evidence_calibrated` can only be assigned through explicit calibration records. |
| HS-31 | Scenario Library CFD Upgrade | Existing ICS scenarios gain CFD-backed expected process evolution. | Startup, maintenance, upset, drift, fault, backwash, excursion, noisy polling, and failover scenarios include process-field truth. |
| HS-31A | Scenario Process-Truth Review | Each scenario receives expected process evolution, observable network effects, operator/historian effects, and "must not claim" text. | Scenarios can be reviewed for realism before becoming demo/training examples. |
| HS-32 | CFD Lab Bundle v2 | Export mesh, geometry, state timeline, scalar fields, flow snapshots, PCAP, transcript, topology, manifest, and checksums. | A bundle can reproduce both network behavior and process-state evidence. |
| HS-33 | Runtime Performance Gate | Benchmark grid sizes, solver time step, memory, CPU, stability, deterministic output, and long-run drift. | Local machine benchmarks define acceptable grid/runtime presets. |
| HS-34 | Digital-Twin Validation Gate | Verification cases, conservation checks, manufactured solutions where possible, and optional external CFD comparison. | HydraSim can claim CFD implementation evidence, but not real-plant validation unless real calibration data exists. |
| HS-34A | External Review And Calibration Evidence Gate | Record optional external CFD comparison, water-treatment SME review, and calibration evidence without changing model status automatically. | Review evidence informs status, but unsupported claims remain blocked. |
| HS-35 | Reference Water Plant CFD Release | First CFD-backed Reference Water Treatment Plant release candidate. | User can run selected-area/full-plant offline CFD scenarios and selected-area live ICS traffic with CFD-coupled state. |

## Implementation Decisions

- CFD runtime strategy: in-process finite-volume solver.
- Solver target: bounded local grids for deterministic simulation, not HPC-scale
  unrestricted plant design.
- Initial model: incompressible water flow, scalar transport, and bounded
  turbulence/mixing.
- Digital-twin layer: geometry references, equipment references, calibration
  records, uncertainty records, telemetry-assimilation hooks, and validation
  status.
- Existing multi-zone CSTR remains legacy/regression and may be used for
  comparison; new "real simulator foundation" claims require CFD-backed paths.
- Modbus/ICS endpoints consume or influence process state, but they do not own
  the CFD solver.
- Unit-process and boundary-condition contracts must be locked before
  CFD-backed scenarios are treated as plant-level realism evidence.
- Calibration and validation are separate: calibration adjusts model parameters,
  while validation evaluates whether the resulting model deserves a stronger
  evidence status.

## Verification Strategy

- Mesh tests: valid/invalid geometry, deterministic cell IDs, boundary tags,
  area selection, and obstacle placement.
- Unit-process tests: each water-treatment unit process declares geometry,
  boundaries, instruments, expected variables, and limitations.
- Solver tests: mass-residual diagnostics, pressure/velocity stability,
  bounded time steps, deterministic output, and simple benchmark cases.
- Scalar tests: advection, diffusion, reaction, source/sink terms,
  nonnegative concentrations, and conservation tolerances.
- Boundary-condition tests: pumps, valves, inlets, outlets, dosing, filter
  media, drains, recirculation, and backwash contracts behave predictably.
- Coupling tests: sensors sample correct cells/regions, actuators change
  source/boundary terms, and controllers produce process-state changes.
- Operator/historian tests: trends, alarms, manual/auto states, maintenance
  windows, and engineering-workstation events remain synthetic and auditable.
- Scenario tests: each CFD-backed scenario emits expected state timeline,
  process caveats, transcript, PCAP, and bundle artifacts.
- Verification tests: conservation, manufactured/simple cases, mesh refinement,
  boundary sensitivity, and long-run drift.
- Performance tests: tiny/small/medium grid CPU time, memory, output size, and
  long-run stability.
- Wording checks: no certification, commissioning, real plant validation,
  safety protection, or full-fidelity design authority claims.

## Current Gate

HS-21 foundation is implemented as code, tests, and documentation. HS-22 through
HS-26 have initial primitives and reference area profiles. HS-26A is implemented
as a unit-process contract catalog. HS-26B is implemented as a reusable
boundary-condition contract library. HS-26C is implemented as an early
performance preset and benchmark envelope. HS-27 is implemented as a simulated
device-to-CFD coupling contract and helper layer. HS-28 is implemented as a
simulated controller-to-CFD coupling contract and bounded action helper. HS-29
is implemented as a synthetic supervisory digital-twin record layer. HS-29A is
implemented as a synthetic operator/historian semantics layer. HS-30 is
implemented as a calibration and uncertainty assessment contract with explicit
evidence-source, residual, confidence, and caveat rules. HS-30A is implemented
as a synthetic numerical verification suite covering constant-scalar
conservation, flow residuals, mesh refinement, boundary response, and long-run
drift. HS-30B is implemented as a calibration evidence model that keeps fitting
separate from validation, preserves rejected data, updates uncertainty, and
requires an explicit calibration record before `evidence_calibrated` status.
HS-31 is implemented as deterministic `synthetic_cfd_process_truth` records on
built-in ICS runtime artifacts and bundles. The full closed-loop CFD runtime,
lab bundle v2 field snapshots, external CFD comparison, and later performance
gates remain future slices.
