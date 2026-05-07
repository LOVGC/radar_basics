from __future__ import annotations

from plotly.graph_objects import Figure

from radar_basics import LfmPulseWaveform, PointTarget, RadarSystem, RectangularArray, Scene, plot_geometry_3d


def test_plot_geometry_3d_returns_plotly_figure() -> None:
    figure = plot_geometry_3d(example_radar(), example_scene())

    assert isinstance(figure, Figure)


def test_plot_geometry_3d_contains_key_teaching_traces() -> None:
    radar = example_radar()

    figure = plot_geometry_3d(radar, example_scene(), look_az_deg=5.0, look_el_deg=15.0)

    trace_names = {trace.name for trace in figure.data}
    assert "ground" in trace_names
    assert "array elements" in trace_names
    assert "array panel" in trace_names
    assert "boresight" in trace_names
    assert "look direction" in trace_names
    assert "azimuth angle" in trace_names
    assert "elevation angle" in trace_names
    assert "target: target-a" in trace_names
    assert "radial velocity: target-a" in trace_names

    array_trace = next(trace for trace in figure.data if trace.name == "array elements")
    assert len(array_trace.x) == radar.array.num_elements


def test_plot_geometry_3d_target_hover_includes_geometry_parameters() -> None:
    figure = plot_geometry_3d(example_radar(), example_scene())

    target_trace = next(trace for trace in figure.data if trace.name == "target: target-a")

    assert "azimuth=" in target_trace.hovertemplate
    assert "elevation=" in target_trace.hovertemplate
    assert "radial velocity=" in target_trace.hovertemplate


def example_radar() -> RadarSystem:
    return RadarSystem(
        carrier_frequency_hz=10.0e9,
        peak_tx_power_w=10_000.0,
        array=RectangularArray(num_y=4, num_x=4, spacing_y_m=0.015, spacing_x_m=0.015),
        waveform=LfmPulseWaveform(
            bandwidth_hz=5.0e6,
            pulse_width_s=2.0e-6,
            prf_hz=10_000.0,
            num_pulses=8,
            sample_rate_hz=10.0e6,
        ),
        temperature_k=0.0,
    )


def example_scene() -> Scene:
    return Scene(
        targets=(
            PointTarget(
                name="target-a",
                position_m=(1000.0, 120.0, 180.0),
                velocity_mps=(15.0, 0.0, 0.0),
                rcs_m2=10.0,
            ),
        )
    )
