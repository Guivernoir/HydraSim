# HydraSim Slice Roadmap

HydraSim development follows a lock-first slice process:

1. Define the slice boundary and prohibited claims.
2. Implement the smallest runtime surface that makes the boundary real.
3. Add deterministic tests and documentation.
4. Verify the current slice before expanding the simulator.

This keeps HydraSim useful as a standalone simulator without turning it into an
unsafe network tool.

## Slice Sequence

| Slice | Name | Output | Status |
| ---: | --- | --- | --- |
| HS-1 | Scenario Runtime Foundation | Built-in Modbus scenario profiles, transcript export, command-center runner, live replay path, custom JSON loading. | Implemented |
| HS-2 | Scenario Validation and Library Gate | Scenario validator, validation CLI, custom scenario safety rules, built-in scenario validation tests. | Implemented |
| HS-3 | Multi-Node Simulated OT Topology | Configurable multi-endpoint process nodes and optional smart-field-device identities. | Implemented |
| HS-4 | Deterministic PCAP Export | Transcript-derived Ethernet/IPv4/TCP/Modbus PCAP export for supported scenarios. | Implemented |
| HS-5 | Capture-Friendly Lab Orchestration | One-command lab runner with process endpoint, command center, capture notes, and export bundle. | Implemented |
| HS-6 | Scenario Library Expansion | Normal operation, maintenance, abnormal process, unknown-host, misconfiguration, noisy-network, and degraded-operations scenario families. | Implemented |
| HS-7 | Quality and CI Hardening | Folder/file density, formatting, optional dependency gates, documentation checks, CI workflow, and oversized-module baseline. | Implemented |
| HS-8 | ICS Architecture Model Lock | Plant profile schema, hierarchy, presets, subsystem selection, stage vocabulary, zones, conduits, media, and activation-mode rules. | Implemented |
| HS-9 | Stage Activation Runtime | Selectable `field-devices`, `field-controllers`, `supervisory`, `full-cell`, and `offline-export` runtime modes. | Implemented for deterministic artifacts |
| HS-10 | Field Device Fleet by Area | Distinct sensor/actuator/analyzer endpoint personas per plant area with MAC/IP/register-map truth and legacy single-endpoint support. | Implemented |
| HS-11 | Area Controller Layer | Intake, dosing, filtration, disinfection, and pumping PLC/RTU-like personas with polling, bounded control routines, and upstream Modbus surfaces. | Implemented as synthetic personas |
| HS-12 | Supervisory/PCS Profiles | Selectable SCADA-lite, DCS-lite, and PCS-minimal supervisory traffic profiles and polling patterns. | Implemented |
| HS-13 | Plant Topology and Media Profiles | Area zones/conduits, LANs, optional DMZ, Ethernet, serial-gateway, latency/jitter/drop metadata profiles. | Implemented as metadata/artifacts |
| HS-14 | ICS Scenario Library v2 | Staged plant scenarios for startup, normal operation, maintenance, chemical upset, pump failure, sensor drift, analyzer fault, backwash, disinfection excursion, unknown workstation, and noisy polling. | Implemented |
| HS-15 | Real-Time Orchestration | Coordinated multi-process/multi-port local simulator launcher with deterministic lifecycle. | Implemented |
| HS-16 | Passive Capture Lab Mode | Capture-friendly lab metadata, bundle outputs, and passive observer guidance. | Implemented |
| HS-17 | Controller Logic Upgrade | Threshold, PID-lite, interlock-like labels, manual/auto mode, and alarm-state behavior. | Implemented |
| HS-18 | Protocol Expansion Planning | Planning locks for DNP3, OPC-UA metadata, EtherNet/IP/CIP, S7comm, and Profinet/DCP simulation roles. | Documented direction |
| HS-19 | Industrial Simulator Quality Gate | CI coverage for architecture profiles, stage configs, scenario requirements, PCAP determinism, and unsafe-claim checks. | Implemented |
| HS-20 | Reference Water Plant Release Candidate | First configurable Reference Water Plant package and verification checklist. | Implemented |
| HS-21 | CFD/Digital-Twin Architecture Lock | CFD solver scope, mesh model, equations, calibration model, validation vocabulary, and no-overclaim rules. | Implemented foundation |
| HS-22 | Mesh And Geometry Kernel | Structured grid support for tanks, channels, basins, pipes/links, inlets, outlets, baffles, and obstacles. | Foundation primitives implemented |
| HS-23 | Incompressible Flow Solver v1 | Finite-volume velocity/pressure solve for water flow with mass-conservation diagnostics. | Foundation primitives implemented |
| HS-24 | Scalar Transport CFD | Advection-diffusion-reaction transport for water-treatment scalars. | Foundation primitives implemented |
| HS-25 | Turbulence And Mixing Model | Bounded small-grid turbulence/mixing support. | Foundation primitives implemented |
| HS-26 | Area CFD Models | Intake, dosing, clarification, filtration, disinfection, and storage/pumping geometry/flow models. | Initial reference profiles implemented |
| HS-26A | Water-Treatment Unit Process Decomposition | CFD-backed unit-process contracts for intake, rapid-mix/dosing, flocculation-ready placeholder, clarifier, filter/backwash, contact basin, clearwell, pumping, chemical feed, and waste/backwash metadata. | Implemented |
| HS-26B | CFD Boundary Condition Library | Reusable inlets, outlets, pumps, valves, dosing injection, mixers, baffles, filter media, drains, recirculation, and backwash contracts. | Implemented |
| HS-26C | Early CFD Performance Envelope | Tiny/small/medium grid budgets before live coupling. | Implemented |
| HS-27 | Device-To-CFD Coupling | Sensors sample CFD cells/regions; actuators alter CFD boundary conditions or source terms. | Implemented foundation |
| HS-27A | Sensor/Actuator Spatial Coupling Contract | Sampling regions, sample-line delay, sensor health, actuator source/boundary effects, stale data, calibration state, and noisy measurement behavior. | Foundation contracts implemented |
| HS-28 | Controller-To-CFD Coupling | PLC/RTU-like routines affect actuator setpoints and CFD source/boundary terms. | Implemented foundation |
| HS-29 | Supervisory Digital-Twin Layer | HMI/historian/engineering workstation profiles consume CFD state summaries and metadata. | Implemented foundation |
| HS-29A | Operator And Historian Semantics | Alarm states, trend tags, historian sampling rates, operator setpoint changes, maintenance windows, engineering workstation events, and manual/auto context. | Implemented foundation |
| HS-30 | Calibration And Uncertainty Framework | Calibration records, source evidence, confidence, residuals, and uncertainty bounds. | Implemented foundation |
| HS-30A | Numerical Verification Suite | Manufactured/simple reference cases, conservation checks, mesh-refinement sensitivity, boundary-condition tests, and long-run drift checks. | Implemented foundation |
| HS-30B | Calibration Evidence Model | Parameter fitting separated from validation, with source evidence, residuals, accepted ranges, rejected data, and uncertainty updates. | Implemented foundation |
| HS-31 | Scenario Library CFD Upgrade | Existing ICS scenarios gain CFD-backed expected process evolution. | Implemented foundation |
| HS-31A | Scenario Process-Truth Review | Scenario process evolution, network effects, operator/historian effects, and prohibited claims reviewed before demo/training use. | Planned |
| HS-32 | CFD Lab Bundle v2 | Export mesh, geometry, state timeline, scalar fields, flow snapshots, PCAP, transcript, topology, manifest, and checksums. | Planned |
| HS-33 | Runtime Performance Gate | Benchmark grid sizes, solver time step, memory, CPU, stability, deterministic output, and long-run drift. | Planned |
| HS-34 | Digital-Twin Validation Gate | Verification cases, conservation checks, manufactured solutions, and optional external CFD comparison. | Planned |
| HS-34A | External Review And Calibration Evidence Gate | Optional external CFD comparison, water-treatment SME review, and calibration evidence recorded without automatic status upgrades. | Planned |
| HS-35 | Reference Water Plant CFD Release | First CFD-backed Reference Water Treatment Plant release candidate. | Planned |

## Current Gate

The Reference Water Plant surface is implemented and documented in
[HydraSim Reference Water Plant](REFERENCE_WATER_PLANT.md). Current scenarios
cover normal operations, startup, maintenance, smart-field topology, chemical
upset, pump failure, sensor drift, analyzer fault, filter backwash,
disinfection excursion, unknown workstation review, noisy polling, and
controller failover context.

The controlling industrial-simulator roadmap is
[HydraSim Industrial Simulator Roadmap](INDUSTRIAL_SIMULATOR_ROADMAP.md).
The controlling CFD/digital-twin roadmap is
[HydraSim CFD/Digital-Twin Roadmap](CFD_DIGITAL_TWIN_ROADMAP.md).
HS-27 now adds validated simulated device-coupling contracts so sensors can
sample spatial CFD regions and actuators can apply bounded source terms without
turning ICS endpoints into physics owners.
HS-28 adds validated simulated controller-to-CFD contracts so controller
setpoint/error logic can produce bounded source effects through declared
actuator regions without claiming real PLC firmware, calibrated control, or
safety behavior.
HS-29 adds validated synthetic supervisory records so HMI, historian, and
engineering-workstation style consumers can read CFD state summaries and
digital-twin metadata without inventing site identity or operational historian
evidence.
HS-29A adds validated synthetic operator/historian semantic bundles with trend
tags, advisory alarm states, maintenance windows, operator actions, and
engineering events while preserving review-only wording.
HS-30 adds validated calibration and uncertainty assessment contracts with
`uncalibrated`, `calibration_ready`, `synthetic_calibrated`,
`evidence_calibrated`, and `rejected` statuses. The default reference areas
remain uncalibrated synthetic models, and even accepted calibration evidence is
not real-plant validation.
HS-30A adds a validated synthetic numerical verification suite for
constant-scalar conservation, flow residuals, mesh refinement, boundary
response, and long-run drift. Passing those cases is numerical implementation
evidence, not real-plant validation.
HS-30B adds a validated calibration evidence model with `fitted_not_validated`
fit records, preserved rejected data, accepted ranges, residuals, uncertainty
updates, and the rule that `evidence_calibrated` requires an explicit
calibration record.
HS-31 adds deterministic `synthetic_cfd_process_truth` records to built-in ICS
runtime artifacts and bundles. The records describe scenario process evolution
for selected areas while remaining synthetic process truth, not real-plant
validation.

## Safety Boundaries

- HydraSim scenarios target configured HydraSim endpoints only.
- HydraSim does not scan external networks.
- HydraSim does not discover devices.
- HydraSim does not claim operational validation.
- Unknown-host or abnormal behavior remains synthetic review behavior, not an
  attack, incident, compromise, or safety-impact conclusion.
- Passive observers are metadata only and must not be scenario participants.
- "Real ICS" means realistic simulator layering and traffic behavior, not
  certification-grade plant emulation or a safety-system claim.
- "Entire plant" means a configurable synthetic reference plant with
  representative areas and ICS layers, not a certified digital twin.
- CFD/digital-twin outputs start as synthetic model evidence, not real-plant
  validation, commissioning evidence, or safety-system proof.
- CFD calibration and validation are separate gates; one does not imply the
  other.
- CFD performance budgets must be measured before live plant-wide coupling is
  expanded.

## Completion Standard

A slice is complete only when:

- runtime behavior matches the slice boundary;
- docs describe how to use it;
- tests cover positive and rejection paths;
- generated files are not left in the working tree;
- full unittest discovery passes, including the live `pymodbus` Modbus
  end-to-end tests installed through `.[dev,modbus]`.
