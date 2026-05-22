from app.models.composition import PlanetComposition
from app.utils.math_utils import clamp


def estimate_atmosphere_score(
    composition: PlanetComposition,
    gravity_g: float,
    escape_velocity_km_s: float,
    surface_temperature_k: float,
    volcanism_score: float,
) -> float:
    atmosphere = (
        composition.nitrogen * 0.25
        + composition.methane * 0.15
        + composition.ammonia * 0.15
        + composition.water_ice * 0.15
        + volcanism_score * 0.20
        + min(gravity_g, 2.0) * 0.10
    )

    if gravity_g < 0.4:
        atmosphere *= 0.4

    if escape_velocity_km_s < 5.0:
        atmosphere *= 0.6

    if surface_temperature_k > 450:
        atmosphere *= 0.5

    if surface_temperature_k < 120:
        atmosphere *= 0.7

    return clamp(atmosphere)