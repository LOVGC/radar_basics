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
Completed through Step 5A.
Step 5B Doppler Processing has been added and is ready for learner review.
```

Recent additions:

- Step 5A now includes detailed `range_compress()` dissection.
- Step 5A includes plots comparing:
  - transmitted LFM chirp;
  - raw complex IQ before compression;
  - pulse/range compressed complex IQ;
  - compressed magnitude peak.
- Step 5B introduces Doppler processing along the pulse / slow-time dimension.

## Learner's Current Understanding

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

## Next Step

Next teaching target:

```text
Step 5B: Doppler Processing
```

Focus:

- Explain why Doppler processing operates along the pulse / slow-time dimension.
- Connect pulse-to-pulse phase progression to radial velocity.
- Show that `doppler_process(range_data, radar)` transforms:

  ```text
  range_data shape = (array_y, array_x, pulse, range_bin)
  ```

  into:

  ```text
  doppler_data shape = (array_y, array_x, range_bin, doppler_bin)
  ```

- Help the learner understand why the example target with `radial_velocity_mps = 0.0` lands near the 0 m/s Doppler bin.

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
- Current progress should be treated as Step 5A understood, Step 5B added but not yet learner-confirmed.
- The next teaching interaction should begin from Doppler processing, not restart from YAML/config.
