from __future__ import annotations

import hashlib
from typing import Any


COMPOSITION_FIELDS = (
    "silicates",
    "iron_magnesium",
    "water_ice",
    "carbon",
    "sulfur",
    "titanium",
    "radioactive_elements",
    "nitrogen",
    "methane",
    "ammonia",
    "phosphorus",
)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def get_value(source: Any, field: str) -> float:
    return clamp01(getattr(source, field, 0.0))


def composition_render_seed(planet_input: Any, salt: str = "surface") -> int:
    c = planet_input.composition

    payload = (
        f"{planet_input.seed}:"
        f"{salt}:"
        f"{get_value(c, 'silicates'):.4f}:"
        f"{get_value(c, 'iron_magnesium'):.4f}:"
        f"{get_value(c, 'water_ice'):.4f}:"
        f"{get_value(c, 'carbon'):.4f}:"
        f"{get_value(c, 'sulfur'):.4f}:"
        f"{get_value(c, 'titanium'):.4f}:"
        f"{get_value(c, 'radioactive_elements'):.4f}:"
        f"{get_value(c, 'nitrogen'):.4f}:"
        f"{get_value(c, 'methane'):.4f}:"
        f"{get_value(c, 'ammonia'):.4f}:"
        f"{get_value(c, 'phosphorus'):.4f}"
    )

    digest = hashlib.sha256(payload.encode("utf-8")).digest()

    return int.from_bytes(digest[:8], "big") % (2**32)


def compute_composition_influence(planet_input: Any) -> dict:
    c = planet_input.composition

    values = {
        field: get_value(c, field)
        for field in COMPOSITION_FIELDS
    }

    silicates = values["silicates"]
    iron = values["iron_magnesium"]
    water = values["water_ice"]
    carbon = values["carbon"]
    sulfur = values["sulfur"]
    titanium = values["titanium"]
    radioactive = values["radioactive_elements"]
    nitrogen = values["nitrogen"]
    methane = values["methane"]
    ammonia = values["ammonia"]
    phosphorus = values["phosphorus"]

    solid_budget = max(
        silicates + iron + water + carbon + sulfur + titanium + radioactive + phosphorus,
        0.0001,
    )

    volatile_budget = max(
        water + nitrogen + methane + ammonia,
        0.0001,
    )

    rocky_fraction = clamp01((silicates + iron + titanium + radioactive) / solid_budget)
    volatile_fraction = clamp01((water + nitrogen + methane + ammonia) / volatile_budget)
    organic_fraction = clamp01((carbon + phosphorus + methane + ammonia) / max(solid_budget + volatile_budget, 0.0001))

    density_driver = clamp01(
        iron * 0.62
        + silicates * 0.25
        + titanium * 0.08
        + radioactive * 0.05
        - water * 0.18
    )

    relief_strength = clamp01(
        0.45
        + silicates * 0.28
        + iron * 0.22
        + radioactive * 0.18
        - water * 0.16
    )

    volcanism_driver = clamp01(
        radioactive * 0.55
        + iron * 0.22
        + sulfur * 0.13
        + silicates * 0.10
    )

    greenhouse_driver = clamp01(
        methane * 0.48
        + ammonia * 0.27
        + nitrogen * 0.10
        + water * 0.15
    )

    cloud_driver = clamp01(
        nitrogen * 0.28
        + water * 0.25
        + ammonia * 0.23
        + methane * 0.16
        + sulfur * 0.08
    )

    toxic_atmosphere_driver = clamp01(
        methane * 0.38
        + ammonia * 0.36
        + sulfur * 0.18
        + radioactive * 0.08
    )

    visual_water = clamp01(water * 0.85)

    ice_visual = clamp01(
        water * 0.68
        + ammonia * 0.12
        + nitrogen * 0.08
    )

    basalt_tint = clamp01(
        iron * 0.70
        + silicates * 0.20
        + titanium * 0.10
    )

    rust_tint = clamp01(
        iron * (0.65 + sulfur * 0.15) * (1.0 - water * 0.22)
    )

    sulfur_deposits = clamp01(
        sulfur * (0.65 + volcanism_driver * 0.35)
    )

    carbon_darkening = clamp01(
        carbon * 0.80
        + methane * 0.12
    )

    titanium_highlights = clamp01(
        titanium * (0.75 + silicates * 0.25)
    )

    radioactive_lava = clamp01(
        radioactive * 0.72
        + sulfur * 0.10
        + iron * 0.10
    )

    bio_green_potential = clamp01(
        phosphorus * 0.30
        + water * 0.28
        + nitrogen * 0.24
        + carbon * 0.18
        - toxic_atmosphere_driver * 0.20
        - radioactive * 0.22
    )

    methane_haze = clamp01(
        methane * 0.72
        + carbon * 0.10
        + ammonia * 0.08
    )

    ammonia_clouds = clamp01(
        ammonia * 0.72
        + nitrogen * 0.14
        + water * 0.14
    )

    nitrogen_buffer = clamp01(
        nitrogen * 0.82
        + water * 0.08
        + ammonia * 0.05
        + methane * 0.05
    )

    icy_ring_material = clamp01(
        water * 0.72
        + ammonia * 0.18
        + nitrogen * 0.10
    )

    dusty_ring_material = clamp01(
        silicates * 0.35
        + carbon * 0.28
        + sulfur * 0.22
        + titanium * 0.15
    )

    rocky_ring_material = clamp01(
        silicates * 0.40
        + iron * 0.35
        + titanium * 0.15
        + radioactive * 0.10
    )

    return {
        "raw": values,
        "fractions": {
            "rocky_fraction": round(rocky_fraction, 4),
            "volatile_fraction": round(volatile_fraction, 4),
            "organic_fraction": round(organic_fraction, 4),
        },
        "physics": {
            "density_driver": round(density_driver, 4),
            "rocky_body": round(rocky_fraction, 4),
            "volatile_budget": round(volatile_fraction, 4),
        },
        "geology": {
            "relief_strength": round(relief_strength, 4),
            "volcanism_driver": round(volcanism_driver, 4),
            "radiogenic_heating": round(radioactive, 4),
            "core_metallicity": round(iron, 4),
            "silicate_crust": round(silicates, 4),
        },
        "climate": {
            "greenhouse_driver": round(greenhouse_driver, 4),
            "cloud_driver": round(cloud_driver, 4),
            "toxic_atmosphere_driver": round(toxic_atmosphere_driver, 4),
        },
        "surface": {
            "visual_water": round(visual_water, 4),
            "ice_visual": round(ice_visual, 4),
            "basalt_tint": round(basalt_tint, 4),
            "rust_tint": round(rust_tint, 4),
            "sulfur_deposits": round(sulfur_deposits, 4),
            "carbon_darkening": round(carbon_darkening, 4),
            "titanium_highlights": round(titanium_highlights, 4),
            "radioactive_lava": round(radioactive_lava, 4),
            "bio_green_potential": round(bio_green_potential, 4),
        },
        "atmosphere": {
            "nitrogen_buffer": round(nitrogen_buffer, 4),
            "methane_haze": round(methane_haze, 4),
            "ammonia_clouds": round(ammonia_clouds, 4),
            "cloud_driver": round(cloud_driver, 4),
        },
        "rings": {
            "icy_material": round(icy_ring_material, 4),
            "dusty_material": round(dusty_ring_material, 4),
            "rocky_material": round(rocky_ring_material, 4),
        },
    }