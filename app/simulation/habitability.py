from app.models.composition import PlanetComposition
from app.utils.math_utils import bell_score, clamp


def estimate_chemistry_score(composition: PlanetComposition) -> float:
    chemistry = (
        composition.carbon * 0.25
        + composition.nitrogen * 0.25
        + composition.phosphorus * 0.20
        + composition.water_ice * 0.20
        + composition.sulfur * 0.10
    )

    return clamp(chemistry * 3.0)


def estimate_stability_score(
    gravity_g: float,
    volcanism_score: float,
    atmosphere_score: float,
    surface_temperature_k: float,
) -> float:
    stability = 1.0

    if gravity_g < 0.3 or gravity_g > 3.0:
        stability *= 0.5

    if volcanism_score > 0.85:
        stability *= 0.6

    if atmosphere_score < 0.2:
        stability *= 0.4

    if surface_temperature_k < 180.0 or surface_temperature_k > 500.0:
        stability *= 0.2

    return clamp(stability)


def calculate_habitability_score(
    surface_temperature_k: float,
    ocean_coverage: float,
    atmosphere_score: float,
    chemistry_score: float,
    stability_score: float,
) -> float:
    temperature_score = bell_score(surface_temperature_k, ideal=288.0, tolerance=120.0)

    habitability = (
        temperature_score * 0.30
        + ocean_coverage * 0.25
        + atmosphere_score * 0.20
        + chemistry_score * 0.15
        + stability_score * 0.10
    )

    return clamp(habitability) * 100.0