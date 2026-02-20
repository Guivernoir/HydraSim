# Water Treatment Simulator

Water treatment process simulator with:
- Multi-zone reactor physics (mixing, advection, pH/chlorine chemistry, temperature)
- Actuator dynamics (valves and dosing pump behavior)
- Sensor dynamics (delay, noise, drift, warm-up, faults)
- Modbus TCP server for plant-style command/feedback integration

The goal is practical plant-behavior emulation for integration and control testing. It is not a full CFD model and should not be treated as design authority for safety-critical decisions.

## Architecture

Runtime loop:
1. Read Modbus holding registers/coils.
2. Apply commands to actuator models.
3. Map actuator outputs to reactor boundary flows.
4. Step reactor physics.
5. Read sensors from reactor state.
6. Publish sensor values/status to Modbus input registers/discrete inputs.

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
python -m wt_simulator --host 127.0.0.1 --port 5020
```

Without Modbus:

```bash
python -m wt_simulator --no-modbus --duration 120 --dt 1
```

## Test

```bash
./venv/bin/python -m unittest discover -s tests -v
```

## Project Layout

- `src/wt_simulator/core`: reactor physics and transport/chemistry models
- `src/wt_simulator/actuators`: valves and dosing pump dynamics
- `src/wt_simulator/sensors`: sensor models and suite factory
- `src/wt_simulator/modbus`: register map, encoding, and Modbus server
- `src/wt_simulator/__main__.py`: runtime orchestration loop
- `tests`: unit and end-to-end Modbus tests

## Documentation

- `docs/MODEL_SCOPE.md`: what the model includes and what it does not
- `docs/MODBUS_INTERFACE.md`: command/feedback register behavior and control loop mapping

## License

MIT
