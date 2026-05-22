from app.models.composition import PlanetComposition
from app.simulation.constants import (
    EARTH_DENSITY_G_CM3,
    EARTH_ESCAPE_VELOCITY_KM_S,
    MATERIAL_DENSITIES_G_CM3,
)


def estimate_density(composition: PlanetComposition) -> float:
    values = composition.model_dump()

    density = 0.0

    for material, fraction in values.items():
        density += fraction * MATERIAL_DENSITIES_G_CM3[material]

    return density


def estimate_radius_earth(mass_earth: float, density_g_cm3: float) -> float:
    density_relative = density_g_cm3 / EARTH_DENSITY_G_CM3
    density_relative = max(density_relative, 0.05)

    return (mass_earth / density_relative) ** (1.0 / 3.0)


def estimate_gravity_g(mass_earth: float, radius_earth: float) -> float:
    radius_earth = max(radius_earth, 0.01)

    return mass_earth / (radius_earth ** 2)


def estimate_escape_velocity_km_s(mass_earth: float, radius_earth: float) -> float:
    radius_earth = max(radius_earth, 0.01)

    return EARTH_ESCAPE_VELOCITY_KM_S * ((mass_earth / radius_earth) ** 0.5)