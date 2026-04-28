from __future__ import annotations

import numpy as np

from radar_basics.config import ProcessingConfig
from radar_basics.core import RadarCubeAxes, SPEED_OF_LIGHT
from radar_basics.data import ProcessedDwell, RadarCube, RawDwellData
from radar_basics.detection import detect_radar_cube
from radar_basics.radar import RadarSystem


def range_compress(raw: RawDwellData, radar: RadarSystem) -> np.ndarray:
    waveform_samples = radar.waveform.samples()
    matched_filter = np.conj(waveform_samples[::-1])
    num_fast_time = raw.iq.shape[-1]
    full_length = num_fast_time + waveform_samples.size - 1
    spectrum = np.fft.fft(raw.iq, n=full_length, axis=-1)
    filter_spectrum = np.fft.fft(matched_filter, n=full_length)
    compressed_full = np.fft.ifft(spectrum * filter_spectrum, axis=-1)
    start = waveform_samples.size - 1
    return compressed_full[..., start : start + num_fast_time]


def doppler_process(range_data: np.ndarray, radar: RadarSystem) -> tuple[np.ndarray, np.ndarray]:
    doppler = np.fft.fftshift(np.fft.fft(range_data, axis=2), axes=2)
    doppler = np.moveaxis(doppler, 2, 3)
    frequency_hz = np.fft.fftshift(np.fft.fftfreq(radar.waveform.num_pulses, d=radar.waveform.pri_s))
    radial_velocity_mps = -frequency_hz * radar.wavelength_m / 2.0
    return doppler, radial_velocity_mps


def beamform_angle_grid(
    doppler_data: np.ndarray,
    radar: RadarSystem,
    azimuths_deg: tuple[float, ...],
    elevations_deg: tuple[float, ...],
) -> np.ndarray:
    num_range = doppler_data.shape[2]
    num_doppler = doppler_data.shape[3]
    cube = np.empty((num_range, num_doppler, len(azimuths_deg), len(elevations_deg)), dtype=np.complex128)
    normalizer = float(radar.array.num_elements)
    for az_index, az_deg in enumerate(azimuths_deg):
        for el_index, el_deg in enumerate(elevations_deg):
            steering = radar.array.steering_vector(radar.wavelength_m, az_deg, el_deg)
            cube[:, :, az_index, el_index] = (
                np.tensordot(np.conj(steering), doppler_data, axes=([0, 1], [0, 1])) / normalizer
            )
    return cube


def process_dwell(
    raw: RawDwellData,
    radar: RadarSystem,
    config: ProcessingConfig,
) -> ProcessedDwell:
    compressed = range_compress(raw, radar)
    doppler_data, radial_velocity_axis = doppler_process(compressed, radar)
    cube_data = beamform_angle_grid(
        doppler_data,
        radar,
        config.angle_grid_az_deg,
        config.angle_grid_el_deg,
    )
    range_axis = np.arange(cube_data.shape[0], dtype=np.float64) * SPEED_OF_LIGHT / (
        2.0 * radar.waveform.sample_rate_hz
    )
    radar_cube = RadarCube(
        data=cube_data,
        axes=RadarCubeAxes(
            range_m=range_axis,
            radial_velocity_mps=radial_velocity_axis,
            azimuth_deg=np.asarray(config.angle_grid_az_deg, dtype=np.float64),
            elevation_deg=np.asarray(config.angle_grid_el_deg, dtype=np.float64),
        ),
    )
    detections = detect_radar_cube(radar_cube, raw.task, config.detector)
    range_doppler_power = np.max(np.abs(cube_data) ** 2, axis=(2, 3))
    return ProcessedDwell(
        range_doppler_power=range_doppler_power,
        radar_cube=radar_cube,
        detections=detections,
        task=raw.task,
    )

