from __future__ import annotations

from pathlib import Path

import numpy as np

from radar_basics.config import (
    ExperimentConfig,
    build_radar_system,
    build_scene,
    load_experiment_config,
)
from radar_basics.data import ProcessedDwell, RawDwellData, SimulationRunResult
from radar_basics.processing import process_dwell
from radar_basics.scheduler import ScriptedScanScheduler
from radar_basics.synthesis import synthesize_dwell
from radar_basics.tracking import NearestNeighborTracker


def run_experiment(config_or_path: ExperimentConfig | str | Path) -> SimulationRunResult:
    config = _coerce_config(config_or_path)
    radar = build_radar_system(config)
    scene = build_scene(config)
    scheduler = ScriptedScanScheduler(
        azimuths_deg=config.scan.azimuths_deg,
        elevations_deg=config.scan.elevations_deg,
        prf_hz=radar.waveform.prf_hz,
        num_pulses=radar.waveform.num_pulses,
        mode=config.scan.mode,
    )
    tasks = scheduler.tasks(num_scan_cycles=config.run.num_scan_cycles)
    rng = np.random.default_rng(config.run.seed)
    tracker = NearestNeighborTracker(config.processing.tracker)

    raw_dwells: list[RawDwellData] = []
    processed_dwells: list[ProcessedDwell] = []
    for task in tasks:
        raw = synthesize_dwell(radar, scene, task, rng)
        processed = process_dwell(raw, radar, config.processing)
        tracker.update(processed.detections, task.center_time_s)
        if config.run.store_raw:
            raw_dwells.append(raw)
        processed_dwells.append(processed)

    return SimulationRunResult(
        config=config,
        tasks=tasks,
        raw_dwells=tuple(raw_dwells),
        processed_dwells=tuple(processed_dwells),
        tracks=tracker.tracks,
    )


def _coerce_config(config_or_path: ExperimentConfig | str | Path) -> ExperimentConfig:
    if isinstance(config_or_path, ExperimentConfig):
        return config_or_path
    return load_experiment_config(config_or_path)

