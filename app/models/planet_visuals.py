from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class PlanetTextureMaps(BaseModel):
    surface_map_url: str
    cloud_map_url: str | None = None
    height_map_url: str | None = None


class PlanetRingBand(BaseModel):
    inner_radius_planet_radii: float
    outer_radius_planet_radii: float
    opacity: float
    color: str


class PlanetRingConfig(BaseModel):
    has_rings: bool
    reason: str
    score: float
    composition: str
    inner_radius_planet_radii: float
    outer_radius_planet_radii: float
    tilt_degrees: float
    bands: list[PlanetRingBand]


class PlanetVisuals(BaseModel):
    render_id: str
    maps: PlanetTextureMaps
    rings: PlanetRingConfig
    influence_map: dict[str, Any] | None = None