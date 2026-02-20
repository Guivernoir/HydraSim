# Modbus Interface

This simulator exposes process I/O through a Modbus TCP server so an external controller can behave as if it is connected to a plant.

## Control Direction

Inputs from controller:
- Holding registers: analog commands (flow rates, stock concentrations)
- Coils: enable/disable bits and run/pause bit

Feedback to controller:
- Input registers: sensor values and runtime status
- Discrete inputs: sensor fault bits

The Modbus server does not generate autonomous control actions. It receives commands and publishes process feedback.

## Runtime Mapping

Each simulation cycle:
1. Read Modbus command registers/coils.
2. Apply command setpoints to actuator models.
3. Step actuators and write resulting flows into reactor boundary conditions.
4. Step reactor physics.
5. Read sensors from updated reactor state.
6. Publish sensor values and fault/status bits to Modbus inputs.

## Addressing Notes

- Register names and base addresses are defined in `src/wt_simulator/modbus/register_map.py`.
- Use register names through the in-process API (`ModbusSlave.read_holding_register(...)`, etc.) where possible.
- External clients should use the documented Modbus addresses from the register map.

## Common Signals

## Holding registers (examples)
- `acid_flow_rate`
- `chlorine_flow_rate`
- `inlet_flow_rate`
- `acid_concentration`
- `chlorine_concentration`

## Coils (examples)
- `acid_pump_enable`
- `chlorine_pump_enable`
- `simulation_running`

## Input registers (examples)
- `pH_inlet`, `pH_middle`, `pH_outlet`
- `chlorine_inlet`, `chlorine_outlet`
- `flow_rate`
- `temperature_inlet`, `temperature_outlet`
- `simulation_time`, `system_status`

## Discrete inputs (examples)
- `sensor_fault_pH_inlet`
- `sensor_fault_pH_outlet`
- `sensor_fault_chlorine`

## Verification

Run end-to-end tests:

```bash
./venv/bin/python -m unittest tests/test_modbus_e2e.py -v
```
