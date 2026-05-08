# Learning Session Instructions

This file records the tutorial plan, current learning progress, learner understanding, and teaching rules for `learning/learn_coding_myself.ipynb`.

Codex should use this file to continue teaching from the learner's current mental model instead of restarting from scratch.

## Update Rule

Codex should update this file when learning progress changes.

Update it when:

- a step is completed or clearly understood by the learner;
- a new step is added to `learning/learn_coding_myself.ipynb`;
- the learner develops a new summary or mental model;
- the learner identifies a knowledge gap or asks to explore a concept more deeply;
- the tutorial plan changes.

The purpose of this file is to help Codex track:

```text
tutorial outline
current progress
learner's understanding
learner's knowledge gaps
next teaching step
```

Codex should keep this file concise, accurate, and useful for continuation.

## Tutorial Goal

Guide the learner step by step through the `radar_basics` codebase by writing and discussing `learning/learn_coding_myself.ipynb`.

The learning style is interactive:

```text
write a small notebook section
learner runs and studies it
learner asks questions
Codex explores/explains
learner summarizes understanding
Codex records progress
continue to next step
```

The goal is for the learner to develop a clear mental model of the radar simulation pipeline.

## Tutorial Outline

Current high-level plan:

```text
Step 1: YAML is the experiment specification
Step 2: Config -> Python dataclass objects
Step 3A: Radar module
Step 3B: Scene module
Step 3C: Scheduler module
Step 4: One dwell raw IQ
Step 5A: Range compression / pulse compression
Step 5B: Doppler processing
Step 5C: Angle beamforming
Step 6: Detection
Step 7: Full experiment + tracking
Step 8: Experiment variations
```

## Current Progress

Notebook:

```text
learning/learn_coding_myself.ipynb
```

Current status:

```text
Completed through Step 6.
Step 5C Angle Beamforming has been reviewed and wrapped up by the learner.
Step 6 Detection has been reviewed and wrapped up by the learner.
Step 7 Full experiment + tracking has been added and is ready for learner review.
Tutorial example target has been changed to azimuth 5 deg, elevation 3 deg, radial velocity +10 m/s.
```

Recent additions:

- Step 5A now includes detailed `range_compress()` dissection.
- Step 5A includes plots comparing:
  - transmitted LFM chirp;
  - raw complex IQ before compression;
  - pulse/range compressed complex IQ;
  - compressed magnitude peak.
- Step 5B introduces Doppler processing along the pulse / slow-time dimension.
- Step 5B now includes:
  - single-target raw IQ signal model connecting fast-time delay, slow-time phase rotation, and array-space phase pattern;
  - compact mathematical mental model for Doppler velocity estimation from slow-time phase slope;
  - line-by-line explanation of `doppler_process()`;
  - Doppler-bin table with frequency, radial velocity, and magnitude;
  - current moving-target Doppler plot;
  - toy nonzero-velocity slow-time signal and Doppler plot.
- Step 5C introduces angle beamforming from the full signal model:
  - raw IQ model -> range-focused model -> Doppler-focused model -> array snapshot model;
  - `beamform_angle_grid()` line-by-line code mapping;
  - array snapshot magnitude/phase plots, with clarification that magnitude may stay nearly flat while phase carries angle information;
  - off-boresight steering-vector phase demo to make the spatial phase ramp visible;
  - azimuth/elevation beamforming response plots.
- Step 5C was wrapped up with the learner's higher-level understanding that the simple radar signal model makes range, Doppler, and angle processing approximately separable and computationally practical.
- A Step 5C wrap-up markdown cell was appended to `learning/learn_coding_myself.ipynb`, organizing the learner's understanding of signal-model assumptions, separability, and why staged template matching is computationally practical.
- Step 6 introduces detection on the processed radar cube:
  - intro recap summarizing the pipeline before detection: config -> raw IQ -> range compression -> Doppler processing -> angle beamforming -> radar cube;
  - `RadarCube` construction from `cube_data` and physical axes;
  - `detect_radar_cube()` output as structured `Detection` objects;
  - manual dissection of power cube, background power, threshold power, candidate cells, and index-to-axis conversion;
  - explanation of `guard_cells` as simple non-maximum suppression around accepted detections.
  - note that the current zero-noise config can make threshold candidates numerous because the median background estimate is tiny.
  - detection visualization plots for range-Doppler power, angle power, candidate mask, and sorted power distribution.
  - learner asked where `config.processing` comes from; clarify that `config` is the `ExperimentConfig` created by `load_config(CONFIG_PATH)` in Step 2, and `.processing.detector` is parsed from the YAML `processing.detector` section.
  - Step 6 wrap-up markdown cell summarizes detection as processed-cube cell classification plus index-to-physical-measurement conversion.
- Step 7 introduces full experiment + tracking:
  - `run_experiment(CONFIG_PATH)` as the top-level pipeline entrypoint;
  - multiple `DwellTask`s over scan time, each producing processed dwells and detections;
  - detections per dwell and final track summary;
  - tracking formulation as cross-time association and state estimation;
  - `Detection(range, radial_velocity, az, el, snr, time)` versus `Track(id, state_xyz_vxyz, covariance, status, hits, misses)`;
  - note that the current toy tracker updates from Cartesian position only and does not directly use detection radial velocity in `_correct()`.
  - from-scratch minimal two-target tracking example added under Step 7:
    - intentionally does not use `NearestNeighborTracker`, `Track`, `Detection`, or `TrackerConfig`;
    - uses plain lists/dicts plus NumPy in 2D with `state = [x, y, vx, vy]`;
    - demonstrates data association, state estimation, and track management step by step across five dwells;
    - target A persists, target B disappears and is deleted after too many misses.

## Learner's Current Understanding

The learner's current radar working mental model:

```text
transmitter
-> sends a waveform / beam into space
-> the waveform may or may not illuminate an object
-> an illuminated object can reflect an echo
-> receiver records the returned signal as raw IQ over one dwell / CPI
-> signal processing extracts structured information from raw IQ
-> detection reports target-like measurements
```

Important correction to preserve:

```text
One dwell first produces raw IQ data.
The detector's direct input is not raw IQ, but the processed radar cube produced from that dwell.
```

The learner currently understands the main pipeline as:

```text
YAML spec
-> Python dict
-> dataclass config
-> runtime objects: radar / scene / tasks
-> synthesize_dwell()
-> raw IQ data
-> range compression
-> Doppler processing
-> angle beamforming
```

Key mental models established:

- YAML is a human-readable simulation specification.
- `raw_config` and `ExperimentConfig` represent the same simulation parameters in more Python-friendly structures.
- `radar`, `scene`, and `tasks` define the simulation stage:

  ```text
  radar: how the radar transmits and receives
  scene: what exists in the truth world
  task: where the radar looks during this dwell
  ```

- `synthesize_dwell(radar, scene, task)` makes these objects interact and produces one CPI of waveform-level raw IQ data.
- `raw.iq` has shape:

  ```text
  (array_y, array_x, pulse, fast_time)
  ```

- The dimensions carry different physical information:

  ```text
  array dimensions -> angle / spatial phase
  pulse dimension  -> Doppler / velocity
  fast-time        -> range / delay
  ```

- The learner has formed a higher-level template-matching mental model:

  ```text
  matched filtering, Doppler processing, and beamforming are all inner-product projections.
  The measurement is compared against a family of known templates.
  The matching template gives a large coherent sum; mismatched templates tend to cancel or be suppressed.
  ```

- The learner now understands the core signal-processing pipeline as relying on an approximately separable signal model:

  ```text
  fast-time structure       -> range / delay
  pulse slow-time structure -> Doppler / radial velocity
  array-channel structure   -> angle / spatial phase
  ```

  This separability is what makes the engineering problem tractable: instead of matching over one large joint range-velocity-angle template space, the code can do smaller projections along fast-time, slow-time, and array dimensions.

- Important nuance to preserve in future teaching:

  ```text
  The dimensions are not absolutely independent in all radar regimes.
  The tutorial is using a simplified model where the coupling is small enough to process range, Doppler, and angle in stages.
  ```

- Signal-model assumptions the learner has identified or partially identified:

  ```text
  far-field / plane-wave approximation across the array
  narrowband spatial array model
  point-target style scatterer model
  limited motion over one CPI, so target energy mostly stays in one range/Doppler neighborhood
  ```

## Range Compression Understanding

The learner's current understanding:

```text
Range compression / pulse compression is matched filtering along the fast-time axis.
For each antenna element and each pulse, the received delayed LFM chirp is matched-filtered by the transmitted chirp.
This compresses a wide delayed chirp into a narrow range peak, making target range easier to localize.
```

More concretely:

```text
raw.iq[array_y, array_x, pulse, fast_time]
```

Range compression operates like:

```text
for each array element:
  for each pulse:
    matched filter along fast_time
```

It does not estimate velocity or angle yet.

## Angle Beamforming Understanding

The learner's current understanding:

```text
After beamforming, cube_data has shape:

(range, doppler, az, el)

For a fixed range bin and Doppler bin, the az/el slice is an angle response map.
If a target is present in that range-Doppler cell, the peak magnitude/power over az/el indicates the likely target direction.
If no target is present in that range-Doppler cell, the az/el slice may still contain noise or sidelobes, but should not show a strong reliable peak above the detection threshold.
```

## Detection Understanding

The learner's current understanding:

```text
Detection is formulated as:

given a processed radar cube, decide which cells correspond to target-like returns and which cells correspond to background.

The core assumption is that cells containing a target should have larger power than background cells.
```

For the current tutorial pipeline, this means:

```text
one dwell of received raw IQ
-> range compression
-> Doppler processing
-> angle beamforming
-> processed radar cube
-> detector
-> detections
```

So the detector output is a set of detections from one processed dwell, not the full raw receive data itself.

The learner also understands that the processed radar cube axes are already a physical parameter space:

```text
range axis    -> range_m
Doppler axis  -> radial_velocity_mps
az axis       -> az_deg
el axis       -> el_deg
```

An accepted cube cell therefore becomes a measurement by mapping its index through `radar_cube.axes`. The power at that cell gives detection strength / SNR information.

The learner understands `detect_radar_cube()` as a deliberately simple, heuristic detector:

```text
power cube
-> estimate background power using the median of positive cells
-> threshold by SNR
-> collect candidate cells
-> keep local maxima
-> suppress nearby cells with guard-cell neighborhoods
-> convert accepted cube indices into physical Detection objects
```

Important nuance:

```text
The current guard_cells implementation is mainly local-maximum / non-maximum suppression around accepted detections.
It helps avoid reporting many adjacent cells from the same target response as separate detections.
It is not a full CFAR-style training/guard-cell background estimator.
```

The learner also understands that this detector uses only one processed radar cube; temporal association or track-level evidence comes later in tracking. The detector is intentionally rule-based / heuristic, not a Bitter Lesson-style learned or scaled approach.

## Tracking Understanding

The learner's current conceptual intuition:

```text
A track can be viewed as a sequence/history of detections that are believed to belong to the same target.
```

Important implementation distinction in this project:

```text
The `Track` dataclass does not store the full list of associated detections.
It stores a filtered state estimate plus uncertainty and lifecycle counters.
```

Current `Track` state representation:

```text
state_xyz_vxyz.shape = (6,)
state_xyz_vxyz = [x, y, z, vx, vy, vz]

covariance.shape = (6, 6)
```

Mental model to preserve:

```text
Detection history view:
  raw evidence over time
  [detection_1, detection_2, detection_3, ...]

State-estimation view used by this code:
  compressed belief about the target
  [x, y, z, vx, vy, vz] + covariance + status/hits/misses
```

So in future teaching, distinguish:

```text
tracking association problem:
  decide which detections belong to the same target

track object in this implementation:
  current estimated target state, not the complete detection history
```

The learner is clarifying tracking as three linked problems:

```text
1. Data association:
   Which detections belong to the same physical target?

2. State estimation:
   What is each target's current state, e.g. position and velocity?

3. Track management:
   When should a track be created, confirmed, marked missed, or deleted?
```

Step 7 now includes a minimal from-scratch example to make these three problems visible without relying on the existing tracker implementation or heavy abstraction layers.

## Next Step

Next teaching target:

```text
Step 7: Full experiment + tracking
```

Focus:

- Review the newly added Step 7 cells with the learner.
- Connect `run_experiment()` to the lower-level functions already studied: `synthesize_dwell()`, `process_dwell()`, and `detect_radar_cube()`.
- Explain how detections become structured measurements for tracking.
- Explain `NearestNeighborTracker` conceptually as prediction, nearest-neighbor association, correction, new-track creation, and stale-track deletion.
- Keep the first tracking pass conceptual before diving into line-by-line Kalman filter implementation details.

## Teaching Rules

- Continue in small interactive steps.
- Do not write a full tutorial all at once.
- Prefer 2-4 notebook cells per teaching step.
- After each step, pause for learner questions and learner summary.
- When the learner gives a summary, help refine it and then record the refined understanding here when useful.
- Use diagrams or plots when they clarify signal processing concepts.
- Keep explanations tied to the actual code in `src/radar_basics`.
- Use `uv run` for Python execution.
- Preserve UTF-8 when editing notebook or Markdown files containing Chinese text.

## Assumptions

- `learning/AGENTS.md` is meant to be maintained as a living learning-state file.
- Current progress should be treated as Step 5C understood enough to proceed; Step 6 has been added but not yet learner-confirmed.
- The next teaching interaction should review detection, not restart from YAML/config or angle beamforming.
