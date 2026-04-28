from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from radar_basics.core import cartesian_to_spherical, radial_velocity_mps


@dataclass(frozen=True)
class TargetSnapshot:
    name: str
    position_m: np.ndarray
    velocity_mps: np.ndarray
    range_m: float
    az_deg: float
    el_deg: float
    radial_velocity_mps: float
    rcs_m2: float


@dataclass(frozen=True)
class PointTarget:
    name: str
    position_m: tuple[float, float, float]
    velocity_mps: tuple[float, float, float]
    rcs_m2: float

    def position_at(self, time_s: float) -> np.ndarray:
        return np.asarray(self.position_m, dtype=np.float64) + time_s * np.asarray(
            self.velocity_mps,
            dtype=np.float64,
        )

    def velocity_at(self, time_s: float) -> np.ndarray:
        del time_s
        return np.asarray(self.velocity_mps, dtype=np.float64)

    def snapshot_at(self, time_s: float) -> TargetSnapshot:
        position = self.position_at(time_s)
        velocity = self.velocity_at(time_s)
        range_m, az_deg, el_deg = cartesian_to_spherical(position)
        vr_mps = radial_velocity_mps(position, velocity)
        return TargetSnapshot(
            name=self.name,
            position_m=position,
            velocity_mps=velocity,
            range_m=range_m,
            az_deg=az_deg,
            el_deg=el_deg,
            radial_velocity_mps=vr_mps,
            rcs_m2=self.rcs_m2,
        )


@dataclass(frozen=True)
class Scene:
    targets: tuple[PointTarget, ...]

    def snapshots_at(self, time_s: float) -> tuple[TargetSnapshot, ...]:
        return tuple(target.snapshot_at(time_s) for target in self.targets)

