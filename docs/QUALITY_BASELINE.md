# HydraSim Quality Baseline

HydraSim now uses a local quality gate:

```bash
python tools/check_project_quality.py
python -m black --check src/wt_simulator/scenarios tests/test_mvp_modbus_scenarios.py tools
python -m unittest discover -s tests -v
```

The gate enforces:

- built-in scenario validation;
- built-in scenario documentation coverage;
- local Markdown link resolution;
- folder-density limits;
- a 500-line limit for new Python modules;
- formatting on the new scenario runtime, its tests, and local quality tools;
- an explicit legacy exception list for oversized modules that existed before
  the scenario runtime work.

## Legacy Oversized Modules

The quality checker allows the existing physics, sensor, maintenance, Modbus,
and runtime orchestration modules to exceed 500 lines as known technical debt.
The CI formatting gate also avoids mass-formatting those legacy scientific
modules until they are refactored intentionally. New scenario-runtime code is
below the line limit and Black-formatted. Future refactors should reduce the
legacy exception list instead of adding to it.

## Optional Dependency Boundary

`pymodbus` remains optional. Unit tests that require it are allowed to skip when
the optional dependency is absent. Scenario transcript, PCAP, validation, and
bundle generation must remain usable without `pymodbus`.
