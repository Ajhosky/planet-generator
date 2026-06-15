from fastapi import APIRouter, HTTPException

from app.models.planet_input import PlanetInput
from app.models.planet_output import PlanetOutput
from app.simulation.simulator import PlanetSimulator
from app.jobs.planet_jobs import create_planet_job, get_planet_job

router = APIRouter()
simulator = PlanetSimulator()


@router.post("/simulate", response_model=PlanetOutput)
def simulate_planet(data: PlanetInput) -> PlanetOutput:
    return simulator.simulate(data)

@router.post("/jobs")
def create_planet_render_job(data: PlanetInput):
    return create_planet_job(data)


@router.get("/jobs/{job_id}")
def read_planet_render_job(job_id: str):
    job = get_planet_job(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Planet job not found")

    return job