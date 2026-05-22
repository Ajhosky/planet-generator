from app.models.composition import PlanetComposition
from app.utils.math_utils import clamp


def estimate_internal_heat(
    composition: PlanetComposition,
    mass_earth: float,
    age_billion_years: float,
) -> float:
    age_billion_years = max(age_billion_years, 0.1)

    heat = (
        composition.radioactive_elements * 2.0
        + composition.iron_magnesium * 0.5
        + mass_earth * 0.15
    ) / age_billion_years

    return clamp(heat)


def estimate_volcanism_score(
    composition: PlanetComposition,
    mass_earth: float,
    age_billion_years: float,
) -> float:
    age_factor = clamp(1.2 - age_billion_years / 5.0, 0.2, 1.2)
    mass_factor = clamp(mass_earth / 2.0)

    volcanism = (
        composition.radioactive_elements * 0.45
        + composition.sulfur * 0.20
        + composition.titanium * 0.10
        + composition.iron_magnesium * 0.10
        + mass_factor * 0.15
    )

    return clamp(volcanism * age_factor)