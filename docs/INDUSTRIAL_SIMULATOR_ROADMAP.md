# HydraSim Industrial Simulator Roadmap

HydraSim will evolve from a water-treatment process simulator with Modbus
scenarios into a configurable reference water-treatment plant simulator. The
chosen direction is **water-treatment-first, architecture-generic**: keep the
existing water-treatment physics as the reference plant, while adding ICS
layers around it that can later support other process domains.

This roadmap is aligned with the component-oriented framing in CISA's ICS
training catalog, including the Common ICS Components training path:
<https://www.cisa.gov/resources-tools/programs/ics-training-available-through-cisa>.

## Direction

HydraSim should model either a full synthetic water-treatment plant or a
selected plant subsystem/stage. It should support:

- reference plant hierarchy;
- selectable plant presets;
- field devices;
- field controllers;
- SCADA/PCS-style supervisory roles;
- historian and polling behavior;
- engineering workstation behavior;
- topology, zones, conduits, and media profiles;
- passive-observer-friendly transcript, PCAP, and lab-bundle outputs.

HydraSim remains a simulator. It does not claim operational validation, safety
protection, certified behavior, real plant identity, attack confirmation,
commissioning authority, or full-fidelity plant design authority.

## Plant Hierarchy

| Level | Meaning |
| --- | --- |
| `plant` | The full reference water-treatment plant. |
| `area` | A major subsystem such as intake, dosing, clarification, filtration, disinfection, storage/pumping, or optional distribution edge. |
| `unit` | A tank/reactor, pump, valve, sensor, analyzer, dosing skid, filter, controller, HMI, or historian. |
| `stage` | A runtime activation slice such as field devices, controllers, supervisory roles, full cell, or offline export. |

## Plant Areas

| Area | Purpose |
| --- | --- |
| `intake` | Raw-water intake and initial flow/quality context. |
| `dosing` | Chemical dosing skids, dosing valves, pumps, and analyzer context. |
| `clarification` | Clarification/settling context and associated instrumentation. |
| `filtration` | Filter units, backwash context, differential-pressure style metadata, and instrumentation. |
| `disinfection` | Chlorine/pH process context, analyzer behavior, and dosing feedback. |
| `storage-pumping` | Clearwell/storage and pump/valve behavior. |
| `distribution-edge` | Optional downstream edge context; planned as metadata first, not full distribution-system chemistry. |

## Plant Presets

| Preset | Meaning |
| --- | --- |
| `single-stage-legacy` | Current-style single Modbus process endpoint. |
| `field-device-lab` | Only field devices, sensors, actuators, and endpoint personas. |
| `controller-cell` | Field devices plus PLC/RTU-like controller personas. |
| `supervisory-lab` | HMI, historian, engineering workstation, and supervisory traffic only. |
| `reference-water-plant` | Full multi-area synthetic plant with field, controller, and supervisory layers. |

## Stage Vocabulary

| Stage | Meaning |
| --- | --- |
| `field-devices` | Only simulated sensors, actuators, and field endpoints are active. |
| `field-controllers` | PLC/RTU-like controller personas are active, with simulated or live field I/O. |
| `supervisory` | HMI, historian, engineering workstation, and PCS/SCADA-style clients are active. |
| `full-cell` | Field devices, controllers, and supervisory roles run together. |
| `offline-export` | No sockets are opened; deterministic transcript, PCAP, and bundle artifacts are generated. |

## Implemented CLI Surface

These commands are implemented for profile validation, deterministic selected
stage rendering, PCAP export, lab-bundle export, and selected-area live launch
planning/orchestration:

```bash
wts-ics list-profiles
wts-ics validate-profile <profile>
wts-ics run <profile> --scenario <scenario> --area <area|all> --stage <stage>
wts-ics export-bundle <profile> <scenario> <output-dir>
wts-ics launch-live <profile> --scenario <scenario> --area <area> --stage <stage>
```

Implemented profile choices:

```bash
--area intake|dosing|clarification|filtration|disinfection|storage-pumping|distribution-edge|all
--control-system scada-lite|pcs-minimal|dcs-lite
--media ethernet|serial-gateway-placeholder|mixed-lab
--topology flat-cell|segmented-cell|plant-zones
```

Runtime defaults:

- default area is `all` only for offline export;
- live runtime defaults to a selected area until orchestration is proven;
- default control-system profile is `scada-lite`;
- default media profile is `ethernet`;
- default protocol is Modbus TCP.

Current `wts-ics run` behavior is deterministic artifact generation.
`wts-ics launch-live` starts selected-area synthetic endpoint processes using
the common HydraSim Modbus process runtime. Existing `wts-sim` and
`wts-run-scenario` remain legacy live Modbus compatibility surfaces.

Existing commands remain compatibility surfaces:

- `wts-sim`;
- `wts-run-scenario`;
- `wts-validate-scenario`;
- `wts-export-lab-bundle`.

Existing `MVP-MB-HYDRA-*` scenarios remain regression fixtures.

## Slice Sequence

| Slice | Name | Primary output | Exit gate |
| ---: | --- | --- | --- |
| HS-8 | ICS Architecture Model Lock | Plant profile schema, hierarchy, presets, subsystem selection rules, control-system profiles, topology/media choices, zones, conduits, roles, and activation modes. | Implemented: dataclass profile model, built-in profiles, validation, and documentation. |
| HS-9 | Stage Activation Runtime | Configurable stage activation for `field-devices`, `field-controllers`, `supervisory`, `full-cell`, and `offline-export`. | Implemented for deterministic selected-stage artifact generation. |
| HS-10 | Field Device Fleet by Area | Sensor/actuator/analyzer endpoint personas per plant area with distinct MAC/IP/register maps, preserving legacy single-endpoint mode. | Implemented as profile nodes and deterministic transcript/PCAP truth. |
| HS-11 | Area Controller Layer | PLC/RTU-like personas for intake, dosing, filtration, disinfection, and pumping that poll field devices, run simple control routines, and expose upstream Modbus surfaces. | Implemented as controller personas and bounded controller traffic; not real PLC firmware. |
| HS-12 | Supervisory/PCS Profiles | Selectable `scada-lite`, `dcs-lite`, and `pcs-minimal` profiles with HMI/historian/engineering workstation polling behavior. | Implemented as metadata choices and supervisory traffic personas. |
| HS-13 | Plant Topology and Media Profiles | Plant area zones, conduits, controller LAN, supervisory LAN, optional DMZ placeholder, Ethernet media, serial-gateway placeholder, latency/jitter/drop metadata. | Implemented as profile metadata and bundle topology output without physical-fidelity claims. |
| HS-14 | ICS Scenario Library v2 | Startup, normal operation, maintenance, chemical-dosing upset, pump failure, sensor drift, analyzer fault, filter backwash, disinfection excursion, unknown workstation, and noisy polling. | Implemented with `ICS-WTP-001` through `ICS-WTP-012`. |
| HS-15 | Real-Time Orchestration | Coordinated runtime launcher for multi-process/multi-port local simulation with deterministic startup, shutdown, health, and logs. | Implemented: `wts-ics launch-live` builds deterministic launch plans and starts/stops selected-area synthetic Modbus endpoint processes. |
| HS-16 | Passive Capture Lab Mode | Capture-friendly runtime metadata and local capture-helper documentation while keeping capture external/passive. | Implemented: bundles include topology, stage config, transcript, PCAP, checksums, and observer guidance. |
| HS-17 | Controller Logic Upgrade | Bounded control routines: threshold, PID-lite, interlock-like labels, manual/auto mode, and alarm state. | Implemented: runtime artifacts and bundles include deterministic controller state, mode, routine, alarm, setpoint, and effect evidence. |
| HS-18 | Protocol Expansion Planning | Future protocol surfaces for DNP3, OPC-UA metadata, EtherNet/IP/CIP, S7comm, and Profinet/DCP simulation roles. | Documented as future staged protocol expansion; Modbus remains the implemented baseline. |
| HS-19 | Industrial Simulator Quality Gate | CI validates architecture profiles, stage configs, scenario requirements, PCAP determinism, no unsafe claims, and file/folder policy. | Implemented in `tools/check_project_quality.py` and CI format scope. |
| HS-20 | Reference Water Plant Release Candidate | First HydraSim Reference Water Plant release package: docs, profiles, scenario library, runtime commands, lab bundles, and verification checklist. | Implemented as deterministic offline/selected-stage release candidate with selected-area live launch support. |

## Implementation Rules

- Lock the slice before runtime implementation.
- Preserve deterministic transcript and PCAP export for every scenario family.
- Preserve legacy single-endpoint Modbus compatibility until a documented
  deprecation decision exists.
- Keep `pymodbus` optional for non-live export workflows.
- Use supplied/simulated metadata labels for field devices, controllers, media,
  and topology.
- Represent active/adversarial behavior only as synthetic scenario traffic and
  review prompts.
- Treat physical media as topology/timing/metadata first, not raw serial-bus
  emulation.
- Require selected-area live runtime before full-plant live orchestration.

## Test Strategy

- Validate architecture-profile parsing and stage selection.
- Validate plant profiles, areas, units, presets, control-system choices,
  topology choices, and media choices.
- Reject unsafe or ambiguous stage configs.
- Validate unit-process contracts before treating CFD-backed scenarios as
  plant-level realism evidence.
- Test field-only, controller-only, supervisory-only, selected-area full-cell,
  full-plant offline-export, and legacy single-endpoint compatibility.
- Preserve deterministic transcript, PCAP, bundle, checksum, startup-order, and
  scenario-truth behavior.
- Run all unit tests, including the live `pymodbus` Modbus end-to-end tests.
- Ensure no docs or outputs claim operational validation, real plant identity,
  safety protection, certification, attack confirmation, commissioning
  readiness, field readiness, or full physical realism.
- Keep transcript/export features working without optional Modbus dependencies.

## Current Status

HS-1 through HS-20 are implemented for the Reference Water Plant release
candidate boundary. The runtime now supports deterministic selected-stage
artifacts, bundle export, profile validation, selected-area live launch
planning/orchestration, controller-state evidence, passive capture notes, and
quality-gate coverage.

The post-HS-20 path is now the CFD/digital-twin foundation described in
[HydraSim CFD/Digital-Twin Roadmap](CFD_DIGITAL_TWIN_ROADMAP.md). The first
foundation adds structured finite-volume meshes, bounded incompressible-flow
stepping, scalar transport, mixing helpers, reference area models, calibration
metadata, uncertainty records, and deterministic CFD summary export.
HS-26A additionally decomposes the Reference Water Plant into explicit
unit-process contracts for intake, dosing, clarification, filtration,
disinfection, storage/pumping, chemical feed, and waste/backwash handling.
HS-26B adds reusable boundary-condition contracts for inlets, outlets, pumps,
valves, dosing injection, mixers, baffles, filter media, backwash, drains,
recirculation, and free-surface level metadata.
HS-26C adds tiny, small, and medium CFD benchmark presets so later live coupling
work has measured CPU, memory, stability, and wall-time evidence before it
expands.
HS-27 adds simulated device-to-CFD coupling contracts: sensors can sample
declared spatial CFD regions and actuators can apply bounded scalar/source
effects while remaining `simulated_metadata`.
HS-28 adds simulated controller-to-CFD coupling contracts: controller
setpoint/error logic can produce bounded source effects through declared
actuator regions while remaining synthetic and uncalibrated.
HS-29 adds synthetic supervisory digital-twin records: HMI, historian, and
engineering-workstation style consumers can read CFD summaries and metadata
while keeping site identity unknown.
HS-29A adds synthetic operator/historian semantics: trend tags, advisory alarm
states, maintenance windows, operator actions, and engineering events for
training/review without claiming operational records.

Full CFD-coupled plant runtime, CFD-backed scenario truth, closed-loop scenario
timelines, lab bundle v2, calibration workflow, numerical verification,
early/late performance gates, and external validation evidence remain future
slices. Full-plant live orchestration is intentionally outside the HS-20
milestone; full-plant output is currently supported through `offline-export`.
