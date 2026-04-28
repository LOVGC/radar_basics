from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

SPEED_OF_LIGHT = 299_792_458.0
BOLTZMANN_CONSTANT = 1.380649e-23
DEFAULT_TEMPERATURE_K = 290.0


def db_to_power(db_value: float) -> float:
    return 10.0 ** (db_value / 10.0)


def power_to_db(power_value: float, *, floor: float = 1e-300) -> float:
    return 10.0 * math.log10(max(float(power_value), floor))


def direction_vector(az_deg: float, el_deg: float) -> np.ndarray:
    az = math.radians(az_deg)
    el = math.radians(el_deg)
    return np.array(
        [
            math.cos(el) * math.cos(az),
            math.cos(el) * math.sin(az),
            math.sin(el),
        ],
        dtype=np.float64,
    )


def spherical_to_cartesian(range_m: float, az_deg: float, el_deg: float) -> np.ndarray:
    return float(range_m) * direction_vector(az_deg, el_deg)


def cartesian_to_spherical(position_m: np.ndarray) -> tuple[float, float, float]:
    x, y, z = np.asarray(position_m, dtype=np.float64)
    range_m = float(np.linalg.norm(position_m))
    if range_m == 0.0:
        raise ValueError("Cannot convert the radar origin to spherical coordinates")
    az_deg = math.degrees(math.atan2(y, x))
    el_deg = math.degrees(math.atan2(z, math.hypot(x, y)))
    return range_m, az_deg, el_deg


def radial_velocity_mps(position_m: np.ndarray, velocity_mps: np.ndarray) -> float:
    position = np.asarray(position_m, dtype=np.float64)
    velocity = np.asarray(velocity_mps, dtype=np.float64)
    range_m = np.linalg.norm(position)
    if range_m == 0.0:
        raise ValueError("Cannot compute radial velocity at the radar origin")
    return float(np.dot(velocity, position / range_m))


@dataclass(frozen=True)
class RadarCubeAxes:
    range_m: np.ndarray
    radial_velocity_mps: np.ndarray
    azimuth_deg: np.ndarray
    elevation_deg: np.ndarray

