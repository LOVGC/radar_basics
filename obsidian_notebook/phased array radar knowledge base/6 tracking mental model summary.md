# Tracking mental model summary

## 1. 最直觉的理解

雷达不是一次性看完整个世界，而是一个 dwell 一个 dwell 地输出 measurements。

每个 dwell 的 pipeline 可以理解成：

```text
raw IQ
-> processed radar cube
-> detections
```

一个 detection 可以先简化成：

```text
z = (p, t)
```

意思是：在时间 `t`，雷达在空间位置 `p` 测到一个 target-like point。

关键问题是：detection 没有 identity。Detector 只说“这里有一个点”，但不说“这是 target A 还是 target B”。

所以 tracking 最直觉的任务是：

```text
把不同 dwell 里属于同一个真实目标的 detections 串起来。
```

---

## 2. Tracking problem formulation

Tracking 的输入是随时间到来的 detection sets：

```text
dwell 1: {z_11, z_12, ...}
dwell 2: {z_21, z_22, ...}
dwell 3: {z_31, z_32, ...}
...
```

Tracking 要估计：

```text
1. 有几个 targets？
2. 每个 detection 属于哪个 target / track？
3. 每个 target 当前 state 是什么？
```

这里的 target state 通常是位置和速度：

```text
2D: [x, y, vx, vy]
3D: [x, y, z, vx, vy, vz]
```

所以一句话：

> Tracking = 在没有 identity 的 detections 序列上，用运动模型和测量模型维护每个目标的 identity、position、velocity 和 lifecycle。

---

## 3. 三个核心子问题

### Data association

问题：

```text
这个 detection 属于哪条 track？
```

基本思路：

```text
已有 track 先预测当前时刻的位置。
新的 detection 如果离预测位置足够近，就可能属于这条 track。
```

最简单的规则是 gating + nearest neighbor：

```text
只看 gate 内的 detections；
选择距离 predicted position 最近的 detection。
```

### State estimation

问题：

```text
这个 target 现在在哪里？怎么运动？
```

Track 不一定保存完整 detection history。工程实现里，track 经常保存一个 compressed belief：

```text
state estimate + uncertainty + lifecycle counters
```

例如：

```text
state = [x, y, vx, vy]
```

每次新的 detection 关联成功后，tracker 用 measurement 修正 state。

### Track management

问题：

```text
什么时候创建 track？
什么时候确认 track？
什么时候删除 track？
```

常见 lifecycle：

```text
new detection
-> tentative track
-> confirmed track
-> missed / coasting
-> deleted
```

原因是 detection 里会有 false alarms，也会有 missed detections。不能一个点就完全相信，也不能一次漏检就立刻删除。

---

## 4. Track 的两个 mental models

### Association view

从直觉上，track 是同一个目标的一串 detections：

```text
track A = [(p1, t1), (p2, t2), (p3, t3), ...]
```

这个 view 帮助理解 identity：

```text
这些点被认为来自同一个真实目标。
```

### State-estimation view

在实现里，track 通常不是完整 list，而是当前状态估计：

```text
track = target identity + state estimate + uncertainty + status
```

例如：

```text
state = [x, y, vx, vy]
```

这个 view 帮助理解 tracker 为什么要 predict / update。

两种 view 不矛盾：

```text
conceptual track:
  same-target detections over time

implementation track:
  compact state estimate of that target
```

---

## 5. 最小 tracking loop

每来一个 dwell，tracker 通常做：

```text
1. Predict
   用运动模型把已有 tracks 预测到当前时间。

2. Associate
   把当前 detections 分配给已有 tracks。

3. Update
   用 matched detection 修正 track state。

4. Initiate
   unmatched detections 可能创建 new tracks。

5. Delete
   misses 太多的 tracks 被删除。
```

这就是很多 tracking algorithms 的共同骨架。复杂算法主要是在 association、state estimation、track management 这些环节上更强。

---

## 6. 更抽象的 view

Tracking 可以看成一个 sequential inference problem：

```text
hidden variables:
  true target states and identities

observations:
  detections

prior:
  motion model

likelihood:
  measurement model
```

运动模型是对目标怎么动的先验。测量模型描述真实目标会产生什么样的 detection。

更完整的 tracking 要处理：

```text
detections = true detections + false alarms - missed detections
```

因此，tracking 不只是“把点连成线”，而是在 noisy / incomplete / ambiguous measurements 上持续维护目标的 identity 和 state。

---

## 7. 当前阶段的一句话总结

> Tracking 是把多个 dwell 中没有 identity 的 detections，根据时间连续性和运动模型 association 到 persistent tracks 上，并持续估计每个目标的位置、速度和 lifecycle。

