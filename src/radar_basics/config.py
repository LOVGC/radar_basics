from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

import yaml

SPEED_OF_LIGHT = 299_792_458.0
BOLTZMANN_CONSTANT = 1.380649e-23
DEFAULT_TEMPERATURE_K = 290.0
DEFAULT_SNR_THRESHOLD_DB = 13.0
DEFAULT_OVERSAMPLING_FACTOR = 2.0
DEFAULT_STEERING_AZIMUTH_DEG = 0.0


class ConfigError(ValueError):
    """Raised when a simulator YAML configuration is invalid."""


@dataclass(frozen=True)
class NoiseConfig:
    noise_figure_db: float
    system_loss_db: float = 0.0
    temperature_k: float = DEFAULT_TEMPERATURE_K


@dataclass(frozen=True)
class TargetConfig:
    range_m: float
    azimuth_deg: float
    radial_velocity_mps: float
    rcs_m2: float


@dataclass(frozen=True)
class SceneConfig:
    targets: tuple[TargetConfig, ...]


@dataclass(frozen=True)
class ArchitectureRadarConfig:
    carrier_frequency_hz: float
    wavelength_m: float
    num_elements: int
    element_spacing_m: float
    steering_azimuth_deg: float
    chirp_bandwidth_hz: float
    pulse_width_s: float
    pri_s: float
    num_pulses: int
    sample_rate_hz: float
    peak_tx_power_w: float


@dataclass(frozen=True)
class PerformanceRadarConfig:
    carrier_frequency_hz: float
    range_resolution_m: float
    max_unambiguous_range_m: float
    velocity_resolution_mps: float
    max_unambiguous_velocity_mps: float
    tx_3db_beamwidth_deg: float
    detection_range_m: float
    reference_rcs_m2: float
    snr_threshold_db: float = DEFAULT_SNR_THRESHOLD_DB
    oversampling_factor: float = DEFAULT_OVERSAMPLING_FACTOR
    steering_azimuth_deg: float = DEFAULT_STEERING_AZIMUTH_DEG


@dataclass(frozen=True)
class SimulationConfig:
    mode: str
    radar: ArchitectureRadarConfig | PerformanceRadarConfig
    scene: SceneConfig
    noise: NoiseConfig
    seed: int | None = None


@dataclass(frozen=True)
class ResolvedRadarConfig:
    carrier_frequency_hz: float
    wavelength_m: float
    num_elements: int
    element_spacing_m: float
    steering_azimuth_deg: float
    chirp_bandwidth_hz: float
    pulse_width_s: float
    pri_s: float
    num_pulses: int
    sample_rate_hz: float
    peak_tx_power_w: float
    noise_figure_db: float
    system_loss_db: float
    temperature_k: float
    range_resolution_m: float
    max_unambiguous_range_m: float
    velocity_resolution_mps: float
    max_unambiguous_velocity_mps: float
    tx_3db_beamwidth_deg: float
    snr_threshold_db: float | None = None
    oversampling_factor: float | None = None

    @property
    def num_fast_time_samples(self) -> int:
        return math.ceil(self.sample_rate_hz * self.pri_s)


def load_config(path: str | Path) -> SimulationConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle)

    config = _require_mapping(raw_config, "top-level config")
    _check_keys(config, {"mode", "radar", "scene", "noise", "seed"}, "top-level config")

    mode = config.get("mode")
    if mode not in {"architecture", "performance"}:
        raise ConfigError("top-level config must contain mode: architecture | performance")

    radar_section = _require_mapping(config.get("radar"), "radar")
    scene = _parse_scene(_require_mapping(config.get("scene"), "scene"))
    noise = _parse_noise(_require_mapping(config.get("noise"), "noise"))
    seed = _optional_int(config, "seed", "top-level config", minimum=0)

    if mode == "architecture":
        radar = _parse_architecture_radar(radar_section)
    else:
        radar = _parse_performance_radar(radar_section)

    return SimulationConfig(mode=mode, radar=radar, scene=scene, noise=noise, seed=seed)


def resolve_performance_config(cfg: SimulationConfig) -> ResolvedRadarConfig:
    if cfg.mode != "performance" or not isinstance(cfg.radar, PerformanceRadarConfig):
        raise ConfigError("resolve_performance_config expects a performance-mode SimulationConfig")

    radar = cfg.radar
    wavelength_m = SPEED_OF_LIGHT / radar.carrier_frequency_hz
    chirp_bandwidth_hz = SPEED_OF_LIGHT / (2.0 * radar.range_resolution_m)
    pri_s = (2.0 * radar.max_unambiguous_range_m) / SPEED_OF_LIGHT
    max_unambiguous_velocity_mps = wavelength_m / (4.0 * pri_s)
    if max_unambiguous_velocity_mps + 1e-12 < radar.max_unambiguous_velocity_mps:
        raise ConfigError(
            "Requested max_unambiguous_range_m and max_unambiguous_velocity_mps cannot be "
            "satisfied simultaneously by a single-PRF waveform"
        )

    num_pulses = math.ceil(wavelength_m / (2.0 * radar.velocity_resolution_mps * pri_s))
    element_spacing_m = wavelength_m / 2.0
    theta_rad = math.radians(radar.tx_3db_beamwidth_deg)
    aperture_m = 0.886 * wavelength_m / theta_rad
    num_elements = math.ceil(aperture_m / element_spacing_m) + 1
    sample_rate_hz = radar.oversampling_factor * chirp_bandwidth_hz
    pulse_width_s = 1.0 / chirp_bandwidth_hz
    if pulse_width_s >= pri_s:
        raise ConfigError("Derived pulse_width_s must be smaller than pri_s")

    tx_gain_linear = float(num_elements)
    noise_power_w = _noise_power_w(cfg.noise.temperature_k, cfg.noise.noise_figure_db, sample_rate_hz)
    system_loss_linear = _db_to_linear(cfg.noise.system_loss_db)
    snr_linear = _db_to_linear(radar.snr_threshold_db)
    numerator = snr_linear * noise_power_w * ((4.0 * math.pi) ** 3) * (radar.detection_range_m**4)
    denominator = tx_gain_linear * (wavelength_m**2) * radar.reference_rcs_m2
    peak_tx_power_w = (numerator * system_loss_linear) / denominator if denominator else 0.0

    actual_aperture_m = max((num_elements - 1) * element_spacing_m, element_spacing_m)
    tx_3db_beamwidth_deg = math.degrees(0.886 * wavelength_m / actual_aperture_m)

    return ResolvedRadarConfig(
        carrier_frequency_hz=radar.carrier_frequency_hz,
        wavelength_m=wavelength_m,
        num_elements=num_elements,
        element_spacing_m=element_spacing_m,
        steering_azimuth_deg=radar.steering_azimuth_deg,
        chirp_bandwidth_hz=chirp_bandwidth_hz,
        pulse_width_s=pulse_width_s,
        pri_s=pri_s,
        num_pulses=num_pulses,
        sample_rate_hz=sample_rate_hz,
        peak_tx_power_w=peak_tx_power_w,
        noise_figure_db=cfg.noise.noise_figure_db,
        system_loss_db=cfg.noise.system_loss_db,
        temperature_k=cfg.noise.temperature_k,
        range_resolution_m=SPEED_OF_LIGHT / (2.0 * chirp_bandwidth_hz),
        max_unambiguous_range_m=SPEED_OF_LIGHT * pri_s / 2.0,
        velocity_resolution_mps=wavelength_m / (2.0 * num_pulses * pri_s),
        max_unambiguous_velocity_mps=max_unambiguous_velocity_mps,
        tx_3db_beamwidth_deg=tx_3db_beamwidth_deg,
        snr_threshold_db=radar.snr_threshold_db,
        oversampling_factor=radar.oversampling_factor,
    )


def resolve_radar_config(cfg: SimulationConfig) -> ResolvedRadarConfig:
    if cfg.mode == "performance":
        return resolve_performance_config(cfg)
    if not isinstance(cfg.radar, ArchitectureRadarConfig):
        raise ConfigError("architecture mode requires an ArchitectureRadarConfig")
    return _resolve_architecture_config(cfg.radar, cfg.noise)


def _resolve_architecture_config(
    radar: ArchitectureRadarConfig,
    noise: NoiseConfig,
) -> ResolvedRadarConfig:
    actual_aperture_m = max((radar.num_elements - 1) * radar.element_spacing_m, radar.element_spacing_m)
    return ResolvedRadarConfig(
        carrier_frequency_hz=radar.carrier_frequency_hz,
        wavelength_m=radar.wavelength_m,
        num_elements=radar.num_elements,
        element_spacing_m=radar.element_spacing_m,
        steering_azimuth_deg=radar.steering_azimuth_deg,
        chirp_bandwidth_hz=radar.chirp_bandwidth_hz,
        pulse_width_s=radar.pulse_width_s,
        pri_s=radar.pri_s,
        num_pulses=radar.num_pulses,
        sample_rate_hz=radar.sample_rate_hz,
        peak_tx_power_w=radar.peak_tx_power_w,
        noise_figure_db=noise.noise_figure_db,
        system_loss_db=noise.system_loss_db,
        temperature_k=noise.temperature_k,
        range_resolution_m=SPEED_OF_LIGHT / (2.0 * radar.chirp_bandwidth_hz),
        max_unambiguous_range_m=SPEED_OF_LIGHT * radar.pri_s / 2.0,
        velocity_resolution_mps=radar.wavelength_m / (2.0 * radar.num_pulses * radar.pri_s),
        max_unambiguous_velocity_mps=radar.wavelength_m / (4.0 * radar.pri_s),
        tx_3db_beamwidth_deg=math.degrees(0.886 * radar.wavelength_m / actual_aperture_m),
    )


def _parse_scene(scene: dict[str, Any]) -> SceneConfig:
    _check_keys(scene, {"targets"}, "scene")
    raw_targets = scene.get("targets")
    if not isinstance(raw_targets, list):
        raise ConfigError("scene.targets must be a list")

    targets = tuple(_parse_target(target, index) for index, target in enumerate(raw_targets))
    return SceneConfig(targets=targets)


def _parse_target(target: Any, index: int) -> TargetConfig:
    mapping = _require_mapping(target, f"scene.targets[{index}]")
    context = f"scene.targets[{index}]"
    _check_keys(mapping, {"range_m", "azimuth_deg", "radial_velocity_mps", "rcs_m2"}, context)
    return TargetConfig(
        range_m=_required_float(mapping, "range_m", context),
        azimuth_deg=_required_float(mapping, "azimuth_deg", context, positive=False),
        radial_velocity_mps=_required_float(mapping, "radial_velocity_mps", context, positive=False),
        rcs_m2=_required_float(mapping, "rcs_m2", context),
    )


def _parse_noise(noise: dict[str, Any]) -> NoiseConfig:
    _check_keys(noise, {"noise_figure_db", "system_loss_db", "temperature_k"}, "noise")
    return NoiseConfig(
        noise_figure_db=_required_float(noise, "noise_figure_db", "noise", minimum=0.0),
        system_loss_db=_optional_float(noise, "system_loss_db", "noise", default=0.0, minimum=0.0),
        temperature_k=_optional_float(noise, "temperature_k", "noise", default=DEFAULT_TEMPERATURE_K, minimum=0.0),
    )


def _parse_architecture_radar(radar: dict[str, Any]) -> ArchitectureRadarConfig:
    allowed_keys = {
        "carrier_frequency_hz",
        "wavelength_m",
        "num_elements",
        "element_spacing_m",
        "steering_azimuth_deg",
        "chirp_bandwidth_hz",
        "pulse_width_s",
        "pri_s",
        "num_pulses",
        "sample_rate_hz",
        "peak_tx_power_w",
    }
    _check_keys(radar, allowed_keys, "radar")

    carrier_frequency_hz = _optional_float(radar, "carrier_frequency_hz", "radar")
    wavelength_m = _optional_float(radar, "wavelength_m", "radar")
    carrier_frequency_hz, wavelength_m = _resolve_carrier_and_wavelength(
        carrier_frequency_hz,
        wavelength_m,
        "radar",
    )
    element_spacing_m = _optional_float(
        radar,
        "element_spacing_m",
        "radar",
        default=wavelength_m / 2.0,
    )

    pulse_width_s = _required_float(radar, "pulse_width_s", "radar")
    pri_s = _required_float(radar, "pri_s", "radar")
    if pulse_width_s >= pri_s:
        raise ConfigError("radar.pulse_width_s must be smaller than radar.pri_s")

    return ArchitectureRadarConfig(
        carrier_frequency_hz=carrier_frequency_hz,
        wavelength_m=wavelength_m,
        num_elements=_required_int(radar, "num_elements", "radar", minimum=1),
        element_spacing_m=element_spacing_m,
        steering_azimuth_deg=_optional_float(
            radar,
            "steering_azimuth_deg",
            "radar",
            default=DEFAULT_STEERING_AZIMUTH_DEG,
            positive=False,
        ),
        chirp_bandwidth_hz=_required_float(radar, "chirp_bandwidth_hz", "radar"),
        pulse_width_s=pulse_width_s,
        pri_s=pri_s,
        num_pulses=_required_int(radar, "num_pulses", "radar", minimum=1),
        sample_rate_hz=_required_float(radar, "sample_rate_hz", "radar"),
        peak_tx_power_w=_required_float(radar, "peak_tx_power_w", "radar"),
    )


def _parse_performance_radar(radar: dict[str, Any]) -> PerformanceRadarConfig:
    allowed_keys = {
        "carrier_frequency_hz",
        "range_resolution_m",
        "max_unambiguous_range_m",
        "velocity_resolution_mps",
        "max_unambiguous_velocity_mps",
        "tx_3db_beamwidth_deg",
        "detection_range_m",
        "reference_rcs_m2",
        "snr_threshold_db",
        "oversampling_factor",
        "steering_azimuth_deg",
    }
    _check_keys(radar, allowed_keys, "radar")

    return PerformanceRadarConfig(
        carrier_frequency_hz=_required_float(radar, "carrier_frequency_hz", "radar"),
        range_resolution_m=_required_float(radar, "range_resolution_m", "radar"),
        max_unambiguous_range_m=_required_float(radar, "max_unambiguous_range_m", "radar"),
        velocity_resolution_mps=_required_float(radar, "velocity_resolution_mps", "radar"),
        max_unambiguous_velocity_mps=_required_float(radar, "max_unambiguous_velocity_mps", "radar"),
        tx_3db_beamwidth_deg=_required_float(radar, "tx_3db_beamwidth_deg", "radar"),
        detection_range_m=_required_float(radar, "detection_range_m", "radar"),
        reference_rcs_m2=_required_float(radar, "reference_rcs_m2", "radar"),
        snr_threshold_db=_optional_float(
            radar,
            "snr_threshold_db",
            "radar",
            default=DEFAULT_SNR_THRESHOLD_DB,
            minimum=0.0,
        ),
        oversampling_factor=_optional_float(
            radar,
            "oversampling_factor",
            "radar",
            default=DEFAULT_OVERSAMPLING_FACTOR,
        ),
        steering_azimuth_deg=_optional_float(
            radar,
            "steering_azimuth_deg",
            "radar",
            default=DEFAULT_STEERING_AZIMUTH_DEG,
            positive=False,
        ),
    )


def _resolve_carrier_and_wavelength(
    carrier_frequency_hz: float | None,
    wavelength_m: float | None,
    context: str,
) -> tuple[float, float]:
    if carrier_frequency_hz is None and wavelength_m is None:
        raise ConfigError(f"{context} must provide carrier_frequency_hz or wavelength_m")

    if carrier_frequency_hz is not None and carrier_frequency_hz <= 0.0:
        raise ConfigError(f"{context}.carrier_frequency_hz must be positive")
    if wavelength_m is not None and wavelength_m <= 0.0:
        raise ConfigError(f"{context}.wavelength_m must be positive")

    if carrier_frequency_hz is None:
        carrier_frequency_hz = SPEED_OF_LIGHT / wavelength_m  # type: ignore[arg-type]
    if wavelength_m is None:
        wavelength_m = SPEED_OF_LIGHT / carrier_frequency_hz

    derived_wavelength_m = SPEED_OF_LIGHT / carrier_frequency_hz
    if not math.isclose(derived_wavelength_m, wavelength_m, rel_tol=1e-6):
        raise ConfigError(
            f"{context}.carrier_frequency_hz and {context}.wavelength_m describe different carriers"
        )

    return carrier_frequency_hz, wavelength_m


def _required_float(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    minimum: float | None = None,
    positive: bool = True,
) -> float:
    if key not in mapping:
        raise ConfigError(f"Missing {context}.{key}")
    return _validate_float(mapping[key], f"{context}.{key}", minimum=minimum, positive=positive)


def _optional_float(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    default: float | None = None,
    minimum: float | None = None,
    positive: bool = True,
) -> float | None:
    if key not in mapping:
        return default
    return _validate_float(mapping[key], f"{context}.{key}", minimum=minimum, positive=positive)


def _validate_float(
    value: Any,
    name: str,
    *,
    minimum: float | None = None,
    positive: bool = True,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{name} must be a number")

    result = float(value)
    if minimum is not None and result < minimum:
        raise ConfigError(f"{name} must be >= {minimum}")
    if minimum is None:
        if positive and result <= 0.0:
            raise ConfigError(f"{name} must be positive")
    return result


def _required_int(mapping: dict[str, Any], key: str, context: str, *, minimum: int = 0) -> int:
    if key not in mapping:
        raise ConfigError(f"Missing {context}.{key}")
    return _validate_int(mapping[key], f"{context}.{key}", minimum=minimum)


def _optional_int(
    mapping: dict[str, Any],
    key: str,
    context: str,
    *,
    minimum: int = 0,
) -> int | None:
    if key not in mapping:
        return None
    return _validate_int(mapping[key], f"{context}.{key}", minimum=minimum)


def _validate_int(value: Any, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"{name} must be an integer")
    if int(value) != value:
        raise ConfigError(f"{name} must be an integer")
    result = int(value)
    if result < minimum:
        raise ConfigError(f"{name} must be >= {minimum}")
    return result


def _require_mapping(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"{context} must be a mapping")
    return value


def _check_keys(mapping: dict[str, Any], allowed_keys: set[str], context: str) -> None:
    unexpected_keys = sorted(set(mapping) - allowed_keys)
    if unexpected_keys:
        joined = ", ".join(unexpected_keys)
        raise ConfigError(f"Unexpected keys in {context}: {joined}")


def _db_to_linear(db_value: float) -> float:
    return 10.0 ** (db_value / 10.0)


def _noise_power_w(temperature_k: float, noise_figure_db: float, bandwidth_hz: float) -> float:
    return BOLTZMANN_CONSTANT * temperature_k * _db_to_linear(noise_figure_db) * bandwidth_hz
