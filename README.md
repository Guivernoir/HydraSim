# HydraSim

Water treatment process simulator with:
- Multi-zone reactor physics (mixing, advection, pH/chlorine chemistry, temperature)
- Actuator dynamics (valves and dosing pump behavior)
- Sensor dynamics (delay, noise, drift, warm-up, faults)
- Remote maintenance (Modbus-driven recalibration and hardware-replacement actions)
- Modbus TCP server for plant-style command/feedback integration
- Deterministic Modbus MVP scenario profiles for external traffic generators
- Scenario command-center runner for repeatable local Modbus traffic generation

HydraSim is designed to emulate realistic water treatment process behavior for integration and control testing against real-world PLC/SCADA systems. It allows engineers and researchers to prototype control logic, validate operational behaviors, and exercise control loops without access to physical hardware.

The goal is practical plant-behavior emulation for integration and control testing. It is not a full CFD model and should not be treated as design authority for safety-critical decisions.

## Architecture

Runtime loop:
1. Read Modbus holding registers/coils.
2. Apply commands to actuator models.
3. Map actuator outputs to reactor boundary flows.
4. Step reactor physics.
5. Read sensors from reactor state.
6. Publish sensor values/status to Modbus input registers/discrete inputs.
7. Poll maintenance trigger coil; dispatch any pending maintenance action.

This keeps command sources external while the simulator acts like a field-facing process unit.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For Modbus support:

```bash
pip install -e ".[modbus]"
```

## Run

With Modbus:

```bash
python -m src.wt_simulator --host 127.0.0.1 --port 5020
```

Without Modbus:

```bash
python -m src.wt_simulator --no-modbus --duration 120 --dt 1
```

Export a deterministic MVP Modbus scenario transcript:

```bash
wts-mvp-modbus-scenario MVP-MB-HYDRA-002 --format csv --output hydra-002.csv
wts-mvp-modbus-scenario MVP-MB-HYDRA-003 --format markdown --output hydra-003.md
```

Run a built-in command-center scenario against a HydraSim process endpoint:

```bash
wts-sim --host 127.0.0.1 --port 5020
wts-run-scenario water-treatment-normal --mode live --host 127.0.0.1 --port 5020
```

Export a multi-endpoint smart-field scenario:

```bash
wts-run-scenario water-treatment-smart-field --mode transcript --format markdown
```

Export a broader HS-6 scenario family:

```bash
wts-run-scenario water-treatment-misconfiguration --mode transcript --format markdown
wts-run-scenario water-treatment-noisy-network --mode transcript --format pcap --output noisy.pcap
```

Export a complete deterministic lab bundle:

```bash
wts-export-lab-bundle water-treatment-smart-field ./hydrasim-smart-field-bundle
```

Or start the process endpoint and scenario replay from one simulator command:

```bash
wts-sim --host 127.0.0.1 --port 5020 --scenario water-treatment-normal
```

Run or export a custom JSON scenario:

```bash
wts-run-scenario custom --custom-json docs/CUSTOM_SCENARIO_TEMPLATE.json --mode transcript
wts-validate-scenario custom --custom-json docs/CUSTOM_SCENARIO_TEMPLATE.json
wts-sim --scenario custom --scenario-custom-json docs/CUSTOM_SCENARIO_TEMPLATE.json
```

These scenarios describe synthetic external client behavior. HydraSim remains a
simulator; passive observers should remain passive unless a separate test
intentionally makes them clients.

## Test

```bash
./venv/bin/python -m unittest discover -s tests -v
```

Run the local quality gate:

```bash
python tools/check_project_quality.py
python -m black --check src/wt_simulator/scenarios tests/test_mvp_modbus_scenarios.py tools
python -m unittest discover -s tests -v
```

## Project Layout

- `src/wt_simulator/core`: reactor physics and transport/chemistry models
- `src/wt_simulator/actuators`: valves and dosing pump dynamics
- `src/wt_simulator/sensors`: sensor models and suite factory
- `src/wt_simulator/maintenance`: remote recalibration and hardware-replacement manager
- `src/wt_simulator/modbus`: register map, encoding, and Modbus server
- `src/wt_simulator/__main__.py`: runtime orchestration loop
- `tests`: unit and end-to-end Modbus tests

## Documentation

- `docs/MODEL_SCOPE.md`: what the model includes and what it does not
- `docs/IMPLEMENTATION_PROCESS.md`: lock-first slice process and verification expectations
- `docs/MODBUS_INTERFACE.md`: command/feedback register behavior, control loop mapping, and maintenance register protocol
- `docs/MVP_MODBUS_SCENARIOS.md`: deterministic multi-client and unknown-host Modbus scenario profiles for synthetic traffic generation
- `docs/QUALITY_BASELINE.md`: current quality gate and legacy oversized-module baseline
- `docs/SCENARIO_RUNTIME.md`: command-center runner, custom scenarios, live replay, and passive capture boundary
- `docs/SLICE_ROADMAP.md`: HydraSim slice sequence and current implementation gate

## License

MIT
