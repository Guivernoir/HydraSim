"""HydraSim project quality checks.

This checker is intentionally dependency-free so it can run before optional
developer tooling is installed. It enforces the quality shape introduced by the
scenario runtime slices while tracking older oversized modules as known debt.
"""

from __future__ import annotations

import os
import re
import sys
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


def main() -> int:
    errors: list[str] = []
    files = _project_files()
    _check_folder_density(errors)
    _check_line_counts(files, errors)
    _check_markdown_links(files, errors)
    _check_scenario_docs(errors)

    if errors:
        print("HydraSim quality check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("HydraSim quality check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
