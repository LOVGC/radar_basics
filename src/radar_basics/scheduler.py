from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DwellTask:
    id: int
    mode: str
    look_az_deg: float
    look_el_deg: float
    start_time_s: float
    prf_hz: float
    num_pulses: int

    @property
    def pri_s(self) -> float:
        return 1.0 / self.prf_hz

    @property
    def duration_s(self) -> float:
        return self.num_pulses * self.pri_s

    @property
    def center_time_s(self) -> float:
        return self.start_time_s + 0.5 * self.duration_s


@dataclass(frozen=True)
class ScriptedScanScheduler:
    azimuths_deg: tuple[float, ...]
    elevations_deg: tuple[float, ...]
    prf_hz: float
    num_pulses: int
    mode: str = "search"

    def tasks(self, *, num_scan_cycles: int = 1, start_time_s: float = 0.0) -> tuple[DwellTask, ...]:
        if num_scan_cycles <= 0:
            raise ValueError("num_scan_cycles must be positive")
        dwell_duration_s = self.num_pulses / self.prf_hz
        tasks: list[DwellTask] = []
        task_id = 0
        current_time_s = start_time_s
        for _ in range(num_scan_cycles):
            for el_deg in self.elevations_deg:
                for az_deg in self.azimuths_deg:
                    tasks.append(
                        DwellTask(
                            id=task_id,
                            mode=self.mode,
                            look_az_deg=az_deg,
                            look_el_deg=el_deg,
                            start_time_s=current_time_s,
                            prf_hz=self.prf_hz,
                            num_pulses=self.num_pulses,
                        )
                    )
                    task_id += 1
                    current_time_s += dwell_duration_s
        return tuple(tasks)

