from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from pydantic import BaseModel

from app.models.planet_input import PlanetInput
from app.rendering.cache import cleanup_generated_cache
from app.rendering.fingerprint import create_planet_render_id
from app.rendering.texture_generator import generate_planet_texture_maps
from app.simulation.composition_influence import compute_composition_influence
from app.simulation.rings import compute_ring_config
from app.simulation.simulator import PlanetSimulator


GENERATED_ROOT = Path("generated")
GENERATED_CACHE_LIMIT = 2

_executor = ThreadPoolExecutor(max_workers=1)
_jobs_lock = Lock()
_jobs: dict[str, "PlanetJob"] = {}


class PlanetJob(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    created_at: str
    updated_at: str
    result: Any | None = None
    error: str | None = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def model_to_dict(model: BaseModel) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()

    return model.dict()


def clamp_scalar(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, float(value)))


def score_to_01(value: float) -> float:
    value = float(value)
    return clamp_scalar(value / 100.0 if value > 1.0 else value)


def set_job_state(
    job_id: str,
    *,
    status: str | None = None,
    progress: float | None = None,
    message: str | None = None,
    result: Any | None = None,
    error: str | None = None,
) -> None:
    with _jobs_lock:
        job = _jobs[job_id]
        data = model_to_dict(job)

        if status is not None:
            data["status"] = status

        if progress is not None:
            data["progress"] = progress

        if message is not None:
            data["message"] = message

        if result is not None:
            data["result"] = result

        if error is not None:
            data["error"] = error

        data["updated_at"] = utc_now_iso()

        _jobs[job_id] = PlanetJob(**data)


def create_planet_job(planet_input: PlanetInput) -> PlanetJob:
    job_id = str(uuid4())
    now = utc_now_iso()

    job = PlanetJob(
        job_id=job_id,
        status="queued",
        progress=0.0,
        message="Queued",
        created_at=now,
        updated_at=now,
        result=None,
        error=None,
    )

    with _jobs_lock:
        _jobs[job_id] = job

    _executor.submit(run_planet_job, job_id, planet_input)

    return job


def get_planet_job(job_id: str) -> PlanetJob | None:
    with _jobs_lock:
        return _jobs.get(job_id)


def attach_visuals_to_output(planet_output: Any, visuals: dict) -> Any:
    if hasattr(planet_output, "model_copy"):
        return planet_output.model_copy(update={"visuals": visuals})

    if hasattr(planet_output, "copy"):
        return planet_output.copy(update={"visuals": visuals})

    raise TypeError(f"Unsupported PlanetOutput type: {type(planet_output)}")


def with_updated_warnings(planet_output: Any, warnings: list[str]) -> Any:
    existing_warnings = list(getattr(planet_output, "warnings", []) or [])

    for warning in warnings:
        if warning not in existing_warnings:
            existing_warnings.append(warning)

    if hasattr(planet_output, "model_copy"):
        return planet_output.model_copy(update={"warnings": existing_warnings})

    if hasattr(planet_output, "copy"):
        return planet_output.copy(update={"warnings": existing_warnings})

    raise TypeError(f"Unsupported PlanetOutput type: {type(planet_output)}")


def add_water_phase_warnings(
    planet_input: PlanetInput,
    planet_output: Any,
) -> Any:
    water_inventory = clamp_scalar(float(planet_input.composition.water_ice))

    if water_inventory <= 0.05:
        return planet_output

    parameters = planet_output.parameters

    temp_c = float(parameters.surface_temperature_c)
    atmosphere = score_to_01(float(parameters.atmosphere_score))
    boiling_point_c = 100.0 + atmosphere * 35.0

    warnings: list[str] = []

    if temp_c >= 1200.0:
        warnings.append(
            "Surface is far too hot for stable water. Oceans, ice and water clouds were suppressed in the render."
        )
    elif temp_c >= 374.0:
        warnings.append(
            "Surface temperature exceeds the critical point of water. Water cannot exist as liquid oceans and is rendered only as limited vapor or haze."
        )
    elif temp_c >= boiling_point_c:
        warnings.append(
            "Surface is too hot for stable liquid water. Any surface water would mostly evaporate into vapor."
        )
    elif temp_c <= -20.0 and water_inventory > 0.15:
        warnings.append(
            "Surface is cold enough that most visible water is rendered as ice rather than liquid oceans."
        )

    if not warnings:
        return planet_output

    return with_updated_warnings(planet_output, warnings)


def run_planet_job(job_id: str, planet_input: PlanetInput) -> None:
    try:
        set_job_state(
            job_id,
            status="running",
            progress=0.10,
            message="Simulating planet physics",
        )

        simulator = PlanetSimulator()
        planet_output = simulator.simulate(planet_input)

        planet_output = add_water_phase_warnings(
            planet_input=planet_input,
            planet_output=planet_output,
        )

        set_job_state(
            job_id,
            progress=0.28,
            message="Computing composition influence map",
        )

        influence_map = compute_composition_influence(planet_input)

        set_job_state(
            job_id,
            progress=0.38,
            message="Preparing render cache",
        )

        render_id = create_planet_render_id(planet_input)

        set_job_state(
            job_id,
            progress=0.50,
            message="Generating high-resolution texture maps",
        )

        maps = generate_planet_texture_maps(
            planet_input=planet_input,
            planet_output=planet_output,
            render_id=render_id,
            generated_root=GENERATED_ROOT,
        )

        set_job_state(
            job_id,
            progress=0.82,
            message="Computing ring system",
        )

        rings = compute_ring_config(
            planet_input=planet_input,
            parameters=planet_output.parameters,
        )

        visuals = {
            "render_id": render_id,
            "maps": maps,
            "rings": rings,
            "influence_map": influence_map,
        }

        planet_output_with_visuals = attach_visuals_to_output(
            planet_output=planet_output,
            visuals=visuals,
        )

        set_job_state(
            job_id,
            progress=0.94,
            message="Cleaning old generated texture maps",
        )

        cleanup_generated_cache(
            generated_root=GENERATED_ROOT,
            keep_latest=GENERATED_CACHE_LIMIT,
        )

        set_job_state(
            job_id,
            status="succeeded",
            progress=1.0,
            message="Planet render completed",
            result=planet_output_with_visuals,
        )

    except Exception as exc:
        set_job_state(
            job_id,
            status="failed",
            progress=1.0,
            message="Planet render failed",
            error=str(exc),
        )