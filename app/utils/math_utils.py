def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def bell_score(value: float, ideal: float, tolerance: float) -> float:
    if tolerance <= 0:
        return 0.0

    return clamp(1.0 - abs(value - ideal) / tolerance)