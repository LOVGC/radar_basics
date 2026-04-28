from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from radar_basics import (
    ConfigError,
    SPEED_OF_LIGHT,
    build_radar_system,
    build_scene,
    load_config,
)
from radar_basics.scheduler import ScriptedScanScheduler


def test_load_config_parses_v1_yaml(tmp_path: Path) -> None:
    path = write_yaml(tmp_path, base_config())

    config = load_config(path)

    assert config.radar.carrier_frequency_hz == 10.0e9
    assert config.array.num_y == 4
    assert config.waveform.num_pulses == 8
    assert config.scan.azimuths_deg == (-5.0, 0.0, 5.0)
    assert config.processing.angle_grid_el_deg == (-2.0, 0.0, 2.0)


def test_build_radar_uses_half_wavelength_default_spacing(tmp_path: Path) -> None:
    config = load_config(write_yaml(tmp_path, base_config()))
    radar = build_radar_system(config)

    assert math.isclose(radar.array.spacing_x_m, radar.wavelength_m / 2.0)
    assert math.isclose(radar.array.spacing_y_m, radar.wavelength_m / 2.0)
    assert math.isclose(radar.max_unambiguous_range_m, SPEED_OF_LIGHT / (2.0 * 10_000.0))


def test_build_scene_accepts_spherical_target_config(tmp_path: Path) -> None:
    config = load_config(write_yaml(tmp_path, base_config()))
    scene = build_scene(config)
    snapshot = scene.snapshots_at(0.0)[0]

    assert math.isclose(snapshot.range_m, 1500.0, rel_tol=1e-12)
    assert math.isclose(snapshot.az_deg, 0.0, abs_tol=1e-12)
    assert math.isclose(snapshot.el_deg, 0.0, abs_tol=1e-12)
    assert math.isclose(snapshot.radial_velocity_mps, 0.0, abs_tol=1e-12)


def test_scheduler_generates_elevation_major_fixed_scan() -> None:
    scheduler = ScriptedScanScheduler(
        azimuths_deg=(-10.0, 0.0),
        elevations_deg=(0.0, 5.0),
        prf_hz=10_000.0,
        num_pulses=4,
    )

    tasks = scheduler.tasks(num_scan_cycles=1)

    assert [(task.look_az_deg, task.look_el_deg) for task in tasks] == [
        (-10.0, 0.0),
        (0.0, 0.0),
        (-10.0, 5.0),
        (0.0, 5.0),
    ]
    assert math.isclose(tasks[1].start_time_s, 4 / 10_000.0)


def test_load_config_rejects_unexpected_top_level_key(tmp_path: Path) -> None:
    data = base_config()
    data["extra"] = {}

    with pytest.raises(ConfigError, match="Unexpected keys"):
        load_config(write_yaml(tmp_path, data))


def base_config() -> dict:
    return {
        "radar": {
            "carrier_frequency_hz": 10.0e9,
            "peak_tx_power_w": 50_000.0,
            "noise_figure_db": 0.0,
            "system_loss_db": 0.0,
            "temperature_k": 0.0,
        },
        "array": {
            "num_y": 4,
            "num_x": 4,
        },
        "waveform": {
            "bandwidth_hz": 5.0e6,
            "pulse_width_s": 2.0e-6,
            "prf_hz": 10_000.0,
            "num_pulses": 8,
            "sample_rate_hz": 10.0e6,
        },
        "scan": {
            "azimuths_deg": [-5.0, 0.0, 5.0],
            "elevations_deg": [0.0],
        },
        "scene": {
            "targets": [
                {
                    "name": "target-a",
                    "range_m": 1500.0,
                    "az_deg": 0.0,
                    "el_deg": 0.0,
                    "radial_velocity_mps": 0.0,
                    "rcs_m2": 10.0,
                }
            ]
        },
        "processing": {
            "angle_grid": {
                "azimuths_deg": [-5.0, 0.0, 5.0],
                "elevations_deg": [-2.0, 0.0, 2.0],
            },
            "detector": {
                "threshold_snr_db": 12.0,
                "max_detections_per_dwell": 1,
            },
            "tracker": {
                "association_gate_m": 1000.0,
                "confirmation_hits": 2,
            },
        },
        "run": {
            "num_scan_cycles": 1,
            "seed": 1,
        },
    }


def write_yaml(tmp_path: Path, data: dict, name: str = "config.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path

