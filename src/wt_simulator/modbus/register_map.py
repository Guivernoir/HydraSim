"""
Modbus Register Map
===================

Defines the mapping between Modbus registers and data sources.

This module contains ONLY the register layout - it does not:
- Read sensors
- Control actuators
- Implement physics
- Enforce limits

Register Types:
- Input Registers (FC 04): Read-only sensor values
- Holding Registers (FC 03/06/16): Read/write actuator setpoints

Register Encoding:
- All floats use IEEE 754 single-precision (32-bit)
- Each float occupies 2 consecutive 16-bit registers
- Byte order: Big-endian (network byte order)

Maintenance register block  (added February 2026)
-------------------------------------------------
Holding registers (write to command a maintenance action):
  HR 200  maintenance_target_id    uint16   MaintenanceTarget enum value
  HR 201  maintenance_action_code  uint16   MaintenanceAction enum value
  HR 202  maintenance_param        float32  action parameter (HR 202-203)

Coils (write 1 to trigger; simulator auto-clears after execution):
  Coil 10  maintenance_trigger     bool

Input registers (written by simulator after each execution):
  IR 110  maintenance_status_code  uint16   MaintenanceStatus enum value
  IR 111  maintenance_last_target  uint16   echo of target_id
  IR 112  maintenance_last_action  uint16   echo of action_code

Workflow:
  1. Write target_id   → HR 200
  2. Write action_code → HR 201
  3. Write param       → HR 202-203 (float32, 0.0 if unused)
  4. Write True        → Coil 10 (trigger)
  5. Poll IR 110 until it is not PENDING (5)
  6. Read IR 110 for status, IR 111/112 for echo

Author: Guilherme F. G. Santos
Last updated: February 2026
License: MIT
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import IntEnum


class RegisterType(IntEnum):
    """Modbus register types."""

    COIL             = 0  # Discrete output (read/write)
    DISCRETE_INPUT   = 1  # Discrete input (read-only)
    INPUT_REGISTER   = 3  # Analog input (read-only)
    HOLDING_REGISTER = 4  # Analog output (read/write)


@dataclass
class RegisterDefinition:
    """
    Definition of a single Modbus register (or register pair for floats).

    Attributes:
        address: Starting register address (0-based)
        name: Human-readable identifier
        register_type: Coil, discrete input, input register, or holding register
        data_type: 'float32', 'int16', 'uint16', 'bool'
        units: Physical units (e.g., 'pH', 'mg/L', 'L/min')
        description: What this register represents
        read_only: Whether this register can be written
    """

    address:       int
    name:          str
    register_type: RegisterType
    data_type:     str
    units:         str
    description:   str
    read_only:     bool = True

    def validate(self):
        """Validate register definition."""
        if self.address < 0 or self.address > 65535:
            raise ValueError(f"Register address {self.address} out of range [0, 65535]")

        if self.data_type not in ["float32", "int16", "uint16", "bool"]:
            raise ValueError(f"Unknown data type: {self.data_type}")

        if self.register_type == RegisterType.HOLDING_REGISTER and self.read_only:
            raise ValueError(f"Holding register {self.name} marked as read-only")

        if self.register_type == RegisterType.INPUT_REGISTER and not self.read_only:
            raise ValueError(f"Input register {self.name} marked as writable")

    @property
    def size_words(self) -> int:
        """Number of 16-bit words this register occupies."""
        if self.data_type == "float32":
            return 2
        elif self.data_type in ["int16", "uint16"]:
            return 1
        elif self.data_type == "bool":
            return 1
        else:
            raise ValueError(f"Unknown data type: {self.data_type}")


class ModbusRegisterMap:
    """
    Complete Modbus register map for water treatment system.

    This class defines the register layout but does NOT:
    - Read sensor values (that's done by the caller)
    - Write actuator commands (that's done by the caller)
    - Implement control logic
    - Enforce limits

    It only defines WHERE data goes in the Modbus address space.
    """

    def __init__(self):
        """Initialize register map with standard layout."""
        self.input_registers:   List[RegisterDefinition] = []
        self.holding_registers: List[RegisterDefinition] = []
        self.coils:             List[RegisterDefinition] = []
        self.discrete_inputs:   List[RegisterDefinition] = []

        self._define_input_registers()
        self._define_holding_registers()
        self._define_coils()
        self._define_discrete_inputs()

        # Validate all definitions
        self._validate_all()

    # ------------------------------------------------------------------
    # Input registers (read-only)
    # ------------------------------------------------------------------

    def _define_input_registers(self):
        """
        Define input registers (read-only sensor values).

        Address range: 30000-39999 (Modbus convention)
        Base address: 0 (internal addressing)
        """
        # pH sensors
        self.input_registers.extend([
            RegisterDefinition(
                address=0, name="pH_inlet",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="pH",
                description="pH at inlet (zone 0)", read_only=True,
            ),
            RegisterDefinition(
                address=2, name="pH_middle",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="pH",
                description="pH at middle (zone n/2)", read_only=True,
            ),
            RegisterDefinition(
                address=4, name="pH_outlet",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="pH",
                description="pH at outlet (zone -1)", read_only=True,
            ),
        ])

        # Chlorine sensors
        self.input_registers.extend([
            RegisterDefinition(
                address=6, name="chlorine_inlet",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="mg/L",
                description="Free chlorine at inlet", read_only=True,
            ),
            RegisterDefinition(
                address=8, name="chlorine_outlet",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="mg/L",
                description="Free chlorine at outlet", read_only=True,
            ),
        ])

        # Flow sensor
        self.input_registers.extend([
            RegisterDefinition(
                address=10, name="flow_rate",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="L/min",
                description="Main flow rate", read_only=True,
            ),
        ])

        # Temperature sensors
        self.input_registers.extend([
            RegisterDefinition(
                address=12, name="temperature_inlet",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="°C",
                description="Water temperature at inlet", read_only=True,
            ),
            RegisterDefinition(
                address=14, name="temperature_outlet",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="°C",
                description="Water temperature at outlet", read_only=True,
            ),
        ])

        # System status
        self.input_registers.extend([
            RegisterDefinition(
                address=100, name="simulation_time",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="float32", units="s",
                description="Simulation elapsed time", read_only=True,
            ),
            RegisterDefinition(
                address=102, name="system_status",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="uint16", units="",
                description="System status code (0=OK, >0=fault)", read_only=True,
            ),
        ])

        # ----------------------------------------------------------------
        # Maintenance feedback registers (read by external client to check
        # result after setting the trigger coil)
        # ----------------------------------------------------------------
        self.input_registers.extend([
            RegisterDefinition(
                address=110, name="maintenance_status_code",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="uint16", units="",
                description=(
                    "Last maintenance result code "
                    "(0=SUCCESS 1=INVALID_TARGET 2=INVALID_ACTION "
                    "3=NOT_SUPPORTED 4=EXEC_ERROR 5=PENDING)"
                ),
                read_only=True,
            ),
            RegisterDefinition(
                address=111, name="maintenance_last_target",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="uint16", units="",
                description="Target ID echoed after last maintenance op",
                read_only=True,
            ),
            RegisterDefinition(
                address=112, name="maintenance_last_action",
                register_type=RegisterType.INPUT_REGISTER,
                data_type="uint16", units="",
                description="Action code echoed after last maintenance op",
                read_only=True,
            ),
        ])

    # ------------------------------------------------------------------
    # Holding registers (read/write)
    # ------------------------------------------------------------------

    def _define_holding_registers(self):
        """
        Define holding registers (read/write actuator setpoints).

        Address range: 40000-49999 (Modbus convention)
        Base address: 0 (internal addressing)
        """
        # Process actuator setpoints
        self.holding_registers.extend([
            RegisterDefinition(
                address=0, name="acid_flow_rate",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="float32", units="L/min",
                description="Acid dosing pump flow rate setpoint",
                read_only=False,
            ),
            RegisterDefinition(
                address=2, name="chlorine_flow_rate",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="float32", units="L/min",
                description="Chlorine dosing pump flow rate setpoint",
                read_only=False,
            ),
            RegisterDefinition(
                address=4, name="inlet_flow_rate",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="float32", units="L/min",
                description="Main inlet flow rate setpoint",
                read_only=False,
            ),
        ])

        # Dosing concentrations
        self.holding_registers.extend([
            RegisterDefinition(
                address=10, name="acid_concentration",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="float32", units="mol/L",
                description="Acid stock solution concentration",
                read_only=False,
            ),
            RegisterDefinition(
                address=12, name="chlorine_concentration",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="float32", units="mg/L",
                description="Chlorine stock solution concentration",
                read_only=False,
            ),
        ])

        # Simulation control
        self.holding_registers.extend([
            RegisterDefinition(
                address=100, name="simulation_timestep",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="float32", units="s",
                description="Simulation time step",
                read_only=False,
            ),
        ])

        # ----------------------------------------------------------------
        # Maintenance command registers
        # Write target, action, param → then pulse Coil 10 to execute.
        # ----------------------------------------------------------------
        self.holding_registers.extend([
            RegisterDefinition(
                address=200, name="maintenance_target_id",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="uint16", units="",
                description=(
                    "Target device ID for maintenance action "
                    "(0=pH_inlet … 10=inlet_valve; see MaintenanceTarget enum)"
                ),
                read_only=False,
            ),
            RegisterDefinition(
                address=201, name="maintenance_action_code",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="uint16", units="",
                description=(
                    "Action code (0=CALIBRATE … 11=REPLACE_TUBE; "
                    "see MaintenanceAction enum)"
                ),
                read_only=False,
            ),
            RegisterDefinition(
                address=202, name="maintenance_param",
                register_type=RegisterType.HOLDING_REGISTER,
                data_type="float32", units="",
                description=(
                    "Action parameter (float32, HR 202-203). "
                    "For CALIBRATE: reference value (add 1000 to skip warmup). "
                    "Unused actions: write 0.0"
                ),
                read_only=False,
            ),
        ])

    # ------------------------------------------------------------------
    # Coils (read/write discrete)
    # ------------------------------------------------------------------

    def _define_coils(self):
        self.coils.extend([
            RegisterDefinition(
                address=0, name="acid_pump_enable",
                register_type=RegisterType.COIL,
                data_type="bool", units="",
                description="Enable acid dosing pump (True=ON, False=OFF)",
                read_only=False,
            ),
            RegisterDefinition(
                address=1, name="chlorine_pump_enable",
                register_type=RegisterType.COIL,
                data_type="bool", units="",
                description="Enable chlorine dosing pump (True=ON, False=OFF)",
                read_only=False,
            ),
            RegisterDefinition(
                address=2, name="simulation_running",
                register_type=RegisterType.COIL,
                data_type="bool", units="",
                description="Simulation running (True=running, False=paused)",
                read_only=False,
            ),
            # ----------------------------------------------------------------
            # Maintenance trigger coil — write True to fire the action whose
            # parameters are in HR 200-203.  The simulator auto-clears this
            # coil once the action has completed (success or error).
            # ----------------------------------------------------------------
            RegisterDefinition(
                address=10, name="maintenance_trigger",
                register_type=RegisterType.COIL,
                data_type="bool", units="",
                description=(
                    "Write True to execute maintenance action defined in "
                    "HR 200-203. Simulator auto-clears to False after execution."
                ),
                read_only=False,
            ),
        ])

    # ------------------------------------------------------------------
    # Discrete inputs (read-only)
    # ------------------------------------------------------------------

    def _define_discrete_inputs(self):
        self.discrete_inputs.extend([
            RegisterDefinition(
                address=0, name="sensor_fault_pH_inlet",
                register_type=RegisterType.DISCRETE_INPUT,
                data_type="bool", units="",
                description="pH inlet sensor fault status", read_only=True,
            ),
            RegisterDefinition(
                address=1, name="sensor_fault_pH_outlet",
                register_type=RegisterType.DISCRETE_INPUT,
                data_type="bool", units="",
                description="pH outlet sensor fault status", read_only=True,
            ),
            RegisterDefinition(
                address=2, name="sensor_fault_chlorine",
                register_type=RegisterType.DISCRETE_INPUT,
                data_type="bool", units="",
                description="Chlorine sensor fault status", read_only=True,
            ),
        ])

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate_all(self):
        all_registers = (
            self.input_registers
            + self.holding_registers
            + self.coils
            + self.discrete_inputs
        )
        for reg in all_registers:
            reg.validate()

        self._check_address_conflicts(self.input_registers,   "Input registers")
        self._check_address_conflicts(self.holding_registers, "Holding registers")
        self._check_address_conflicts(self.coils,             "Coils")
        self._check_address_conflicts(self.discrete_inputs,   "Discrete inputs")

    def _check_address_conflicts(
        self, registers: List[RegisterDefinition], type_name: str
    ):
        address_ranges = []
        for reg in registers:
            start = reg.address
            end   = reg.address + reg.size_words - 1
            address_ranges.append((start, end, reg.name))

        address_ranges.sort(key=lambda x: x[0])

        for i in range(len(address_ranges) - 1):
            curr_start, curr_end, curr_name = address_ranges[i]
            next_start, next_end, next_name = address_ranges[i + 1]

            if curr_end >= next_start:
                raise ValueError(
                    f"{type_name} address conflict: {curr_name} "
                    f"[{curr_start}-{curr_end}] overlaps with {next_name} "
                    f"[{next_start}-{next_end}]"
                )

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def get_register_by_name(self, name: str) -> Optional[RegisterDefinition]:
        all_registers = (
            self.input_registers
            + self.holding_registers
            + self.coils
            + self.discrete_inputs
        )
        for reg in all_registers:
            if reg.name == name:
                return reg
        return None

    def get_register_by_address(
        self, address: int, register_type: RegisterType
    ) -> Optional[RegisterDefinition]:
        if register_type == RegisterType.INPUT_REGISTER:
            registers = self.input_registers
        elif register_type == RegisterType.HOLDING_REGISTER:
            registers = self.holding_registers
        elif register_type == RegisterType.COIL:
            registers = self.coils
        elif register_type == RegisterType.DISCRETE_INPUT:
            registers = self.discrete_inputs
        else:
            return None

        for reg in registers:
            if reg.address <= address < reg.address + reg.size_words:
                return reg
        return None

    def print_register_map(self):
        """Print complete register map for documentation."""
        print("=" * 80)
        print("MODBUS REGISTER MAP")
        print("=" * 80)

        print("\nINPUT REGISTERS (Read-Only)")
        print("-" * 80)
        print(f"{'Address':<12} {'Name':<30} {'Type':<10} {'Units':<10} {'Description'}")
        print("-" * 80)
        for reg in self.input_registers:
            base = 30001 + reg.address
            addr = f"{base}-{base+1}" if reg.data_type == "float32" else str(base)
            print(f"{addr:<12} {reg.name:<30} {reg.data_type:<10} {reg.units:<10} {reg.description}")

        print("\nHOLDING REGISTERS (Read/Write)")
        print("-" * 80)
        print(f"{'Address':<12} {'Name':<30} {'Type':<10} {'Units':<10} {'Description'}")
        print("-" * 80)
        for reg in self.holding_registers:
            base = 40001 + reg.address
            addr = f"{base}-{base+1}" if reg.data_type == "float32" else str(base)
            print(f"{addr:<12} {reg.name:<30} {reg.data_type:<10} {reg.units:<10} {reg.description}")

        print("\nCOILS (Read/Write)")
        print("-" * 80)
        print(f"{'Address':<12} {'Name':<30} {'Description'}")
        print("-" * 80)
        for reg in self.coils:
            print(f"{1+reg.address:<12} {reg.name:<30} {reg.description}")

        print("\nDISCRETE INPUTS (Read-Only)")
        print("-" * 80)
        print(f"{'Address':<12} {'Name':<30} {'Description'}")
        print("-" * 80)
        for reg in self.discrete_inputs:
            print(f"{10001+reg.address:<12} {reg.name:<30} {reg.description}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    reg_map = ModbusRegisterMap()
    reg_map.print_register_map()