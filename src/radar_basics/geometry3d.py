from __future__ import annotations

import math
from typing import Iterable

import numpy as np

from radar_basics.core import direction_vector
from radar_basics.radar import RadarSystem
from radar_basics.scenario import Scene, TargetSnapshot


def plot_geometry_3d(
    radar: RadarSystem,
    scene: Scene,
    *,
    time_s: float = 0.0,
    look_az_deg: float = 0.0,
    look_el_deg: float = 20.0,
    radar_height_m: float = 2.0,
    beam_length_m: float | None = None,
):
    """Build an interactive 3D Plotly view of the radar geometry.

    The view uses the package coordinate convention: radar +x is boresight,
    +y is positive azimuth, and +z is positive elevation/up. The physical array
    aperture is visually enlarged so individual elements remain visible next to
    kilometer-scale target ranges.
    """

    import plotly.graph_objects as go

    if radar_height_m < 0.0:
        raise ValueError("radar_height_m must be non-negative")

    snapshots = scene.snapshots_at(time_s)
    radar_origin = np.array([0.0, 0.0, radar_height_m], dtype=np.float64)
    resolved_beam_length = _default_beam_length(snapshots, beam_length_m)
    look_direction = direction_vector(look_az_deg, look_el_deg)
    boresight_direction = direction_vector(0.0, 0.0)

    fig = go.Figure()
    _add_ground(fig, snapshots, radar_origin, resolved_beam_length)
    _add_radar_pedestal(fig, radar_origin)
    _add_array(fig, radar, radar_origin, resolved_beam_length)

    boresight_end = radar_origin + boresight_direction * resolved_beam_length * 0.55
    look_end = radar_origin + look_direction * resolved_beam_length
    _add_vector(fig, radar_origin, boresight_end, "boresight", "#1f77b4", cone_scale=0.08)
    _add_vector(fig, radar_origin, look_end, "look direction", "#d62728", cone_scale=0.10)
    _add_angle_arcs(fig, radar_origin, look_az_deg, look_el_deg, resolved_beam_length)
    _add_targets(fig, snapshots, radar_origin, resolved_beam_length)

    fig.update_layout(
        title="Phased-array radar geometry",
        scene={
            "xaxis_title": "x / boresight forward (m)",
            "yaxis_title": "y / positive azimuth (m)",
            "zaxis_title": "z / up, elevation (m)",
            "aspectmode": "data",
            "camera": {"eye": {"x": 1.35, "y": -1.55, "z": 0.85}},
        },
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0.0},
        margin={"l": 0, "r": 0, "t": 54, "b": 0},
        hovermode="closest",
    )
    return fig


def _default_beam_length(snapshots: tuple[TargetSnapshot, ...], beam_length_m: float | None) -> float:
    if beam_length_m is not None:
        if beam_length_m <= 0.0:
            raise ValueError("beam_length_m must be positive")
        return float(beam_length_m)
    if not snapshots:
        return 1000.0
    return max(100.0, 1.1 * max(snapshot.range_m for snapshot in snapshots))


def _add_ground(fig, snapshots: tuple[TargetSnapshot, ...], radar_origin: np.ndarray, beam_length_m: float) -> None:
    import plotly.graph_objects as go

    xy_points = [np.array([0.0, 0.0], dtype=np.float64)]
    xy_points.append((direction_vector(0.0, 0.0) * beam_length_m)[:2])
    for snapshot in snapshots:
        xy_points.append(snapshot.position_m[:2])
    xy = np.asarray(xy_points, dtype=np.float64)
    x_min = min(-0.15 * beam_length_m, float(np.min(xy[:, 0])) - 0.10 * beam_length_m)
    x_max = max(beam_length_m, float(np.max(xy[:, 0])) + 0.10 * beam_length_m)
    y_span = max(0.35 * beam_length_m, float(np.max(np.abs(xy[:, 1]))) + 0.10 * beam_length_m)
    x = np.array([[x_min, x_max], [x_min, x_max]], dtype=np.float64)
    y = np.array([[-y_span, -y_span], [y_span, y_span]], dtype=np.float64)
    z = np.zeros_like(x)

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            name="ground",
            showscale=False,
            opacity=0.34,
            colorscale=[[0.0, "#d8dccf"], [1.0, "#d8dccf"]],
            hoverinfo="skip",
        )
    )
    _add_line(
        fig,
        np.array([[x_min, 0.0, 0.0], [x_max, 0.0, 0.0]], dtype=np.float64),
        "ground x-axis",
        "#8a8a8a",
        width=2,
        showlegend=False,
    )
    _add_line(
        fig,
        np.array([[0.0, -y_span, 0.0], [0.0, y_span, 0.0]], dtype=np.float64),
        "ground y-axis",
        "#8a8a8a",
        width=2,
        showlegend=False,
    )


def _add_radar_pedestal(fig, radar_origin: np.ndarray) -> None:
    import plotly.graph_objects as go

    _add_line(
        fig,
        np.array([[radar_origin[0], radar_origin[1], 0.0], radar_origin], dtype=np.float64),
        "radar pedestal",
        "#444444",
        width=6,
    )
    fig.add_trace(
        go.Scatter3d(
            x=[radar_origin[0]],
            y=[radar_origin[1]],
            z=[radar_origin[2]],
            mode="markers+text",
            name="radar origin",
            text=["radar"],
            textposition="top center",
            marker={"size": 5, "color": "#111111"},
            hovertemplate="radar origin<br>x=%{x:.1f} m<br>y=%{y:.1f} m<br>z=%{z:.1f} m<extra></extra>",
        )
    )


def _add_array(fig, radar: RadarSystem, radar_origin: np.ndarray, beam_length_m: float) -> None:
    import plotly.graph_objects as go

    element_positions = radar.array.positions_m.reshape(-1, 3)
    visual_positions = radar_origin + _scaled_array_positions(element_positions, beam_length_m)

    fig.add_trace(
        go.Scatter3d(
            x=visual_positions[:, 0],
            y=visual_positions[:, 1],
            z=visual_positions[:, 2],
            mode="markers",
            name="array elements",
            marker={"size": 6, "color": "#2ca02c", "symbol": "square"},
            customdata=element_positions,
            hovertemplate=(
                "antenna element"
                "<br>local x=%{customdata[0]:.3f} m"
                "<br>local y=%{customdata[1]:.3f} m"
                "<br>local z=%{customdata[2]:.3f} m"
                "<extra></extra>"
            ),
        )
    )

    y_min, y_max = float(np.min(visual_positions[:, 1])), float(np.max(visual_positions[:, 1]))
    z_min, z_max = float(np.min(visual_positions[:, 2])), float(np.max(visual_positions[:, 2]))
    x = float(radar_origin[0])
    outline = np.array(
        [
            [x, y_min, z_min],
            [x, y_max, z_min],
            [x, y_max, z_max],
            [x, y_min, z_max],
            [x, y_min, z_min],
        ],
        dtype=np.float64,
    )
    _add_line(fig, outline, "array panel", "#2ca02c", width=4)


def _scaled_array_positions(element_positions: np.ndarray, beam_length_m: float) -> np.ndarray:
    aperture = max(
        float(np.ptp(element_positions[:, 1])) if len(element_positions) else 0.0,
        float(np.ptp(element_positions[:, 2])) if len(element_positions) else 0.0,
    )
    min_visual_aperture = 0.055 * beam_length_m
    if aperture <= 0.0:
        scale = 1.0
    else:
        scale = max(1.0, min_visual_aperture / aperture)
    return element_positions * scale


def _add_angle_arcs(
    fig,
    radar_origin: np.ndarray,
    look_az_deg: float,
    look_el_deg: float,
    beam_length_m: float,
) -> None:
    arc_radius = 0.18 * beam_length_m
    ground_z = 0.02
    az_arc = _azimuth_arc_points(look_az_deg, arc_radius, ground_z)
    _add_line(fig, az_arc, "azimuth angle", "#9467bd", width=5)
    _add_text(fig, az_arc[len(az_arc) // 2], "azimuth", "azimuth label", "#9467bd")

    el_arc = _elevation_arc_points(radar_origin, look_az_deg, look_el_deg, arc_radius)
    _add_line(fig, el_arc, "elevation angle", "#ff7f0e", width=5)
    _add_text(fig, el_arc[len(el_arc) // 2], "elevation", "elevation label", "#ff7f0e")


def _azimuth_arc_points(az_deg: float, radius_m: float, z_m: float) -> np.ndarray:
    steps = max(12, int(abs(az_deg) / 2.0) + 2)
    angles = np.linspace(0.0, math.radians(az_deg), steps)
    return np.column_stack(
        [
            radius_m * np.cos(angles),
            radius_m * np.sin(angles),
            np.full_like(angles, z_m),
        ]
    )


def _elevation_arc_points(
    radar_origin: np.ndarray,
    az_deg: float,
    el_deg: float,
    radius_m: float,
) -> np.ndarray:
    steps = max(12, int(abs(el_deg) / 2.0) + 2)
    elevations = np.linspace(0.0, math.radians(el_deg), steps)
    az = math.radians(az_deg)
    horizontal = np.array([math.cos(az), math.sin(az), 0.0], dtype=np.float64)
    points = [
        radar_origin + radius_m * (math.cos(el) * horizontal + math.sin(el) * np.array([0.0, 0.0, 1.0]))
        for el in elevations
    ]
    return np.asarray(points, dtype=np.float64)


def _add_targets(
    fig,
    snapshots: tuple[TargetSnapshot, ...],
    radar_origin: np.ndarray,
    beam_length_m: float,
) -> None:
    import plotly.graph_objects as go

    for snapshot in snapshots:
        target_position = radar_origin + snapshot.position_m
        fig.add_trace(
            go.Scatter3d(
                x=[target_position[0]],
                y=[target_position[1]],
                z=[target_position[2]],
                mode="markers+text",
                name=f"target: {snapshot.name}",
                text=[snapshot.name],
                textposition="top center",
                marker={"size": 7, "color": "#000000", "symbol": "diamond"},
                hovertemplate=_target_hover_text(snapshot),
            )
        )
        _add_line(
            fig,
            np.vstack([radar_origin, target_position]),
            f"line of sight: {snapshot.name}",
            "#000000",
            width=3,
        )
        _add_target_velocity(fig, snapshot, target_position, beam_length_m)
        _add_radial_velocity(fig, snapshot, target_position, beam_length_m)


def _add_target_velocity(
    fig,
    snapshot: TargetSnapshot,
    target_position: np.ndarray,
    beam_length_m: float,
) -> None:
    speed = float(np.linalg.norm(snapshot.velocity_mps))
    if speed == 0.0:
        return
    visual_length = 0.10 * beam_length_m
    end = target_position + (snapshot.velocity_mps / speed) * visual_length
    _add_vector(fig, target_position, end, f"target velocity: {snapshot.name}", "#17becf", cone_scale=0.08)


def _add_radial_velocity(
    fig,
    snapshot: TargetSnapshot,
    target_position: np.ndarray,
    beam_length_m: float,
) -> None:
    if snapshot.range_m == 0.0:
        return
    radial_unit = snapshot.position_m / snapshot.range_m
    sign = 1.0 if snapshot.radial_velocity_mps >= 0.0 else -1.0
    length = max(0.06 * beam_length_m, min(0.14 * beam_length_m, abs(snapshot.radial_velocity_mps) * 0.01 * beam_length_m))
    end = target_position + sign * radial_unit * length
    _add_vector(fig, target_position, end, f"radial velocity: {snapshot.name}", "#e377c2", cone_scale=0.07)
    _add_text(
        fig,
        end,
        f"radial velocity {snapshot.radial_velocity_mps:.1f} m/s",
        f"radial velocity label: {snapshot.name}",
        "#e377c2",
    )


def _add_vector(
    fig,
    start: np.ndarray,
    end: np.ndarray,
    name: str,
    color: str,
    *,
    cone_scale: float,
) -> None:
    import plotly.graph_objects as go

    vector = end - start
    length = float(np.linalg.norm(vector))
    if length == 0.0:
        return
    unit = vector / length
    _add_line(fig, np.vstack([start, end]), name, color, width=5)
    fig.add_trace(
        go.Cone(
            x=[end[0]],
            y=[end[1]],
            z=[end[2]],
            u=[unit[0]],
            v=[unit[1]],
            w=[unit[2]],
            name=f"{name} arrow",
            anchor="tip",
            sizemode="absolute",
            sizeref=max(length * cone_scale, 1e-9),
            showscale=False,
            colorscale=[[0.0, color], [1.0, color]],
            hoverinfo="skip",
        )
    )


def _add_line(
    fig,
    points: np.ndarray,
    name: str,
    color: str,
    *,
    width: int,
    showlegend: bool = True,
) -> None:
    import plotly.graph_objects as go

    fig.add_trace(
        go.Scatter3d(
            x=points[:, 0],
            y=points[:, 1],
            z=points[:, 2],
            mode="lines",
            name=name,
            line={"color": color, "width": width},
            showlegend=showlegend,
            hoverinfo="skip",
        )
    )


def _add_text(fig, point: Iterable[float], text: str, name: str, color: str) -> None:
    import plotly.graph_objects as go

    x, y, z = point
    fig.add_trace(
        go.Scatter3d(
            x=[x],
            y=[y],
            z=[z],
            mode="text",
            name=name,
            text=[text],
            textfont={"color": color, "size": 12},
            showlegend=False,
            hoverinfo="skip",
        )
    )


def _target_hover_text(snapshot: TargetSnapshot) -> str:
    return (
        f"{snapshot.name}"
        f"<br>range={snapshot.range_m:.1f} m"
        f"<br>azimuth={snapshot.az_deg:.2f} deg"
        f"<br>elevation={snapshot.el_deg:.2f} deg"
        f"<br>radial velocity={snapshot.radial_velocity_mps:.2f} m/s"
        f"<br>RCS={snapshot.rcs_m2:.2f} m^2"
        "<extra></extra>"
    )
