from __future__ import annotations

from radar_basics.data import ProcessedDwell
from radar_basics.detection import Detection
from radar_basics.scheduler import DwellTask
from radar_basics.tracking import Track


def plot_range_doppler(processed: ProcessedDwell):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    image = ax.imshow(
        processed.range_doppler_power.T,
        origin="lower",
        aspect="auto",
        extent=[
            processed.radar_cube.axes.range_m[0],
            processed.radar_cube.axes.range_m[-1],
            processed.radar_cube.axes.radial_velocity_mps[0],
            processed.radar_cube.axes.radial_velocity_mps[-1],
        ],
    )
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Radial velocity (m/s)")
    ax.set_title(f"Dwell {processed.task.id} range-Doppler")
    fig.colorbar(image, ax=ax, label="Power")
    return fig, ax


def plot_scan_beams(tasks: tuple[DwellTask, ...]):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.scatter([task.look_az_deg for task in tasks], [task.look_el_deg for task in tasks], c=[task.id for task in tasks])
    for task in tasks:
        ax.annotate(str(task.id), (task.look_az_deg, task.look_el_deg), textcoords="offset points", xytext=(4, 4))
    ax.set_xlabel("Azimuth (deg)")
    ax.set_ylabel("Elevation (deg)")
    ax.set_title("Scripted scan beams")
    ax.grid(True)
    return fig, ax


def plot_air_picture(detections: tuple[Detection, ...], tracks: tuple[Track, ...] = ()):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    if detections:
        xs = [d.range_m for d in detections]
        ys = [d.az_deg for d in detections]
        ax.scatter(xs, ys, marker="x", label="detections")
    if tracks:
        ranges = []
        azimuths = []
        labels = []
        from radar_basics.core import cartesian_to_spherical

        for track in tracks:
            range_m, az_deg, _ = cartesian_to_spherical(track.state_xyz_vxyz[:3])
            ranges.append(range_m)
            azimuths.append(az_deg)
            labels.append(str(track.id))
        ax.scatter(ranges, azimuths, marker="o", facecolors="none", edgecolors="black", label="tracks")
        for range_m, az_deg, label in zip(ranges, azimuths, labels):
            ax.annotate(label, (range_m, az_deg), textcoords="offset points", xytext=(4, 4))
    ax.set_xlabel("Range (m)")
    ax.set_ylabel("Azimuth (deg)")
    ax.set_title("Air picture")
    ax.grid(True)
    if detections or tracks:
        ax.legend()
    return fig, ax

