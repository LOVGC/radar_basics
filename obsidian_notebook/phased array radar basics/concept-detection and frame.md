这里两个词容易让人误解，因为它们是从不同抽象层来的。

## 1. Detection 是什么？

**Detection** 可以翻译成：

> **一次目标候选测量 / 一次检测点 / 一个雷达量测。**

它不是“已经确认的目标”，而是：

> **雷达在处理后的 range-Doppler-angle 数据里发现了一个超过门限的局部峰值。**

也就是说，雷达先处理原始 IQ 数据，得到类似：

$$
Y[R, f_D, \theta, \phi]
$$

然后在这个四维空间里做 CFAR / thresholding。如果某个 cell 或局部峰值足够强，就输出一个 detection。

一个 detection 通常长这样：

$$
z =
(R,\ v_r,\ \theta,\ \phi,\ \text{SNR},\ t,\ \text{beam id})
$$

也就是：

| 字段 | 含义 |
| --- | --- |
| $R$ | 距离 |
| $v_r$ | 径向速度 |
| $\theta$ | 方位角 |
| $\phi$ | 俯仰角 |
| SNR | 信噪比 / 检测强度 |
| $t$ | 这个量测发生的时间 |
| beam id | 来自哪个 dwell / beam position |

重要的是：

> **detection 不等于 target。**

一个 detection 可能是：

- 真实目标；
- 地杂波；
- 海杂波；
- 鸟群；
- 旁瓣进来的强回波；
- 干扰；
- noise false alarm；
- 多径 ghost target。

所以 detection 只是“这里有一个值得注意的测量点”。

然后 tracker 会把 detections 和已有 tracks 做关联：

$$
\text{detections} \rightarrow \text{data association} \rightarrow \text{track update}
$$

如果某个 detection 连续几次都能和运动模型一致，它才可能变成 confirmed track。

---

## 2. Track 是什么？

**Track** 是雷达对某个目标状态的持续估计。

它不是单次测量，而是多次 detections 经过时间滤波后的结果。

例如一个 track 的状态可以是：

$$
x =
[x,\ y,\ z,\ v_x,\ v_y,\ v_z]^T
$$

同时还有一个不确定性矩阵：

$$
P
$$

所以 track 表示：

> **我相信有一个目标在这个位置，以这个速度运动，并且我知道这个估计有多不确定。**

可以这样理解：

| 层级 | 含义 |
| --- | --- |
| raw IQ | 最底层复数采样 |
| radar cube | 距离-多普勒-角度处理结果 |
| detection | 某个 cell / peak 超过门限 |
| track | 多次 detections 关联和滤波后的目标状态 |

一句话：

> **detection 是瞬时证据；track 是时间上的信念。**

---

## 3. “帧”是什么意思？

我前面用“帧”这个词时，是借用了视觉系统里的说法，但在雷达里它有点不严谨。雷达里的“帧”可能有几种含义，要看上下文。

---

### 含义 1：一个 dwell / CPI 的处理帧

这是最底层的“帧”。

例如雷达指向某个方向，发射 64 个脉冲，形成一个 CPI。

这段数据是：

$$
X_l[m,p,n]
$$

其中：

- $m$：接收通道；
- $p$：第几个脉冲；
- $n$：fast-time sample；
- $l$：第几个 dwell。

这个 dwell 处理完后，可能输出一批 detections：

$$
\mathcal{D}_l
=
\{z_{l,1}, z_{l,2}, \dots\}
$$

这种意义下，“一帧”大概就是：

> **一次 dwell / CPI 的数据处理结果。**

---

### 含义 2：一次完整 scan / volume scan 的帧

如果雷达要扫描一个空域，它可能要执行多个 dwell：

$$
u_1,u_2,\dots,u_L
$$

每个 dwell 看一个角域。

所有 dwell 做完以后，才算完成一次 search volume 的刷新。

这时可以把：

$$
\mathcal{D}
=
\bigcup_{l=1}^{L}
\mathcal{D}_l
$$

看成一次 scan frame 的检测集合。

这种意义下，“一帧”是：

> **一次完整空域扫描产生的 detection set。**

---

### 含义 3：tracker 的更新帧

tracking 系统可能每隔一段时间收集当前可用的 detections，然后做一次更新。

这时候“帧”指的是：

$$
k \rightarrow k+1
$$

也就是第 $k$ 次 tracking update。

但在现代相控阵雷达里，更新不一定是严格同步的。因为不同目标可能在不同时间被不同 beam 更新。

所以更准确地说：

> **tracker 收到的是带时间戳的 detections，而不是像摄像机那样整齐的一张张图像帧。**

---

## 4. 用一个例子说明

假设雷达要扫 6 个 beam positions：

```text
dwell 1: 看 (-20°, 5°)
dwell 2: 看 (0°, 5°)
dwell 3: 看 (20°, 5°)
dwell 4: 看 (-20°, 15°)
dwell 5: 看 (0°, 15°)
dwell 6: 看 (20°, 15°)
```

每个 dwell 处理完，会得到一些 detections：

```text
dwell 1 detections: D1
dwell 2 detections: D2
dwell 3 detections: D3
...
dwell 6 detections: D6
```

如果你说 **dwell frame**，那就是某一个 $D_l$。

如果你说 **scan frame**，那就是：

$$
D_1 \cup D_2 \cup D_3 \cup D_4 \cup D_5 \cup D_6
$$

如果你说 **tracking frame**，那就是 tracker 在某个更新时间点拿到的一批 detections，用来更新 tracks。

---

## 5. 更准确的说法

为了避免混淆，最好少用“帧”，而改用更具体的词：

| 不严谨说法 | 更准确说法 |
| --- | --- |
| 一帧雷达数据 | 一个 dwell / 一个 CPI / 一个 scan cycle |
| 帧里的目标 | 该 dwell 或 scan 中的 detections |
| 连续帧跟踪 | 连续 dwell / scan 的 detections 关联成 tracks |
| 当前帧 | 当前 processing epoch / 当前 dwell / 当前 scan update |

---

最简洁地说：

> **Detection 是一次雷达处理后输出的候选目标量测，通常包含距离、径向速度、角度、SNR 和时间戳；它不一定是真目标。Track 是多次 detections 经过关联和滤波后形成的持续目标状态。“帧”在雷达里不是严格像相机图像那样的概念，可能指一个 dwell/CPI、一次完整 scan，或者 tracker 的一次更新周期。**
