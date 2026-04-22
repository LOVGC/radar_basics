from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from radar_basics import (
    BOLTZMANN_CONSTANT,
    ConfigError,
    SPEED_OF_LIGHT,
    load_config,
    resolve_performance_config,
)


def test_load_config_parses_architecture_yaml(tmp_path: Path) -> None:
    path = write_yaml(
        tmp_path,
        architecture_config(
            targets=[
                {
                    "range_m": 1500.0,
                    "azimuth_deg": 5.0,
                    "radial_velocity_mps": 0.0,
                    "rcs_m2": 1.0,
                }
            ]
        ),
    )

    config = load_config(path)

    assert config.mode == "architecture"
    assert config.radar.num_elements == 4
    assert config.noise.noise_figure_db == 0.0
    assert config.scene.targets[0].range_m == 1500.0


def test_load_config_rejects_missing_required_field(tmp_path: Path) -> None:
    data = architecture_config()
    del data["radar"]["num_elements"]
    path = write_yaml(tmp_path, data)

    with pytest.raises(ConfigError, match="Missing radar.num_elements"):
        load_config(path)


def test_load_config_rejects_conflicting_carrier_and_wavelength(tmp_path: Path) -> None:
    data = architecture_config()
    data["radar"]["wavelength_m"] = 1.0
    path = write_yaml(tmp_path, data)

    with pytest.raises(ConfigError, match="describe different carriers"):
        load_config(path)


def test_resolve_performance_config_matches_closed_form_rules(tmp_path: Path) -> None:
    data = performance_config()
    path = write_yaml(tmp_path, data)
    config = load_config(path)

    resolved = resolve_performance_config(config)

    wavelength_m = SPEED_OF_LIGHT / data["radar"]["carrier_frequency_hz"]
    expected_bandwidth_hz = SPEED_OF_LIGHT / (2.0 * data["radar"]["range_resolution_m"])
    expected_pri_s = (2.0 * data["radar"]["max_unambiguous_range_m"]) / SPEED_OF_LIGHT
    expected_num_pulses = math.ceil(
        wavelength_m / (2.0 * data["radar"]["velocity_resolution_mps"] * expected_pri_s)
    )
    theta_rad = math.radians(data["radar"]["tx_3db_beamwidth_deg"])
    expected_num_elements = math.ceil(
        (0.886 * wavelength_m / theta_rad) / (wavelength_m / 2.0)
    ) + 1
    expected_sample_rate_hz = 2.0 * expected_bandwidth_hz
    expected_noise_power_w = (
        BOLTZMANN_CONSTANT
        * data["noise"]["temperature_k"]
        * (10.0 ** (data["noise"]["noise_figure_db"] / 10.0))
        * expected_sample_rate_hz
    )
    expected_peak_tx_power_w = (
        (10.0 ** (data["radar"]["snr_threshold_db"] / 10.0))
        * expected_noise_power_w
        * ((4.0 * math.pi) ** 3)
        * (data["radar"]["detection_range_m"] ** 4)
        * (10.0 ** (data["noise"]["system_loss_db"] / 10.0))
        / (expected_num_elements * (wavelength_m**2) * data["radar"]["reference_rcs_m2"])
    )

    assert math.isclose(resolved.chirp_bandwidth_hz, expected_bandwidth_hz, rel_tol=1e-12)
    assert math.isclose(resolved.pri_s, expected_pri_s, rel_tol=1e-12)
    assert resolved.num_pulses == expected_num_pulses
    assert resolved.num_elements == expected_num_elements
    assert math.isclose(resolved.sample_rate_hz, expected_sample_rate_hz, rel_tol=1e-12)
    assert math.isclose(resolved.peak_tx_power_w, expected_peak_tx_power_w, rel_tol=1e-12)


def test_resolve_performance_config_rejects_incompatible_unambiguity_targets(tmp_path: Path) -> None:
    data = performance_config()
    data["radar"]["max_unambiguous_range_m"] = 50000.0
    data["radar"]["max_unambiguous_velocity_mps"] = 100.0
    path = write_yaml(tmp_path, data)
    config = load_config(path)

    with pytest.raises(ConfigError, match="cannot be satisfied simultaneously"):
        resolve_performance_config(config)


def architecture_config(*, targets: list[dict] | None = None) -> dict:
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
            "targets": targets or [],
        },
    }


def performance_config() -> dict:
    return {
        "mode": "performance",
        "seed": 1,
        "radar": {
            "carrier_frequency_hz": 10.0e9,
            "range_resolution_m": 7.5,
            "max_unambiguous_range_m": 15000.0,
            "velocity_resolution_mps": 2.0,
            "max_unambiguous_velocity_mps": 35.0,
            "tx_3db_beamwidth_deg": 12.0,
            "detection_range_m": 8000.0,
            "reference_rcs_m2": 1.0,
            "snr_threshold_db": 13.0,
        },
        "noise": {
            "noise_figure_db": 5.0,
            "system_loss_db": 1.5,
            "temperature_k": 290.0,
        },
        "scene": {
            "targets": [
                {
                    "range_m": 6200.0,
                    "azimuth_deg": 0.0,
                    "radial_velocity_mps": 18.0,
                    "rcs_m2": 1.0,
                }
            ]
        },
    }


def write_yaml(tmp_path: Path, data: dict, name: str = "config.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path
