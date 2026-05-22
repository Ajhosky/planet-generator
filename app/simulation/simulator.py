from app.models.planet_input import PlanetInput
from app.models.planet_output import PlanetOutput, PlanetParameters
from app.simulation.atmosphere import estimate_atmosphere_score
from app.simulation.bulk_physics import (
    estimate_density,
    estimate_escape_velocity_km_s,
    estimate_gravity_g,
    estimate_radius_earth,
)
from app.simulation.climate import (
    estimate_albedo,
    estimate_equilibrium_temperature,
    estimate_greenhouse_effect,
    estimate_surface_temperature,
)
from app.simulation.geology import (
    estimate_internal_heat,
    estimate_volcanism_score,
)
from app.simulation.habitability import (
    calculate_habitability_score,
    estimate_chemistry_score,
    estimate_stability_score,
)
from app.simulation.hydrosphere import (
    estimate_liquid_water_factor,
    estimate_ocean_coverage,
)


class PlanetSimulator:
    def simulate(self, planet_input: PlanetInput) -> PlanetOutput:
        composition = planet_input.composition.normalized()

        density = estimate_density(composition)

        radius = estimate_radius_earth(
            mass_earth=planet_input.mass_earth,
            density_g_cm3=density,
        )

        gravity = estimate_gravity_g(
            mass_earth=planet_input.mass_earth,
            radius_earth=radius,
        )

        escape_velocity = estimate_escape_velocity_km_s(
            mass_earth=planet_input.mass_earth,
            radius_earth=radius,
        )

        internal_heat = estimate_internal_heat(
            composition=composition,
            mass_earth=planet_input.mass_earth,
            age_billion_years=planet_input.age_billion_years,
        )

        volcanism = estimate_volcanism_score(
            composition=composition,
            mass_earth=planet_input.mass_earth,
            age_billion_years=planet_input.age_billion_years,
        )

        albedo = estimate_albedo(composition)

        equilibrium_temperature = estimate_equilibrium_temperature(
            distance_au=planet_input.distance_au,
            star_luminosity=planet_input.star_luminosity,
            albedo=albedo,
        )

        temporary_greenhouse = estimate_greenhouse_effect(
            composition=composition,
            atmosphere_score=0.5,
        )

        temporary_surface_temperature = estimate_surface_temperature(
            equilibrium_temperature_k=equilibrium_temperature,
            greenhouse_k=temporary_greenhouse,
            internal_heating_score=internal_heat,
        )

        atmosphere = estimate_atmosphere_score(
            composition=composition,
            gravity_g=gravity,
            escape_velocity_km_s=escape_velocity,
            surface_temperature_k=temporary_surface_temperature,
            volcanism_score=volcanism,
        )

        greenhouse = estimate_greenhouse_effect(
            composition=composition,
            atmosphere_score=atmosphere,
        )

        surface_temperature = estimate_surface_temperature(
            equilibrium_temperature_k=equilibrium_temperature,
            greenhouse_k=greenhouse,
            internal_heating_score=internal_heat,
        )

        liquid_water_factor = estimate_liquid_water_factor(
            surface_temperature_k=surface_temperature,
            atmosphere_score=atmosphere,
        )

        ocean_coverage = estimate_ocean_coverage(
            composition=composition,
            liquid_water_factor=liquid_water_factor,
        )

        chemistry_score = estimate_chemistry_score(composition)

        stability_score = estimate_stability_score(
            gravity_g=gravity,
            volcanism_score=volcanism,
            atmosphere_score=atmosphere,
            surface_temperature_k=surface_temperature,
        )

        habitability_score = calculate_habitability_score(
            surface_temperature_k=surface_temperature,
            ocean_coverage=ocean_coverage,
            atmosphere_score=atmosphere,
            chemistry_score=chemistry_score,
            stability_score=stability_score,
        )

        parameters = PlanetParameters(
            density_g_cm3=round(density, 3),
            radius_earth=round(radius, 3),
            gravity_g=round(gravity, 3),
            escape_velocity_km_s=round(escape_velocity, 3),
            equilibrium_temperature_k=round(equilibrium_temperature, 3),
            surface_temperature_k=round(surface_temperature, 3),
            surface_temperature_c=round(surface_temperature - 273.15, 3),
            volcanism_score=round(volcanism, 3),
            atmosphere_score=round(atmosphere, 3),
            ocean_coverage=round(ocean_coverage, 3),
            chemistry_score=round(chemistry_score, 3),
            stability_score=round(stability_score, 3),
            habitability_score=round(habitability_score, 3),
        )

        classification = self._classify_planet(parameters)
        warnings = self._generate_warnings(parameters)

        return PlanetOutput(
            parameters=parameters,
            classification=classification,
            warnings=warnings,
        )

    def _classify_planet(self, parameters: PlanetParameters) -> str:
        if parameters.habitability_score >= 75:
            return "Temperate habitable world"

        if parameters.ocean_coverage > 0.6:
            return "Ocean world"

        if parameters.surface_temperature_c < -80:
            return "Frozen world"

        if parameters.surface_temperature_c > 120:
            return "Hot greenhouse world"

        if parameters.volcanism_score > 0.75:
            return "Volcanic world"

        if parameters.atmosphere_score < 0.2:
            return "Airless rocky world"

        return "Marginal terrestrial world"

    def _generate_warnings(self, parameters: PlanetParameters) -> list[str]:
        warnings = []

        if parameters.gravity_g < 0.3:
            warnings.append("Very low gravity may prevent long-term atmosphere retention.")

        if parameters.gravity_g > 3.0:
            warnings.append("Very high gravity would be dangerous for Earth-like organisms.")

        if parameters.surface_temperature_c < -80:
            warnings.append("Surface temperature is extremely low.")

        if parameters.surface_temperature_c > 120:
            warnings.append("Surface temperature is extremely high.")

        if parameters.atmosphere_score < 0.2:
            warnings.append("Atmosphere is probably too thin for surface habitability.")

        if parameters.volcanism_score > 0.85:
            warnings.append("Extreme volcanism may destabilize the surface environment.")

        return warnings