# HydraSim

Water treatment process simulator with:
- Multi-zone reactor physics (mixing, advection, pH/chlorine chemistry, temperature)
- Actuator dynamics (valves and dosing pump behavior)
- Sensor dynamics (delay, noise, drift, warm-up, faults)
- Remote maintenance (Modbus-driven recalibration and hardware-replacement actions)
- Modbus TCP server for plant-style command/feedback integration
- Deterministic Modbus MVP scenario profiles for external traffic generators
- Scenario command-center runner for repeatable local Modbus traffic generation
- Configurable Reference Water Plant profiles for staged ICS-style lab bundles
- CFD/digital-twin foundation primitives for bounded finite-volume water-treatment models
- CFD-backed process-evolution truth for built-in reference plant scenarios
- Scenario process-truth review records for demo/training coherence checks
- CFD Lab Bundle v2 artifacts with compact mesh, geometry, scalar, flow, and state evidence
- Runtime Performance Gate evidence for bounded local CFD presets
- Digital-Twin Validation Gate evidence separating implementation verification from real-plant validation
- External Review And Calibration Evidence Gate records for non-validating review evidence
- Reference Water Plant CFD release-candidate checklist and command surface

HydraSim is designed to emulate realistic water treatment process behavior for integration and control testing against real-world PLC/SCADA systems. It allows engineers and researchers to prototype control logic, validate operational behaviors, and exercise control loops without access to physical hardware.

The goal is practical plant-behavior emulation for integration and control testing. The post-HS-20 direction adds bounded in-process CFD/digital-twin primitives, including `synthetic_digital_twin_validation_gate` records whose current real-plant validation status is `blocked_missing_real_calibration_and_external_validation`. HS-34A also adds `synthetic_external_review_calibration_gate` records that default to `pending_external_review` and never auto-upgrade model status. HS-35 adds `synthetic_reference_water_plant_cfd_release_candidate` evidence tying the current offline, selected-area live, CFD gate, and bundle surfaces into one release-candidate checklist. HydraSim still must not be treated as certified design authority, commissioning evidence, safety validation, or real-plant equivalence without separate calibration and validation evidence.

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
pip install -e ".[dev,modbus]"
```

For runtime-only Modbus support outside development:

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

List and export staged Reference Water Plant profiles:

```bash
wts-ics list-profiles
wts-ics validate-profile reference-water-plant
wts-ics run reference-water-plant --scenario ICS-WTP-002 --area disinfection --stage full-cell --format markdown
wts-ics export-bundle reference-water-plant ICS-WTP-002 ./reference-water-bundle --area all --stage offline-export
wts-ics launch-live reference-water-plant --scenario ICS-WTP-002 --area disinfection --stage full-cell --dry-run
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
.venv/bin/python -m pip install -e ".[dev,modbus]"
.venv/bin/python -m unittest discover -s tests -v
```

Run the local quality gate:

```bash
.venv/bin/python -m pip install -e ".[dev,modbus]"
.venv/bin/python tools/check_project_quality.py
.venv/bin/python -m black --check src/wt_simulator/scenarios src/wt_simulator/ics src/wt_simulator/hydraulics tests/test_mvp_modbus_scenarios.py tests/test_ics_runtime.py tests/test_cfd_digital_twin.py tests/test_cfd_coupling.py tests/test_cfd_operator_semantics.py tests/test_cfd_calibration_evidence.py tests/test_cfd_verification.py tools
.venv/bin/python -m unittest discover -s tests -v
```

The full quality gate requires the `pymodbus` dependency so the live Modbus
end-to-end tests run instead of being skipped.

## Project Layout

- `src/wt_simulator/core`: reactor physics and transport/chemistry models
- `src/wt_simulator/hydraulics`: CFD/digital-twin foundations for bounded water-treatment meshes, flow, scalar transport, and area models
- `src/wt_simulator/actuators`: valves and dosing pump dynamics
- `src/wt_simulator/sensors`: sensor models and suite factory
- `src/wt_simulator/maintenance`: remote recalibration and hardware-replacement manager
- `src/wt_simulator/modbus`: register map, encoding, and Modbus server
- `src/wt_simulator/ics`: staged Reference Water Plant profiles, scenarios, artifacts, and CLI
- `src/wt_simulator/__main__.py`: runtime orchestration loop
- `tests`: unit and end-to-end Modbus tests

## Documentation

- `docs/MODEL_SCOPE.md`: what the model includes and what it does not
- `docs/CFD_DIGITAL_TWIN_ROADMAP.md`: HS-21 through HS-35 CFD/digital-twin foundation roadmap and current gate
- `docs/HYDRASIM_TODAY_BEFORE_AFTER.md`: summary of the Reference Water Plant roadmap and implementation changes
- `docs/IMPLEMENTATION_PROCESS.md`: lock-first slice process and verification expectations
- `docs/INDUSTRIAL_SIMULATOR_ROADMAP.md`: HS-8 through HS-20 plan for staged ICS simulator evolution
- `docs/MODBUS_INTERFACE.md`: command/feedback register behavior, control loop mapping, and maintenance register protocol
- `docs/MVP_MODBUS_SCENARIOS.md`: deterministic multi-client and unknown-host Modbus scenario profiles for synthetic traffic generation
- `docs/QUALITY_BASELINE.md`: current quality gate and legacy oversized-module baseline
- `docs/REFERENCE_WATER_PLANT.md`: profile-driven Reference Water Plant commands, scenarios, artifacts, and limits
- `docs/SCENARIO_RUNTIME.md`: command-center runner, custom scenarios, live replay, and passive capture boundary
- `docs/SLICE_ROADMAP.md`: HydraSim slice sequence and current implementation gate

## License

MIT
