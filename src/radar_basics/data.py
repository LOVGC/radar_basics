from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from radar_basics.core import RadarCubeAxes
from radar_basics.scenario import TargetSnapshot
from radar_basics.scheduler import DwellTask

if TYPE_CHECKING:
    from radar_basics.detection import Detection
    from radar_basics.tracking import Track


@dataclass(frozen=True)
class RawDwellAxes:
    fast_time_s: np.ndarray
    pulse_times_s: np.ndarray
    array_positions_m: np.ndarray


@dataclass(frozen=True)
class RawDwellData:
    iq: np.ndarray
    axes: RawDwellAxes
    task: DwellTask
    truth: tuple[TargetSnapshot, ...]


@dataclass(frozen=True)
class RadarCube:
    data: np.ndarray
    axes: RadarCubeAxes


@dataclass(frozen=True)
class ProcessedDwell:
    range_doppler_power: np.ndarray
    radar_cube: RadarCube
    detections: tuple["Detection", ...]
    task: DwellTask


@dataclass(frozen=True)
class SimulationRunResult:
    config: Any
    tasks: tuple[DwellTask, ...]
    raw_dwells: tuple[RawDwellData, ...]
    processed_dwells: tuple[ProcessedDwell, ...]
    tracks: tuple["Track", ...]

