from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from radar_basics.core import (
    BOLTZMANN_CONSTANT,
    DEFAULT_TEMPERATURE_K,
    SPEED_OF_LIGHT,
    db_to_power,
    direction_vector,
)


@dataclass(frozen=True)
class RectangularArray:
    """A planar array in the radar y-z plane.

    The raw IQ tensor uses shape ``(num_y, num_x, num_pulses, num_fast_time)``.
    In physical coordinates, the second index spans radar-y and the first index
    spans radar-z. Radar-x is boresight/forward, so element x-coordinates are 0.
    """

    num_y: int
    num_x: int
    spacing_y_m: float
    spacing_x_m: float

    def __post_init__(self) -> None:
        if self.num_y <= 0 or self.num_x <= 0:
            raise ValueError("Array dimensions must be positive")
        if self.spacing_y_m <= 0.0 or self.spacing_x_m <= 0.0:
            raise ValueError("Array spacings must be positive")

    @property
    def num_elements(self) -> int:
        return self.num_y * self.num_x

    @property
    def positions_m(self) -> np.ndarray:
        row_indices = np.arange(self.num_y, dtype=np.float64) - ((self.num_y - 1) / 2.0)
        col_indices = np.arange(self.num_x, dtype=np.float64) - ((self.num_x - 1) / 2.0)
        z_coords = row_indices * self.spacing_y_m
        y_coords = col_indices * self.spacing_x_m
        yy, zz = np.meshgrid(y_coords, z_coords)
        positions = np.zeros((self.num_y, self.num_x, 3), dtype=np.float64)
        positions[..., 1] = yy
        positions[..., 2] = zz
        return positions

    def steering_vector(self, wavelength_m: float, az_deg: float, el_deg: float) -> np.ndarray:
        direction = direction_vector(az_deg, el_deg)
        phase = (2.0 * math.pi / wavelength_m) * np.tensordot(
            self.positions_m,
            direction,
            axes=([-1], [0]),
        )
        return np.exp(1j * phase)

    def transmit_field_gain(
        self,
        wavelength_m: float,
        look_az_deg: float,
        look_el_deg: float,
        target_az_deg: float,
        target_el_deg: float,
    ) -> float:
        look = direction_vector(look_az_deg, look_el_deg)
        target = direction_vector(target_az_deg, target_el_deg)
        phase = (2.0 * math.pi / wavelength_m) * np.tensordot(
            self.positions_m,
            target - look,
            axes=([-1], [0]),
        )
        return float(abs(np.mean(np.exp(1j * phase))))


@dataclass(frozen=True)
class LfmPulseWaveform:
    bandwidth_hz: float
    pulse_width_s: float
    prf_hz: float
    num_pulses: int
    sample_rate_hz: float

    def __post_init__(self) -> None:
        if self.bandwidth_hz <= 0.0:
            raise ValueError("bandwidth_hz must be positive")
        if self.pulse_width_s <= 0.0:
            raise ValueError("pulse_width_s must be positive")
        if self.prf_hz <= 0.0:
            raise ValueError("prf_hz must be positive")
        if self.num_pulses <= 0:
            raise ValueError("num_pulses must be positive")
        if self.sample_rate_hz <= 0.0:
            raise ValueError("sample_rate_hz must be positive")
        if self.pulse_width_s >= self.pri_s:
            raise ValueError("pulse_width_s must be smaller than PRI")

    @property
    def pri_s(self) -> float:
        return 1.0 / self.prf_hz

    @property
    def chirp_slope_hz_per_s(self) -> float:
        return self.bandwidth_hz / self.pulse_width_s

    @property
    def num_fast_time_samples(self) -> int:
        return math.ceil(self.sample_rate_hz * self.pri_s)

    @property
    def num_pulse_samples(self) -> int:
        return max(1, math.ceil(self.sample_rate_hz * self.pulse_width_s))

    def fast_time_axis_s(self) -> np.ndarray:
        return np.arange(self.num_fast_time_samples, dtype=np.float64) / self.sample_rate_hz

    def pulse_time_axis_s(self) -> np.ndarray:
        return np.arange(self.num_pulses, dtype=np.float64) * self.pri_s

    def samples(self) -> np.ndarray:
        t = np.arange(self.num_pulse_samples, dtype=np.float64) / self.sample_rate_hz
        return np.exp(1j * math.pi * self.chirp_slope_hz_per_s * t**2)


@dataclass(frozen=True)
class RadarSystem:
    carrier_frequency_hz: float
    peak_tx_power_w: float
    array: RectangularArray
    waveform: LfmPulseWaveform
    noise_figure_db: float = 0.0
    system_loss_db: float = 0.0
    temperature_k: float = DEFAULT_TEMPERATURE_K

    def __post_init__(self) -> None:
        if self.carrier_frequency_hz <= 0.0:
            raise ValueError("carrier_frequency_hz must be positive")
        if self.peak_tx_power_w < 0.0:
            raise ValueError("peak_tx_power_w must be non-negative")
        if self.noise_figure_db < 0.0:
            raise ValueError("noise_figure_db must be non-negative")
        if self.system_loss_db < 0.0:
            raise ValueError("system_loss_db must be non-negative")
        if self.temperature_k < 0.0:
            raise ValueError("temperature_k must be non-negative")

    @property
    def wavelength_m(self) -> float:
        return SPEED_OF_LIGHT / self.carrier_frequency_hz

    @property
    def max_unambiguous_range_m(self) -> float:
        return SPEED_OF_LIGHT * self.waveform.pri_s / 2.0

    @property
    def range_resolution_m(self) -> float:
        return SPEED_OF_LIGHT / (2.0 * self.waveform.bandwidth_hz)

    @property
    def velocity_resolution_mps(self) -> float:
        cpi_s = self.waveform.num_pulses * self.waveform.pri_s
        return self.wavelength_m / (2.0 * cpi_s)

    @property
    def max_unambiguous_velocity_mps(self) -> float:
        return self.wavelength_m * self.waveform.prf_hz / 4.0

    @property
    def system_loss_linear(self) -> float:
        return db_to_power(self.system_loss_db)

    @property
    def noise_power_w(self) -> float:
        return (
            BOLTZMANN_CONSTANT
            * self.temperature_k
            * db_to_power(self.noise_figure_db)
            * self.waveform.sample_rate_hz
        )

