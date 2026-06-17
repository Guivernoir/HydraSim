"""
Main simulation orchestrator.

Entry point for the water treatment simulator runtime.
"""

import argparse
import time
import logging
import signal
import sys
from typing import Dict, Tuple, Optional, Any
from contextlib import suppress
from pathlib import Path

# Physics engine
from .core import IntegratedCSTR, ReactorConfiguration, BoundaryConditions, ReactorState

# Actuators
from .actuators import create_realistic_actuator_suite

# Sensors
from .sensors import (
    create_realistic_sensor_suite,
    SensorReading,
    SensorStatus,
    SensorFault,
)

# Maintenance
from .maintenance import MaintenanceManager

# Modbus (optional dependency)
MODBUS_AVAILABLE = True
MODBUS_IMPORT_ERROR: Optional[str] = None
try:
    from .modbus import ModbusSlave, ModbusRegisterMap, ModbusServerConfig
except ModuleNotFoundError as exc:
    if exc.name != "pymodbus":
        raise
    MODBUS_AVAILABLE = False
    MODBUS_IMPORT_ERROR = str(exc)
    ModbusSlave = Any  # type: ignore
    ModbusRegisterMap = Any  # type: ignore
    ModbusServerConfig = Any  # type: ignore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global running flag for graceful shutdown
running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C for clean shutdown."""
    global running
    logger.info("Shutdown signal received. Stopping simulation...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# Input validation helpers
def validate_flow_rate(value: float, max_value: float = 20.0) -> float:
    """Validate and clamp flow rate within safe bounds."""
    if not isinstance(value, (int, float)):
        return 0.0
    if value != value:  # Check for NaN
        return 0.0
    return max(0.0, min(float(value), max_value))


def validate_concentration(value: float, max_value: float = 1.0) -> float:
    """Validate and clamp concentration within safe bounds."""
    if not isinstance(value, (int, float)):
        return 0.0
    if value != value:  # Check for NaN
        return 0.0
    return max(0.0, min(float(value), max_value))


def validate_ph(value: float) -> float:
    """Validate pH value within physical bounds."""
    if not isinstance(value, (int, float)):
        return 7.0
    if value != value:  # Check for NaN
        return 7.0
    return max(0.0, min(float(value), 14.0))


def initialize_sensors(config, sim_start_time: float, verbose: bool = False):
    """Initialize and calibrate sensors with error handling."""
    logger.info("Initializing sensor suite...")

    try:
        sensors = create_realistic_sensor_suite(config)
    except Exception as e:
        logger.error(f"Failed to create sensor suite: {type(e).__name__}")
        raise RuntimeError("Sensor initialization failed")

    # Calibrate all sensors at startup
    calibration_errors = 0
    for name, sensor in sensors.items():
        try:
            if "pH" in name:
                sensor.calibrate(7.0, sim_start_time, "system_init")
            elif "chlorine" in name:
                sensor.calibrate(config.initial_chlorine, sim_start_time, "system_init")
            elif "temp" in name:
                sensor.calibrate(config.temperature, sim_start_time, "system_init")
            elif "flow" in name:
                sensor.calibrate(config.flow_rate, sim_start_time, "system_init")

            if verbose:
                logger.info(f"  Calibrated {name}")

        except Exception:
            calibration_errors += 1
            logger.warning(f"  Could not calibrate {name}")

    if calibration_errors > len(sensors) // 2:
        raise RuntimeError("Too many sensor calibration failures")

    logger.info(f"Initialized {len(sensors)} sensors ({calibration_errors} errors)")
    return sensors


def read_all_sensors(
    sensors: Dict, state: ReactorState, sim_time: float, verbose: bool = False
) -> Dict[str, SensorReading]:
    """Read all sensors with graceful error handling."""
    readings = {}
    error_count = 0

    for name, sensor in sensors.items():
        try:
            reading = sensor.read(state, current_time=sim_time)
            readings[name] = reading

            # Log warnings/faults
            if reading.status != SensorStatus.NORMAL:
                if verbose or reading.status not in [
                    SensorStatus.WARMING_UP,
                    SensorStatus.CALIBRATING,
                ]:
                    logger.warning(f"{name}: {reading.status.value}")

            if reading.fault != SensorFault.NONE:
                logger.error(f"{name}: FAULT - {reading.fault.value}")
                error_count += 1

        except Exception:
            error_count += 1
            # Graceful degradation: use safe default values
            readings[name] = SensorReading(
                timestamp=sim_time,
                value=float("nan"),
                raw_value=float("nan"),
                noise=0.0,
                drift=0.0,
                status=SensorStatus.FAILED,
                uncertainty=float("inf"),
                fault=SensorFault.OPEN_CIRCUIT,
            )

    # Alert if too many sensors are failing
    if error_count > len(sensors) // 2:
        logger.error(f"{error_count}/{len(sensors)} sensors in fault state")

    return readings


def update_modbus_inputs(
    slave: Optional[ModbusSlave], readings: Dict[str, SensorReading], sim_time: float
) -> bool:
    """
    Update Modbus input registers with sensor values.

    Returns:
        True if update succeeded, False otherwise
    """
    if slave is None or not slave.is_running:
        return False

    # Helper to safely get value (return 0.0 if None or NaN)
    def safe_value(key: str) -> float:
        reading = readings.get(key)
        if reading is None:
            return 0.0
        val = reading.value
        if val != val or val == float("inf") or val == float("-inf"):
            return 0.0
        return val

    # Helper to check fault status
    def has_fault(key: str) -> bool:
        reading = readings.get(key)
        return reading is not None and reading.fault != SensorFault.NONE

    try:
        # Update analog inputs (input registers)
        slave.update_input_register("pH_inlet", safe_value("pH_inlet"))
        slave.update_input_register("pH_middle", safe_value("pH_middle"))
        slave.update_input_register("pH_outlet", safe_value("pH_outlet"))

        slave.update_input_register("chlorine_inlet", safe_value("chlorine_inlet"))
        slave.update_input_register("chlorine_outlet", safe_value("chlorine_outlet"))

        slave.update_input_register("flow_rate", safe_value("flow_main"))

        slave.update_input_register("temperature_inlet", safe_value("temp_inlet"))
        slave.update_input_register("temperature_outlet", safe_value("temp_outlet"))

        # Update system status inputs
        slave.update_input_register("simulation_time", sim_time)

        # Calculate aggregate system status (0=OK, 1=Fault)
        any_fault = any(r.fault != SensorFault.NONE for r in readings.values())
        slave.update_input_register("system_status", 1 if any_fault else 0)

        # Update discrete inputs (fault bits)
        slave.update_discrete_input("sensor_fault_pH_inlet", has_fault("pH_inlet"))
        slave.update_discrete_input("sensor_fault_pH_outlet", has_fault("pH_outlet"))

        chlorine_fault = has_fault("chlorine_inlet") or has_fault("chlorine_outlet")
        slave.update_discrete_input("sensor_fault_chlorine", chlorine_fault)

        return True

    except Exception as e:
        logger.error(f"Modbus update failed: {type(e).__name__}")
        return False


def read_modbus_commands(slave: Optional[ModbusSlave]) -> Tuple[float, float, float]:
    """
    Read actuator commands from Modbus with range checks.

    Returns:
        Tuple of (acid_flow_rate, chlorine_flow_rate, inlet_flow_rate)
    """
    if slave is None or not slave.is_running:
        return 0.0, 0.0, 0.0

    try:
        # Read commands with validation
        acid_rate = slave.read_holding_register("acid_flow_rate")
        chlorine_rate = slave.read_holding_register("chlorine_flow_rate")
        inlet_rate = slave.read_holding_register("inlet_flow_rate")

        # Clamp to configured ranges.
        acid_rate = validate_flow_rate(acid_rate, max_value=2.0)
        chlorine_rate = validate_flow_rate(chlorine_rate, max_value=1.0)
        inlet_rate = validate_flow_rate(inlet_rate, max_value=20.0)

        return acid_rate, chlorine_rate, inlet_rate

    except Exception as e:
        logger.error(f"Modbus read failed: {type(e).__name__}")
        return 0.0, 0.0, 0.0


def read_modbus_enable_bits(slave: Optional[ModbusSlave]) -> Tuple[bool, bool, bool]:
    """
    Read actuator and simulation enable bits from Modbus coils.

    Returns:
        (acid_enabled, chlorine_enabled, simulation_running)
    """
    if slave is None or not slave.is_running:
        return True, True, True

    try:
        acid_enabled = slave.read_coil("acid_pump_enable")
        chlorine_enabled = slave.read_coil("chlorine_pump_enable")
        simulation_running = slave.read_coil("simulation_running")
        return bool(acid_enabled), bool(chlorine_enabled), bool(simulation_running)
    except Exception:
        # Fail-open for operation continuity if comms are degraded
        return True, True, True


def read_modbus_dosing_concentrations(
    slave: Optional[ModbusSlave], boundary: BoundaryConditions
) -> Tuple[float, float]:
    """
    Read dosing stock concentrations from Modbus holding registers.

    Returns:
        (acid_concentration_mol_L, chlorine_concentration_mg_L)
    """
    if slave is None or not slave.is_running:
        return boundary.acid_concentration, boundary.chlorine_concentration

    try:
        acid_conc = slave.read_holding_register("acid_concentration")
        chlorine_conc = slave.read_holding_register("chlorine_concentration")

        acid_conc = validate_concentration(acid_conc, max_value=5.0)  # mol/L
        chlorine_conc = validate_concentration(chlorine_conc, max_value=200.0)  # mg/L

        return acid_conc, chlorine_conc
    except Exception:
        return boundary.acid_concentration, boundary.chlorine_concentration


def initialize_actuators(boundary: BoundaryConditions) -> Dict[str, Any]:
    """Initialize and prime realistic actuator models."""
    actuators = create_realistic_actuator_suite(
        {
            "max_acid_flow": 2.0,
            "max_chlorine_flow": 1.0,
            "max_inlet_flow": 20.0,
            "acid_pressure_drop": 2.0,
            "chlorine_discharge_pressure": 2.0,
            "inlet_pressure_drop": 1.5,
        }
    )

    # Prime actuators to initial operating point so simulation starts near steady state.
    actuators["acid_valve"].set_flow_rate(
        validate_flow_rate(boundary.acid_flow_rate, 2.0)
    )
    actuators["chlorine_pump"].set_flow_rate(
        validate_flow_rate(boundary.chlorine_flow_rate, 1.0)
    )
    actuators["inlet_valve"].set_flow_rate(
        validate_flow_rate(boundary.inlet_flow_rate, 20.0)
    )

    for _ in range(3):
        actuators["acid_valve"].step(10.0)
        actuators["chlorine_pump"].step(10.0)
        actuators["inlet_valve"].step(10.0)

    return actuators


def apply_actuator_commands(
    actuators: Dict[str, Any],
    commands: Tuple[float, float, float],
    enable_bits: Tuple[bool, bool, bool],
    current_inlet_flow: float,
) -> None:
    """Apply desired flow commands to actuator setpoints."""
    acid_rate, chlorine_rate, inlet_rate = commands
    acid_enabled, chlorine_enabled, _simulation_running = enable_bits

    target_acid = acid_rate if acid_enabled else 0.0
    target_chlorine = chlorine_rate if chlorine_enabled else 0.0
    # Respect explicit low-flow/closed commands for main inlet valve.
    # Keep current flow only for invalid negative values (defensive fallback).
    target_inlet = inlet_rate if inlet_rate >= 0.0 else current_inlet_flow

    actuators["acid_valve"].set_flow_rate(validate_flow_rate(target_acid, 2.0))
    actuators["chlorine_pump"].set_flow_rate(validate_flow_rate(target_chlorine, 1.0))
    actuators["inlet_valve"].set_flow_rate(validate_flow_rate(target_inlet, 20.0))


def step_actuators_into_boundary(
    actuators: Dict[str, Any],
    boundary: BoundaryConditions,
    dt: float,
) -> None:
    """Advance actuator dynamics and map actual outputs into reactor boundary flows."""
    acid_flow = actuators["acid_valve"].step(dt)
    chlorine_flow = actuators["chlorine_pump"].step(dt)
    inlet_flow = actuators["inlet_valve"].step(dt)

    boundary.acid_flow_rate = validate_flow_rate(acid_flow, max_value=2.0)
    boundary.chlorine_flow_rate = validate_flow_rate(chlorine_flow, max_value=1.0)
    boundary.inlet_flow_rate = validate_flow_rate(inlet_flow, max_value=20.0)


def initialize_modbus_defaults(
    slave: Optional[ModbusSlave], boundary: BoundaryConditions
) -> None:
    """Prime Modbus writable registers/coils with meaningful startup defaults."""
    if slave is None or not slave.is_running:
        return

    with suppress(Exception):
        slave.write_holding_register("acid_flow_rate", boundary.acid_flow_rate)
        slave.write_holding_register("chlorine_flow_rate", boundary.chlorine_flow_rate)
        slave.write_holding_register("inlet_flow_rate", boundary.inlet_flow_rate)
        slave.write_holding_register("acid_concentration", boundary.acid_concentration)
        slave.write_holding_register(
            "chlorine_concentration", boundary.chlorine_concentration
        )
        slave.write_coil("acid_pump_enable", True)
        slave.write_coil("chlorine_pump_enable", True)
        slave.write_coil("simulation_running", True)


def main():
    parser = argparse.ArgumentParser(description="Water Treatment Reactor Simulation")
    parser.add_argument("--port", type=int, default=5020, help="Modbus TCP port")
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Modbus bind address"
    )
    parser.add_argument(
        "--dt", type=float, default=1.0, help="Simulation timestep [seconds]"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=float("inf"),
        help="Total simulation duration [seconds]",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose sensor warnings"
    )
    parser.add_argument(
        "--no-modbus",
        action="store_true",
        help="Run without Modbus server (testing mode)",
    )
    parser.add_argument(
        "--scenario",
        help="Optional built-in scenario ID or alias to replay against this simulator",
    )
    parser.add_argument(
        "--scenario-custom-json",
        type=Path,
        help="Optional custom scenario JSON file for replay",
    )
    parser.add_argument(
        "--scenario-time-scale",
        type=float,
        default=1.0,
        help="Scenario replay timing scale; 0 runs immediately",
    )
    parser.add_argument(
        "--scenario-delay",
        type=float,
        default=1.0,
        help="Seconds to wait after Modbus startup before scenario replay",
    )
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("WATER TREATMENT REACTOR SIMULATION")
    logger.info("=" * 70)

    # ========================================================================
    # PHASE 1: Initialize Physics Engine
    # ========================================================================
    logger.info("\n[PHASE 1] Initializing physics engine...")

    try:
        config = ReactorConfiguration(
            volume=1000.0,
            n_zones=5,
            flow_rate=5.0,
            initial_pH=7.2,
            initial_chlorine=2.0,
            temperature=20.0,
        )

        reactor = IntegratedCSTR(config)
        logger.info("Physics engine initialized")

    except Exception as e:
        logger.error(f"Physics engine initialization failed: {type(e).__name__}")
        sys.exit(1)

    # ========================================================================
    # PHASE 2: Initialize Boundary Conditions
    # ========================================================================
    boundary = BoundaryConditions(
        inlet_flow_rate=5.0,
        inlet_pH=config.inlet_pH,
        inlet_chlorine=config.inlet_chlorine,
        inlet_chloramine=config.inlet_chloramine,
        inlet_ammonia=config.inlet_ammonia,
        inlet_chlorine_demand=config.inlet_chlorine_demand,
        inlet_temperature=config.inlet_temperature,
        acid_flow_rate=0.0,
        acid_concentration=0.1,
        chlorine_flow_rate=0.0,
    )

    # ========================================================================
    # PHASE 3: Initialize Actuators
    # ========================================================================
    logger.info("\n[PHASE 3] Initializing actuator suite...")
    try:
        actuators = initialize_actuators(boundary)
        logger.info("Actuator suite initialized")
    except Exception as e:
        logger.error(f"Actuator initialization failed: {type(e).__name__}")
        sys.exit(1)

    # ========================================================================
    # PHASE 4: Initialize Sensors
    # ========================================================================
    sim_start_time = time.monotonic()

    try:
        sensors = initialize_sensors(config, sim_start_time, args.verbose)
    except Exception as e:
        logger.error(f"Sensor initialization failed: {type(e).__name__}")
        sys.exit(1)

    # ========================================================================
    # PHASE 5: Initialize Modbus Interface
    # ========================================================================
    slave = None

    if not args.no_modbus and not MODBUS_AVAILABLE:
        logger.warning(
            f"\n[PHASE 5] Modbus unavailable ({MODBUS_IMPORT_ERROR}). "
            "Run with --no-modbus or install pymodbus."
        )
    elif not args.no_modbus:
        logger.info("\n[PHASE 5] Initializing Modbus server...")

        reg_map = ModbusRegisterMap()
        modbus_config = ModbusServerConfig(
            host=args.host,
            port=args.port,
            unit_id=1,
            startup_timeout_sec=5.0,
            shutdown_timeout_sec=3.0,
        )

        try:
            maintenance_manager = MaintenanceManager(sensors, actuators)
            slave = ModbusSlave(
                reg_map, modbus_config, maintenance_manager=maintenance_manager
            )
            slave.start(blocking=False)
            initialize_modbus_defaults(slave, boundary)
            logger.info(f"Modbus server started on {args.host}:{args.port}")
            if args.scenario or args.scenario_custom_json:
                from .scenarios.live import start_live_scenario_thread

                start_live_scenario_thread(
                    args.scenario or "custom",
                    args.host,
                    args.port,
                    unit_id=1,
                    time_scale=args.scenario_time_scale,
                    startup_delay_s=args.scenario_delay,
                    custom_json=args.scenario_custom_json,
                    logger=logger,
                )
                logger.info("Scenario replay scheduled")

        except RuntimeError as e:
            logger.error(f"Modbus server startup failed: {e}")
            logger.warning("Continuing in no-Modbus mode")
            slave = None

        except Exception as e:
            logger.error(f"Modbus initialization error: {type(e).__name__}")
            logger.warning("Continuing in no-Modbus mode")
            slave = None
    else:
        logger.info("\n[PHASE 5] Skipping Modbus (--no-modbus)")
        if args.scenario or args.scenario_custom_json:
            logger.warning("Scenario replay skipped because Modbus is disabled")

    # ========================================================================
    # PHASE 6: Main Simulation Loop
    # ========================================================================
    logger.info("\n[PHASE 6] Starting simulation loop...")
    logger.info("Press Ctrl+C to stop gracefully")

    sim_time = 0.0
    step_count = 0
    log_interval = 60
    warmup_steps = int(10.0 / args.dt)

    modbus_error_count = 0
    max_modbus_errors = 10
    state = reactor.state

    try:
        while running and sim_time < args.duration:
            step_start = time.monotonic()
            current_sim_time = sim_start_time + sim_time

            # --- Step 1: Read external commands ---
            commands = (
                boundary.acid_flow_rate,
                boundary.chlorine_flow_rate,
                boundary.inlet_flow_rate,
            )
            enable_bits = (True, True, True)

            if slave:
                commands = read_modbus_commands(slave)
                enable_bits = read_modbus_enable_bits(slave)
                acid_conc, chlorine_conc = read_modbus_dosing_concentrations(
                    slave, boundary
                )
                boundary.acid_concentration = acid_conc
                boundary.chlorine_concentration = chlorine_conc

            simulation_enabled = enable_bits[2]

            # --- Step 2: Apply actuator dynamics and run physics ---
            if simulation_enabled:
                apply_actuator_commands(
                    actuators, commands, enable_bits, boundary.inlet_flow_rate
                )
                step_actuators_into_boundary(actuators, boundary, args.dt)
                try:
                    state = reactor.step(args.dt, boundary=boundary)
                except Exception as e:
                    logger.error(f"Physics step failed: {type(e).__name__}")
                    break

            # --- Step 3: Read sensors ---
            readings = read_all_sensors(sensors, state, current_sim_time, args.verbose)

            # --- Step 4: Update Modbus inputs ---
            if slave:
                if not update_modbus_inputs(slave, readings, sim_time):
                    modbus_error_count += 1
                    if modbus_error_count >= max_modbus_errors:
                        logger.error("Too many Modbus errors, disabling interface")
                        slave = None

            # --- Step 5: Dispatch maintenance commands ---
            if slave:
                with suppress(Exception):
                    slave.poll_maintenance()

            # --- Periodic logging ---
            if step_count % log_interval == 0:
                sensors_ready = all(
                    r.status not in [SensorStatus.WARMING_UP, SensorStatus.CALIBRATING]
                    for r in readings.values()
                )

                if sensors_ready or step_count >= warmup_steps:
                    # Safe access to readings
                    pH_in = readings.get("pH_inlet")
                    pH_out = readings.get("pH_outlet")
                    cl_out = readings.get("chlorine_outlet")
                    flow = readings.get("flow_main")

                    logger.info(
                        f"t={sim_time:.0f}s | "
                        f"pH_in={pH_in.value if pH_in else 0:.2f} | "
                        f"pH_out={pH_out.value if pH_out else 0:.2f} | "
                        f"Cl_out={cl_out.value if cl_out else 0:.2f} | "
                        f"Flow={flow.value if flow else 0:.1f} | "
                        f"AcidSP={commands[0]:.2f} | "
                        f"AcidAct={boundary.acid_flow_rate:.2f}"
                    )
                else:
                    logger.info(f"t={sim_time:.0f}s | Sensors warming up...")

            step_count += 1
            sim_time += args.dt

            # --- Real-time pacing ---
            elapsed = time.monotonic() - step_start
            sleep_time = max(0.0, args.dt - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")

    except Exception as e:
        logger.error(f"Simulation error: {type(e).__name__}")

    finally:
        # ====================================================================
        # CLEANUP: Ensure resources are properly released
        # ====================================================================
        logger.info("\nShutting down...")

        if slave:
            logger.info("Stopping Modbus server...")
            with suppress(Exception):
                slave.stop()

        logger.info("Simulation stopped cleanly")


if __name__ == "__main__":
    main()
