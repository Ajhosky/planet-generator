import math

from app.models.composition import PlanetComposition


def estimate_albedo(composition: PlanetComposition) -> float:
    albedo = (
        composition.water_ice * 0.55
        + composition.silicates * 0.25
        + composition.iron_magnesium * 0.18
        + composition.carbon * 0.10
    )

    return max(0.05, min(0.85, albedo))


def estimate_equilibrium_temperature(
    distance_au: float,
    star_luminosity: float,
    albedo: float,
) -> float:
    distance_au = max(distance_au, 0.01)
    star_luminosity = max(star_luminosity, 0.001)

    return 278.0 * (star_luminosity ** 0.25) * ((1.0 - albedo) ** 0.25) / math.sqrt(distance_au)


def estimate_greenhouse_effect(
    composition: PlanetComposition,
    atmosphere_score: float,
) -> float:
    greenhouse = (
        composition.carbon * 80.0
        + composition.methane * 120.0
        + composition.ammonia * 60.0
        + composition.nitrogen * 20.0
    )

    return greenhouse * (0.3 + atmosphere_score)


def estimate_surface_temperature(
    equilibrium_temperature_k: float,
    greenhouse_k: float,
    internal_heating_score: float,
) -> float:
    internal_heating_k = internal_heating_score * 20.0

    return equilibrium_temperature_k + greenhouse_k + internal_heating_k