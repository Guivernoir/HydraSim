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

## Current Gate

HS-7 adds a repeatable project-quality gate. Current scenarios cover normal
operations, unknown-host review behavior, smart-field topology, maintenance
windows, abnormal process response, misconfiguration review, noisy Modbus
polling, and degraded operations.

The next roadmap decision should choose whether to refactor legacy oversized
physics/runtime modules, add richer multi-process endpoint orchestration, or
begin deeper process-scenario realism work.

## Safety Boundaries

- HydraSim scenarios target configured HydraSim endpoints only.
- HydraSim does not scan external networks.
- HydraSim does not discover devices.
- HydraSim does not claim operational validation.
- Unknown-host or abnormal behavior remains synthetic review behavior, not an
  attack, incident, compromise, or safety-impact conclusion.
- Passive observers are metadata only and must not be scenario participants.

## Completion Standard

A slice is complete only when:

- runtime behavior matches the slice boundary;
- docs describe how to use it;
- tests cover positive and rejection paths;
- generated files are not left in the working tree;
- full unittest discovery passes, allowing documented optional-dependency skips.
