from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from radar_basics.config import DetectorConfig
from radar_basics.core import power_to_db
from radar_basics.data import RadarCube
from radar_basics.scheduler import DwellTask


@dataclass(frozen=True)
class Detection:
    range_m: float
    radial_velocity_mps: float
    az_deg: float
    el_deg: float
    snr_db: float
    time_s: float
    dwell_id: int


def detect_radar_cube(
    radar_cube: RadarCube,
    task: DwellTask,
    config: DetectorConfig,
) -> tuple[Detection, ...]:
    if config.max_detections_per_dwell == 0:
        return ()

    power = np.abs(radar_cube.data) ** 2
    if power.size == 0 or float(np.max(power)) <= 0.0:
        return ()

    background_power = _estimate_background_power(power)
    threshold_power = background_power * (10.0 ** (config.threshold_snr_db / 10.0))
    candidate_indices = np.argwhere(power > threshold_power)
    if candidate_indices.size == 0:
        return ()

    candidate_indices = sorted(
        (tuple(int(i) for i in index) for index in candidate_indices),
        key=lambda index: float(power[index]),
        reverse=True,
    )

    detections: list[Detection] = []
    occupied: list[tuple[int, int, int, int]] = []
    for index in candidate_indices:
        if _is_suppressed(index, occupied, config.guard_cells):
            continue
        if not _is_local_maximum(power, index, config.guard_cells):
            continue

        range_index, doppler_index, az_index, el_index = index
        cell_power = float(power[index])
        detections.append(
            Detection(
                range_m=float(radar_cube.axes.range_m[range_index]),
                radial_velocity_mps=float(radar_cube.axes.radial_velocity_mps[doppler_index]),
                az_deg=float(radar_cube.axes.azimuth_deg[az_index]),
                el_deg=float(radar_cube.axes.elevation_deg[el_index]),
                snr_db=power_to_db(cell_power / background_power),
                time_s=task.center_time_s,
                dwell_id=task.id,
            )
        )
        occupied.append(index)
        if len(detections) >= config.max_detections_per_dwell:
            break

    return tuple(detections)


def _estimate_background_power(power: np.ndarray) -> float:
    positive = power[power > 0.0]
    if positive.size == 0:
        return 1e-300
    median = float(np.median(positive))
    if median > 0.0:
        return median
    return max(float(np.max(positive)) * 1e-12, 1e-300)


def _is_local_maximum(
    power: np.ndarray,
    index: tuple[int, int, int, int],
    guard_cells: tuple[int, int, int, int],
) -> bool:
    slices = _neighborhood_slices(power.shape, index, guard_cells)
    return float(power[index]) >= float(np.max(power[slices]))


def _is_suppressed(
    index: tuple[int, int, int, int],
    occupied: list[tuple[int, int, int, int]],
    guard_cells: tuple[int, int, int, int],
) -> bool:
    for accepted in occupied:
        if all(abs(index[dim] - accepted[dim]) <= guard_cells[dim] for dim in range(4)):
            return True
    return False


def _neighborhood_slices(
    shape: tuple[int, int, int, int],
    index: tuple[int, int, int, int],
    guard_cells: tuple[int, int, int, int],
) -> tuple[slice, slice, slice, slice]:
    bounds = []
    for dim, guard in enumerate(guard_cells):
        start = max(0, index[dim] - guard)
        stop = min(shape[dim], index[dim] + guard + 1)
        bounds.append(slice(start, stop))
    return tuple(bounds)  # type: ignore[return-value]


def synthetic_detection_grid(
    detections: tuple[Detection, ...],
) -> tuple[tuple[float, float, float, float], ...]:
    """Small helper for tests and notebooks."""

    return tuple((d.range_m, d.radial_velocity_mps, d.az_deg, d.el_deg) for d in detections)
