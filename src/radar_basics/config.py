from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from radar_basics.core import DEFAULT_TEMPERATURE_K, spherical_to_cartesian
from radar_basics.radar import LfmPulseWaveform, RadarSystem, RectangularArray
from radar_basics.scenario import PointTarget, Scene


class ConfigError(ValueError):
    """Raised when an experiment YAML configuration is invalid."""


@dataclass(frozen=True)
class RadarConfig:
    carrier_frequency_hz: float
    peak_tx_power_w: float
    noise_figure_db: float = 0.0
    system_loss_db: float = 0.0
    temperature_k: float = DEFAULT_TEMPERATURE_K


@dataclass(frozen=True)
class ArrayConfig:
    num_y: int
    num_x: int
    spacing_y_m: float | None = None
    spacing_x_m: float | None = None


@dataclass(frozen=True)
class WaveformConfig:
    bandwidth_hz: float
    pulse_width_s: float
    prf_hz: float
    num_pulses: int
    sample_rate_hz: float


@dataclass(frozen=True)
class ScanConfig:
    azimuths_deg: tuple[float, ...]
    elevations_deg: tuple[float, ...]
    mode: str = "search"


@dataclass(frozen=True)
class TargetConfig:
    name: str
    position_m: tuple[float, float, float]
    velocity_mps: tuple[float, float, float]
    rcs_m2: float


@dataclass(frozen=True)
class SceneConfig:
    targets: tuple[TargetConfig, ...]


@dataclass(frozen=True)
class DetectorConfig:
    method: str = "threshold"
    threshold_snr_db: float = 12.0
    max_detections_per_dwell: int = 10
    guard_cells: tuple[int, int, int, int] = (1, 1, 1, 1)


@dataclass(frozen=True)
class TrackerConfig:
    association_gate_m: float = 1_500.0
    confirmation_hits: int = 2
    max_misses: int = 2
    process_noise_mps2: float = 20.0
    measurement_noise_m: float = 100.0


@dataclass(frozen=True)
class ProcessingConfig:
    angle_grid_az_deg: tuple[float, ...]
    angle_grid_el_deg: tuple[float, ...]
    detector: DetectorConfig
    tracker: TrackerConfig


@dataclass(frozen=True)
class RunConfig:
    num_scan_cycles: int = 1
    seed: int | None = None
    store_raw: bool = True


@dataclass(frozen=True)
class ExperimentConfig:
    radar: RadarConfig
    array: ArrayConfig
    waveform: WaveformConfig
    scan: ScanConfig
    scene: SceneConfig
    processing: ProcessingConfig
    run: RunConfig


def load_config(path: str | Path) -> ExperimentConfig:
    return load_experiment_config(path)


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle)
    return parse_experiment_config(raw_config)


def parse_experiment_config(raw_config: Any) -> ExperimentConfig:
    config = _require_mapping(raw_config, "top-level config")
    _check_keys(config, {"radar", "array", "waveform", "scan", "scene", "processing", "run"}, "top-level config")

    scan = _parse_scan(_require_mapping(config.get("scan"), "scan"))
    processing = _parse_processing(
        _optional_mapping(config.get("processing"), "processing"),
        default_azimuths=scan.azimuths_deg,
        default_elevations=scan.elevations_deg,
    )
    return ExperimentConfig(
        radar=_parse_radar(_require_mapping(config.get("radar"), "radar")),
        array=_parse_array(_require_mapping(config.get("array"), "array")),
        waveform=_parse_waveform(_require_mapping(config.get("waveform"), "waveform")),
        scan=scan,
        scene=_parse_scene(_require_mapping(config.get("scene"), "scene")),
        processing=processing,
        run=_parse_run(_optional_mapping(config.get("run"), "run")),
    )


def build_radar_system(config: ExperimentConfig) -> RadarSystem:
    waveform = LfmPulseWaveform(
        bandwidth_hz=config.waveform.bandwidth_hz,
        pulse_width_s=config.waveform.pulse_width_s,
        prf_hz=config.waveform.prf_hz,
        num_pulses=config.waveform.num_pulses,
        sample_rate_hz=config.waveform.sample_rate_hz,
    )
    wavelength_m = 299_792_458.0 / config.radar.carrier_frequency_hz
    array = RectangularArray(
        num_y=config.array.num_y,
        num_x=config.array.num_x,
        spacing_y_m=config.array.spacing_y_m or (wavelength_m / 2.0),
        spacing_x_m=config.array.spacing_x_m or (wavelength_m / 2.0),
    )
    return RadarSystem(
        carrier_frequency_hz=config.radar.carrier_frequency_hz,
        peak_tx_power_w=config.radar.peak_tx_power_w,
        array=array,
        waveform=waveform,
        noise_figure_db=config.radar.noise_figure_db,
        system_loss_db=config.radar.system_loss_db,
        temperature_k=config.radar.temperature_k,
    )


def build_scene(config: ExperimentConfig) -> Scene:
    return Scene(
        targets=tuple(
            PointTarget(
                name=target.name,
                position_m=target.position_m,
                velocity_mps=target.velocity_mps,
                rcs_m2=target.rcs_m2,
            )
            for target in config.scene.targets
        )
    )


def _parse_radar(radar: dict[str, Any]) -> RadarConfig:
    _check_keys(
        radar,
        {"carrier_frequency_hz", "peak_tx_power_w", "noise_figure_db", "system_loss_db", "temperature_k"},
        "radar",
    )
    return RadarConfig(
        carrier_frequency_hz=_required_float(radar, "carrier_frequency_hz", "radar"),
        peak_tx_power_w=_optional_float(
            radar,
            "peak_tx_power_w",
            "radar",
            default=1_000.0,
            minimum=0.0,
            positive=False,
        ),
        noise_figure_db=_optional_float(
            radar,
            "noise_figure_db",
            "radar",
            default=0.0,
            minimum=0.0,
            positive=False,
        ),
        system_loss_db=_optional_float(
            radar,
            "system_loss_db",
            "radar",
            default=0.0,
            minimum=0.0,
            positive=False,
        ),
        temperature_k=_optional_float(
            radar,
            "temperature_k",
            "radar",
            default=DEFAULT_TEMPERATURE_K,
            minimum=0.0,
            positive=False,
        ),
    )


def _parse_array(array: dict[str, Any]) -> ArrayConfig:
    _check_keys(array, {"num_y", "num_x", "spacing_y_m", "spacing_x_m"}, "array")
    return ArrayConfig(
        num_y=_required_int(array, "num_y", "array", minimum=1),
        num_x=_required_int(array, "num_x", "array", minimum=1),
        spacing_y_m=_optional_float(array, "spacing_y_m", "array", default=None),
        spacing_x_m=_optional_float(array, "spacing_x_m", "array", default=None),
    )


def _parse_waveform(waveform: dict[str, Any]) -> WaveformConfig:
    _check_keys(waveform, {"bandwidth_hz", "pulse_width_s", "prf_hz", "num_pulses", "sample_rate_hz"}, "waveform")
    return WaveformConfig(
        bandwidth_hz=_required_float(waveform, "bandwidth_hz", "waveform"),
        pulse_width_s=_required_float(waveform, "pulse_width_s", "waveform"),
        prf_hz=_required_float(waveform, "prf_hz", "waveform"),
        num_pulses=_required_int(waveform, "num_pulses", "waveform", minimum=1),
        sample_rate_hz=_required_float(waveform, "sample_rate_hz", "waveform"),
    )


def _parse_scan(scan: dict[str, Any]) -> ScanConfig:
    _check_keys(scan, {"azimuths_deg", "elevations_deg", "mode"}, "scan")
    return ScanConfig(
        azimuths_deg=_required_float_tuple(scan, "azimuths_deg", "scan"),
        elevations_deg=_required_float_tuple(scan, "elevations_deg", "scan"),
        mode=str(scan.get("mode", "search")),
    )


def _parse_scene(scene: dict[str, Any]) -> SceneConfig:
    _check_keys(scene, {"targets"}, "scene")
    raw_targets = scene.get("targets", [])
    if not isinstance(raw_targets, list):
        raise ConfigError("scene.targets must be a list")
    return SceneConfig(targets=tuple(_parse_target(target, index) for index, target in enumerate(raw_targets)))


def _parse_target(target: Any, index: int) -> TargetConfig:
    mapping = _require_mapping(target, f"scene.targets[{index}]")
    _check_keys(
        mapping,
        {
            "name",
            "range_m",
            "az_deg",
            "azimuth_deg",
            "el_deg",
            "elevation_deg",
            "radial_velocity_mps",
            "position_m",
            "velocity_mps",
            "rcs_m2",
        },
        f"scene.targets[{index}]",
    )
    name = str(mapping.get("name", f"target-{index}"))
    rcs_m2 = _required_float(mapping, "rcs_m2", f"scene.targets[{index}]")
    if "position_m" in mapping:
        position_m = _required_vector3(mapping, "position_m", f"scene.targets[{index}]")
        velocity_mps = _required_vector3(mapping, "velocity_mps", f"scene.targets[{index}]")
    else:
        range_m = _required_float(mapping, "range_m", f"scene.targets[{index}]")
        az_deg = _angle_alias(mapping, f"scene.targets[{index}]", "az_deg", "azimuth_deg")
        el_deg = _angle_alias(mapping, f"scene.targets[{index}]", "el_deg", "elevation_deg")
        radial_velocity = _optional_float(
            mapping,
            "radial_velocity_mps",
            f"scene.targets[{index}]",
            default=0.0,
            positive=False,
        )
        direction = spherical_to_cartesian(1.0, az_deg, el_deg)
        position = spherical_to_cartesian(range_m, az_deg, el_deg)
        velocity = radial_velocity * direction
        position_m = _vector_to_tuple(position)
        velocity_mps = _vector_to_tuple(velocity)
    return TargetConfig(name=name, position_m=position_m, velocity_mps=velocity_mps, rcs_m2=rcs_m2)


def _parse_processing(processing: dict[str, Any], *, default_azimuths: tuple[float, ...], default_elevations: tuple[float, ...]) -> ProcessingConfig:
    _check_keys(processing, {"angle_grid", "detector", "tracker"}, "processing")
    angle_grid = _optional_mapping(processing.get("angle_grid"), "processing.angle_grid")
    _check_keys(angle_grid, {"azimuths_deg", "elevations_deg"}, "processing.angle_grid")
    detector = _parse_detector(_optional_mapping(processing.get("detector"), "processing.detector"))
    tracker = _parse_tracker(_optional_mapping(processing.get("tracker"), "processing.tracker"))
    return ProcessingConfig(
        angle_grid_az_deg=_optional_float_tuple(
            angle_grid,
            "azimuths_deg",
            "processing.angle_grid",
            default=default_azimuths,
        ),
        angle_grid_el_deg=_optional_float_tuple(
            angle_grid,
            "elevations_deg",
            "processing.angle_grid",
            default=default_elevations,
        ),
        detector=detector,
        tracker=tracker,
    )


def _parse_detector(detector: dict[str, Any]) -> DetectorConfig:
    _check_keys(detector, {"method", "threshold_snr_db", "max_detections_per_dwell", "guard_cells"}, "processing.detector")
    method = str(detector.get("method", "threshold"))
    if method not in {"threshold"}:
        raise ConfigError("processing.detector.method must be 'threshold' for v1")
    return DetectorConfig(
        method=method,
        threshold_snr_db=_optional_float(
            detector,
            "threshold_snr_db",
            "processing.detector",
            default=12.0,
            minimum=0.0,
            positive=False,
        ),
        max_detections_per_dwell=_optional_int(
            detector,
            "max_detections_per_dwell",
            "processing.detector",
            default=10,
            minimum=0,
        ),
        guard_cells=_optional_int_tuple4(
            detector,
            "guard_cells",
            "processing.detector",
            default=(1, 1, 1, 1),
        ),
    )


def _parse_tracker(tracker: dict[str, Any]) -> TrackerConfig:
    _check_keys(
        tracker,
        {"association_gate_m", "confirmation_hits", "max_misses", "process_noise_mps2", "measurement_noise_m"},
        "processing.tracker",
    )
    return TrackerConfig(
        association_gate_m=_optional_float(tracker, "association_gate_m", "processing.tracker", default=1_500.0),
        confirmation_hits=_optional_int(tracker, "confirmation_hits", "processing.tracker", default=2, minimum=1),
        max_misses=_optional_int(tracker, "max_misses", "processing.tracker", default=2, minimum=0),
        process_noise_mps2=_optional_float(tracker, "process_noise_mps2", "processing.tracker", default=20.0),
        measurement_noise_m=_optional_float(tracker, "measurement_noise_m", "processing.tracker", default=100.0),
    )


def _parse_run(run: dict[str, Any]) -> RunConfig:
    _check_keys(run, {"num_scan_cycles", "seed", "store_raw"}, "run")
    return RunConfig(
        num_scan_cycles=_optional_int(run, "num_scan_cycles", "run", default=1, minimum=1),
        seed=_optional_int(run, "seed", "run", default=None, minimum=0),
        store_raw=bool(run.get("store_raw", True)),
    )


def _require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{context} must be a mapping")
    return value


def _optional_mapping(value: Any, context: str) -> dict[str, Any]:
    if value is None:
        return {}
    return _require_mapping(value, context)


def _check_keys(mapping: dict[str, Any], allowed_keys: set[str], context: str) -> None:
    unexpected = sorted(set(mapping) - allowed_keys)
    if unexpected:
        raise ConfigError(f"Unexpected keys in {context}: {', '.join(unexpected)}")


def _required_float(mapping: dict[str, Any], key: str, context: str, *, positive: bool = True) -> float:
    if key not in mapping:
        raise ConfigError(f"Missing {context}.{key}")
    return _validate_float(mapping[key], f"{context}.{key}", positive=positive)


def _optional_float(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    default: float | None,
    minimum: float | None = None,
    positive: bool = True,
) -> float | None:
    if key not in mapping:
        return default
    value = _validate_float(mapping[key], f"{context}.{key}", positive=positive)
    if minimum is not None and value < minimum:
        raise ConfigError(f"{context}.{key} must be >= {minimum}")
    return value


def _validate_float(value: Any, name: str, *, positive: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{name} must be a number")
    result = float(value)
    if positive and result <= 0.0:
        raise ConfigError(f"{name} must be positive")
    return result


def _required_int(mapping: dict[str, Any], key: str, context: str, *, minimum: int) -> int:
    if key not in mapping:
        raise ConfigError(f"Missing {context}.{key}")
    return _validate_int(mapping[key], f"{context}.{key}", minimum=minimum)


def _optional_int(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    default: int | None,
    minimum: int,
) -> int | None:
    if key not in mapping:
        return default
    return _validate_int(mapping[key], f"{context}.{key}", minimum=minimum)


def _validate_int(value: Any, name: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{name} must be an integer")
    if int(value) != value:
        raise ConfigError(f"{name} must be an integer")
    result = int(value)
    if result < minimum:
        raise ConfigError(f"{name} must be >= {minimum}")
    return result


def _required_float_tuple(mapping: dict[str, Any], key: str, context: str) -> tuple[float, ...]:
    if key not in mapping:
        raise ConfigError(f"Missing {context}.{key}")
    return _validate_float_tuple(mapping[key], f"{context}.{key}")


def _optional_float_tuple(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    default: tuple[float, ...],
) -> tuple[float, ...]:
    if key not in mapping:
        return default
    return _validate_float_tuple(mapping[key], f"{context}.{key}")


def _validate_float_tuple(value: Any, name: str) -> tuple[float, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{name} must be a non-empty list")
    return tuple(_validate_float(item, f"{name}[{index}]", positive=False) for index, item in enumerate(value))


def _optional_int_tuple4(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    default: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    if key not in mapping:
        return default
    value = mapping[key]
    if not isinstance(value, list) or len(value) != 4:
        raise ConfigError(f"{context}.{key} must be a list of four integers")
    return tuple(_validate_int(item, f"{context}.{key}[{index}]", minimum=0) for index, item in enumerate(value))  # type: ignore[return-value]


def _required_vector3(mapping: dict[str, Any], key: str, context: str) -> tuple[float, float, float]:
    if key not in mapping:
        raise ConfigError(f"Missing {context}.{key}")
    value = mapping[key]
    if not isinstance(value, list) or len(value) != 3:
        raise ConfigError(f"{context}.{key} must be a list of three numbers")
    return (
        _validate_float(value[0], f"{context}.{key}[0]", positive=False),
        _validate_float(value[1], f"{context}.{key}[1]", positive=False),
        _validate_float(value[2], f"{context}.{key}[2]", positive=False),
    )


def _angle_alias(mapping: dict[str, Any], context: str, primary: str, alias: str) -> float:
    if primary in mapping and alias in mapping:
        raise ConfigError(f"{context} must not provide both {primary} and {alias}")
    if primary in mapping:
        return _validate_float(mapping[primary], f"{context}.{primary}", positive=False)
    if alias in mapping:
        return _validate_float(mapping[alias], f"{context}.{alias}", positive=False)
    raise ConfigError(f"Missing {context}.{primary}")


def _vector_to_tuple(vector: Any) -> tuple[float, float, float]:
    return (float(vector[0]), float(vector[1]), float(vector[2]))
