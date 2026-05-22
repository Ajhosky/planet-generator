from pydantic import BaseModel, Field

from app.models.composition import PlanetComposition


class PlanetInput(BaseModel):
    composition: PlanetComposition = Field(default_factory=PlanetComposition)

    mass_earth: float = Field(1.0, ge=0.1, le=10.0)
    distance_au: float = Field(1.0, ge=0.01, le=20.0)
    star_luminosity: float = Field(1.0, ge=0.001, le=100.0)

    age_billion_years: float = Field(4.5, ge=0.1, le=13.8)
    rotation_period_hours: float = Field(24.0, ge=1.0, le=1000.0)

    planet_type: str = "regular"
    seed: int = 42