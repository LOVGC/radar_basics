from __future__ import annotations

import math

import numpy as np

from radar_basics.core import SPEED_OF_LIGHT
from radar_basics.data import RawDwellAxes, RawDwellData
from radar_basics.radar import RadarSystem
from radar_basics.scenario import Scene
from radar_basics.scheduler import DwellTask


def synthesize_dwell(
    radar: RadarSystem,
    scene: Scene,
    task: DwellTask,
    rng: np.random.Generator | None = None,
) -> RawDwellData:
    waveform = radar.waveform
    fast_time_s = waveform.fast_time_axis_s()
    pulse_times_s = np.arange(task.num_pulses, dtype=np.float64) * task.pri_s
    iq = np.zeros(
        (radar.array.num_y, radar.array.num_x, task.num_pulses, waveform.num_fast_time_samples),
        dtype=np.complex128,
    )

    for target in scene.targets:
        for pulse_index, relative_pulse_time_s in enumerate(pulse_times_s):
            absolute_time_s = task.start_time_s + relative_pulse_time_s
            snapshot = target.snapshot_at(absolute_time_s)
            if snapshot.range_m <= 0.0:
                continue
            if snapshot.range_m >= radar.max_unambiguous_range_m:
                continue

            delay_s = 2.0 * snapshot.range_m / SPEED_OF_LIGHT
            shifted_fast_time_s = fast_time_s - delay_s
            valid = (shifted_fast_time_s >= 0.0) & (shifted_fast_time_s < waveform.pulse_width_s)
            if not np.any(valid):
                continue

            transmit_field_gain = radar.array.transmit_field_gain(
                radar.wavelength_m,
                task.look_az_deg,
                task.look_el_deg,
                snapshot.az_deg,
                snapshot.el_deg,
            )
            received_power_w = (
                radar.peak_tx_power_w
                * radar.array.num_elements
                * (radar.wavelength_m**2)
                * snapshot.rcs_m2
                / (((4.0 * math.pi) ** 3) * (snapshot.range_m**4) * radar.system_loss_linear)
            )
            amplitude = math.sqrt(max(received_power_w, 0.0)) * transmit_field_gain
            propagation_phase = np.exp(-1j * 4.0 * math.pi * snapshot.range_m / radar.wavelength_m)
            steering = radar.array.steering_vector(radar.wavelength_m, snapshot.az_deg, snapshot.el_deg)
            chirp = np.exp(
                1j * math.pi * waveform.chirp_slope_hz_per_s * shifted_fast_time_s[valid] ** 2
            )

            iq[:, :, pulse_index, valid] += (
                amplitude * propagation_phase * steering[:, :, None] * chirp[None, None, :]
            )

    if radar.noise_power_w > 0.0:
        generator = rng or np.random.default_rng()
        noise_std = math.sqrt(radar.noise_power_w / 2.0)
        iq += noise_std * (
            generator.standard_normal(iq.shape) + 1j * generator.standard_normal(iq.shape)
        )

    return RawDwellData(
        iq=iq,
        axes=RawDwellAxes(
            fast_time_s=fast_time_s,
            pulse_times_s=pulse_times_s,
            array_positions_m=radar.array.positions_m,
        ),
        task=task,
        truth=scene.snapshots_at(task.center_time_s),
    )

