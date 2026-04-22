from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np

from radar_basics.config import (
    BOLTZMANN_CONSTANT,
    ConfigError,
    ResolvedRadarConfig,
    SPEED_OF_LIGHT,
    SimulationConfig,
    TargetConfig,
    load_config,
    resolve_radar_config,
)


@dataclass(frozen=True)
class SimulationAxes:
    fast_time_s: np.ndarray
    pulse_times_s: np.ndarray
    channel_positions_m: np.ndarray


@dataclass(frozen=True)
class SimulationResult:
    raw_cube: np.ndarray
    axes: SimulationAxes
    truth: tuple[TargetConfig, ...]
    resolved_config: ResolvedRadarConfig


def simulate_cpi(config_or_path: SimulationConfig | str | Path) -> SimulationResult:
    config = _coerce_config(config_or_path)
    resolved = resolve_radar_config(config)

    fast_time_s = np.arange(resolved.num_fast_time_samples, dtype=np.float64) / resolved.sample_rate_hz
    pulse_times_s = np.arange(resolved.num_pulses, dtype=np.float64) * resolved.pri_s
    channel_positions_m = _channel_positions_m(resolved)
    raw_cube = np.zeros(
        (resolved.num_fast_time_samples, resolved.num_pulses, resolved.num_elements),
        dtype=np.complex128,
    )

    chirp_slope_hz_per_s = resolved.chirp_bandwidth_hz / resolved.pulse_width_s
    tx_gain_linear = float(resolved.num_elements)
    system_loss_linear = _db_to_linear(resolved.system_loss_db)
    steering_azimuth_rad = math.radians(resolved.steering_azimuth_deg)
    steering_spatial_term = math.sin(steering_azimuth_rad)

    for target in config.scene.targets:
        if target.range_m >= resolved.max_unambiguous_range_m:
            raise ConfigError(
                f"Target at range {target.range_m} m exceeds the single-PRI unambiguous range "
                f"{resolved.max_unambiguous_range_m} m"
            )

        azimuth_rad = math.radians(target.azimuth_deg)
        sin_azimuth = math.sin(azimuth_rad)
        transmit_field_gain = np.abs(
            np.mean(
                np.exp(
                    1j
                    * 2.0
                    * math.pi
                    * channel_positions_m
                    * (sin_azimuth - steering_spatial_term)
                    / resolved.wavelength_m
                )
            )
        )
        channel_response = np.exp(
            1j * 2.0 * math.pi * channel_positions_m * sin_azimuth / resolved.wavelength_m
        )

        pulse_ranges_m = target.range_m + target.radial_velocity_mps * pulse_times_s
        if np.any(pulse_ranges_m <= 0.0):
            raise ConfigError("Target range must remain positive over the simulated CPI")

        pulse_delays_s = 2.0 * pulse_ranges_m / SPEED_OF_LIGHT
        carrier_phase = np.exp(-1j * 4.0 * math.pi * pulse_ranges_m / resolved.wavelength_m)
        received_power_w = (
            resolved.peak_tx_power_w
            * tx_gain_linear
            * (resolved.wavelength_m**2)
            * target.rcs_m2
            / (((4.0 * math.pi) ** 3) * (pulse_ranges_m**4) * system_loss_linear)
        )
        target_amplitude = np.sqrt(received_power_w) * transmit_field_gain

        for pulse_index, delay_s in enumerate(pulse_delays_s):
            shifted_fast_time_s = fast_time_s - delay_s
            valid = (shifted_fast_time_s >= 0.0) & (shifted_fast_time_s < resolved.pulse_width_s)
            if not np.any(valid):
                continue

            chirp = np.exp(1j * math.pi * chirp_slope_hz_per_s * shifted_fast_time_s[valid] ** 2)
            raw_cube[valid, pulse_index, :] += (
                target_amplitude[pulse_index]
                * carrier_phase[pulse_index]
                * chirp[:, None]
                * channel_response[None, :]
            )

    noise_power_w = _noise_power_w(resolved)
    if noise_power_w > 0.0:
        rng = np.random.default_rng(config.seed)
        noise_std = math.sqrt(noise_power_w / 2.0)
        raw_cube += noise_std * (
            rng.standard_normal(raw_cube.shape) + 1j * rng.standard_normal(raw_cube.shape)
        )

    return SimulationResult(
        raw_cube=raw_cube,
        axes=SimulationAxes(
            fast_time_s=fast_time_s,
            pulse_times_s=pulse_times_s,
            channel_positions_m=channel_positions_m,
        ),
        truth=config.scene.targets,
        resolved_config=resolved,
    )


def _coerce_config(config_or_path: SimulationConfig | str | Path) -> SimulationConfig:
    if isinstance(config_or_path, SimulationConfig):
        return config_or_path
    return load_config(config_or_path)


def _channel_positions_m(resolved: ResolvedRadarConfig) -> np.ndarray:
    element_indices = np.arange(resolved.num_elements, dtype=np.float64)
    centered_indices = element_indices - ((resolved.num_elements - 1) / 2.0)
    return centered_indices * resolved.element_spacing_m


def _db_to_linear(db_value: float) -> float:
    return 10.0 ** (db_value / 10.0)


def _noise_power_w(resolved: ResolvedRadarConfig) -> float:
    return (
        BOLTZMANN_CONSTANT
        * resolved.temperature_k
        * _db_to_linear(resolved.noise_figure_db)
        * resolved.sample_rate_hz
    )
