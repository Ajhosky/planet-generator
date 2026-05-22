from fastapi import APIRouter

from app.models.planet_input import PlanetInput
from app.models.planet_output import PlanetOutput
from app.simulation.simulator import PlanetSimulator

router = APIRouter()
simulator = PlanetSimulator()


@router.post("/simulate", response_model=PlanetOutput)
def simulate_planet(data: PlanetInput) -> PlanetOutput:
    return simulator.simulate(data)