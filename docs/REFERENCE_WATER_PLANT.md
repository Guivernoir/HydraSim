# HydraSim Reference Water Plant

HydraSim now includes a configurable synthetic reference water-treatment plant
surface for local training, integration, traffic-generation, and passive
analysis labs. It can model the full plant or a selected area/stage while
preserving legacy single-endpoint behavior.

This is a simulator. It is not a certified digital twin, commissioning model,
plant-design authority, safety system, or operational validation artifact.

## Profiles

| Profile | Purpose |
| --- | --- |
| `single-stage-legacy` | Compatibility profile for current single-endpoint Modbus behavior. |
| `field-device-lab` | Sensors, analyzers, actuators, and field endpoint personas. |
| `controller-cell` | Field endpoints plus PLC/RTU-like controller personas. |
| `supervisory-lab` | HMI, historian, engineering workstation, controller targets, and passive observer metadata. |
| `reference-water-plant` | Multi-area reference water plant with field, controller, and supervisory layers. |

## Areas

| Area | Contents |
| --- | --- |
| `intake` | Raw-water intake, flow, and intake valve context. |
| `dosing` | pH analyzer and chemical dosing pump context. |
| `clarification` | Clarifier/settling context and level instrumentation. |
| `filtration` | Filter differential pressure and backwash valve context. |
| `disinfection` | Chlorine analyzer and chlorine dosing context. |
| `storage-pumping` | Clearwell level and finished-water pumping context. |
| `distribution-edge` | Optional downstream edge-meter metadata context. |

## Stages

| Stage | Behavior |
| --- | --- |
| `field-devices` | Keeps field-device activation and field endpoint traffic. |
| `field-controllers` | Keeps PLC/RTU-like polling and bounded controller writes. |
| `supervisory` | Keeps HMI, historian, and engineering workstation traffic. |
| `full-cell` | Keeps field, controller, and supervisory traffic for one selected area. |
| `offline-export` | Allows `--area all` and writes deterministic transcript, PCAP, topology, manifest, and checksum artifacts. |

`--area all` is accepted only for `offline-export`. Selected-area runtime is
the safer default until live multi-process orchestration is separately proven.

## Control, Topology, And Media Choices

The `wts-ics` command accepts metadata overrides for:

- `--control-system scada-lite|pcs-minimal|dcs-lite`;
- `--topology flat-cell|segmented-cell|plant-zones`;
- `--media ethernet|serial-gateway-placeholder|mixed-lab`.

These choices affect generated metadata and lab artifacts. They do not claim
vendor emulation, serial-bus fidelity, physical-media fidelity, or real site
architecture.

## Built-In Scenarios

| Scenario | Name | Primary use |
| --- | --- | --- |
| `ICS-WTP-001` | Reference plant startup | Startup polling and activation traffic. |
| `ICS-WTP-002` | Reference plant normal operation | Routine polling and bounded control writes. |
| `ICS-WTP-003` | Planned maintenance | Maintenance-window reads and commands. |
| `ICS-WTP-004` | Chemical dosing upset | Dosing deviation context and corrective writes. |
| `ICS-WTP-005` | Pump failure context | Pumping-area alarm/review context. |
| `ICS-WTP-006` | Sensor drift context | Repeated analyzer polling with drift labels. |
| `ICS-WTP-007` | Analyzer fault context | Exception response and follow-up polling. |
| `ICS-WTP-008` | Filter backwash | Backwash command and follow-up polling. |
| `ICS-WTP-009` | Disinfection excursion | Disinfection review context and corrective writes. |
| `ICS-WTP-010` | Unknown workstation review | Range reads and writes that deserve review. |
| `ICS-WTP-011` | Noisy polling | Historian/HMI chatter and invalid-access noise. |
| `ICS-WTP-012` | Controller failover context | Primary/alternate controller review traffic. |

Scenario labels such as `must_review`, `exception_pattern`, or
`process_deviation_context` are synthetic review prompts. They are not incident,
attack, equipment-failure, or safety conclusions.

## Commands

List available profiles:

```bash
wts-ics list-profiles
```

Validate a profile:

```bash
wts-ics validate-profile reference-water-plant
```

Render a selected-stage transcript:

```bash
wts-ics run reference-water-plant \
  --scenario ICS-WTP-002 \
  --area disinfection \
  --stage full-cell \
  --format csv
```

Render a deterministic PCAP:

```bash
wts-ics run reference-water-plant \
  --scenario ICS-WTP-002 \
  --area all \
  --stage offline-export \
  --format pcap \
  --output reference-water-plant.pcap
```

Export a full lab bundle:

```bash
wts-ics export-bundle reference-water-plant ICS-WTP-002 ./reference-water-bundle \
  --area all \
  --stage offline-export
```

Preview a selected-area live endpoint launch plan:

```bash
wts-ics launch-live reference-water-plant \
  --scenario ICS-WTP-002 \
  --area disinfection \
  --stage full-cell \
  --dry-run
```

Launch selected-area synthetic endpoints for a short local run:

```bash
wts-ics launch-live reference-water-plant \
  --scenario ICS-WTP-002 \
  --area disinfection \
  --stage full-cell \
  --duration 30 \
  --log-dir ./reference-water-live-logs
```

Live launch starts local HydraSim Modbus process endpoints for the selected
area. It uses the common water-process runtime for each endpoint and does not
claim vendor PLC, RTU, HMI, or historian emulation.

Render the HS-35 Reference Water Plant CFD Release Candidate checklist:

```bash
wts-ics release-candidate --format markdown
wts-ics release-candidate --scenario ICS-WTP-004 --area dosing --format json
```

The release-candidate output has evidence status
`synthetic_reference_water_plant_cfd_release_candidate`. It ties together the
full-plant `offline-export` path, selected-area `full-cell` path,
selected-area live launch plan, CFD runtime performance gate, digital-twin
validation gate, external review/calibration gate, and expected bundle
artifacts. It is a release-candidate checklist, not real-plant validation,
commissioning evidence, certification, safety evidence, or field readiness.

The bundle contains:

- `summary.md`;
- `transcript.csv`;
- `topology.md`;
- `controller-states.csv`;
- `process-evolution.csv`;
- `process-review.csv`;
- `cfd-mesh-geometry.json`;
- `cfd-state-timeline.csv`;
- `cfd-scalar-fields.csv`;
- `cfd-flow-snapshots.csv`;
- `scenario.pcap`;
- `capture-notes.md`;
- `manifest.json`;
- `checksums.sha256`.

## HS-31 Scenario Library CFD Upgrade

HS-31 adds CFD-backed process evolution truth to each built-in reference water
plant scenario. Runtime artifacts and bundles now include
`synthetic_cfd_process_truth` records that describe selected area, scalar,
start value, end value, trend, CFD basis, and limitations.

The `process-evolution.csv` artifact is deterministic synthetic simulator truth.
It is useful for scenario review and regression, but it is not real-plant
validation, commissioning evidence, compliance evidence, or safety evidence.

## HS-31A Scenario Process-Truth Review

HS-31A adds a deterministic `process-review.csv` artifact to reference water
plant bundles. Each record ties together:

- the scenario's CFD process evolution;
- observable network effects such as reads, writes, exceptions, and review hints;
- operator, historian, HMI, engineering-workstation, and controller-state effects;
- reviewer questions for demo/training use;
- explicit `must_not_claim` text.

The process review evidence status is `synthetic_scenario_process_review`. It
is designed to help a reviewer check whether a scenario is coherent before it
is used in demos, training, or passive-analysis labs. It does not prove a real
plant condition, real equipment behavior, certification, safety impact,
operational validation, or calibrated plant equivalence.

## HS-32 CFD Lab Bundle v2

HS-32 adds compact CFD process-state evidence to reference water plant bundles:

- `cfd-mesh-geometry.json` records mesh dimensions, extents, boundaries,
  obstacles, digital-twin references, limitations, and the
  `synthetic_cfd_lab_bundle_v2` evidence status.
- `cfd-state-timeline.csv` records scenario process-state changes tied to the
  selected scenario and area.
- `cfd-scalar-fields.csv` records deterministic sampled scalar-field values at
  bounded mesh sample cells.
- `cfd-flow-snapshots.csv` records deterministic sampled velocity, pressure,
  mass-residual, CFL, and stability evidence.

These files let a lab bundle reproduce both network behavior and process-state
evidence in a compact form. They intentionally do not export unrestricted
full-field arrays and do not claim real-plant validation, commissioning
evidence, certification, safety-system protection, or full physical fidelity.

## HS-35 Reference Water Plant CFD Release Candidate

HS-35 adds a deterministic release-candidate checklist for the CFD-backed
Reference Water Plant surface. The checklist confirms:

- the `reference-water-plant` profile is available;
- a full-plant `offline-export` artifact can be built;
- a selected-area `full-cell` artifact can be built;
- a selected-area live orchestration plan has launchable synthetic Modbus
  endpoints;
- CFD runtime performance records pass for bounded local presets;
- the Digital-Twin Validation Gate remains implementation evidence only;
- the External Review And Calibration Evidence Gate remains pending or recorded
  without automatic model-status upgrade;
- the expected bundle artifact set includes transcript, PCAP, topology,
  controller state, process evolution, process review, compact CFD artifacts,
  manifest, notes, and checksums.

HS-35 does not add full-plant live orchestration, hardware qualification,
real-site calibration, operational validation, safety certification, or vendor
system emulation.

## Legacy Compatibility

The following commands remain supported:

- `wts-sim`;
- `wts-run-scenario`;
- `wts-validate-scenario`;
- `wts-export-lab-bundle`;
- `wts-mvp-modbus-scenario`.

Existing `MVP-MB-HYDRA-*` scenarios remain regression surfaces. The new
Reference Water Plant scenarios are additive.

## Current Boundary

Implemented:

- profile-driven plant hierarchy;
- selected-area and selected-stage artifact generation;
- selected-area live endpoint launch planning and orchestration;
- deterministic transcript and classic Ethernet PCAP export;
- controller/HMI/historian/engineering-workstation traffic personas;
- deterministic controller mode/routine/alarm/setpoint/effect evidence;
- deterministic CFD-backed process evolution evidence;
- deterministic scenario process-truth review evidence;
- compact CFD Lab Bundle v2 process-state evidence;
- deterministic Reference Water Plant CFD Release Candidate checklist;
- topology, media, and control-system metadata;
- create-new lab bundle export;
- profile/scenario documentation coverage checks.

Not claimed:

- vendor SCADA, DCS, PLC, RTU, historian, or engineering workstation emulation;
- area-specific multi-physics coupling for every launched endpoint;
- safety-system or SIS behavior;
- certified, commissioning-grade, or physically complete water-treatment design;
- real operational validation or field readiness.
