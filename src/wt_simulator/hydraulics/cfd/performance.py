"""Early CFD performance envelope helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass

from .fields import ScalarField
from .mesh import BoundaryPatch, StructuredMesh, create_rectangular_mesh
from .scalar import ScalarTransportConfig, step_scalar_transport
from .solver import FlowSolverConfig, initialize_flow, solve_flow_step

BYTES_PER_FLOAT64 = 8
FLOW_ARRAY_COUNT = 4


@dataclass(frozen=True)
class CfdPerformancePreset:
    preset_id: str
    cells: tuple[int, int, int]
    extents: tuple[float, float, float]
    solver_dt: float
    scalar_count: int
    intended_use: str

    def validate(self) -> None:
        if not self.preset_id:
            raise ValueError("preset_id is required")
        if min(self.cells) <= 0:
            raise ValueError(f"{self.preset_id}: cells must be positive")
        if min(self.extents) <= 0.0:
            raise ValueError(f"{self.preset_id}: extents must be positive")
        if self.solver_dt <= 0.0:
            raise ValueError(f"{self.preset_id}: solver_dt must be positive")
        if self.scalar_count < 1:
            raise ValueError(f"{self.preset_id}: scalar_count must be positive")
        if not self.intended_use:
            raise ValueError(f"{self.preset_id}: intended_use is required")


@dataclass(frozen=True)
class CfdBenchmarkResult:
    preset_id: str
    cell_count: int
    estimated_field_memory_bytes: int
    iterations: int
    wall_time_seconds: float
    stable: bool
    max_cfl: float
    mass_residual: float

    def validate(self) -> None:
        if self.cell_count <= 0:
            raise ValueError("cell_count must be positive")
        if self.estimated_field_memory_bytes <= 0:
            raise ValueError("estimated memory must be positive")
        if self.iterations <= 0:
            raise ValueError("iterations must be positive")
        if self.wall_time_seconds < 0.0:
            raise ValueError("wall time cannot be negative")


def performance_presets() -> tuple[CfdPerformancePreset, ...]:
    return (
        CfdPerformancePreset(
            preset_id="tiny-grid",
            cells=(6, 3, 2),
            extents=(3.0, 1.0, 0.8),
            solver_dt=0.01,
            scalar_count=2,
            intended_use="unit tests and smoke checks",
        ),
        CfdPerformancePreset(
            preset_id="small-grid",
            cells=(10, 4, 3),
            extents=(5.0, 1.5, 1.2),
            solver_dt=0.01,
            scalar_count=3,
            intended_use="selected-area offline scenario checks",
        ),
        CfdPerformancePreset(
            preset_id="medium-grid",
            cells=(16, 6, 4),
            extents=(8.0, 3.0, 1.8),
            solver_dt=0.005,
            scalar_count=4,
            intended_use="pre-coupling benchmark ceiling on developer machines",
        ),
    )


def get_performance_preset(preset_id: str) -> CfdPerformancePreset:
    for preset in performance_presets():
        if preset.preset_id == preset_id:
            return preset
    raise ValueError(f"unknown performance preset: {preset_id}")


def performance_preset_ids() -> tuple[str, ...]:
    return tuple(preset.preset_id for preset in performance_presets())


def mesh_for_preset(preset: CfdPerformancePreset) -> StructuredMesh:
    preset.validate()
    return create_rectangular_mesh(
        cells=preset.cells,
        extents=preset.extents,
        boundaries=(
            BoundaryPatch("benchmark-inlet", "xmin", "inlet", 0.02),
            BoundaryPatch("benchmark-outlet", "xmax", "outlet", 0.0),
            BoundaryPatch("benchmark-floor", "zmin", "wall", 0.0),
            BoundaryPatch("benchmark-surface", "zmax", "symmetry", 0.0),
        ),
    )


def estimate_field_memory_bytes(
    mesh: StructuredMesh, *, scalar_count: int, include_mask: bool = True
) -> int:
    if scalar_count < 0:
        raise ValueError("scalar_count cannot be negative")
    float_arrays = FLOW_ARRAY_COUNT + scalar_count
    mask_bytes = mesh.cell_count if include_mask else 0
    return (mesh.cell_count * float_arrays * BYTES_PER_FLOAT64) + mask_bytes


def run_cfd_benchmark(
    preset: CfdPerformancePreset, *, iterations: int = 3
) -> CfdBenchmarkResult:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    mesh = mesh_for_preset(preset)
    flow = initialize_flow(mesh)
    scalar = ScalarField.uniform(mesh, name="benchmark_scalar", units="a.u.", value=1.0)
    flow_config = FlowSolverConfig(dt=preset.solver_dt, pressure_iterations=2)
    scalar_config = ScalarTransportConfig(dt=preset.solver_dt, diffusivity=1.0e-5)

    started = time.perf_counter()
    stable = True
    max_cfl = 0.0
    mass_residual = 0.0
    for _ in range(iterations):
        flow, flow_result = solve_flow_step(mesh, flow, flow_config)
        scalar, scalar_result = step_scalar_transport(
            mesh,
            scalar,
            flow,
            scalar_config,
            source_cells=((0, 0, 0, 0.01),),
        )
        stable = stable and flow_result.stable and scalar_result.stable
        max_cfl = max(max_cfl, flow_result.max_cfl)
        mass_residual = flow_result.mass_residual
    elapsed = time.perf_counter() - started

    result = CfdBenchmarkResult(
        preset_id=preset.preset_id,
        cell_count=mesh.cell_count,
        estimated_field_memory_bytes=estimate_field_memory_bytes(
            mesh, scalar_count=preset.scalar_count
        ),
        iterations=iterations,
        wall_time_seconds=elapsed,
        stable=stable,
        max_cfl=max_cfl,
        mass_residual=mass_residual,
    )
    result.validate()
    return result
