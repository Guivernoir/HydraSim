# HydraSim Scenario Runtime

HydraSim now has two explicit runtime roles:

1. The **process endpoint**: the water-treatment physics model, sensors,
   actuators, maintenance model, and Modbus TCP server.
2. The **scenario command center**: deterministic synthetic clients that can
   read, write, and exercise the process endpoint according to a selected
   scenario.

This keeps the simulator useful as a standalone OT test environment. It can run
the process side, drive realistic client behavior, and allow any passive
capture/analysis tool to observe the resulting traffic.

## Locked Runtime Boundary

- HydraSim drives only the configured HydraSim Modbus endpoint.
- HydraSim does not scan networks.
- HydraSim does not discover external devices.
- HydraSim does not claim operational, safety, or field validation.
- Built-in scenarios are deterministic and synthetic.
- Custom scenarios must be explicit JSON files.
- Live scenario execution requires the optional `pymodbus` dependency.

## Built-In Scenarios

| Alias | Canonical ID | Purpose |
| --- | --- | --- |
| `water-treatment-normal` | `MVP-MB-HYDRA-002` | HMI-like, historian-like, and maintenance client behavior against the process endpoint. |
| `water-treatment-unknown-host` | `MVP-MB-HYDRA-003` | Normal behavior plus unknown-client reads, exception-style access, and writes that deserve review. |
| `water-treatment-smart-field` | `MVP-MB-HYDRA-004` | Process endpoint plus explicitly modeled networked pH probe and chlorine pump endpoint identities. |
| `water-treatment-maintenance-window` | `MVP-MB-HYDRA-005` | Planned maintenance precheck, action selection, trigger, and status-poll sequence. |
| `water-treatment-process-fault` | `MVP-MB-HYDRA-006` | Abnormal process context with corrective operator adjustments. |
| `water-treatment-misconfiguration` | `MVP-MB-HYDRA-007` | Unusual configuration-like writes that deserve review. |
| `water-treatment-noisy-network` | `MVP-MB-HYDRA-008` | High-chatter polling plus invalid-access Modbus responses. |
| `water-treatment-degraded-operations` | `MVP-MB-HYDRA-009` | Lower-rate polling and reduced setpoint context. |

The unknown-host scenario is intentionally phrased as review-worthy synthetic
behavior, not an incident, compromise, malicious-intent, or safety-impact claim.

## Export Transcript

```bash
wts-run-scenario water-treatment-normal --mode transcript --format csv
wts-run-scenario water-treatment-unknown-host --mode transcript --format markdown
wts-run-scenario water-treatment-noisy-network --mode transcript --format csv
```

Transcript mode does not open a network connection. It exports scenario truth
for documentation, traffic generation, or replay planning.

## Export Deterministic PCAP

HS-4 adds dependency-free classic-PCAP export for validated scenarios:

```bash
wts-run-scenario water-treatment-normal --mode transcript --format pcap --output normal.pcap
wts-run-scenario water-treatment-smart-field --mode transcript --format pcap --output smart-field.pcap
```

PCAP export creates deterministic Ethernet/IPv4/TCP/Modbus request and response
frames from scenario truth. It is transcript-derived synthetic traffic, not raw
operational capture and not proof of field behavior.

## Export Lab Bundle

HS-5 adds a one-command deterministic lab bundle:

```bash
wts-export-lab-bundle water-treatment-smart-field ./hydrasim-smart-field-bundle
```

The bundle contains:

- `transcript.csv`;
- `summary.md`;
- `scenario.pcap`;
- `manifest.json`;
- `capture-notes.md`;
- `checksums.sha256`.

The bundle is intended for repeatable local lab use. It is still synthetic
simulator output and does not contain operational traffic.

## Scenario Library Families

The built-in library now covers:

- normal multi-client operations;
- planned maintenance windows;
- abnormal process-response context;
- unknown-host review behavior;
- misconfiguration review behavior;
- high-chatter Modbus/noisy polling;
- degraded-operations context;
- explicit smart-field endpoint topology.

These families are deterministic source truth for lab traffic. They are not
evidence of real attacks, operator mistakes, plant health, safety impact, or
field deployment behavior.

## Run Live Against HydraSim

Start the process endpoint:

```bash
wts-sim --host 127.0.0.1 --port 5020
```

In a second terminal, run the command center:

```bash
wts-run-scenario water-treatment-normal --mode live --host 127.0.0.1 --port 5020
```

Live mode uses Modbus client requests to produce real local traffic. Use
`--time-scale 0` for immediate replay or a positive value to preserve relative
scenario timing.

## One-Command Scenario Replay

For convenience, `wts-sim` can start the process endpoint and schedule scenario
replay from the same command:

```bash
wts-sim --host 127.0.0.1 --port 5020 --scenario water-treatment-normal
```

Custom scenarios can also be replayed this way:

```bash
wts-sim --scenario custom --scenario-custom-json custom-scenario.json
```

The scenario runner waits briefly after Modbus startup before connecting. Use
`--scenario-delay` and `--scenario-time-scale` to tune startup timing and replay
speed.

One-command replay is intended for single-endpoint scenarios. Multi-endpoint
live replay should use `wts-run-scenario --target` so each server node maps to a
specific local endpoint.

## Multi-Endpoint Scenario Replay

`water-treatment-smart-field` models the process endpoint, a networked pH probe,
and a networked chlorine pump as separate Modbus server identities.

Transcript mode works immediately:

```bash
wts-run-scenario water-treatment-smart-field --mode transcript --format markdown
```

Live mode requires explicit targets for every server node:

```bash
wts-run-scenario water-treatment-smart-field --mode live \
  --target hydra_a=127.0.0.1:5020 \
  --target ph_probe_a=127.0.0.1:5021 \
  --target chlorine_pump_a=127.0.0.1:5022
```

HydraSim does not automatically create multiple process endpoints in HS-3. The
multi-target replay boundary exists so later slices can attach concrete
multi-endpoint simulator instances without changing scenario truth.

## Custom Scenario JSON

Custom scenarios use the same profile shape as built-in scenarios:

```json
{
  "scenario_id": "CUSTOM-001",
  "name": "Custom read-only check",
  "purpose": "Exercise a custom client against HydraSim.",
  "nodes": [
    {
      "node_id": "client",
      "label": "Custom client",
      "mac": "02:00:00:00:40:10",
      "ipv4": "203.0.113.10",
      "role": "client"
    },
    {
      "node_id": "hydra",
      "label": "HydraSim endpoint",
      "mac": "02:00:00:00:40:20",
      "ipv4": "203.0.113.20",
      "role": "Modbus TCP process endpoint",
      "modbus_port": 502
    }
  ],
  "field_points": [],
  "transactions": [
    {
      "ordinal": 1,
      "timestamp_ms": 0,
      "actor_id": "client",
      "server_id": "hydra",
      "function_code": 4,
      "operation": "read_input_registers",
      "address": 0,
      "quantity": 2,
      "response": "ok",
      "scenario_label": "custom_read"
    }
  ],
  "limitations": ["custom synthetic scenario"]
}
```

Run it with:

```bash
wts-validate-scenario custom --custom-json custom-scenario.json
wts-run-scenario custom --custom-json custom-scenario.json --mode transcript
```

Supported live Modbus operations are:

| Function code | Operation |
| ---: | --- |
| `3` | Read holding registers |
| `4` | Read input registers |
| `5` | Write single coil |
| `6` | Write single register |
| `16` | Write multiple registers |

Write operations must include `wire_values`, a list of unsigned 16-bit register
or coil values. This makes replay deterministic and avoids guessing how a
human-readable value summary should be encoded.

## Scenario Validation

HS-2 makes validation mandatory before a scenario becomes source truth. The
validator checks:

- unique node and field-point IDs;
- monotonic transaction timestamps;
- valid actor and server references;
- no passive observer as actor or server;
- supported Modbus function codes;
- operation names that match function codes;
- deterministic `wire_values` for writes;
- source limitations.

Validate built-ins or custom JSON with:

```bash
wts-validate-scenario water-treatment-normal
wts-validate-scenario custom --custom-json custom-scenario.json
```

## Passive Capture Use

HydraSim does not need to know which tool is observing it. To capture traffic,
run the process endpoint and command center, then use a separate passive capture
tool on the chosen interface. The observer should not transmit traffic into the
scenario unless a separate test deliberately makes it a client.
