from pydantic import BaseModel


class PlanetParameters(BaseModel):
    density_g_cm3: float
    radius_earth: float
    gravity_g: float
    escape_velocity_km_s: float

    equilibrium_temperature_k: float
    surface_temperature_k: float
    surface_temperature_c: float

    volcanism_score: float
    atmosphere_score: float
    ocean_coverage: float

    chemistry_score: float
    stability_score: float
    habitability_score: float


class PlanetOutput(BaseModel):
    parameters: PlanetParameters
    classification: str
    warnings: list[str]