# HydraSim Today: Before And After

This note summarizes the full set of changes made today across the HydraSim
industrial-simulator direction. It covers the roadmap refinement and the
implemented Reference Water Plant surface, not only the final coding pass.

## Before

HydraSim was already useful as a water-treatment process simulator with:

- reactor physics, transport, chemistry, sensors, actuators, maintenance, and
  Modbus integration;
- a single process endpoint runtime through `wts-sim`;
- deterministic MVP Modbus scenarios through `wts-mvp-modbus-scenario`;
- command-center scenarios through `wts-run-scenario`;
- deterministic scenario PCAP/lab-bundle export through
  `wts-export-lab-bundle`;
- quality checks for scenario validation, Markdown links, folder density, line
  limits, and legacy oversized-module debt.

The main limitation was structural: HydraSim behaved mostly like a process unit
or scenario generator, not a staged ICS simulator with selectable plant areas,
controllers, supervisory roles, topology, media metadata, and full-plant
offline bundles.

## After

HydraSim now has a configurable Reference Water Plant layer:

- plant hierarchy: plant, area, unit, stage;
- plant areas: intake, dosing, clarification, filtration, disinfection,
  storage-pumping, and distribution-edge;
- plant presets:
  - `single-stage-legacy`;
  - `field-device-lab`;
  - `controller-cell`;
  - `supervisory-lab`;
  - `reference-water-plant`;
- stage selections:
  - `field-devices`;
  - `field-controllers`;
  - `supervisory`;
  - `full-cell`;
  - `offline-export`;
- control-system metadata choices:
  - `scada-lite`;
  - `pcs-minimal`;
  - `dcs-lite`;
- topology/media metadata choices:
  - `flat-cell`;
  - `segmented-cell`;
  - `plant-zones`;
  - `ethernet`;
  - `serial-gateway-placeholder`;
  - `mixed-lab`.

## New Runtime Surface

The new `wts-ics` command provides:

```bash
wts-ics list-profiles
wts-ics validate-profile reference-water-plant
wts-ics run reference-water-plant --scenario ICS-WTP-002 --area disinfection --stage full-cell --format markdown
wts-ics run reference-water-plant --scenario ICS-WTP-002 --area all --stage offline-export --format pcap --output reference-water-plant.pcap
wts-ics export-bundle reference-water-plant ICS-WTP-002 ./reference-water-bundle --area all --stage offline-export
wts-ics launch-live reference-water-plant --scenario ICS-WTP-002 --area disinfection --stage full-cell --dry-run
```

The `run` and `export-bundle` paths generate deterministic artifacts. The
`launch-live` path can preview or start selected-area local synthetic Modbus
endpoint processes with deterministic port assignment and lifecycle handling.

## New Scenario Library

The Reference Water Plant adds these staged scenarios:

| Scenario | Name |
| --- | --- |
| `ICS-WTP-001` | Reference plant startup |
| `ICS-WTP-002` | Reference plant normal operation |
| `ICS-WTP-003` | Planned maintenance |
| `ICS-WTP-004` | Chemical dosing upset |
| `ICS-WTP-005` | Pump failure context |
| `ICS-WTP-006` | Sensor drift context |
| `ICS-WTP-007` | Analyzer fault context |
| `ICS-WTP-008` | Filter backwash |
| `ICS-WTP-009` | Disinfection excursion |
| `ICS-WTP-010` | Unknown workstation review |
| `ICS-WTP-011` | Noisy polling |
| `ICS-WTP-012` | Controller failover context |

Each scenario remains synthetic and deterministic. Review labels are prompts for
analysis and training, not incident, attack, safety, failure, or commissioning
conclusions.

## New Artifacts

`wts-ics export-bundle` writes:

- `summary.md`;
- `transcript.csv`;
- `topology.md`;
- `controller-states.csv`;
- `scenario.pcap`;
- `capture-notes.md`;
- `manifest.json`;
- `checksums.sha256`.

The PCAP is transcript-derived classic Ethernet/IPv4/TCP/Modbus traffic with
synthetic locally administered MAC addresses and documentation-safe IPv4
addresses.

## New Quality Guardrails

The quality gate now validates:

- every built-in ICS profile;
- every built-in ICS scenario documentation reference;
- deterministic Reference Water Plant transcript output;
- deterministic Reference Water Plant PCAP output;
- Reference Water Plant live orchestration plan/lifecycle behavior;
- line-count policy for the new `src/wt_simulator/ics` modules;
- Black formatting for the new package and tests.

The large scenario data file introduced during development was split into
smaller modules so the new code stays under the 500-line policy.

## Preserved Compatibility

The following remain supported:

- `wts-sim`;
- `wts-run-scenario`;
- `wts-validate-scenario`;
- `wts-export-lab-bundle`;
- `wts-mvp-modbus-scenario`;
- existing `MVP-MB-HYDRA-*` scenario profiles.

## Honest Remaining Gaps

HydraSim still does not claim:

- certified water-treatment fidelity;
- commissioning-grade plant design authority;
- operational validation;
- field readiness;
- safety protection;
- real PLC/RTU/HMI/historian vendor emulation;
- attack confirmation;
- vendor-accurate multi-process plant orchestration;
- area-specific physics per launched endpoint.

The next major engineering step should be deeper fidelity: area-specific
process physics and richer controller behavior for each launched endpoint.
