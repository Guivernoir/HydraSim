"""Scenario registry for staged ICS simulation."""

from __future__ import annotations

from .models import IcsScenario
from .scenario_data import SCENARIOS


def scenario_ids() -> tuple[str, ...]:
    return tuple(scenario.scenario_id for scenario in SCENARIOS)


def get_scenario(scenario_id: str) -> IcsScenario:
    for scenario in SCENARIOS:
        if scenario.scenario_id == scenario_id:
            return scenario
    known = ", ".join(scenario_ids())
    raise ValueError(f"unknown ICS scenario {scenario_id!r}; expected one of: {known}")
