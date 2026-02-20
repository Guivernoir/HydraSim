# Model Scope

This simulator is intended for controls integration, operator training, and software testing workflows where realistic process dynamics matter.

## Included

### Reactor Physics
- Multi-zone CSTR state (pH, free chlorine, chloramine, ammonia, chlorine-demand precursor, temperature)
- Inter-zone exchange and through-flow advection
- Mixed influent composition from main flow + dosing streams
- Temperature and pH dependent chlorine kinetics
- Simple heat-loss term to ambient

### Actuators
- Control valve dynamics with lag/stiction/hysteresis/leakage
- Dosing pump dynamics with stroke behavior and pressure effects
- Commanded value vs delivered flow separation

### Sensors
- First-order measurement response
- Noise, drift, calibration offset/expiry
- Warm-up behavior
- Optional sample-line transport delay
- Fault/state reporting

### Maintenance
- Remote recalibration of sensors over Modbus (single-point, with optional warm-up skip)
- pH electrode cleaning (water rinse, acid clean)
- Chlorine sensor hardware replacement (amperometric membrane, DPD reagent)
- Actuator fault reset and zero/span calibration
- ControlValve positioner drift reset
- DosingPump component replacement (diaphragm, check valves, peristaltic tube)
- Per-action result status published to Modbus input registers

### Modbus Integration
- Holding registers/coils for incoming commands
- Input registers/discrete inputs for process feedback and faults
- Runtime loop that maps Modbus commands -> actuators -> physics -> sensors -> Modbus feedback

## Not Included

- CFD-scale hydrodynamics
- Biological process models (biofilm growth, pathogen inactivation chains)
- Full distribution-system chemistry
- Regulatory compliance logic, safety interlocks, or SIS behavior
- Hardware timing jitter from real PLC/RTU stacks

## Practical Limits

- The model is tuned for control behavior realism, not plant design certification.
- Parameters should be adjusted using site data before using it for commissioning-like tests.
- Batch and low-flow conditions are supported, but stability and realism still depend on selected parameters.