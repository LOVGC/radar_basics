from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from radar_basics.config import TrackerConfig
from radar_basics.core import spherical_to_cartesian
from radar_basics.detection import Detection


@dataclass
class Track:
    id: int
    state_xyz_vxyz: np.ndarray
    covariance: np.ndarray
    status: str
    last_update_s: float
    hits: int = 1
    misses: int = 0


class NearestNeighborTracker:
    def __init__(self, config: TrackerConfig):
        self.config = config
        self._tracks: list[Track] = []
        self._next_id = 1

    @property
    def tracks(self) -> tuple[Track, ...]:
        return tuple(self._tracks)

    def update(self, detections: tuple[Detection, ...], time_s: float) -> tuple[Track, ...]:
        for track in self._tracks:
            self._predict(track, time_s)

        assigned_detections: set[int] = set()
        for track in self._tracks:
            detection_index = self._nearest_detection(track, detections, assigned_detections)
            if detection_index is None:
                track.misses += 1
                continue
            assigned_detections.add(detection_index)
            self._correct(track, detections[detection_index])

        for index, detection in enumerate(detections):
            if index not in assigned_detections:
                self._start_track(detection)

        self._tracks = [
            track
            for track in self._tracks
            if track.misses <= self.config.max_misses
        ]
        return self.tracks

    def _predict(self, track: Track, time_s: float) -> None:
        dt = max(0.0, time_s - track.last_update_s)
        if dt == 0.0:
            return
        transition = np.eye(6)
        transition[0, 3] = dt
        transition[1, 4] = dt
        transition[2, 5] = dt
        q = self.config.process_noise_mps2**2
        process = np.zeros((6, 6), dtype=np.float64)
        process[:3, :3] = np.eye(3) * (0.25 * dt**4 * q)
        process[:3, 3:] = np.eye(3) * (0.5 * dt**3 * q)
        process[3:, :3] = np.eye(3) * (0.5 * dt**3 * q)
        process[3:, 3:] = np.eye(3) * (dt**2 * q)
        track.state_xyz_vxyz = transition @ track.state_xyz_vxyz
        track.covariance = transition @ track.covariance @ transition.T + process
        track.last_update_s = time_s

    def _nearest_detection(
        self,
        track: Track,
        detections: tuple[Detection, ...],
        assigned: set[int],
    ) -> int | None:
        best_index: int | None = None
        best_distance = self.config.association_gate_m
        for index, detection in enumerate(detections):
            if index in assigned:
                continue
            measurement = _detection_position(detection)
            distance = float(np.linalg.norm(measurement - track.state_xyz_vxyz[:3]))
            if distance < best_distance:
                best_distance = distance
                best_index = index
        return best_index

    def _correct(self, track: Track, detection: Detection) -> None:
        measurement = _detection_position(detection)
        h = np.zeros((3, 6), dtype=np.float64)
        h[:, :3] = np.eye(3)
        measurement_cov = np.eye(3) * (self.config.measurement_noise_m**2)
        innovation = measurement - h @ track.state_xyz_vxyz
        innovation_cov = h @ track.covariance @ h.T + measurement_cov
        kalman_gain = track.covariance @ h.T @ np.linalg.inv(innovation_cov)
        track.state_xyz_vxyz = track.state_xyz_vxyz + kalman_gain @ innovation
        track.covariance = (np.eye(6) - kalman_gain @ h) @ track.covariance
        track.hits += 1
        track.misses = 0
        track.last_update_s = detection.time_s
        if track.hits >= self.config.confirmation_hits:
            track.status = "confirmed"

    def _start_track(self, detection: Detection) -> None:
        position = _detection_position(detection)
        state = np.zeros(6, dtype=np.float64)
        state[:3] = position
        covariance = np.diag(
            [
                self.config.measurement_noise_m**2,
                self.config.measurement_noise_m**2,
                self.config.measurement_noise_m**2,
                (2.0 * self.config.process_noise_mps2) ** 2,
                (2.0 * self.config.process_noise_mps2) ** 2,
                (2.0 * self.config.process_noise_mps2) ** 2,
            ]
        )
        self._tracks.append(
            Track(
                id=self._next_id,
                state_xyz_vxyz=state,
                covariance=covariance,
                status="tentative",
                last_update_s=detection.time_s,
            )
        )
        self._next_id += 1


def _detection_position(detection: Detection) -> np.ndarray:
    return spherical_to_cartesian(detection.range_m, detection.az_deg, detection.el_deg)

