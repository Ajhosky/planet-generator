from app.models.composition import PlanetComposition
from app.utils.math_utils import clamp


def estimate_liquid_water_factor(
    surface_temperature_k: float,
    atmosphere_score: float,
) -> float:
    if 273.15 <= surface_temperature_k <= 373.15:
        temp_factor = 1.0
    elif 240.0 <= surface_temperature_k < 273.15:
        temp_factor = 0.4
    elif 373.15 < surface_temperature_k <= 450.0:
        temp_factor = 0.3
    else:
        temp_factor = 0.0

    pressure_factor = clamp(atmosphere_score / 0.4)

    return clamp(temp_factor * pressure_factor)


def estimate_ocean_coverage(
    composition: PlanetComposition,
    liquid_water_factor: float,
) -> float:
    return clamp(composition.water_ice * liquid_water_factor * 3.0)