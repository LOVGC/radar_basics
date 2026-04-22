from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose
import yaml

from radar_basics import BOLTZMANN_CONSTANT, SPEED_OF_LIGHT, load_config, simulate_cpi


def test_single_target_geometry_matches_delay_and_channel_phase(tmp_path: Path) -> None:
    target = {
        "range_m": 1500.0,
        "azimuth_deg": 30.0,
        "radial_velocity_mps": 0.0,
        "rcs_m2": 1.0,
    }
    result = simulate_cpi(write_yaml(tmp_path, architecture_config(targets=[target]), name="geometry.yaml"))

    delay_index = math.ceil(
        2.0 * target["range_m"] * result.resolved_config.sample_rate_hz / SPEED_OF_LIGHT
    )
    assert_allclose(result.raw_cube[:delay_index, 0, 0], 0.0, atol=1e-18)
    assert abs(result.raw_cube[delay_index, 0, 0]) > 0.0

    wavelength_m = result.resolved_config.wavelength_m
    spacing_m = result.resolved_config.element_spacing_m
    expected_ratio = np.exp(1j * 2.0 * math.pi * spacing_m * math.sin(math.radians(30.0)) / wavelength_m)
    observed_ratio = result.raw_cube[delay_index, 0, 1] / result.raw_cube[delay_index, 0, 0]
    assert_allclose(observed_ratio, expected_ratio, atol=1e-12, rtol=1e-12)


def test_nonzero_radial_velocity_creates_slow_time_phase_progression(tmp_path: Path) -> None:
    target = {
        "range_m": 1500.0,
        "azimuth_deg": 0.0,
        "radial_velocity_mps": 15.0,
        "rcs_m2": 1.0,
    }
    data = architecture_config(targets=[target])
    data["radar"]["num_elements"] = 1
    result = simulate_cpi(write_yaml(tmp_path, data, name="doppler.yaml"))

    delay_index = math.ceil(
        2.0 * target["range_m"] * result.resolved_config.sample_rate_hz / SPEED_OF_LIGHT
    )
    observed_ratio = result.raw_cube[delay_index, 1, 0] / result.raw_cube[delay_index, 0, 0]
    observed_ratio /= abs(observed_ratio)
    expected_ratio = np.exp(
        -1j
        * 4.0
        * math.pi
        * target["radial_velocity_mps"]
        * result.resolved_config.pri_s
        / result.resolved_config.wavelength_m
    )
    assert_allclose(observed_ratio, expected_ratio, atol=1e-5, rtol=1e-5)


def test_off_boresight_target_is_attenuated_by_transmit_beam(tmp_path: Path) -> None:
    off_axis_data = architecture_config(
        targets=[
            {
                "range_m": 1500.0,
                "azimuth_deg": 20.0,
                "radial_velocity_mps": 0.0,
                "rcs_m2": 1.0,
            }
        ]
    )
    off_axis_data["radar"]["num_elements"] = 8
    on_axis_data = architecture_config(
        targets=[
            {
                "range_m": 1500.0,
                "azimuth_deg": 0.0,
                "radial_velocity_mps": 0.0,
                "rcs_m2": 1.0,
            }
        ]
    )
    on_axis_data["radar"]["num_elements"] = 8

    on_axis = simulate_cpi(write_yaml(tmp_path, on_axis_data, name="beam_on.yaml"))
    off_axis = simulate_cpi(write_yaml(tmp_path, off_axis_data, name="beam_off.yaml"))

    assert np.max(np.abs(off_axis.raw_cube)) < 0.5 * np.max(np.abs(on_axis.raw_cube))


def test_multiple_targets_superpose_linearly_without_noise(tmp_path: Path) -> None:
    target_a = {
        "range_m": 1500.0,
        "azimuth_deg": 0.0,
        "radial_velocity_mps": 0.0,
        "rcs_m2": 1.0,
    }
    target_b = {
        "range_m": 2100.0,
        "azimuth_deg": 10.0,
        "radial_velocity_mps": -5.0,
        "rcs_m2": 2.0,
    }

    combined = simulate_cpi(write_yaml(tmp_path, architecture_config(targets=[target_a, target_b]), name="ab.yaml"))
    first = simulate_cpi(write_yaml(tmp_path, architecture_config(targets=[target_a]), name="a.yaml"))
    second = simulate_cpi(write_yaml(tmp_path, architecture_config(targets=[target_b]), name="b.yaml"))

    assert_allclose(combined.raw_cube, first.raw_cube + second.raw_cube, atol=1e-12, rtol=1e-12)


def test_noise_power_matches_configured_awgn_level(tmp_path: Path) -> None:
    data = architecture_config(targets=[])
    data["seed"] = 123
    data["radar"]["num_elements"] = 4
    data["radar"]["num_pulses"] = 64
    data["radar"]["sample_rate_hz"] = 5.0e6
    data["radar"]["pri_s"] = 200.0e-6
    data["noise"] = {
        "noise_figure_db": 3.0,
        "system_loss_db": 0.0,
        "temperature_k": 290.0,
    }

    result = simulate_cpi(write_yaml(tmp_path, data, name="noise.yaml"))
    estimated_noise_power_w = float(np.mean(np.abs(result.raw_cube) ** 2))
    expected_noise_power_w = (
        BOLTZMANN_CONSTANT
        * data["noise"]["temperature_k"]
        * (10.0 ** (data["noise"]["noise_figure_db"] / 10.0))
        * data["radar"]["sample_rate_hz"]
    )

    assert math.isclose(estimated_noise_power_w, expected_noise_power_w, rel_tol=0.1)


def test_simulation_result_exposes_expected_shapes_and_axes(tmp_path: Path) -> None:
    target = {
        "range_m": 1500.0,
        "azimuth_deg": 0.0,
        "radial_velocity_mps": 0.0,
        "rcs_m2": 1.0,
    }
    config = load_config(write_yaml(tmp_path, architecture_config(targets=[target]), name="shape.yaml"))
    result = simulate_cpi(config)

    expected_fast_time = math.ceil(config.radar.sample_rate_hz * config.radar.pri_s)
    assert result.raw_cube.shape == (
        expected_fast_time,
        config.radar.num_pulses,
        config.radar.num_elements,
    )
    assert np.iscomplexobj(result.raw_cube)
    assert len(result.axes.fast_time_s) == expected_fast_time
    assert len(result.axes.pulse_times_s) == config.radar.num_pulses
    assert len(result.axes.channel_positions_m) == config.radar.num_elements
    assert result.truth[0].range_m == target["range_m"]
    assert math.isclose(
        result.resolved_config.max_unambiguous_range_m,
        SPEED_OF_LIGHT * config.radar.pri_s / 2.0,
        rel_tol=1e-12,
    )


def architecture_config(*, targets: list[dict]) -> dict:
    return {
        "mode": "architecture",
        "seed": 1,
        "radar": {
            "carrier_frequency_hz": 10.0e9,
            "num_elements": 4,
            "steering_azimuth_deg": 0.0,
            "chirp_bandwidth_hz": 5.0e6,
            "pulse_width_s": 2.0e-6,
            "pri_s": 50.0e-6,
            "num_pulses": 8,
            "sample_rate_hz": 10.0e6,
            "peak_tx_power_w": 1000.0,
        },
        "noise": {
            "noise_figure_db": 0.0,
            "system_loss_db": 0.0,
            "temperature_k": 0.0,
        },
        "scene": {
            "targets": targets,
        },
    }


def write_yaml(tmp_path: Path, data: dict, *, name: str) -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path
