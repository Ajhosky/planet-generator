from __future__ import annotations

import hashlib
import json
from typing import Any


def model_to_plain_dict(value: Any) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    raise TypeError(f"Unsupported model type: {type(value)}")


def create_planet_render_id(planet_input: Any) -> str:
    payload = model_to_plain_dict(planet_input)

    normalized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]