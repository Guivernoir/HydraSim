"""
Maintenance Manager
====================

Transport-agnostic core for remote recalibration and repair of sensors
and actuators in the water treatment simulator.

Callers (e.g. Modbus handler, HTTP endpoint, test code) translate their
wire format into a single call:

    result = manager.execute(target_id, action_code, param)

The manager returns a structured ``MaintenanceResult`` that the caller
can then encode back into whatever wire format it needs.

Design principles
-----------------
- Pure Python, zero I/O, no Modbus imports.
- Never raises; always returns MaintenanceResult with a status field.
- All side-effects confined to the passed-in sensor/actuator objects.
- Health summaries available for external monitoring/logging.

Target IDs
----------
Sensors  : pH_inlet=0, pH_middle=1, pH_outlet=2,
           chlorine_inlet=3, chlorine_outlet=4,
           flow_main=5, temp_inlet=6, temp_outlet=7
Actuators: acid_valve=8, chlorine_pump=9, inlet_valve=10

Action codes
------------
Universal (sensors) : CALIBRATE=0, FULL_RESET=1
pH only             : CLEAN_WATER=2, CLEAN_ACID=3
Amperometric Cl     : REPLACE_MEMBRANE=4
DPD Cl              : REPLACE_REAGENT=5
Universal (actuators): RESET_FAULTS=6, CALIBRATE_ZERO=7
ControlValve only   : RECALIBRATE_POSITIONER=8
DosingPump only     : REPLACE_DIAPHRAGM=9, REPLACE_CHECK_VALVES=10,
                      REPLACE_TUBE=11

CALIBRATE param encoding
------------------------
  param < 1000   →  reference_value = param,       skip_warmup = False
  param ≥ 1000   →  reference_value = param - 1000, skip_warmup = True
  (allows a single float register to carry both pieces of information)

Author: Guilherme F. G. Santos
Date:   February 2026
License: MIT
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public enumerations
# ---------------------------------------------------------------------------

class MaintenanceTarget(IntEnum):
    """Numeric IDs for every field device."""
    PH_INLET        = 0
    PH_MIDDLE       = 1
    PH_OUTLET       = 2
    CHLORINE_INLET  = 3
    CHLORINE_OUTLET = 4
    FLOW_MAIN       = 5
    TEMP_INLET      = 6
    TEMP_OUTLET     = 7
    ACID_VALVE      = 8
    CHLORINE_PUMP   = 9
    INLET_VALVE     = 10


class MaintenanceAction(IntEnum):
    """Numeric codes for every maintenance action."""
    # Universal sensor actions
    CALIBRATE             = 0
    FULL_RESET            = 1
    # pH-specific
    CLEAN_WATER           = 2
    CLEAN_ACID            = 3
    # Amperometric chlorine
    REPLACE_MEMBRANE      = 4
    # DPD chlorine
    REPLACE_REAGENT       = 5
    # Universal actuator actions
    RESET_FAULTS          = 6
    CALIBRATE_ZERO        = 7
    # ControlValve-specific
    RECALIBRATE_POSITIONER = 8
    # DosingPump-specific
    REPLACE_DIAPHRAGM     = 9
    REPLACE_CHECK_VALVES  = 10
    REPLACE_TUBE          = 11


class MaintenanceStatus(IntEnum):
    """Result status codes returned after an action."""
    SUCCESS               = 0
    INVALID_TARGET        = 1
    INVALID_ACTION        = 2
    ACTION_NOT_SUPPORTED  = 3
    EXECUTION_ERROR       = 4
    PENDING               = 5


# ---------------------------------------------------------------------------
# Result and health dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MaintenanceResult:
    """Structured result of a maintenance operation."""
    status:    MaintenanceStatus
    target_id: int
    action_id: int
    message:   str
    timestamp: float = field(default_factory=time.monotonic)

    @property
    def success(self) -> bool:
        return self.status == MaintenanceStatus.SUCCESS


@dataclass
class DeviceHealth:
    """Snapshot of a device's health for diagnostic purposes."""
    target_id:          int
    target_name:        str
    device_type:        str          # "sensor" | "actuator"
    # Universal
    calibration_valid:  bool
    cumulative_drift:   float        # sensor units or %
    # Type-specific extras (populated per device)
    extras:             Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# MaintenanceManager
# ---------------------------------------------------------------------------

class MaintenanceManager:
    """
    Execute maintenance actions on sensors and actuators.

    Parameters
    ----------
    sensors : dict
        Mapping name → sensor object (as returned by
        ``create_realistic_sensor_suite``).
    actuators : dict
        Mapping name → actuator object (as returned by
        ``create_realistic_actuator_suite``).
    """

    # Maps target_id → sensor key in the sensors dict
    _SENSOR_KEYS: Dict[int, str] = {
        MaintenanceTarget.PH_INLET:        "pH_inlet",
        MaintenanceTarget.PH_MIDDLE:       "pH_middle",
        MaintenanceTarget.PH_OUTLET:       "pH_outlet",
        MaintenanceTarget.CHLORINE_INLET:  "chlorine_inlet",
        MaintenanceTarget.CHLORINE_OUTLET: "chlorine_outlet",
        MaintenanceTarget.FLOW_MAIN:       "flow_main",
        MaintenanceTarget.TEMP_INLET:      "temp_inlet",
        MaintenanceTarget.TEMP_OUTLET:     "temp_outlet",
    }

    # Maps target_id → actuator key in the actuators dict
    _ACTUATOR_KEYS: Dict[int, str] = {
        MaintenanceTarget.ACID_VALVE:     "acid_valve",
        MaintenanceTarget.CHLORINE_PUMP:  "chlorine_pump",
        MaintenanceTarget.INLET_VALVE:    "inlet_valve",
    }

    def __init__(
        self,
        sensors:   Dict[str, Any],
        actuators: Dict[str, Any],
    ) -> None:
        self._sensors   = sensors
        self._actuators = actuators

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def execute(
        self,
        target_id:   int,
        action_code: int,
        param:       float = 0.0,
        timestamp:   Optional[float] = None,
    ) -> MaintenanceResult:
        """
        Execute a maintenance action and return its result.

        This method never raises; all errors are captured in the result.

        Parameters
        ----------
        target_id : int
            ``MaintenanceTarget`` value identifying the device.
        action_code : int
            ``MaintenanceAction`` value.
        param : float
            Optional parameter.  For CALIBRATE actions see the module
            docstring for the encoding convention.
        timestamp : float, optional
            Monotonic time to pass to sensor/actuator methods.
            Defaults to ``time.monotonic()``.

        Returns
        -------
        MaintenanceResult
        """
        ts = timestamp if timestamp is not None else time.monotonic()

        try:
            target = MaintenanceTarget(target_id)
        except ValueError:
            msg = f"Unknown target_id={target_id}"
            logger.warning(msg)
            return MaintenanceResult(
                MaintenanceStatus.INVALID_TARGET, target_id, action_code, msg, ts
            )

        try:
            action = MaintenanceAction(action_code)
        except ValueError:
            msg = f"Unknown action_code={action_code}"
            logger.warning(msg)
            return MaintenanceResult(
                MaintenanceStatus.INVALID_ACTION, target_id, action_code, msg, ts
            )

        logger.info(
            "Maintenance: target=%s action=%s param=%.4f",
            target.name, action.name, param,
        )

        if target_id in self._SENSOR_KEYS:
            return self._apply_sensor_action(target, action, param, ts)
        else:
            return self._apply_actuator_action(target, action, param, ts)

    def get_health_summary(self) -> Dict[str, DeviceHealth]:
        """
        Return a health snapshot for every known device.

        Returns
        -------
        dict mapping device name → DeviceHealth
        """
        summary: Dict[str, DeviceHealth] = {}

        for tid, key in self._SENSOR_KEYS.items():
            sensor = self._sensors.get(key)
            if sensor is not None:
                summary[key] = self._sensor_health(tid, key, sensor)

        for tid, key in self._ACTUATOR_KEYS.items():
            actuator = self._actuators.get(key)
            if actuator is not None:
                summary[key] = self._actuator_health(tid, key, actuator)

        return summary

    # ------------------------------------------------------------------
    # Internal: sensor dispatch
    # ------------------------------------------------------------------

    def _apply_sensor_action(
        self,
        target: MaintenanceTarget,
        action: MaintenanceAction,
        param:  float,
        ts:     float,
    ) -> MaintenanceResult:
        key    = self._SENSOR_KEYS[target]
        sensor = self._sensors.get(key)

        if sensor is None:
            msg = f"Sensor '{key}' not found in sensor suite"
            logger.error(msg)
            return MaintenanceResult(
                MaintenanceStatus.EXECUTION_ERROR, target, action, msg, ts
            )

        try:
            # ---- Universal sensor actions --------------------------------
            if action == MaintenanceAction.CALIBRATE:
                ref_val, skip_warmup = self._decode_calibrate_param(param)
                sensor.calibrate(ref_val, ts, skip_warmup=skip_warmup)
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: calibrated to {ref_val:.4f} (skip_warmup={skip_warmup})",
                    ts,
                )

            if action == MaintenanceAction.FULL_RESET:
                sensor.reset()
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: full factory reset applied", ts,
                )

            # ---- pH-specific actions -------------------------------------
            if action == MaintenanceAction.CLEAN_WATER:
                if not hasattr(sensor, "clean_electrode"):
                    return self._not_supported(target, action, key, ts)
                sensor.clean_electrode("water_rinse", ts)
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: water rinse complete (~50% fouling removed)", ts,
                )

            if action == MaintenanceAction.CLEAN_ACID:
                if not hasattr(sensor, "clean_electrode"):
                    return self._not_supported(target, action, key, ts)
                sensor.clean_electrode("acid_clean", ts)
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: acid clean complete (~90% mineral scale removed)", ts,
                )

            # ---- Amperometric chlorine -----------------------------------
            if action == MaintenanceAction.REPLACE_MEMBRANE:
                if not hasattr(sensor, "replace_membrane"):
                    return self._not_supported(target, action, key, ts)
                sensor.replace_membrane(ts)
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: membrane replaced, fouling/polarisation reset", ts,
                )

            # ---- DPD chlorine -------------------------------------------
            if action == MaintenanceAction.REPLACE_REAGENT:
                if not hasattr(sensor, "replace_reagent"):
                    return self._not_supported(target, action, key, ts)
                sensor.replace_reagent(ts)
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: reagent replaced, potency restored to 100%", ts,
                )

            # Actuator codes on a sensor target are invalid
            return MaintenanceResult(
                MaintenanceStatus.ACTION_NOT_SUPPORTED, target, action,
                f"{key}: action '{action.name}' is not valid for sensors", ts,
            )

        except Exception as exc:
            msg = f"{key}: action '{action.name}' raised {type(exc).__name__}: {exc}"
            logger.exception(msg)
            return MaintenanceResult(
                MaintenanceStatus.EXECUTION_ERROR, target, action, msg, ts
            )

    # ------------------------------------------------------------------
    # Internal: actuator dispatch
    # ------------------------------------------------------------------

    def _apply_actuator_action(
        self,
        target: MaintenanceTarget,
        action: MaintenanceAction,
        param:  float,
        ts:     float,
    ) -> MaintenanceResult:
        key      = self._ACTUATOR_KEYS[target]
        actuator = self._actuators.get(key)

        if actuator is None:
            msg = f"Actuator '{key}' not found in actuator suite"
            logger.error(msg)
            return MaintenanceResult(
                MaintenanceStatus.EXECUTION_ERROR, target, action, msg, ts
            )

        try:
            # ---- Universal actuator actions ------------------------------
            if action == MaintenanceAction.RESET_FAULTS:
                actuator.reset_faults()
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: fault codes cleared", ts,
                )

            if action == MaintenanceAction.CALIBRATE_ZERO:
                actuator.calibrate_zero()
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: zero/span recalibration applied", ts,
                )

            # ---- ControlValve-specific ----------------------------------
            if action == MaintenanceAction.RECALIBRATE_POSITIONER:
                if not hasattr(actuator, "recalibrate_positioner"):
                    return self._not_supported(target, action, key, ts)
                actuator.recalibrate_positioner()
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: positioner drift reset, CALIBRATION fault cleared", ts,
                )

            # ---- DosingPump-specific ------------------------------------
            if action == MaintenanceAction.REPLACE_DIAPHRAGM:
                if not hasattr(actuator, "replace_diaphragm"):
                    return self._not_supported(target, action, key, ts)
                actuator.replace_diaphragm()
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: diaphragm replaced, stroke-wear counter reset", ts,
                )

            if action == MaintenanceAction.REPLACE_CHECK_VALVES:
                if not hasattr(actuator, "replace_check_valves"):
                    return self._not_supported(target, action, key, ts)
                actuator.replace_check_valves()
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: check valves replaced, wear reset", ts,
                )

            if action == MaintenanceAction.REPLACE_TUBE:
                if not hasattr(actuator, "replace_tube"):
                    return self._not_supported(target, action, key, ts)
                actuator.replace_tube()
                return MaintenanceResult(
                    MaintenanceStatus.SUCCESS, target, action,
                    f"{key}: peristaltic tube replaced", ts,
                )

            # Sensor codes on an actuator target are invalid
            return MaintenanceResult(
                MaintenanceStatus.ACTION_NOT_SUPPORTED, target, action,
                f"{key}: action '{action.name}' is not valid for actuators", ts,
            )

        except Exception as exc:
            msg = f"{key}: action '{action.name}' raised {type(exc).__name__}: {exc}"
            logger.exception(msg)
            return MaintenanceResult(
                MaintenanceStatus.EXECUTION_ERROR, target, action, msg, ts
            )

    # ------------------------------------------------------------------
    # Internal: health snapshots
    # ------------------------------------------------------------------

    def _sensor_health(
        self, tid: int, key: str, sensor: Any
    ) -> DeviceHealth:
        """Build a DeviceHealth snapshot from a sensor object."""
        # Calibration validity (uses the most recent calibration record)
        cal_valid = False
        if hasattr(sensor, "calibration_history") and sensor.calibration_history:
            last_cal = sensor.calibration_history[-1]
            cal_valid = not last_cal.is_expired(time.monotonic())

        drift = getattr(sensor, "cumulative_drift", 0.0)

        extras: Dict[str, Any] = {}

        # pH sensor
        if hasattr(sensor, "slope_percentage"):
            extras["slope_pct"]        = sensor.slope_percentage
            extras["membrane_fouling"] = sensor.membrane_fouling
            extras["glass_etching"]    = sensor.glass_etching

        # Chlorine amperometric
        if hasattr(sensor, "membrane_fouling") and not hasattr(sensor, "slope_percentage"):
            extras["membrane_fouling"]  = sensor.membrane_fouling
            extras["membrane_age_days"] = sensor.membrane_age_days

        # Chlorine DPD
        if hasattr(sensor, "reagent_potency"):
            extras["reagent_potency"]  = sensor.reagent_potency
            extras["reagent_age_days"] = sensor.reagent_age_days

        # Actuator-related status
        extras["status"] = getattr(sensor, "status", None)
        extras["fault"]  = getattr(sensor, "fault", None)

        return DeviceHealth(
            target_id         = tid,
            target_name       = key,
            device_type       = "sensor",
            calibration_valid = cal_valid,
            cumulative_drift  = drift,
            extras            = extras,
        )

    def _actuator_health(
        self, tid: int, key: str, actuator: Any
    ) -> DeviceHealth:
        """Build a DeviceHealth snapshot from an actuator object."""
        diag = actuator.diagnostics()

        extras: Dict[str, Any] = {
            "cycles_count":        diag.cycles_count,
            "hours_runtime":       diag.hours_runtime,
            "wear_factor":         diag.wear_factor,
            "health_status":       diag.health_status,
            "fault_code":          diag.fault_code,
            "avg_response_time_s": diag.average_response_time,
        }

        # ControlValve-specific
        if hasattr(actuator, "_accumulated_drift"):
            extras["positioner_drift_pct"] = actuator._accumulated_drift

        # DosingPump-specific
        if hasattr(actuator, "_diaphragm_wear"):
            extras["diaphragm_wear"]    = actuator._diaphragm_wear
            extras["check_valve_wear"]  = actuator._check_valve_wear
            extras["total_strokes"]     = actuator._total_strokes
        if hasattr(actuator, "_tube_wear"):
            extras["tube_wear"] = actuator._tube_wear

        return DeviceHealth(
            target_id         = tid,
            target_name       = key,
            device_type       = "actuator",
            calibration_valid = True,   # actuators don't expire calibration
            cumulative_drift  = extras.get("positioner_drift_pct", 0.0),
            extras            = extras,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_calibrate_param(param: float):
        """
        Decode the composite CALIBRATE parameter.

        Convention:
          param < 1000  → reference_value=param,        skip_warmup=False
          param ≥ 1000  → reference_value=param-1000,   skip_warmup=True
        """
        if param >= 1000.0:
            return param - 1000.0, True
        return param, False

    @staticmethod
    def _not_supported(
        target: MaintenanceTarget,
        action: MaintenanceAction,
        key:    str,
        ts:     float,
    ) -> MaintenanceResult:
        msg = (
            f"{key}: action '{action.name}' not applicable to this device type"
        )
        logger.warning(msg)
        return MaintenanceResult(
            MaintenanceStatus.ACTION_NOT_SUPPORTED, target, action, msg, ts
        )