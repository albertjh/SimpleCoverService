from __future__ import annotations

def angular_diff_deg(a: float, b: float) -> float:
    """Minimal absolute difference between two azimuth angles in degrees."""
    d = abs(a - b) % 360.0
    return d if d <= 180.0 else 360.0 - d
