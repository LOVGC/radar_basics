# Radar Basics Development Log

This is a living development document for the `radar_basics` simulation project. It records what has been built, why it was built that way, what is currently verified, and what should remain visible for future work.

---

## 2026-04-28 — Concise Summary

Today we built the first usable version of the radar simulation learning framework.

Completed:
- Implemented the V1 waveform-level 2D phased-array radar simulator.
- Added the end-to-end chain: truth -> dwell -> raw IQ -> range/Doppler/angle processing -> detections -> tracks -> display.
- Added example config: `example_configs/architecture.yaml`.
- Added tests for config, signal synthesis, processing, detection, tracking, and display helpers.
- Added human-facing docs in `HUMAN.md`.
- Added tutorial notebook: `learning/phased_array_radar_simulation_tutorial.ipynb`.
- Refined the notebook's signal-model explanation, including variable types, index meanings, and Doppler phase notation.
- Removed the Mermaid diagram after it proved less clear than the formula/table explanation.

Verified:
- `uv run pytest` passes with `13 passed`.
- The example simulation produces 18 dwell tasks, 18 detections, and 1 confirmed track.

Current state:
- V1 is ready as an educational waveform-level simulator.
- The next valuable work is improving detection toward CFAR, adding clutter, and expanding the tutorial from ideal point targets toward more realistic radar effects.

---

## 2026-04-28 — V1 waveform-level architecture implemented

### Original Goal

Build a Python simulation that helps systematically understand the operation of a 2D phased-array pulse-Doppler radar:

```text
scan a specified air volume
  -> generate / process radar data
  -> apply filtering / detection / tracking
  -> produce display-level outputs
```

The guiding principle was:

> software architecture should be a good representation of the well-organized mental knowledge framework of the subject.

So the implementation is intentionally structured around the radar mental model:

```text
Scenario / Truth
  -> Dwell / CPI
  -> multi-channel complex IQ tensor
  -> range compression
  -> Doppler processing
  -> angle beamforming
  -> detection
  -> tracking
  -> display
```

### Key Architecture Decision

For V1, we chose a **waveform-level end-to-end educational simulator** rather than a full multi-fidelity Radar Toolbox clone.

Chosen V1 scope:

- fixed 2D scan schedule;
- one dwell / CPI at a time;
- rectangular planar array;
- LFM pulse waveform;
- ideal point targets;
- AWGN;
- conventional digital beamforming;
- threshold-style detection;
- simple nearest-neighbor + Kalman tracking;
- notebook / matplotlib friendly display.

Explicitly deferred:

- clutter;
- jamming / interference;
- multipath;
- analog beamforming;
- adaptive beamforming;
- multiple / staggered PRF ambiguity resolution;
- closed-loop resource management;
- hardware I/O.

### Implemented Conceptual Data Flow

The current software implements this end-to-end chain:

```text
ExperimentConfig
  -> RadarSystem + Scene
  -> ScriptedScanScheduler
  -> DwellTask
  -> synthesize_dwell()
  -> RawDwellData.iq
  -> process_dwell()
  -> RadarCube
  -> Detection
  -> NearestNeighborTracker
  -> Track
  -> display helpers
```

Raw dwell data shape:

```text
(num_y, num_x, num_pulses, num_fast_time)
```

Processed radar cube shape:

```text
(range, doppler, azimuth, elevation)
```

Detection output concept:

```text
(range_m, radial_velocity_mps, az_deg, el_deg, snr_db, time_s, dwell_id)
```

Track state concept:

```text
(x, y, z, vx, vy, vz)
```

Coordinate convention:

- radar at origin;
- `x` = boresight / forward;
- `y` = right;
- `z` = up;
- azimuth rotates in the `x-y` plane;
- elevation is positive upward.

### Implemented Modules

Current package modules under `src/radar_basics`:

| Module | Role |
| --- | --- |
| `core.py` | Physical constants, dB conversion, coordinate transforms, radial velocity. |
| `config.py` | YAML parsing, config dataclasses, `build_radar_system()`, `build_scene()`. |
| `scenario.py` | `PointTarget`, `Scene`, `TargetSnapshot`; constant-velocity truth model. |
| `radar.py` | `RectangularArray`, `LfmPulseWaveform`, `RadarSystem`; steering vectors and radar derived metrics. |
| `scheduler.py` | `DwellTask`, `ScriptedScanScheduler`; fixed 2D beam-grid scan. |
| `synthesis.py` | `synthesize_dwell()`; waveform-level IQ generation. |
| `processing.py` | `range_compress()`, `doppler_process()`, `beamform_angle_grid()`, `process_dwell()`. |
| `detection.py` | `Detection`, `detect_radar_cube()`; threshold detector with local peak suppression. |
| `tracking.py` | `Track`, `NearestNeighborTracker`; nearest-neighbor association + constant-velocity Kalman filter. |
| `display.py` | Matplotlib helpers for range-Doppler, scan beams, and air picture. |
| `experiment.py` | `run_experiment()` top-level API. |
| `data.py` | Shared data containers: `RawDwellData`, `RadarCube`, `ProcessedDwell`, `SimulationRunResult`. |
| `simulator.py` | Compatibility re-export for simulation entry points. |

### Public Entry Point

The main API is:

```python
from radar_basics import run_experiment

result = run_experiment("example_configs/architecture.yaml")
```

Useful result fields:

```python
result.tasks
result.raw_dwells
result.processed_dwells
result.tracks
```

### Example Config

Added / updated:

```text
example_configs/architecture.yaml
```

The example config currently runs:

- 4 x 4 planar array;
- 10 GHz carrier;
- 5 MHz LFM bandwidth;
- 16 pulses per dwell;
- 3 x 3 scan grid;
- one point target at 1500 m;
- 2 scan cycles;
- no thermal noise in the example, to keep first learning behavior deterministic.

### Human Documentation

Added:

```text
HUMAN.md
```

This document explains:

- what the architecture conceptually implements;
- module responsibilities;
- config structure;
- get-started commands;
- `run_experiment()` examples;
- display examples;
- current V1 limits.

### Tests and Verification

Added tests in:

```text
tests/test_config.py
tests/test_simulator.py
```

Covered scenarios:

- YAML config parsing;
- default half-wavelength array spacing;
- spherical target config to scene truth;
- fixed scan scheduler order;
- steering vector phase slope;
- LFM fast-time delay placement;
- Doppler slow-time phase progression;
- multiple-target linear superposition;
- AWGN power level;
- full processing chain detection;
- end-to-end scan and confirmed track;
- display helper rendering with matplotlib Agg backend.

Verification command:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; uv run pytest
```

Verified result:

```text
13 passed
```

Also manually checked:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; uv run python -c "from radar_basics import run_experiment; r=run_experiment('example_configs/architecture.yaml'); print(len(r.tasks), sum(len(d.detections) for d in r.processed_dwells), [(t.id, t.status) for t in r.tracks])"
```

Observed:

```text
18 18 [(1, 'confirmed')]
```

### Repository Notes

Current implementation follows the project rule:

```text
Use uv for dependency management and execution.
```

So Python should be run through:

```powershell
uv run ...
```

`.gitignore` was updated to ignore Python bytecode caches:

```text
__pycache__/
*.py[cod]
```

Important: the worktree already contained unrelated deleted / untracked files around old notebooks, old configs, old `__pycache__`, and Obsidian notes. Those were not intentionally cleaned up as part of this architecture implementation.

### Current Mental Model Alignment

The code now directly represents this radar understanding:

| Mental model concept | Software representation |
| --- | --- |
| 雷达看一个方向 | `DwellTask` |
| 扫描空域 | `ScriptedScanScheduler` |
| 目标 truth | `Scene`, `PointTarget`, `TargetSnapshot` |
| 二维孔径 | `RectangularArray` |
| 发射波形 | `LfmPulseWaveform` |
| 多通道 IQ | `RawDwellData.iq` |
| fast-time delay | `synthesize_dwell()` + `range_compress()` |
| slow-time phase rotation | `synthesize_dwell()` + `doppler_process()` |
| array-space phase slope | `steering_vector()` + `beamform_angle_grid()` |
| radar cube peak | `RadarCube` |
| detection | `Detection` |
| track | `Track`, `NearestNeighborTracker` |
| display | `display.py` plotting helpers |

### Near-Term Next Steps

Possible next development tasks:

1. Improve detection from simple thresholding toward CA-CFAR / OS-CFAR with explicit training and guard cells.
2. Add clutter models as a separate environment layer, not inside the core target model.
3. Add a notebook tutorial that walks from raw IQ to range-Doppler-angle cube.
4. Add visual checks for `plot_range_doppler()`, `plot_scan_beams()`, and `plot_air_picture()`.
5. Add measurement-level simulation path for faster tracking experiments.
6. Add resource-manager interface for future search-confirm-track scheduling.
7. Add more explicit documentation of units, signs, Doppler convention, and array indexing.

The main design constraint for future work:

> Keep the chain `truth -> dwell -> IQ -> cube -> detection -> track -> display` visible. New realism should enter through well-named layers, not by turning the simulator into one large opaque function.
