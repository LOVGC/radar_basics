# Radar Basics Simulation: Human Guide

这个项目的第一版实现的是一个 **waveform-level、端到端、教育用途的二维相控阵脉冲多普勒雷达仿真器**。

它不是追求真实雷达工程细节的完整复刻，而是把一个清晰的 mental model 写成可运行的软件结构：

```text
Scenario / Truth
  -> fixed 2D scan schedule
  -> one dwell / CPI at a time
  -> waveform-level multi-channel IQ: X[i, j, p, n]
  -> range compression
  -> Doppler processing
  -> angle beamforming
  -> detections
  -> tracks
  -> notebook-friendly display
```

最核心的概念是：

> 一个目标在原始雷达数据中表现为 fast-time delay、slow-time Doppler phase rotation、array-space phase slope。  
> 仿真器先生成这个复数张量，再沿这三个维度做匹配处理，把它变成 detection 和 track。

坐标系约定：

- 雷达在原点。
- `x` 是 boresight / forward。
- `y` 是右向。
- `z` 是上向。
- azimuth 在 `x-y` 平面内旋转。
- elevation 向上为正。
- 外部 YAML 配置使用 degree；内部计算使用 SI units 和 radians。

原始 IQ 数据 shape 固定为：

```text
(num_y, num_x, num_pulses, num_fast_time)
```

对应：

```text
array elevation index
array azimuth index
slow time / pulse index
fast time / sample index
```

处理后的 radar cube shape 是：

```text
(range, doppler, azimuth, elevation)
```

## What This Architecture Implements

这个实现把相控阵雷达分成几个层次：

1. **World / truth layer**
   场景里有点目标，每个目标有初始位置、速度和 RCS。目标按 constant-velocity 运动。

2. **Radar hardware abstraction layer**
   雷达有 carrier frequency、peak transmit power、二维 rectangular planar array、LFM pulse waveform、noise figure 和 system loss。

3. **Operation layer**
   雷达不是一次看完整空域，而是由 fixed scan scheduler 生成一串 `DwellTask`。每个 dwell 指向一个 azimuth/elevation look direction。

4. **Waveform synthesis layer**
   对每个 dwell，仿真器生成多阵元、多脉冲、fast-time 的复数 IQ 数据。点目标回波由 delay、Doppler phase、array steering phase 和 two-way power loss 共同决定。

5. **Signal processing layer**
   对 IQ 数据做 range compression、Doppler FFT 和 conventional digital beamforming，得到 range-Doppler-angle cube。

6. **Detection layer**
   在 radar cube 中寻找强峰值，输出：

   ```text
   (range_m, radial_velocity_mps, az_deg, el_deg, snr_db, time_s, dwell_id)
   ```

7. **Tracking layer**
   把 detection 转成 Cartesian position，用 nearest-neighbor association 和 constant-velocity Kalman filter 维护 tracks。

8. **Display layer**
   提供 notebook / matplotlib 友好的绘图函数，用于观察 range-Doppler map、scan beam grid 和 air picture。

## Module Map

| Module | Purpose |
| --- | --- |
| `radar_basics.core` | 物理常数、dB 转换、坐标转换、range/az/el 与 Cartesian 互转、radial velocity 计算。 |
| `radar_basics.config` | YAML schema、配置解析、配置 dataclass、`build_radar_system()`、`build_scene()`。 |
| `radar_basics.scenario` | `PointTarget`、`Scene`、`TargetSnapshot`。描述 ground truth 和目标运动。 |
| `radar_basics.radar` | `RectangularArray`、`LfmPulseWaveform`、`RadarSystem`。描述阵列、波形、雷达派生指标。 |
| `radar_basics.scheduler` | `DwellTask` 和 `ScriptedScanScheduler`。第一版只做固定二维 beam grid 扫描。 |
| `radar_basics.synthesis` | `synthesize_dwell()`。生成 waveform-level raw IQ tensor。 |
| `radar_basics.processing` | `range_compress()`、`doppler_process()`、`beamform_angle_grid()`、`process_dwell()`。 |
| `radar_basics.detection` | `Detection` 和 `detect_radar_cube()`。第一版使用 threshold detector + local peak suppression。 |
| `radar_basics.tracking` | `Track` 和 `NearestNeighborTracker`。实现简单 nearest-neighbor + constant-velocity Kalman tracking。 |
| `radar_basics.display` | `plot_range_doppler()`、`plot_scan_beams()`、`plot_air_picture()`。 |
| `radar_basics.experiment` | `run_experiment()`。端到端 API：load config、build radar/scene、scan、process、detect、track。 |
| `radar_basics.data` | `RawDwellData`、`RadarCube`、`ProcessedDwell`、`SimulationRunResult` 等公共数据结构。 |
| `radar_basics.simulator` | 兼容性入口，目前 re-export `run_experiment()` 和 `synthesize_dwell()`。 |

## Config Structure

主配置文件分成这些 top-level sections：

```yaml
radar:      # carrier, power, noise, loss
array:      # rectangular planar array geometry
waveform:   # LFM pulse waveform and CPI settings
scan:       # fixed beam grid
scene:      # point targets
processing: # angle grid, detector, tracker
run:        # scan cycles, random seed, raw-data storage
```

可以从示例开始：

```text
example_configs/architecture.yaml
```

## Get Started

先同步环境：

```powershell
uv sync --all-groups
```

跑测试：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; uv run pytest
```

运行示例仿真：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; uv run python -c "from radar_basics import run_experiment; r = run_experiment('example_configs/architecture.yaml'); print('dwells:', len(r.tasks)); print('detections:', sum(len(d.detections) for d in r.processed_dwells)); print('tracks:', [(t.id, t.status) for t in r.tracks])"
```

预期会看到类似：

```text
dwells: 18
detections: 18
tracks: [(1, 'confirmed')]
```

在 Python / notebook 中使用：

```python
from radar_basics import run_experiment
from radar_basics.display import plot_air_picture, plot_range_doppler, plot_scan_beams

result = run_experiment("example_configs/architecture.yaml")

print(f"num dwells: {len(result.tasks)}")
print(f"num detections: {sum(len(d.detections) for d in result.processed_dwells)}")
print(f"tracks: {[(track.id, track.status) for track in result.tracks]}")

first_dwell = result.processed_dwells[0]
all_detections = tuple(
    detection
    for dwell in result.processed_dwells
    for detection in dwell.detections
)

plot_scan_beams(result.tasks)
plot_range_doppler(first_dwell)
plot_air_picture(all_detections, result.tracks)
```

如果想直接看某个 dwell 的底层数据：

```python
from radar_basics import build_radar_system, build_scene, load_config, process_dwell, synthesize_dwell
from radar_basics.scheduler import ScriptedScanScheduler

config = load_config("example_configs/architecture.yaml")
radar = build_radar_system(config)
scene = build_scene(config)

scheduler = ScriptedScanScheduler(
    azimuths_deg=config.scan.azimuths_deg,
    elevations_deg=config.scan.elevations_deg,
    prf_hz=radar.waveform.prf_hz,
    num_pulses=radar.waveform.num_pulses,
)

task = scheduler.tasks()[0]
raw = synthesize_dwell(radar, scene, task)
processed = process_dwell(raw, radar, config.processing)

print(raw.iq.shape)                 # (num_y, num_x, num_pulses, num_fast_time)
print(processed.radar_cube.data.shape)  # (range, doppler, azimuth, elevation)
print(processed.detections)
```

## Current V1 Limits

第一版刻意保持简单：

- 支持 monostatic colocated TX/RX。
- 支持 rectangular planar array。
- 支持 narrowband steering。
- 支持 LFM pulse waveform。
- 支持 ideal point targets + AWGN。
- 支持 conventional digital beamforming。
- 支持 fixed scan grid。
- 支持 basic threshold detection 和 simple Kalman tracking。

暂时不包含：

- clutter；
- jamming / interference；
- multipath；
- analog beamforming；
- adaptive beamforming；
- multiple / staggered PRF ambiguity resolution；
- closed-loop resource management；
- real hardware I/O。

后续扩展时，建议仍然保持这条主线：

```text
truth -> dwell -> IQ -> cube -> detection -> track -> display
```

新增工程现实因素时，优先明确它进入哪一层，而不是直接把所有细节塞进一个巨大的 simulator function。
