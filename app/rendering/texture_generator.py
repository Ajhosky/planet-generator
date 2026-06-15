from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from app.simulation.composition_influence import (
    composition_render_seed,
    compute_composition_influence,
)


SURFACE_WIDTH = 3072
SURFACE_HEIGHT = 1536

CLOUD_WIDTH = 2048
CLOUD_HEIGHT = 1024


def clamp01(value):
    return np.clip(value, 0.0, 1.0)


def clamp_scalar(value: float, min_value: float = 0.0, max_value: float = 1.0) -> float:
    return max(min_value, min(max_value, float(value)))


def score_to_01(value: float) -> float:
    value = float(value)
    return clamp_scalar(value / 100.0 if value > 1.0 else value)


def smoothstep(edge0: float, edge1: float, value):
    if edge0 == edge1:
        return np.zeros_like(value, dtype=np.float32)

    x = clamp01((value - edge0) / (edge1 - edge0))
    return x * x * (3.0 - 2.0 * x)


def smoothstep_scalar(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0

    x = clamp_scalar((value - edge0) / (edge1 - edge0))
    return x * x * (3.0 - 2.0 * x)


def compute_visual_water_state(
    temp_c: float,
    atmosphere_score: float,
    water_inventory: float,
) -> dict[str, float]:
    """
    Uproszczony model fazy wody do renderowania.

    Zasada:
    - water_inventory mówi, ile wody może być wizualnie dostępne,
    - temperatura decyduje, czy pokazujemy ją jako ocean, lód, parę albo wcale.

    Przy ekstremalnie wysokich temperaturach, np. 3000°C,
    nie renderujemy niebieskich oceanów ani lodu.
    """
    atmosphere = score_to_01(float(atmosphere_score))
    water_inventory = clamp_scalar(water_inventory, 0.0, 1.0)

    boiling_point_c = 100.0 + atmosphere * 35.0

    if water_inventory <= 0.01:
        return {
            "liquid": 0.0,
            "ice": 0.0,
            "vapor": 0.0,
        }

    # Ekstremalne temperatury: brak widocznej stabilnej wody.
    # Przy takich warunkach nie pokazujemy oceanów, lodu ani klasycznych chmur wodnych.
    if temp_c >= 1200.0:
        return {
            "liquid": 0.0,
            "ice": 0.0,
            "vapor": 0.0,
        }

    # Powyżej punktu krytycznego wody nie pokazujemy cieczy.
    # Zostawiamy tylko trochę pary/haze, która zanika przy wzroście temperatury.
    if temp_c >= 374.0:
        survival = 1.0 - smoothstep_scalar(374.0, 1200.0, temp_c)
        vapor = water_inventory * 0.55 * survival

        return {
            "liquid": 0.0,
            "ice": 0.0,
            "vapor": clamp_scalar(vapor, 0.0, 0.55),
        }

    # Powyżej uproszczonego punktu wrzenia: ocean szybko zanika, para rośnie.
    if temp_c >= boiling_point_c:
        overheat = clamp_scalar((temp_c - boiling_point_c) / 180.0, 0.0, 1.0)

        liquid = water_inventory * (1.0 - overheat) * 0.25
        vapor = water_inventory * (0.45 + overheat * 0.45)

        return {
            "liquid": clamp_scalar(liquid),
            "ice": 0.0,
            "vapor": clamp_scalar(vapor, 0.0, 0.9),
        }

    # Zimna planeta: głównie lód, trochę cieczy jeśli nie jest ekstremalnie zimno.
    if temp_c <= -20.0:
        freeze_factor = clamp_scalar((-20.0 - temp_c) / 80.0, 0.0, 1.0)

        ice = water_inventory * (0.65 + freeze_factor * 0.30)
        liquid = water_inventory * (0.16 * (1.0 - freeze_factor))
        vapor = water_inventory * 0.03

        return {
            "liquid": clamp_scalar(liquid),
            "ice": clamp_scalar(ice),
            "vapor": clamp_scalar(vapor),
        }

    # Zakres umiarkowany: oceany mogą istnieć.
    liquid = water_inventory * 0.86
    ice = clamp_scalar(max(0.0, -temp_c / 35.0) * water_inventory * 0.28)
    vapor = water_inventory * 0.08

    return {
        "liquid": clamp_scalar(liquid),
        "ice": clamp_scalar(ice),
        "vapor": clamp_scalar(vapor),
    }


def create_value_noise(
    rng: np.random.Generator,
    width: int,
    height: int,
    grid_w: int,
    grid_h: int,
) -> np.ndarray:
    small = rng.random((grid_h, grid_w), dtype=np.float32)
    image = Image.fromarray((small * 255).astype(np.uint8), mode="L")
    image = image.resize((width, height), Image.Resampling.BICUBIC)
    return np.asarray(image, dtype=np.float32) / 255.0


def create_fractal_noise(
    rng: np.random.Generator,
    width: int,
    height: int,
    octaves: list[tuple[int, int, float]],
) -> np.ndarray:
    result = np.zeros((height, width), dtype=np.float32)
    weight_sum = 0.0

    for grid_w, grid_h, weight in octaves:
        result += create_value_noise(rng, width, height, grid_w, grid_h) * weight
        weight_sum += weight

    result /= max(weight_sum, 0.0001)

    min_value = float(result.min())
    max_value = float(result.max())
    result = (result - min_value) / max(max_value - min_value, 0.0001)

    return result.astype(np.float32)


def mix_color(
    base: np.ndarray,
    mask: np.ndarray,
    color: tuple[int, int, int],
    strength: float,
) -> np.ndarray:
    color_array = np.array(color, dtype=np.float32).reshape(1, 1, 3)
    factor = np.clip(mask[..., None] * strength, 0.0, 1.0)
    return base * (1.0 - factor) + color_array * factor


def color_tuple(values: np.ndarray) -> tuple[int, int, int]:
    values = np.clip(values, 0, 255).astype(int)
    return int(values[0]), int(values[1]), int(values[2])


def generate_surface_map(
    planet_input: Any,
    planet_output: Any,
    output_path: Path,
) -> None:
    seed = composition_render_seed(planet_input, "surface")
    rng = np.random.default_rng(seed)

    influence = compute_composition_influence(planet_input)

    raw = influence["raw"]
    surface = influence["surface"]
    geology = influence["geology"]

    water_ice = float(raw["water_ice"])
    silicates = float(raw["silicates"])
    iron = float(raw["iron_magnesium"])
    carbon = float(raw["carbon"])
    sulfur = float(raw["sulfur"])
    titanium = float(raw["titanium"])
    radioactive = float(raw["radioactive_elements"])

    p = planet_output.parameters

    temp_c = float(p.surface_temperature_c)
    atmosphere_score = float(p.atmosphere_score)
    ocean_coverage = score_to_01(float(p.ocean_coverage))
    habitability = score_to_01(float(p.habitability_score))
    volcanism = score_to_01(float(p.volcanism_score))

    width = SURFACE_WIDTH
    height = SURFACE_HEIGHT

    y = np.linspace(-1.0, 1.0, height, dtype=np.float32)[:, None]
    latitude_abs = np.abs(y)

    terrain = create_fractal_noise(
        rng,
        width,
        height,
        [
            (8, 4, 0.50),
            (16, 8, 0.24),
            (32, 16, 0.15),
            (96, 48, 0.11),
        ],
    )

    detail = create_fractal_noise(
        rng,
        width,
        height,
        [
            (64, 32, 0.42),
            (160, 80, 0.35),
            (384, 192, 0.23),
        ],
    )

    mineral_noise = create_fractal_noise(
        rng,
        width,
        height,
        [
            (24, 12, 0.38),
            (72, 36, 0.34),
            (220, 110, 0.28),
        ],
    )

    rust_noise = create_fractal_noise(
        rng,
        width,
        height,
        [
            (48, 24, 0.45),
            (128, 64, 0.35),
            (320, 160, 0.20),
        ],
    )

    relief_strength = float(geology["relief_strength"])
    terrain = np.clip(
        terrain * (0.88 + relief_strength * 0.20)
        + detail * relief_strength * 0.035,
        0.0,
        1.0,
    )

    base_water_inventory = clamp_scalar(
        max(
            ocean_coverage,
            float(surface["visual_water"]),
        )
    )

    water_state = compute_visual_water_state(
        temp_c=temp_c,
        atmosphere_score=atmosphere_score,
        water_inventory=base_water_inventory,
    )

    visual_water = clamp_scalar(water_state["liquid"])

    if visual_water <= 0.01:
        water_mask = np.zeros((height, width), dtype=bool)
        land_mask = ~water_mask
        land_float = land_mask.astype(np.float32)
        sea_level = 0.0
    else:
        sea_level = float(np.quantile(terrain, visual_water))
        water_mask = terrain < sea_level
        land_mask = ~water_mask
        land_float = land_mask.astype(np.float32)

    cold_factor = 1.0 - smoothstep_scalar(-30.0, 35.0, temp_c)
    hot_factor = smoothstep_scalar(45.0, 260.0, temp_c)
    extreme_heat_factor = smoothstep_scalar(650.0, 1200.0, temp_c)

    ice_latitude = smoothstep(0.45, 0.95, latitude_abs)

    ice_mask = np.clip(
        (
            cold_factor * (0.48 + water_state["ice"] * 0.52)
            + ice_latitude * water_state["ice"] * 0.95
            + float(surface["ice_visual"]) * water_state["ice"] * 0.35
        )
        * (1.0 - extreme_heat_factor)
        - detail * 0.30,
        0.0,
        1.0,
    )

    desert_factor = clamp_scalar(
        smoothstep_scalar(20.0, 95.0, temp_c) * (1.0 - visual_water * 0.72),
    )

    vegetation_factor = clamp_scalar(
        habitability
        * (0.55 + float(surface["bio_green_potential"]) * 0.45)
        * (1.0 - hot_factor * 0.75)
        * (1.0 - cold_factor * 0.45)
        * (1.0 - float(surface["carbon_darkening"]) * 0.20)
        * (1.0 - iron * 0.24)
        * (1.0 - extreme_heat_factor)
    )

    lava_factor = clamp_scalar(
        volcanism * 0.55
        + float(surface["radioactive_lava"]) * 0.65
        + hot_factor * 0.24
        + extreme_heat_factor * 0.48
        - water_state["liquid"] * 0.22,
    )

    lava_mask = ((detail > 0.74) & land_mask).astype(np.float32) * lava_factor

    basalt_factor = float(surface["basalt_tint"])
    rust_factor = float(surface["rust_tint"])
    sulfur_factor = float(surface["sulfur_deposits"])
    carbon_factor = float(surface["carbon_darkening"])
    titanium_factor = float(surface["titanium_highlights"])

    ocean_deep = np.array([8, 34, 82], dtype=np.float32)
    ocean_shallow = np.array([22, 112, 150], dtype=np.float32)

    rock = np.array(
        [
            105 + 24 * sulfur,
            96 - 18 * iron + 8 * silicates,
            82 - 24 * iron + 4 * titanium,
        ],
        dtype=np.float32,
    )

    basalt = np.array(
        [
            48 + 42 * iron,
            50 - 22 * iron,
            56 - 30 * iron,
        ],
        dtype=np.float32,
    )

    sand = np.array(
        [
            181 + 20 * sulfur,
            151 - 24 * iron + 8 * silicates,
            94 - 34 * iron,
        ],
        dtype=np.float32,
    )

    vegetation = np.array(
        [
            56 - 18 * iron,
            118 - 28 * iron,
            73 - 20 * iron,
        ],
        dtype=np.float32,
    )

    ice = np.array([218, 236, 245], dtype=np.float32)
    sulfur_color = np.array([190, 156, 54], dtype=np.float32)
    iron_color = np.array([138, 68, 43], dtype=np.float32)
    carbon_color = np.array([38, 37, 36], dtype=np.float32)
    titanium_color = np.array([184, 188, 192], dtype=np.float32)
    lava = np.array([235, 73, 34], dtype=np.float32)
    heat_glow = np.array([196, 58, 34], dtype=np.float32)

    ocean_depth = np.clip(
        (sea_level - terrain) / max(abs(sea_level), 0.0001),
        0.0,
        1.0,
    )

    ocean_color = (
        ocean_shallow * (1.0 - ocean_depth[..., None])
        + ocean_deep * ocean_depth[..., None]
    )

    land_base = rock * (1.0 - detail[..., None] * 0.25) + basalt * (
        detail[..., None] * (0.15 + basalt_factor * 0.35)
    )

    land_base = land_base * (1.0 - desert_factor * 0.36) + sand * (
        desert_factor * 0.36
    )

    land_base = land_base * (1.0 - extreme_heat_factor * 0.30) + heat_glow * (
        extreme_heat_factor * 0.30
    )

    image = np.where(water_mask[..., None], ocean_color, land_base)

    carbon_mask = (
        (mineral_noise > 0.48).astype(np.float32)
        * land_float
        * carbon_factor
    )

    image = mix_color(
        image,
        carbon_mask,
        color_tuple(carbon_color),
        0.48,
    )

    iron_mask = (
        (mineral_noise > 0.40).astype(np.float32)
        * land_float
        * basalt_factor
    )

    image = mix_color(
        image,
        iron_mask,
        color_tuple(iron_color),
        0.50,
    )

    rust_mask = (
        (rust_noise > (0.46 + 0.16 * water_ice)).astype(np.float32)
        * land_float
        * rust_factor
    )

    image = mix_color(
        image,
        rust_mask,
        (154, 72, 42),
        0.58,
    )

    sulfur_mask = (
        (detail > (0.54 - sulfur_factor * 0.10)).astype(np.float32)
        * land_float
        * sulfur_factor
    )

    image = mix_color(
        image,
        sulfur_mask,
        color_tuple(sulfur_color),
        0.48,
    )

    titanium_mask = (
        (mineral_noise > 0.72).astype(np.float32)
        * land_float
        * titanium_factor
    )

    image = mix_color(
        image,
        titanium_mask,
        color_tuple(titanium_color),
        0.34,
    )

    image = mix_color(
        image,
        land_float * vegetation_factor,
        color_tuple(vegetation),
        0.46,
    )

    image = mix_color(
        image,
        ice_mask,
        color_tuple(ice),
        0.82,
    )

    image = mix_color(
        image,
        lava_mask,
        color_tuple(lava),
        0.95,
    )

    image = np.clip(image, 0, 255).astype(np.uint8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image, mode="RGB").save(output_path, optimize=True)


def generate_height_map(
    planet_input: Any,
    output_path: Path,
) -> None:
    seed = composition_render_seed(planet_input, "height")
    rng = np.random.default_rng(seed)

    influence = compute_composition_influence(planet_input)
    geology = influence["geology"]
    surface = influence["surface"]

    relief_strength = clamp_scalar(
        0.82
        + float(geology["relief_strength"]) * 0.82
        + float(surface["basalt_tint"]) * 0.24
        + float(surface["radioactive_lava"]) * 0.22
        - float(surface["visual_water"]) * 0.10,
        0.55,
        1.85,
    )

    continent = create_fractal_noise(
        rng,
        SURFACE_WIDTH,
        SURFACE_HEIGHT,
        [
            (8, 4, 0.48),
            (16, 8, 0.25),
            (32, 16, 0.15),
            (96, 48, 0.12),
        ],
    )

    mountains = create_fractal_noise(
        rng,
        SURFACE_WIDTH,
        SURFACE_HEIGHT,
        [
            (36, 18, 0.36),
            (96, 48, 0.34),
            (240, 120, 0.20),
            (520, 260, 0.10),
        ],
    )

    ridges = np.abs(mountains * 2.0 - 1.0)
    ridges = 1.0 - ridges
    ridges = np.power(np.clip(ridges, 0.0, 1.0), 1.55)

    craters = create_fractal_noise(
        rng,
        SURFACE_WIDTH,
        SURFACE_HEIGHT,
        [
            (80, 40, 0.40),
            (220, 110, 0.35),
            (620, 310, 0.25),
        ],
    )

    crater_mask = np.clip((craters - 0.62) / 0.28, 0.0, 1.0)

    terrain = (
        continent * 0.58
        + ridges * 0.34 * relief_strength
        + crater_mask * 0.18
    )

    terrain = np.clip(terrain, 0.0, 1.0)

    low = float(np.quantile(terrain, 0.04))
    high = float(np.quantile(terrain, 0.97))

    terrain = np.clip((terrain - low) / max(high - low, 0.0001), 0.0, 1.0)

    terrain = np.power(terrain, 0.82)

    image = (terrain * 255).astype(np.uint8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(image, mode="L").save(output_path, optimize=True)


def generate_cloud_map(
    planet_input: Any,
    planet_output: Any,
    output_path: Path,
) -> None:
    seed = composition_render_seed(planet_input, "clouds")
    rng = np.random.default_rng(seed)

    influence = compute_composition_influence(planet_input)

    atmosphere_inf = influence["atmosphere"]
    climate_inf = influence["climate"]
    raw = influence["raw"]

    p = planet_output.parameters

    atmosphere = score_to_01(float(p.atmosphere_score))
    ocean_coverage = score_to_01(float(p.ocean_coverage))
    temp_c = float(p.surface_temperature_c)

    nitrogen = float(raw["nitrogen"])
    methane = float(raw["methane"])
    ammonia = float(raw["ammonia"])
    sulfur = float(raw["sulfur"])
    water = float(raw["water_ice"])

    water_inventory = clamp_scalar(max(water, ocean_coverage))

    water_state = compute_visual_water_state(
        temp_c=temp_c,
        atmosphere_score=float(p.atmosphere_score),
        water_inventory=water_inventory,
    )

    thermal_cloud_survival = 1.0 - smoothstep_scalar(650.0, 1600.0, temp_c)
    chemical_haze_survival = 1.0 - smoothstep_scalar(900.0, 2200.0, temp_c)

    chemical_haze_driver = clamp_scalar(
        methane * 0.38
        + ammonia * 0.24
        + sulfur * 0.22
        + nitrogen * 0.06,
    ) * chemical_haze_survival

    cloud_strength = clamp_scalar(
        (
            atmosphere * 0.36
            + float(climate_inf["cloud_driver"]) * 0.32
            + float(atmosphere_inf["nitrogen_buffer"]) * 0.10
            + float(atmosphere_inf["methane_haze"]) * 0.10 * chemical_haze_survival
            + float(atmosphere_inf["ammonia_clouds"]) * 0.12 * chemical_haze_survival
            + water_state["vapor"] * 0.28
            + chemical_haze_driver * 0.18
            - smoothstep_scalar(180.0, 520.0, temp_c) * 0.16
        )
        * thermal_cloud_survival,
        0.0,
        1.0,
    )

    large_noise = create_fractal_noise(
        rng,
        CLOUD_WIDTH,
        CLOUD_HEIGHT,
        [
            (8, 4, 0.46),
            (18, 9, 0.30),
            (48, 24, 0.16),
            (120, 60, 0.08),
        ],
    )

    detail_noise = create_fractal_noise(
        rng,
        CLOUD_WIDTH,
        CLOUD_HEIGHT,
        [
            (40, 20, 0.34),
            (120, 60, 0.34),
            (300, 150, 0.22),
            (700, 350, 0.10),
        ],
    )

    y = np.linspace(-1.0, 1.0, CLOUD_HEIGHT, dtype=np.float32)[:, None]

    banding = 0.5 + 0.5 * np.sin(
        y * (14.0 + atmosphere * 8.0)
        + large_noise * 6.0
        + methane * 2.0
    )

    polar_clouds = smoothstep(0.55, 0.95, np.abs(y))

    cloud = np.clip(
        large_noise * 0.48
        + detail_noise * 0.30
        + banding * 0.18
        + polar_clouds * 0.12,
        0.0,
        1.0,
    )

    threshold = 0.42 - cloud_strength * 0.12
    alpha = np.clip((cloud - threshold) / 0.32, 0.0, 1.0)

    haze = np.clip(
        large_noise
        * (
            water_state["vapor"] * 0.30
            + methane * 0.18 * chemical_haze_survival
            + ammonia * 0.12 * chemical_haze_survival
            + sulfur * 0.10 * chemical_haze_survival
        ),
        0.0,
        1.0,
    )

    alpha = np.clip(alpha * 0.82 + haze * 0.35, 0.0, 1.0)
    alpha = alpha * cloud_strength

    cloud_rgb = np.array(
        [
            232 + ammonia * 10 + methane * 34 + sulfur * 18,
            236 + ammonia * 6 - methane * 10 + sulfur * 7,
            242 + nitrogen * 7 - methane * 48 + ammonia * 10,
        ],
        dtype=np.float32,
    )

    cloud_rgb = np.clip(cloud_rgb, 120, 255).astype(np.uint8)

    rgb = np.zeros((CLOUD_HEIGHT, CLOUD_WIDTH, 3), dtype=np.uint8)
    rgb[:, :, 0] = cloud_rgb[0]
    rgb[:, :, 1] = cloud_rgb[1]
    rgb[:, :, 2] = cloud_rgb[2]

    alpha_channel = (np.clip(alpha, 0.0, 1.0) * 235).astype(np.uint8)

    rgba = np.dstack([rgb, alpha_channel])

    image = Image.fromarray(rgba, mode="RGBA")
    image = image.filter(ImageFilter.GaussianBlur(radius=0.45))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, optimize=True)


def generate_planet_texture_maps(
    planet_input: Any,
    planet_output: Any,
    render_id: str,
    generated_root: Path,
) -> dict:
    render_dir = generated_root / render_id
    surface_path = render_dir / "surface_map.png"
    cloud_path = render_dir / "cloud_map.png"
    height_path = render_dir / "height_map.png"

    if not surface_path.exists():
        generate_surface_map(planet_input, planet_output, surface_path)

    if not cloud_path.exists():
        generate_cloud_map(planet_input, planet_output, cloud_path)

    if not height_path.exists():
        generate_height_map(planet_input, height_path)

    render_dir.mkdir(parents=True, exist_ok=True)
    os.utime(render_dir, None)

    return {
        "surface_map_url": f"/generated/{render_id}/surface_map.png",
        "cloud_map_url": f"/generated/{render_id}/cloud_map.png",
        "height_map_url": f"/generated/{render_id}/height_map.png",
    }