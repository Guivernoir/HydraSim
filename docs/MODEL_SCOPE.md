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

### CFD/Digital-Twin Foundation
- Structured finite-volume mesh primitives for small local water-treatment areas
- Incompressible-flow stepping with bounded CFL and mass-residual diagnostics
- Scalar transport stepping for water-quality fields such as chlorine, pH proxy species, temperature, ammonia, chloramine, turbidity, and demand precursor
- Bounded turbulence/mixing helper for small-grid local simulation
- Reference area CFD profiles for intake, dosing, clarification, filtration, disinfection, and storage/pumping
- Unit-process contracts for intake channel, rapid-mix/dosing, flocculation placeholder, clarifier, filter/backwash, contact basin, clearwell, pumping header, chemical feed skid, and waste/backwash handling
- Boundary-condition contracts for inlets, outlets, pumps, valves, dosing injection, mixers, baffles, filter media, backwash, drains, recirculation, and free-surface level metadata
- Early CFD performance presets and benchmark evidence for tiny, small, and medium local grids
- Device-to-CFD coupling contracts where simulated sensors sample spatial mesh regions and simulated actuators apply bounded scalar/source effects
- Controller-to-CFD coupling contracts where synthetic controller actions produce bounded source effects through declared actuator regions
- Supervisory digital-twin records for synthetic HMI, historian, and engineering-workstation consumers of CFD summaries and metadata
- Operator/historian semantics for synthetic trend tags, advisory alarm states, maintenance windows, operator actions, and engineering-workstation events
- Calibration and uncertainty assessments for `uncalibrated`, `calibration_ready`, `synthetic_calibrated`, `evidence_calibrated`, and `rejected` calibration evidence
- Calibration evidence fits with `fitted_not_validated` status, accepted ranges, residuals, preserved rejected data, and explicit calibration records
- Numerical verification suite results for constant-scalar conservation, flow residual, mesh refinement, boundary response, and long-run drift checks
- Scenario-level CFD process evolution truth for built-in reference plant scenarios and bundle exports
- Digital-twin metadata records for geometry, equipment context, calibration status, uncertainty, and validation status
- Deterministic CFD summary export for lab-bundle and regression use

## Not Included

- Biological process models (biofilm growth, pathogen inactivation chains)
- Full distribution-system chemistry
- Regulatory compliance logic, safety interlocks, or SIS behavior
- Hardware timing jitter from real PLC/RTU stacks
- Calibrated real-plant digital-twin equivalence
- Commissioning-grade plant validation or plant-design authority
- Certification-grade CFD verification, external-solver conformance, or safety-system protection
- HPC-scale whole-plant CFD for unrestricted grid sizes

## Practical Limits

- The model is tuned for control behavior realism, not plant design certification.
- Parameters should be adjusted using site data before using it for commissioning-like tests.
- Batch and low-flow conditions are supported, but stability and realism still depend on selected parameters.
- CFD/digital-twin outputs start as `synthetic_unvalidated` unless calibration and validation evidence explicitly changes that status.
- Calibration assessment can update parameter-evidence status, but it is not real-plant validation without a later validation gate and separate evidence.
- Calibration fitting is not validation; `evidence_calibrated` requires an explicit calibration record and still remains separate from real-plant validation.
- Numerical verification suite results are bounded synthetic implementation checks, not external CFD conformance or real-plant validation.
- Scenario-level CFD process evolution is `synthetic_cfd_process_truth`, not real-plant validation, commissioning evidence, or safety evidence.
- CFD grids are bounded for developer-workstation simulation and lab traffic generation, not high-fidelity hydraulic design.
- Device-to-CFD coupling uses `simulated_metadata` until calibrated device placement, sample-line behavior, and actuator effects have separate evidence.
- Controller-to-CFD coupling is synthetic setpoint/error behavior; it is not real PLC firmware, certified control, or safety-interlock validation.
- Supervisory records keep site identity unknown and are not operational historian, HMI, SCADA, DCS, PCS, or engineering-workstation evidence.
- Operator/historian semantics are review/training prompts only; they are not incidents, real operator authorizations, real maintenance records, or vendor engineering-tool events.
