可以。tracking problem 最清楚的 formulation 是：

```text
Given:
  a sequence of detections over time

Estimate:
  which detections belong to the same physical target,
  and what each target's current state is.
```

在雷达 pipeline 里：

```text
dwell 0 -> detections
dwell 1 -> detections
dwell 2 -> detections
...
```

每个 detection 是 single-time measurement：

```text
Detection = (range, radial_velocity, az, el, snr, time)
```

Tracking 要做的是把这些 single-time measurements 组织成 persistent objects：

```text
Track = target identity + state estimate over time
```

---

**核心问题**

Tracking 其实包含三个子问题：

```text
1. Data association
   哪些 detection 是同一个目标？

2. State estimation
   这个目标现在的位置和速度是多少？

3. Track management
   什么时候创建 track？
   什么时候确认 track？
   什么时候删除 track？
```

所以 tracking 不是单纯“保存 detections list”。保存历史只是其中一种 view。

---

**两个 Mental Models**

你现在混乱的地方，主要是因为 `track` 有两个合理含义。

**1. Association view**

从直觉上，一个 track 是：

```text
[detection_1, detection_2, detection_3, ...]
```

这些 detections 被认为来自同一个真实目标。

这个 view 很重要，因为 tracking 的第一步确实是：

```text
把 detections 串起来
```

**2. State-estimation view**

在代码实现里，一个 track 通常存成：

```text
state estimate + uncertainty
```

比如当前项目里：

```text
state_xyz_vxyz = [x, y, z, vx, vy, vz]
covariance     = uncertainty of that 6D state
```

也就是说，tracker 用历史 detections 不断更新一个 belief：

```text
目标现在大概在哪里？
目标现在大概怎么运动？
这个估计有多不确定？
```

所以：

```text
conceptual track:
  same-target detections over time

implementation Track:
  compressed belief about that target
```

---

**更正式一点**

假设每个时刻都有一组 detections：

```text
Z_t = {z_t1, z_t2, z_t3, ...}
```

每个 detection 是一个 measurement：

```text
z = (range, az, el, radial_velocity, snr)
```

背后真实世界里有一些目标状态：

```text
x_i(t) = [position, velocity]
```

Tracking problem 是估计：

```text
1. 有几个 targets？
2. 每个 detection 属于哪个 target？
3. 每个 target 当前 state 是什么？
```

难点是 detection 本身没有 identity。Detector 只说：

```text
这里有一个 target-like measurement
```

但它不说：

```text
这是 target 1 还是 target 2
```

这个 identity 是 tracker 维护出来的。

---

**当前代码里的简化版本**

`NearestNeighborTracker` 做的是一个简单版本：

```text
for each new dwell:
  1. predict existing tracks to current time
  2. find nearest detection for each track
  3. if close enough, update the track
  4. unmatched detections start new tracks
  5. tracks with too many misses are deleted
```

也就是：

```text
prediction
-> association
-> correction
-> creation/deletion
```

当前实现里的一个重要限制是：它只用 detection 的 position：

```text
range, az, el -> x, y, z
```

来更新 track，没有直接用 `radial_velocity_mps` 更新 velocity。

---

一句话总结：

> Tracking problem = 给定一串随时间出现的 detections，判断哪些 detections 属于同一个真实目标，并持续估计每个目标的 identity、position、velocity 和 uncertainty。