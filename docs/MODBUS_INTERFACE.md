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

## Maintenance Protocol

Field devices (sensors and actuators) can be recalibrated or have hardware components replaced remotely via a dedicated set of Modbus registers. The `MaintenanceManager` processes these commands in the simulation loop immediately after sensor feedback is published.

### Registers

| Space | Address | Name | Type | Description |
|---|---|---|---|---|
| Holding | HR 200 | `maintenance_target_id` | uint16 | Target device (see table below) |
| Holding | HR 201 | `maintenance_action_code` | uint16 | Action to perform (see table below) |
| Holding | HR 202–203 | `maintenance_param` | float32 | Action parameter; write `0.0` if unused |
| Coil | Coil 10 | `maintenance_trigger` | bool | Write `True` to execute; auto-cleared after execution |
| Input | IR 110 | `maintenance_status_code` | uint16 | Result: 0=SUCCESS, 1=INVALID_TARGET, 2=INVALID_ACTION, 3=NOT_SUPPORTED, 4=EXECUTION_ERROR, 5=PENDING |
| Input | IR 111 | `maintenance_last_target` | uint16 | Echo of `target_id` |
| Input | IR 112 | `maintenance_last_action` | uint16 | Echo of `action_code` |

### Workflow

1. Write `target_id`   → HR 200
2. Write `action_code` → HR 201
3. Write `param`       → HR 202–203 (float32; write `0.0` if unused)
4. Write `True`        → Coil 10 (triggers execution on next simulation tick)
5. Poll IR 110 until value ≠ 5 (PENDING)
6. Read IR 110 for final status; IR 111–112 for echo confirmation

### Target IDs

| ID | Name | Device type |
|---|---|---|
| 0 | pH_inlet | Sensor |
| 1 | pH_middle | Sensor |
| 2 | pH_outlet | Sensor |
| 3 | chlorine_inlet | Sensor (amperometric) |
| 4 | chlorine_outlet | Sensor (DPD) |
| 5 | flow_main | Sensor |
| 6 | temp_inlet | Sensor |
| 7 | temp_outlet | Sensor |
| 8 | acid_valve | Actuator (ControlValve) |
| 9 | chlorine_pump | Actuator (DosingPump) |
| 10 | inlet_valve | Actuator (ControlValve) |

### Action Codes

| Code | Name | Applicable to | `param` usage |
|---|---|---|---|
| 0 | CALIBRATE | All sensors | Reference value; add 1000 to skip warm-up reset (e.g. `param=1007.0` → ref=7.0, skip_warmup=True) |
| 1 | FULL_RESET | All sensors | Unused |
| 2 | CLEAN_WATER | pH sensors | Unused |
| 3 | CLEAN_ACID | pH sensors | Unused |
| 4 | REPLACE_MEMBRANE | Chlorine (amperometric) | Unused |
| 5 | REPLACE_REAGENT | Chlorine (DPD) | Unused |
| 6 | RESET_FAULTS | All actuators | Unused |
| 7 | CALIBRATE_ZERO | All actuators | Unused |
| 8 | RECALIBRATE_POSITIONER | ControlValve only | Unused |
| 9 | REPLACE_DIAPHRAGM | DosingPump only | Unused |
| 10 | REPLACE_CHECK_VALVES | DosingPump only | Unused |
| 11 | REPLACE_TUBE | DosingPump (peristaltic) only | Unused |