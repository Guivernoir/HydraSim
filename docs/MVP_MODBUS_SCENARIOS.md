# MVP Modbus Scenario Profiles

HydraSim can export deterministic Modbus MVP scenario profiles and run them as
local command-center traffic against the HydraSim process endpoint.

These profiles are source truth for synthetic traffic generation. The process
endpoint remains separate from the command-center runner. Passive observers are
collection roles only and should not appear as Modbus participants unless a
test deliberately makes them clients.

## Scenario IDs

| Scenario | Purpose |
| --- | --- |
| `MVP-MB-HYDRA-002` | Normal multi-client operations with HMI-like, historian-like, and maintenance clients interacting with the HydraSim process endpoint. |
| `MVP-MB-HYDRA-003` | Normal operations plus an unknown client that performs enumeration-like reads, invalid accesses, and writes that deserve review. |
| `MVP-MB-HYDRA-004` | Process endpoint plus explicitly modeled networked field sensor and actuator endpoint identities. |
| `MVP-MB-HYDRA-005` | Planned maintenance-window command sequence with precheck, maintenance writes, trigger, and post-maintenance polling. |
| `MVP-MB-HYDRA-006` | Abnormal process response context with corrective operator adjustments. |
| `MVP-MB-HYDRA-007` | Misconfiguration review scenario with unusual configuration-like writes. |
| `MVP-MB-HYDRA-008` | Noisy Modbus polling and invalid-access coverage scenario. |
| `MVP-MB-HYDRA-009` | Degraded-operations scenario with lower-rate polling and reduced setpoint context. |

HydraSim's richer built-in profiles start at `HYDRA-002` to distinguish them
from earlier single-endpoint external fixture work.

## Passive-Listener Boundary

The scenario profiles include a `Passive capture observer` node as collection
metadata only. It is not used as a Modbus client, server, scanner, controller,
or writer. Normal scenario traces should not contain the observer as a traffic
participant.

## Field Points vs Network Assets

HydraSim models pH, chlorine, flow, temperature, valves, and dosing equipment.
In the MVP scenario profiles, these are **supplied simulated field points**
behind the process endpoint, not automatically separate MAC/IP assets.

This is intentional. Many OT sensors and actuators are represented as field
points behind a PLC, RTU, remote I/O rack, or gateway. A later smart-field or
IIoT scenario may give selected sensors/actuators their own network identities,
but that should be a separate scenario so reviewers can see the difference.

## Export Commands

After installing the package:

```bash
wts-mvp-modbus-scenario MVP-MB-HYDRA-002 --format csv --output hydra-002.csv
wts-mvp-modbus-scenario MVP-MB-HYDRA-003 --format markdown --output hydra-003.md
```

The newer unified runner can export the same scenarios or run them live:

```bash
wts-validate-scenario water-treatment-normal
wts-run-scenario water-treatment-normal --mode transcript --format csv
wts-run-scenario water-treatment-unknown-host --mode live --host 127.0.0.1 --port 5020
wts-run-scenario water-treatment-misconfiguration --mode transcript --format markdown
```

Without installation, run from the repository root:

```bash
python -m wt_simulator.scenarios.mvp_modbus MVP-MB-HYDRA-002 --format csv
```

The CSV transcript columns are:

| Column | Meaning |
| --- | --- |
| `ordinal` | Deterministic transaction order. |
| `timestamp_ms` | Scenario timestamp in milliseconds. |
| `actor_id` | Synthetic external client role. |
| `server_id` | HydraSim process endpoint. |
| `function_code` | Modbus function code. |
| `operation` | Human-readable operation name. |
| `address` | Starting register or coil address. |
| `quantity` | Quantity or single-value width depending on operation. |
| `value_summary` | Scenario-level value summary for writes. |
| `response` | Expected high-level response status. |
| `scenario_label` | Normal, maintenance, or unknown-host scenario tag. |
| `review_hint` | Optional review-candidate label for external reporting tools. |
| `wire_values` | Deterministic uint16 values used for live write replay. |

## Deterministic PCAP Export

Validated scenarios can also be exported as classic Ethernet PCAP files:

```bash
wts-run-scenario water-treatment-normal --mode transcript --format pcap --output normal.pcap
```

PCAP output is generated from scenario truth with deterministic Ethernet,
IPv4, TCP, and Modbus frames. It is synthetic and reproducible; it is not a raw
capture from an operational network.

## Normal Operations Scenario

`MVP-MB-HYDRA-002` contains:

- HMI-like reads of process/status values.
- Historian-like read-only polling.
- Operator writes to process setpoints.
- Engineering/maintenance reads and writes during a maintenance window.
- Maintenance trigger coil activity.

## Unknown-Host Scenario

`MVP-MB-HYDRA-003` extends the normal scenario with:

- an unknown client reading multiple distinct ranges;
- invalid or unsupported register access;
- writes to process and maintenance registers outside the normal actor profile.

These activities are review candidates only. They are not attack, compromise,
incident, malicious-intent, process-impact, or safety-impact claims.

## Smart-Field Multi-Node Scenario

`MVP-MB-HYDRA-004` models:

- the primary HydraSim process endpoint;
- a networked pH probe endpoint;
- a networked chlorine pump endpoint;
- HMI-like, historian-like, and maintenance clients.

This scenario exists to show the difference between field points behind a
process endpoint and explicitly modeled networked field devices. It does not
mean HydraSim has discovered real devices, and it does not automatically launch
multiple Modbus servers. Live replay requires explicit target mappings for each
server node.

## Expanded Scenario Families

HS-6 adds a broader scenario menu:

- `MVP-MB-HYDRA-005` / `water-treatment-maintenance-window`: a planned
  maintenance sequence with precheck reads, maintenance target/action writes,
  trigger coil activity, and after-action polling.
- `MVP-MB-HYDRA-006` / `water-treatment-process-fault`: abnormal process
  context and corrective operator adjustments. The labels are scenario truth,
  not proof of real process deviation.
- `MVP-MB-HYDRA-007` / `water-treatment-misconfiguration`: unusual
  configuration-like writes that deserve review. This does not claim operator
  error, malicious intent, or process impact.
- `MVP-MB-HYDRA-008` / `water-treatment-noisy-network`: high-chatter polling
  and invalid-access responses. This models Modbus traffic noise, not packet
  loss or malformed Ethernet.
- `MVP-MB-HYDRA-009` / `water-treatment-degraded-operations`: reduced setpoint
  and slower-poll context for degraded-mode conversation. This is synthetic
  scenario context, not proof of a real plant state.

## Limitations

- Scenario outputs are synthetic and deterministic.
- They are not operational captures.
- They are not customer data.
- They do not validate field safety.
- They do not imply HydraSim physics are externally validated.
- Scenario labels are prompts for testing and discussion, not operational
  conclusions.

## Passive Analysis Integration

Any passive analysis tool can consume these profiles as source truth for
transcript-derived captures or live replay. Analysis tools should record their
own source manifest, checksum, fixture truth, report assertions, and limitations
outside the HydraSim repository.
