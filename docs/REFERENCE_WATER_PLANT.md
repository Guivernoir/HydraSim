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

The bundle contains:

- `summary.md`;
- `transcript.csv`;
- `topology.md`;
- `controller-states.csv`;
- `process-evolution.csv`;
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
- topology, media, and control-system metadata;
- create-new lab bundle export;
- profile/scenario documentation coverage checks.

Not claimed:

- vendor SCADA, DCS, PLC, RTU, historian, or engineering workstation emulation;
- area-specific multi-physics coupling for every launched endpoint;
- safety-system or SIS behavior;
- certified, commissioning-grade, or physically complete water-treatment design;
- real operational validation or field readiness.
