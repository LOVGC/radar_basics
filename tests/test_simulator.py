from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose
import yaml

from radar_basics import (
    BOLTZMANN_CONSTANT,
    SPEED_OF_LIGHT,
    build_radar_system,
    build_scene,
    load_config,
    process_dwell,
    run_experiment,
    synthesize_dwell,
)
from radar_basics.config import DetectorConfig, ProcessingConfig, TrackerConfig
from radar_basics.radar import LfmPulseWaveform, RadarSystem, RectangularArray
from radar_basics.scenario import PointTarget, Scene
from radar_basics.scheduler import DwellTask


def test_rectangular_array_steering_phase_slopes() -> None:
    wavelength_m = 0.03
    array = RectangularArray(num_y=1, num_x=2, spacing_y_m=wavelength_m / 2.0, spacing_x_m=wavelength_m / 2.0)

    steering = array.steering_vector(wavelength_m, az_deg=30.0, el_deg=0.0)

    expected_ratio = np.exp(1j * math.pi * math.sin(math.radians(30.0)))
    assert_allclose(steering[0, 1] / steering[0, 0], expected_ratio, atol=1e-12)


def test_synthesis_places_lfm_echo_at_expected_fast_time_delay() -> None:
    sample_rate_hz = 10.0e6
    delay_index = 100
    target_range_m = delay_index * SPEED_OF_LIGHT / (2.0 * sample_rate_hz)
    radar = single_element_radar(sample_rate_hz=sample_rate_hz, temperature_k=0.0)
    scene = Scene(
        targets=(
            PointTarget(
                name="target-a",
                position_m=(target_range_m, 0.0, 0.0),
                velocity_mps=(0.0, 0.0, 0.0),
                rcs_m2=1.0,
            ),
        )
    )

    raw = synthesize_dwell(radar, scene, dwell_task(), np.random.default_rng(1))

    assert_allclose(raw.iq[0, 0, 0, :delay_index], 0.0, atol=1e-18)
    assert abs(raw.iq[0, 0, 0, delay_index]) > 0.0


def test_nonzero_radial_velocity_creates_slow_time_phase_progression() -> None:
    radar = single_element_radar(temperature_k=0.0)
    radial_velocity_mps = radar.wavelength_m / (4.0 * radar.waveform.pri_s)
    scene = Scene(
        targets=(
            PointTarget(
                name="target-a",
                position_m=(1500.0, 0.0, 0.0),
                velocity_mps=(radial_velocity_mps, 0.0, 0.0),
                rcs_m2=1.0,
            ),
        )
    )
    raw = synthesize_dwell(radar, scene, dwell_task(), np.random.default_rng(1))
    delay_index = math.ceil(2.0 * 1500.0 * radar.waveform.sample_rate_hz / SPEED_OF_LIGHT)

    observed_ratio = raw.iq[0, 0, 1, delay_index] / raw.iq[0, 0, 0, delay_index]
    observed_ratio /= abs(observed_ratio)

    assert_allclose(observed_ratio, -1.0 + 0.0j, atol=2e-2)


def test_multiple_targets_superpose_linearly_without_noise() -> None:
    radar = single_element_radar(temperature_k=0.0)
    target_a = PointTarget("a", (1500.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.0)
    target_b = PointTarget("b", (2100.0, 100.0, 0.0), (-5.0, 0.0, 0.0), 2.0)
    task = dwell_task()

    combined = synthesize_dwell(radar, Scene((target_a, target_b)), task, np.random.default_rng(1))
    first = synthesize_dwell(radar, Scene((target_a,)), task, np.random.default_rng(1))
    second = synthesize_dwell(radar, Scene((target_b,)), task, np.random.default_rng(1))

    assert_allclose(combined.iq, first.iq + second.iq, atol=1e-18)


def test_noise_power_matches_configured_awgn_level() -> None:
    radar = single_element_radar(sample_rate_hz=5.0e6, noise_figure_db=3.0, temperature_k=290.0)

    raw = synthesize_dwell(radar, Scene(()), dwell_task(), np.random.default_rng(123))

    estimated_noise_power_w = float(np.mean(np.abs(raw.iq) ** 2))
    expected_noise_power_w = (
        BOLTZMANN_CONSTANT
        * radar.temperature_k
        * (10.0 ** (radar.noise_figure_db / 10.0))
        * radar.waveform.sample_rate_hz
    )
    assert math.isclose(estimated_noise_power_w, expected_noise_power_w, rel_tol=0.25)


def test_full_processing_chain_detects_single_on_axis_target(tmp_path: Path) -> None:
    config = load_config(write_yaml_dict(tmp_path, full_chain_config(num_scan_cycles=1)))
    radar = build_radar_system(config)
    scene = build_scene(config)
    raw = synthesize_dwell(radar, scene, dwell_task(num_pulses=config.waveform.num_pulses), np.random.default_rng(1))

    processed = process_dwell(raw, radar, config.processing)

    assert processed.radar_cube.data.shape == (radar.waveform.num_fast_time_samples, radar.waveform.num_pulses, 3, 3)
    assert processed.detections
    detection = processed.detections[0]
    assert abs(detection.range_m - 1500.0) < 2.0 * SPEED_OF_LIGHT / (2.0 * radar.waveform.sample_rate_hz)
    assert abs(detection.radial_velocity_mps) <= radar.velocity_resolution_mps
    assert detection.az_deg == 0.0
    assert detection.el_deg == 0.0


def test_run_experiment_scans_and_confirms_track(tmp_path: Path) -> None:
    result = run_experiment(write_yaml_dict(tmp_path, full_chain_config(num_scan_cycles=2)))

    all_detections = [d for dwell in result.processed_dwells for d in dwell.detections]

    assert len(result.tasks) == 2
    assert len(all_detections) >= 2
    assert result.tracks
    assert result.tracks[0].status == "confirmed"


def test_display_helpers_render_with_matplotlib_agg(tmp_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    from radar_basics.display import plot_air_picture, plot_range_doppler, plot_scan_beams

    result = run_experiment(write_yaml_dict(tmp_path, full_chain_config(num_scan_cycles=1)))
    processed = result.processed_dwells[0]

    fig1, _ = plot_range_doppler(processed)
    fig2, _ = plot_scan_beams(result.tasks)
    fig3, _ = plot_air_picture(processed.detections, result.tracks)

    assert fig1 is not None
    assert fig2 is not None
    assert fig3 is not None


def single_element_radar(
    *,
    sample_rate_hz: float = 10.0e6,
    noise_figure_db: float = 0.0,
    temperature_k: float = 0.0,
) -> RadarSystem:
    return RadarSystem(
        carrier_frequency_hz=10.0e9,
        peak_tx_power_w=10_000.0,
        array=RectangularArray(num_y=1, num_x=1, spacing_y_m=0.015, spacing_x_m=0.015),
        waveform=LfmPulseWaveform(
            bandwidth_hz=5.0e6,
            pulse_width_s=2.0e-6,
            prf_hz=10_000.0,
            num_pulses=8,
            sample_rate_hz=sample_rate_hz,
        ),
        noise_figure_db=noise_figure_db,
        temperature_k=temperature_k,
    )


def dwell_task(*, num_pulses: int = 8) -> DwellTask:
    return DwellTask(
        id=0,
        mode="search",
        look_az_deg=0.0,
        look_el_deg=0.0,
        start_time_s=0.0,
        prf_hz=10_000.0,
        num_pulses=num_pulses,
    )


def full_chain_config(*, num_scan_cycles: int) -> dict:
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
            "num_pulses": 16,
            "sample_rate_hz": 10.0e6,
        },
        "scan": {
            "azimuths_deg": [0.0],
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
                "guard_cells": [2, 1, 1, 1],
            },
            "tracker": {
                "association_gate_m": 1000.0,
                "confirmation_hits": 2,
                "max_misses": 2,
                "measurement_noise_m": 75.0,
            },
        },
        "run": {
            "num_scan_cycles": num_scan_cycles,
            "seed": 1,
            "store_raw": True,
        },
    }


def write_yaml_dict(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path
