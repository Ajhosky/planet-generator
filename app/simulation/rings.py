from __future__ import annotations

import hashlib
import math
from typing import Any


def clamp(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, value))


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0

    x = clamp((value - edge0) / (edge1 - edge0))
    return x * x * (3.0 - 2.0 * x)


def seeded_unit(seed: int, salt: str) -> float:
    raw = f"{seed}:{salt}".encode("utf-8")
    digest = hashlib.sha256(raw).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64)


def compute_ring_config(planet_input: Any, parameters: Any) -> dict:
    c = planet_input.composition

    mass_earth = float(planet_input.mass_earth)
    distance_au = float(planet_input.distance_au)
    age_billion_years = float(planet_input.age_billion_years)
    rotation_period_hours = float(planet_input.rotation_period_hours)
    seed = int(planet_input.seed)

    density = float(parameters.density_g_cm3)
    escape_velocity = float(parameters.escape_velocity_km_s)
    surface_temp_c = float(parameters.surface_temperature_c)
    habitability = float(parameters.habitability_score)

    water_ice = float(c.water_ice)
    silicates = float(c.silicates)
    iron_magnesium = float(c.iron_magnesium)
    carbon = float(c.carbon)
    sulfur = float(c.sulfur)

    solid_sum = max(
        water_ice + silicates + iron_magnesium + carbon + sulfur,
        0.0001,
    )

    ice_fraction = clamp(water_ice / solid_sum)
    dust_fraction = clamp((silicates + carbon + sulfur) / solid_sum)

    if ice_fraction > 0.55:
        ring_composition = "icy"
        satellite_density = 0.93
        base_color = "#dcecff"
    elif dust_fraction > 0.65:
        ring_composition = "dusty"
        satellite_density = 2.2
        base_color = "#8b8178"
    elif silicates + iron_magnesium > water_ice:
        ring_composition = "rocky"
        satellite_density = 2.8
        base_color = "#aaa095"
    else:
        ring_composition = "mixed"
        satellite_density = 1.6
        base_color = "#b9b8ad"

    roche_limit_planet_radii = 2.44 * math.pow(
        max(density, 0.1) / satellite_density,
        1.0 / 3.0,
    )

    mass_score = smoothstep(0.8, 12.0, mass_earth)
    gravity_score = smoothstep(8.0, 28.0, escape_velocity)
    ice_source_score = smoothstep(0.15, 0.75, water_ice)
    debris_score = clamp(0.45 * dust_fraction + 0.55 * seeded_unit(seed, "collision-debris"))
    cold_score = 1.0 - smoothstep(-40.0, 120.0, surface_temp_c)
    outer_system_score = smoothstep(1.2, 6.0, distance_au)
    fast_rotation_score = 1.0 - smoothstep(18.0, 96.0, rotation_period_hours)
    young_system_score = 1.0 - smoothstep(1.0, 6.5, age_billion_years)

    hot_penalty = smoothstep(120.0, 420.0, surface_temp_c)
    habitable_penalty = smoothstep(0.45, 0.85, habitability)
    tiny_planet_penalty = 1.0 - smoothstep(0.35, 1.0, mass_earth)

    score = (
        0.22 * mass_score
        + 0.18 * gravity_score
        + 0.18 * ice_source_score
        + 0.13 * debris_score
        + 0.10 * cold_score
        + 0.08 * outer_system_score
        + 0.06 * fast_rotation_score
        + 0.05 * young_system_score
    )

    score -= 0.18 * hot_penalty
    score -= 0.16 * habitable_penalty
    score -= 0.18 * tiny_planet_penalty
    score = clamp(score)

    inner_radius = 1.35 + 0.18 * seeded_unit(seed, "ring-inner")
    outer_radius = min(
        roche_limit_planet_radii * 0.92,
        3.75 + 0.25 * seeded_unit(seed, "ring-outer"),
    )

    has_rings = score >= 0.48 and outer_radius > inner_radius + 0.35

    if not has_rings:
        return {
            "has_rings": False,
            "reason": "Ring score too low or Roche zone too narrow",
            "score": round(score, 3),
            "composition": ring_composition,
            "inner_radius_planet_radii": round(inner_radius, 3),
            "outer_radius_planet_radii": round(max(outer_radius, inner_radius), 3),
            "tilt_degrees": 0.0,
            "bands": [],
        }

    tilt_degrees = -24.0 + 48.0 * seeded_unit(seed, "ring-tilt")
    band_count = 3 + int(seeded_unit(seed, "ring-band-count") * 4)

    available_width = outer_radius - inner_radius
    cursor = inner_radius
    bands = []

    for index in range(band_count):
        segment_width = available_width / band_count
        gap = segment_width * (0.10 + 0.18 * seeded_unit(seed, f"ring-gap-{index}"))

        band_inner = cursor
        band_outer = min(cursor + segment_width - gap, outer_radius)

        if band_outer > band_inner + 0.03:
            band_opacity = clamp(
                0.16 + score * 0.46 + 0.12 * seeded_unit(seed, f"ring-opacity-{index}"),
                0.12,
                0.72,
            )

            bands.append(
                {
                    "inner_radius_planet_radii": round(band_inner, 3),
                    "outer_radius_planet_radii": round(band_outer, 3),
                    "opacity": round(band_opacity, 3),
                    "color": base_color,
                }
            )

        cursor += segment_width

    if ring_composition == "icy":
        reason = "Icy moon debris can remain as rings inside the Roche limit"
    elif ring_composition == "dusty":
        reason = "Dusty debris from impacts or small moons can form a faint ring system"
    elif ring_composition == "rocky":
        reason = "Rocky debris can survive as a darker ring system inside the Roche limit"
    else:
        reason = "Mixed icy and dusty debris can form rings inside the Roche limit"

    return {
        "has_rings": True,
        "reason": reason,
        "score": round(score, 3),
        "composition": ring_composition,
        "inner_radius_planet_radii": round(inner_radius, 3),
        "outer_radius_planet_radii": round(outer_radius, 3),
        "tilt_degrees": round(tilt_degrees, 2),
        "bands": bands,
    }