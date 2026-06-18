"""HydraSim project quality checks.

This checker is intentionally dependency-free so it can run before optional
developer tooling is installed. It enforces the quality shape introduced by the
scenario runtime slices while tracking older oversized modules as known debt.
"""

from __future__ import annotations

import os
import re
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

MAX_FILES_PER_FOLDER = 20
MAX_LINES = 500
LEGACY_OVERSIZED = {
    "src/wt_simulator/__main__.py",
    "src/wt_simulator/core/chemistry.py",
    "src/wt_simulator/core/reactor.py",
    "src/wt_simulator/core/spatial.py",
    "src/wt_simulator/core/transport.py",
    "src/wt_simulator/maintenance/maintenance_manager.py",
    "src/wt_simulator/modbus/register_map.py",
    "src/wt_simulator/modbus/slave.py",
    "src/wt_simulator/sensors/base_sensor.py",
    "src/wt_simulator/sensors/chlorine_sensor.py",
    "src/wt_simulator/sensors/ph_sensor.py",
}
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}
LOCAL_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _project_files() -> list[Path]:
    files: list[Path] = []
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for name in names:
            path = Path(base) / name
            files.append(path)
    return files


def _check_folder_density(errors: list[str]) -> None:
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        visible = [name for name in names if not name.startswith(".")]
        if len(visible) > MAX_FILES_PER_FOLDER:
            errors.append(
                f"{_rel(Path(base))}: {len(visible)} files exceeds "
                f"{MAX_FILES_PER_FOLDER}; add subfolders"
            )


def _check_line_counts(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix != ".py":
            continue
        rel = _rel(path)
        lines = path.read_text("utf-8").splitlines()
        if len(lines) > MAX_LINES and rel not in LEGACY_OVERSIZED:
            errors.append(f"{rel}: {len(lines)} lines exceeds {MAX_LINES}")


def _target_exists(source: Path, target: str) -> bool:
    clean = target.split("#", 1)[0].strip()
    if not clean or clean.startswith(("http://", "https://", "mailto:")):
        return True
    if clean.startswith("<") and clean.endswith(">"):
        clean = clean[1:-1]
    candidate = (source.parent / clean).resolve()
    return candidate.exists()


def _check_markdown_links(files: list[Path], errors: list[str]) -> None:
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text("utf-8")
        for match in LOCAL_LINK.finditer(text):
            target = match.group(1)
            if not _target_exists(path, target):
                errors.append(f"{_rel(path)}: broken local link {target!r}")


def _check_scenario_docs(errors: list[str]) -> None:
    from wt_simulator.scenarios import get_scenario, scenario_ids, validate_scenario

    docs = (ROOT / "docs" / "MVP_MODBUS_SCENARIOS.md").read_text("utf-8") + (
        ROOT / "docs" / "SCENARIO_RUNTIME.md"
    ).read_text("utf-8")
    for scenario_id in scenario_ids():
        scenario = get_scenario(scenario_id)
        problems = validate_scenario(scenario)
        if problems:
            errors.append(f"{scenario_id}: validation failed: {problems}")
        if scenario_id not in docs:
            errors.append(f"{scenario_id}: missing from scenario docs")


def _check_ics_docs(errors: list[str]) -> None:
    from wt_simulator.ics import (
        build_runtime_artifact,
        get_profile,
        profile_ids,
        render_process_evolution_csv,
        render_ics_pcap_bytes,
        render_transcript_csv,
        scenario_ids,
        validate_profile,
    )

    docs = (
        (ROOT / "README.md").read_text("utf-8")
        + (ROOT / "docs" / "INDUSTRIAL_SIMULATOR_ROADMAP.md").read_text("utf-8")
        + (ROOT / "docs" / "REFERENCE_WATER_PLANT.md").read_text("utf-8")
        + (ROOT / "docs" / "SLICE_ROADMAP.md").read_text("utf-8")
    )
    for profile_id in profile_ids():
        problems = validate_profile(get_profile(profile_id))
        if problems:
            errors.append(f"{profile_id}: profile validation failed: {problems}")
        if profile_id not in docs:
            errors.append(f"{profile_id}: missing from ICS docs")
    for scenario_id in scenario_ids():
        if scenario_id not in docs:
            errors.append(f"{scenario_id}: missing from ICS docs")
        artifact_for_scenario = build_runtime_artifact(
            "reference-water-plant",
            scenario_id,
            "all",
            "offline-export",
        )
        if not artifact_for_scenario.process_evolution:
            errors.append(f"{scenario_id}: missing CFD process evolution")
        for record in artifact_for_scenario.process_evolution:
            try:
                record.validate()
            except ValueError as exc:
                errors.append(f"{scenario_id}: invalid process evolution: {exc}")
        process_csv = render_process_evolution_csv(artifact_for_scenario)
        if "synthetic_cfd_process_truth" not in process_csv:
            errors.append(f"{scenario_id}: missing process truth evidence status")

    artifact = build_runtime_artifact(
        "reference-water-plant",
        "ICS-WTP-002",
        "all",
        "offline-export",
    )
    if render_transcript_csv(artifact) != render_transcript_csv(artifact):
        errors.append("reference-water-plant: transcript output is not deterministic")
    if render_ics_pcap_bytes(artifact) != render_ics_pcap_bytes(artifact):
        errors.append("reference-water-plant: PCAP output is not deterministic")
    if render_process_evolution_csv(artifact) != render_process_evolution_csv(artifact):
        errors.append("reference-water-plant: process truth is not deterministic")
    for phrase in (
        "HS-31",
        "Scenario Library CFD Upgrade",
        "synthetic_cfd_process_truth",
        "process-evolution.csv",
    ):
        if phrase not in docs:
            errors.append(f"ICS CFD process docs: missing {phrase!r}")


def _check_cfd_docs(errors: list[str]) -> None:
    from wt_simulator.hydraulics.cfd import (
        AREA_IDS,
        CalibrationStatus,
        TwinStatus,
        CalibrationDataPoint,
        CalibrationEvidenceClass,
        CalibrationEvidenceSource,
        CalibrationParameter,
        CalibrationResidual,
        assess_calibration_evidence,
        assess_calibration_fit,
        boundary_condition_catalog,
        build_reference_calibration_assessment,
        build_reference_numerical_verification_suite,
        controller_coupling_catalog,
        device_coupling_catalog,
        export_cfd_summary,
        fit_calibration_parameter,
        performance_presets,
        build_reference_operator_historian_semantics,
        build_reference_supervisory_records,
        reference_area_model,
        supervisory_profile_catalog,
        unit_process_catalog,
    )

    cfd_doc = ROOT / "docs" / "CFD_DIGITAL_TWIN_ROADMAP.md"
    docs = (
        (ROOT / "README.md").read_text("utf-8")
        + (ROOT / "docs" / "MODEL_SCOPE.md").read_text("utf-8")
        + (ROOT / "docs" / "SLICE_ROADMAP.md").read_text("utf-8")
        + cfd_doc.read_text("utf-8")
    )
    required_phrases = (
        "synthetic_unvalidated",
        "synthetic_verified",
        "calibration_ready",
        "evidence_calibrated",
        "certification",
        "real-plant validation",
    )
    for phrase in required_phrases:
        if phrase not in docs:
            errors.append(f"CFD docs: missing required phrase {phrase!r}")
    for area_id in AREA_IDS:
        if area_id not in docs:
            errors.append(f"{area_id}: missing from CFD docs")
        model = reference_area_model(area_id)
        model.validate()
        assessment = build_reference_calibration_assessment(
            area_id,
            uncertainty=model.twin_metadata.uncertainty,
        )
        assessment.validate()
        if assessment.calibration_status != CalibrationStatus.UNCALIBRATED:
            errors.append(f"{area_id}: reference calibration is not uncalibrated")
        if assessment.twin_status != TwinStatus.SYNTHETIC_UNVALIDATED:
            errors.append(f"{area_id}: reference twin status is not unvalidated")
        first = export_cfd_summary(model)
        second = export_cfd_summary(model)
        if first != second:
            errors.append(f"{area_id}: CFD summary export is not deterministic")
    for unit in unit_process_catalog():
        unit.validate()
        if unit.unit_id not in docs:
            errors.append(f"{unit.unit_id}: missing from CFD docs")
        limitation_text = " ".join(unit.limitations)
        if "not a certified design model" not in limitation_text:
            errors.append(f"{unit.unit_id}: missing no-overclaim limitation")
    for contract in boundary_condition_catalog():
        contract.validate()
        if contract.condition_id not in docs:
            errors.append(f"{contract.condition_id}: missing from CFD docs")
        limitation_text = " ".join(contract.limitations)
        if (
            "not a commissioning or design-authority boundary model"
            not in limitation_text
        ):
            errors.append(f"{contract.condition_id}: missing no-overclaim limitation")
    for preset in performance_presets():
        preset.validate()
        if preset.preset_id not in docs:
            errors.append(f"{preset.preset_id}: missing from CFD docs")
    sensor_count = 0
    actuator_count = 0
    for contract in device_coupling_catalog():
        contract.validate()
        tag = getattr(contract, "sensor_tag", None) or getattr(
            contract, "actuator_tag", ""
        )
        if getattr(contract, "evidence_status", "") != "simulated_metadata":
            errors.append(f"{tag}: device coupling evidence status is not simulated")
        if hasattr(contract, "sensor_tag"):
            sensor_count += 1
        if hasattr(contract, "actuator_tag"):
            actuator_count += 1
    if sensor_count == 0:
        errors.append("CFD device coupling: missing sensor contracts")
    if actuator_count == 0:
        errors.append("CFD device coupling: missing actuator contracts")
    for phrase in ("HS-27", "Device-To-CFD Coupling", "simulated_metadata"):
        if phrase not in docs:
            errors.append(f"CFD device coupling docs: missing {phrase!r}")
    controller_count = 0
    for contract in controller_coupling_catalog():
        contract.validate()
        controller_count += 1
        if contract.evidence_status != "simulated_metadata":
            errors.append(
                f"{contract.controller_id}: controller evidence status is not simulated"
            )
    if controller_count == 0:
        errors.append("CFD controller coupling: missing controller contracts")
    for phrase in ("HS-28", "Controller-To-CFD Coupling"):
        if phrase not in docs:
            errors.append(f"CFD controller coupling docs: missing {phrase!r}")
    for profile in supervisory_profile_catalog():
        profile.validate()
        if profile.profile_id not in docs:
            errors.append(f"{profile.profile_id}: missing from CFD docs")
        if profile.evidence_status != "simulated_metadata":
            errors.append(
                f"{profile.profile_id}: supervisory evidence status is not simulated"
            )
    supervisory_record_count = 0
    for area_id in AREA_IDS:
        for record in build_reference_supervisory_records(area_id):
            record.validate()
            supervisory_record_count += 1
            if record.site_identity != "unknown":
                errors.append(f"{record.record_id}: site identity is not unknown")
            if record.evidence_status != "simulated_metadata":
                errors.append(f"{record.record_id}: evidence status is not simulated")
    if supervisory_record_count == 0:
        errors.append("CFD supervisory layer: missing reference records")
    for phrase in ("HS-29", "Supervisory Digital-Twin Layer", "site identity"):
        if phrase not in docs:
            errors.append(f"CFD supervisory docs: missing {phrase!r}")
    semantic_bundle_count = 0
    for area_id in AREA_IDS:
        bundle = build_reference_operator_historian_semantics(area_id)
        bundle.validate()
        semantic_bundle_count += 1
        if bundle.evidence_status != "simulated_metadata":
            errors.append(f"{area_id}: operator/historian bundle is not simulated")
    if semantic_bundle_count == 0:
        errors.append("CFD operator/historian semantics: missing bundles")
    for phrase in (
        "HS-29A",
        "Operator And Historian Semantics",
        "not operational historian evidence",
        "not a real operator action",
    ):
        if phrase not in docs:
            errors.append(f"CFD operator/historian docs: missing {phrase!r}")
    for phrase in (
        "HS-30",
        "Calibration And Uncertainty Framework",
        "synthetic_calibrated",
        "uncalibrated",
        "not real-plant validation",
    ):
        if phrase not in docs:
            errors.append(f"CFD calibration docs: missing {phrase!r}")
    field_source = CalibrationEvidenceSource(
        source_id="quality-field-source",
        evidence_class=CalibrationEvidenceClass.FIELD_TELEMETRY,
        description="quality-check field telemetry placeholder",
        source_reference="quality-check:field-source",
        limitations=("quality-check source only", "not full plant validation"),
    )
    parameter = CalibrationParameter(
        parameter="quality_offset",
        value=0.1,
        units="a.u.",
        source_id=field_source.source_id,
    )
    residual = CalibrationResidual.from_values(
        parameter="quality_offset",
        observed=1.0,
        predicted=1.0,
        tolerance=0.01,
    )
    direct_assessment = assess_calibration_evidence(
        area_id="quality-area",
        sources=(field_source,),
        parameters=(parameter,),
        residuals=(residual,),
    )
    if direct_assessment.calibration_status == CalibrationStatus.EVIDENCE_CALIBRATED:
        errors.append("CFD calibration: evidence status upgraded without record")
    fit = fit_calibration_parameter(
        area_id="quality-area",
        source=field_source,
        parameter="quality_offset",
        units="a.u.",
        samples=(
            CalibrationDataPoint(
                "quality-good-1", field_source.source_id, "quality_offset", 1.1, 1.0
            ),
            CalibrationDataPoint(
                "quality-good-2", field_source.source_id, "quality_offset", 1.2, 1.1
            ),
            CalibrationDataPoint(
                "quality-rejected", "other-source", "quality_offset", 0.0, 0.0
            ),
        ),
        residual_tolerance=0.001,
        accepted_min=-1.0,
        accepted_max=1.0,
    )
    fit.validate()
    if not fit.rejected_data:
        errors.append("CFD calibration: rejected sample data was not preserved")
    fit_assessment = assess_calibration_fit(fit)
    if fit_assessment.calibration_status != CalibrationStatus.EVIDENCE_CALIBRATED:
        errors.append("CFD calibration: explicit record did not support assessment")
    for phrase in (
        "HS-30B",
        "Calibration Evidence Model",
        "fitted_not_validated",
        "rejected data",
        "explicit calibration record",
    ):
        if phrase not in docs:
            errors.append(f"CFD calibration evidence docs: missing {phrase!r}")
    suite = build_reference_numerical_verification_suite()
    suite.validate()
    if not suite.passed:
        errors.append("CFD numerical verification suite: not all cases pass")
    categories = {result.category for result in suite.results}
    required_categories = {
        "manufactured_constant_solution",
        "conservation_check",
        "mesh_refinement_sensitivity",
        "boundary_condition_check",
        "long_run_drift",
    }
    missing_categories = required_categories - categories
    if missing_categories:
        errors.append(
            "CFD numerical verification suite: missing categories "
            f"{sorted(missing_categories)}"
        )
    for phrase in (
        "HS-30A",
        "Numerical Verification Suite",
        "synthetic_numerical_verification",
        "mesh refinement",
        "long-run drift",
    ):
        if phrase not in docs:
            errors.append(f"CFD verification docs: missing {phrase!r}")


def _check_required_test_dependencies(errors: list[str]) -> None:
    if importlib.util.find_spec("pymodbus") is None:
        errors.append(
            "pymodbus is required for the full quality gate; "
            'install with `pip install -e ".[dev,modbus]"`'
        )


def main() -> int:
    errors: list[str] = []
    files = _project_files()
    _check_folder_density(errors)
    _check_line_counts(files, errors)
    _check_markdown_links(files, errors)
    _check_scenario_docs(errors)
    _check_ics_docs(errors)
    _check_cfd_docs(errors)
    _check_required_test_dependencies(errors)

    if errors:
        print("HydraSim quality check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("HydraSim quality check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
