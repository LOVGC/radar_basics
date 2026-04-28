
下面是一份按 **abstraction level 从高到低** 组织的总结。

---

# 0. 一句话总图景

**二维相控阵 PD 雷达 = 可编程孔径 + 可编程波形 + 多维相干信号处理 + 实时资源管理。**

它不是“拍一张图”，而是反复执行下面这个闭环：

$$
\text{选择任务}
\rightarrow
\text{选择波束/波形/PRF/CPI}
\rightarrow
\text{发射}
\rightarrow
\text{接收多通道 IQ}
\rightarrow
\text{距离-速度-角度处理}
\rightarrow
\text{检测/跟踪}
\rightarrow
\text{决定下一次看哪里}
$$

最核心的 mental image 是：

> **一个目标在雷达原始数据中表现为：fast time 上的延迟，slow time 上的相位旋转，array space 上的相位斜率。**

对应：

| 数据维度 | 物理量 | 处理方式 |
|---|---|---|
| fast time | 距离 $R$ | pulse compression / matched filtering |
| slow time | 径向速度 $v_r$ / Doppler | Doppler FFT / Doppler filter bank |
| array space | 方位角、俯仰角 | beamforming / angle estimation |

---

# 1. 最高层：雷达是一个 resource-managed sensing system

现代相控阵雷达不是简单地“扫一圈”。它本质上是一个实时调度系统。

它要在有限资源下决定：

- 看哪个方向；
- 用什么波形；
- 用什么 PRF；
- 用多少脉冲；
- dwell 多久；
- 发射波束多宽；
- 接收波束怎么形成；
- 这次任务是 search、confirm、track，还是 classification / fire-control support。

因此现代 AESA 的核心能力不只是“波束转得快”，而是：

> **在有限时间、功率、孔径、热预算、处理算力下，动态分配雷达资源。**

常见任务模式包括：

| 模式 | 目的 |
|---|---|
| volume search / sector search | 搜索未知目标 |
| cued search | 根据外部 cue 搜索小区域 |
| confirm / acquisition | 确认疑似 detection |
| track-while-scan | 一边搜索，一边更新已有航迹 |
| dedicated track | 对重要目标高频精跟踪 |
| classification / discrimination | 判断目标类型或区分 warhead / debris / decoy |
| engagement support | 为武器系统提供精确跟踪和火控支持 |

所以一个更高级的 mental model 是：

> **搜索是发现目标，跟踪是维护目标状态，资源管理是决定下一次雷达资源应该用在哪里。**

---

# 2. Operation level：一次 dwell / CPI 是基本操作单元

我们讨论的“看一个方向”，专业上通常叫一次：

$$
\text{dwell}
$$

如果这个 dwell 里发射一串相干脉冲，用于 Doppler processing，那么这段时间也叫：

$$
\text{CPI: coherent processing interval}
$$

一次典型 dwell 可以概括为：

1. **选择 look direction**  
   例如选择一个方位角和俯仰角：

$$
u_l = (\theta_l,\phi_l)
$$

2. **设置 transmit beamforming weights**  
   给发射阵列配置相位/幅度权重，使发射方向图主瓣指向 $u_l$。

3. **发射一串 pulse train**  
   发射波形 $s_l(t)$，PRF 为 $\text{PRF}_l$，脉冲数为 $P_l$。

4. **目标和杂波散射回波**  
   目标、地面、海面、天气等散射体把入射电磁波散射回来。

5. **接收阵列采样回波**  
   多个接收阵元或子阵得到多通道复数 IQ 数据。

6. **接收波束形成**  
   对接收阵列数据做 analog beamforming 或 digital beamforming。

7. **距离-多普勒-角度处理**  
   做 range compression、Doppler processing、beamforming / angle estimation。

8. **检测和跟踪**  
   在 processed radar cube 里做 CFAR detection，再更新 tracks。

一句话：

> **一个 dwell 不是看一个数学上的“角度点”，而是用一个有限宽度的 two-way beampattern 看一个小角域。**

---

# 3. 发射波束和接收波束的区别

## 3.1 发射波束：塑造出去的电磁场

发射端控制每个阵元的相位/幅度，使得某个方向上的发射波相干叠加。

发射方向图可以写成：

$$
B_t(u) = a_t^T(u) w_t
$$

其中：

- $u=(\theta,\phi)$：空间方向；
- $a_t(u)$：发射阵列 steering vector；
- $w_t$：发射权重；
- $B_t(u)$：发射方向图的复响应。

直观理解：

> **发射波束决定“往哪里照”。**

---

## 3.2 接收波束：对进来的回波做空间滤波

接收端不能改变回波从哪里来。回波已经由目标散射并传播回来了。

接收波束形成做的是：

> **对不同阵元接收到的复数信号加权求和，使某个方向来的波在合成输出中相干增强，其他方向来的波相对减弱。**

接收波束形成：

$$
y = w_r^H x
$$

其中：

- $x$：阵列接收向量；
- $w_r$：接收权重；
- $y$：波束形成后的输出。

接收方向图：

$$
B_r(u) = w_r^H a_r(u)
$$

所以：

> **接收波束不是控制回波，而是定义阵列对不同入射方向的响应。**

更专业地说：

> **receive beamforming = spatial matched filtering。**

---

## 3.3 发射和接收合起来：two-way beampattern

单基地雷达中，一个方向的总角向响应大致由发射和接收共同决定：

$$
B_2(u)=B_t(u)B_r(u)
$$

功率响应：

$$
G_2(u)=|B_t(u)|^2 |B_r(u)|^2
$$

所以：

> **发射波束决定哪里被照亮；接收波束决定从哪里来的回波被有效合成。**

---

# 4. 数据层：雷达采集的是复数张量，不是普通图像

对于二维相控阵 PD 雷达，原始数据可以想成：

$$
X[i,j,p,n]
$$

其中：

| 维度 | 含义 |
|---|---|
| $i,j$ | 二维接收阵列中的阵元位置 |
| $p$ | 第几个脉冲，slow time |
| $n$ | 单个脉冲内的采样点，fast time |

也可以简写成：

$$
X[m,p,n]
$$

其中 $m$ 是接收通道索引。

所以最底层数据结构是：

$$
\text{array channel}
\times
\text{pulse index}
\times
\text{fast-time sample}
$$

也就是：

> **每个阵元，在每个脉冲上，都采了一条复数 IQ 波形。**

处理后，概念上得到：

$$
Y[R, f_D, \theta, \phi]
$$

或者：

$$
Y[R, v_r, \theta, \phi]
$$

这就是 range-Doppler-angle radar cube。

最终检测输出通常是：

$$
(R,\ v_r,\ \theta,\ \phi,\ \text{SNR},\ t,\ \text{beam id})
$$

再往上，tracking 会把多帧 detections 融合成：

$$
(x,\ y,\ z,\ v_x,\ v_y,\ v_z)
$$

---

# 5. 物理层：目标在数据里是什么样？

对一个目标，雷达主要测到四类参数：

$$
(R,\ v_r,\ \theta,\ \phi)
$$

其中：

$$
\tau = \frac{2R}{c}
$$

$$
f_D = \frac{2v_r}{\lambda}
$$

含义是：

| 参数 | 数据表现 |
|---|---|
| 距离 $R$ | 回波延迟 $\tau$ |
| 径向速度 $v_r$ | Doppler 频率 $f_D$ |
| 方位角 $\theta$ | 阵列水平相位斜率 |
| 俯仰角 $\phi$ | 阵列垂直相位斜率 |

所以最核心的目标模型是：

> **一个散射点 = 延迟后的发射波形 × 脉冲间相位旋转 × 阵列空间相位模式 × 复散射系数。**

---

# 6. 数学建模：单目标信号模型

设第 $l$ 个 dwell 使用发射波形 $s_l(t)$，目标方向为：

$$
u_q=(\theta_q,\phi_q)
$$

目标距离为 $R_q$，径向速度为 $v_{r,q}$。

对应：

$$
\tau_q=\frac{2R_q}{c}
$$

$$
f_{D,q}=\frac{2v_{r,q}}{\lambda}
$$

第 $m$ 个接收阵元、第 $p$ 个脉冲、fast time 为 $t$ 的接收信号可以写成：

$$
x_{l,m}[p,t]
=
\alpha_q
B_{t,l}(u_q)
a_{r,m}(u_q)
s_l(t-\tau_q)
e^{j2\pi f_{D,q}pT_{\text{PRI},l}}
+
n_{l,m}[p,t]
$$

其中：

| 项 | 含义 |
|---|---|
| $\alpha_q$ | 目标复散射系数，包含 RCS、传播相位、损耗等 |
| $B_{t,l}(u_q)$ | 第 $l$ 个 dwell 的发射波束在目标方向的增益 |
| $a_{r,m}(u_q)$ | 目标方向在第 $m$ 个接收阵元上的相位 |
| $s_l(t-\tau_q)$ | 延迟后的发射波形，对应距离 |
| $e^{j2\pi f_{D,q}pT_{\text{PRI},l}}$ | pulse-to-pulse 相位旋转，对应 Doppler |
| $n_{l,m}[p,t]$ | 噪声、杂波、干扰等 |

这个公式就是整个 mental model 的核心。

---

# 7. 多目标 / 杂波场景模型

真实场景中有很多散射体，所以信号是叠加：

$$
x_{l,m}[p,t]
=
\sum_{q=1}^{Q}
\alpha_q
B_{t,l}(u_q)
a_{r,m}(u_q)
s_l(t-\tau_q)
e^{j2\pi f_{D,q}pT_{\text{PRI},l}}
+
c_{l,m}[p,t]
+
i_{l,m}[p,t]
+
n_{l,m}[p,t]
$$

其中：

- $q$：目标或散射体编号；
- $c$：clutter；
- $i$：interference / jamming；
- $n$：thermal noise。

更抽象地看：

$$
X_l
\approx
\sum_{q=1}^{Q}
\beta_q
\,a(u_q)
\otimes
d(f_{D,q})
\otimes
r(\tau_q)
+
N
$$

其中：

| 向量 | 含义 |
|---|---|
| $a(u_q)$ | 阵列 steering vector，描述角度 |
| $d(f_{D,q})$ | Doppler steering vector，描述速度 |
| $r(\tau_q)$ | delayed waveform，描述距离 |
| $\beta_q$ | 复幅度 |
| $N$ | 噪声、杂波、干扰、建模误差 |

这句话非常重要：

> **雷达数据可以看成许多由距离、速度、角度参数化的复数模板的叠加。雷达处理就是把数据投影到这些模板上，寻找匹配峰值。**

---

# 8. 阵列 steering vector

如果第 $m$ 个阵元的位置是 $r_m$，方向 $u$ 是单位向量，那么常见的 steering vector 元素为：

$$
a_m(u)
=
e^{-j\frac{2\pi}{\lambda}r_m^T u}
$$

符号正负取决于约定，但物理意义不变：

> **不同方向的来波会在阵列上形成不同的相位斜率。**

二维平面阵列中，阵列在水平和垂直两个方向都有空间采样，因此可以估计：

- azimuth；
- elevation。

所以二维相控阵的本质是：

> **在二维孔径上采样入射波前，并从二维空间相位斜率中估计方向。**

---

# 9. 一个 dwell 的信号处理链

一个 dwell 的原始数据：

$$
X_l[m,p,t]
$$

要被处理成：

$$
Y_l[R,f_D,u]
$$

其中 $u=(\theta,\phi)$。

常见处理链如下。

---

## 9.1 Range compression：fast time 上匹配延迟

对每个接收通道、每个脉冲，和发射波形做 matched filtering：

$$
z_{l,m}[p,\tau]
=
\int
x_{l,m}[p,t]s_l^*(t-\tau)dt
$$

这一步叫：

- matched filtering；
- pulse compression；
- range compression。

输出是 range bins。

核心关系：

$$
\Delta R \approx \frac{c}{2B}
$$

带宽越大，距离分辨率越好。

---

## 9.2 Doppler processing：slow time 上匹配相位旋转

对同一个 range bin，沿 pulse index 做 FFT：

$$
Z_{l,m}[\tau,f_D]
=
\sum_{p=0}^{P-1}
z_{l,m}[p,\tau]
e^{-j2\pi f_D pT_{\text{PRI}}}
$$

这一步叫：

- Doppler FFT；
- Doppler filter bank；
- MTD processing。

输出是 range-Doppler map。

速度分辨率近似为：

$$
\Delta v \approx \frac{\lambda}{2T_{\text{CPI}}}
$$

CPI 越长，Doppler 分辨率越好。

---

## 9.3 Beamforming / angle processing：array space 上匹配相位斜率

对每个 range-Doppler cell，拿到一个阵列向量：

$$
Z_l[:,\tau,f_D]
$$

对方向 $u$ 做接收波束形成：

$$
Y_l[\tau,f_D,u]
=
w_r^H(u) Z_l[:,\tau,f_D]
$$

如果使用 conventional beamforming：

$$
w_r(u)=a_r(u)
$$

则：

$$
Y_l[\tau,f_D,u]
=
a_r^H(u)Z_l[:,\tau,f_D]
$$

这一步把 array channel 转换成 angle bins。

角分辨率粗略受孔径限制：

$$
\Delta \theta \sim \frac{\lambda}{D}
$$

---

## 9.4 Detection：CFAR 检测

在 range-Doppler-angle cube 中寻找局部峰值。

通常不是用固定门限，而是用 CFAR：

$$
|Y|^2 > \alpha \hat{P}_{\text{local background}}
$$

含义是：

> **目标不是绝对亮就行，而是要相对于周围背景显著亮。**

常见 CFAR：

- CA-CFAR；
- GO-CFAR；
- SO-CFAR；
- OS-CFAR；
- clutter-map CFAR。

---

## 9.5 Tracking：从 detections 到 tracks

dwell 处理完得到 detections：

$$
\mathcal{D}_l
=
\{(R,\ v_r,\ \theta,\ \phi,\ \text{SNR})\}
$$

tracking 模块会做：

- coordinate transform；
- data association；
- track initiation；
- track update；
- track deletion；
- maneuver handling；
- covariance management。

常见滤波器：

- Kalman filter；
- Extended Kalman filter；
- Unscented Kalman filter；
- IMM filter；
- JPDA；
- MHT。

一句话：

> **detection 是瞬时证据；track 是时间上的状态估计。**

---

# 10. 统一的处理公式

一个 dwell 的完整处理可以概念化为：

$$
Y_l(\tau,f_D,u)
=
\sum_m
\sum_p
\int
X_l[m,p,t]
a_m^*(u)
e^{-j2\pi f_DpT_{\text{PRI},l}}
s_l^*(t-\tau)
dt
$$

这个式子同时包含三种匹配：

| 匹配项 | 对应维度 | 得到什么 |
|---|---|---|
| $s_l^*(t-\tau)$ | fast time | range |
| $e^{-j2\pi f_DpT_{\text{PRI}}}$ | slow time | Doppler / velocity |
| $a_m^*(u)$ | array space | angle |

所以雷达信号处理可以总结为：

> **对原始多通道 IQ 数据，投影到由 $(R,f_D,\theta,\phi)$ 参数化的一组物理模板上。模板匹配得好，就出现峰值。**

---

# 11. Analog beamforming 和 digital beamforming

## Analog beamforming

在 ADC 之前，用硬件移相器、真延时、合成网络等把多个阵元信号合成为较少通道。

$$
\text{antenna signals}
\rightarrow
\text{phase shifters}
\rightarrow
\text{combiner}
\rightarrow
\text{ADC}
$$

特点：

- 前端就已经做了空间滤波；
- 数据率较低；
- 硬件相对省；
- 同时形成的接收波束数量有限；
- 原始阵元级信息可能丢失。

---

## Digital beamforming

每个阵元或子阵独立 ADC，然后在数字域加权：

$$
\text{antenna signals}
\rightarrow
\text{ADC per channel}
\rightarrow
\text{digital weights}
\rightarrow
\text{multiple beams}
$$

特点：

- 灵活性高；
- 可以同一份数据形成多个接收波束；
- 可以做更复杂的自适应处理；
- 数据率、ADC、同步、校准、算力要求更高。

关键点：

> **DBF 可以复用同一份接收数据形成多个空间滤波器，但不能凭空看到没有被发射波束有效照亮、没有足够 SNR 的方向。**

---

# 12. 扫描空域：不是一次性得到全空域 cube

扫描整个空域，本质上是把搜索区域离散成多个 beam positions。

设搜索区域为：

$$
\Omega_{\text{search}}
$$

选择一组 look directions：

$$
u_1,u_2,\dots,u_L
$$

每个方向对应一个 dwell：

$$
X_1,X_2,\dots,X_L
$$

每个 dwell 处理后得到局部 cube：

$$
Y_l[R,f_D,u]
$$

最后 detections 合并：

$$
\mathcal{D}
=
\bigcup_{l=1}^{L}
\mathcal{D}_l
$$

所以：

> **完整 volume scan 不是一次性产生一个瞬时全空域 radar cube，而是在时间上依次获得多个局部观测，再融合到统一坐标系中。**

---

# 13. 一个最小 PD 相控阵扫描例子

假设雷达要搜索一个二维角域：

$$
\theta \in [-30^\circ,30^\circ]
$$

$$
\phi \in [0^\circ,20^\circ]
$$

为了简单起见，选择 3 个方位 beam 和 2 个俯仰 beam：

$$
\theta \in \{-20^\circ,0^\circ,20^\circ\}
$$

$$
\phi \in \{5^\circ,15^\circ\}
$$

于是共有：

$$
L=3\times 2=6
$$

个 beam positions。

可以把 scan schedule 写成：

| dwell id | look direction |
|---|---|
| 1 | $(-20^\circ,5^\circ)$ |
| 2 | $(0^\circ,5^\circ)$ |
| 3 | $(20^\circ,5^\circ)$ |
| 4 | $(-20^\circ,15^\circ)$ |
| 5 | $(0^\circ,15^\circ)$ |
| 6 | $(20^\circ,15^\circ)$ |

---

## 13.1 第 $l$ 个 dwell 做什么？

对第 $l$ 个 look direction：

$$
u_l=(\theta_l,\phi_l)
$$

雷达设置发射权重：

$$
w_{t,l}
$$

形成发射波束：

$$
B_{t,l}(u)
$$

然后发射 $P$ 个脉冲。

接收端获得：

$$
X_l[m,p,n]
$$

其中：

- $m$：接收通道；
- $p=0,\dots,P-1$：脉冲编号；
- $n$：fast-time sample。

---

## 13.2 处理第 $l$ 个 dwell 的数据

处理链：

$$
X_l[m,p,n]
$$

先做 range compression：

$$
\rightarrow z_l[m,p,R]
$$

再做 Doppler FFT：

$$
\rightarrow Z_l[m,R,f_D]
$$

再做 beamforming / angle estimation：

$$
\rightarrow Y_l[R,f_D,\theta,\phi]
$$

然后做 CFAR：

$$
\rightarrow \mathcal{D}_l
$$

每个 detection 可能长这样：

$$
(R,\ v_r,\ \theta,\ \phi,\ \text{SNR},\ l)
$$

比如：

$$
(42\,\text{km},\ -180\,\text{m/s},\ 3^\circ,\ 6^\circ,\ 18\,\text{dB},\ \text{dwell 2})
$$

含义是：

> 在第 2 个 dwell 的观测中，雷达发现一个目标，距离约 42 km，径向速度约 $-180$ m/s，方向大约在 $(3^\circ,6^\circ)$。

---

## 13.3 六个 dwell 做完以后

把所有 detections 合并：

$$
\mathcal{D}
=
\mathcal{D}_1
\cup
\mathcal{D}_2
\cup
\dots
\cup
\mathcal{D}_6
$$

然后转换到统一坐标系：

$$
(R,\theta,\phi)
\rightarrow
(x,y,z)
$$

再和已有 tracks 做 data association：

$$
\text{detections}
\rightarrow
\text{track update}
$$

如果是新目标：

$$
\text{detection}
\rightarrow
\text{tentative track}
\rightarrow
\text{confirmed track}
$$

如果是已有目标：

$$
\text{detection}
+
\text{predicted track}
\rightarrow
\text{updated track}
$$

---

# 14. 最小扫描例子的显示方式

雷达可以在不同层级显示数据。

## 14.1 当前 dwell 的 range-Doppler map

对某个 beam position 显示：

$$
Y_l[R,f_D]
$$

横轴距离，纵轴 Doppler / velocity，亮点表示候选目标。

这是低层信号处理视角。

---

## 14.2 当前 dwell 的 angle-Doppler 或 range-angle map

如果接收端做了多波束 / angle estimation，可以显示：

$$
Y_l[\theta,\phi]
$$

或者：

$$
Y_l[R,\theta]
$$

这是局部角域视角。

---

## 14.3 全局 PPI / 3D air picture

把所有 dwell 的 detections 和 tracks 放到统一空间坐标：

$$
(x,y,z)
$$

然后显示：

- 目标位置；
- 航迹编号；
- 速度向量；
- track quality；
- threat level；
- search sector；
- beam schedule 状态。

这是系统级态势图。

---

# 15. Search、confirm、track 在扫描中的关系

最简单的 search-only schedule 是：

$$
u_1 \rightarrow u_2 \rightarrow \dots \rightarrow u_L
$$

不断重复。

但真实雷达通常是：

$$
\text{search dwell}
\rightarrow
\text{possible detection}
\rightarrow
\text{confirm dwell}
\rightarrow
\text{track initiation}
\rightarrow
\text{track update dwell}
$$

所以 schedule 可能长这样：

```text
search beam 1
search beam 2
search beam 3
confirm possible target A
search beam 4
track update target B
search beam 5
classification dwell target C
search beam 6
...
```

这就是 resource management 的作用。

它不断回答：

> **下一次 dwell 最值得用在哪里？**

---

# 16. 常见关键 trade-offs

## 16.1 距离分辨率

$$
\Delta R \approx \frac{c}{2B}
$$

带宽越大，距离分辨率越好。

---

## 16.2 速度分辨率

$$
\Delta v \approx \frac{\lambda}{2T_{\text{CPI}}}
$$

CPI 越长，速度分辨率越好，但 dwell 更长，scan 更慢。

---

## 16.3 角分辨率

$$
\Delta \theta \sim \frac{\lambda}{D}
$$

孔径越大，波长越短，角分辨率越好。

---

## 16.4 Scan time

如果有 $L$ 个 beam positions，每个 dwell 时间为 $T_{\text{dwell}}$，则：

$$
T_{\text{scan}}\approx L T_{\text{dwell}}
$$

想扫更大空域，需要更多 beams。  
想提高 SNR 或 Doppler 分辨率，需要更长 dwell。  
想更快刷新，就要牺牲覆盖、灵敏度或分辨率。

---

## 16.5 PRF ambiguity

PRF 影响 range ambiguity 和 Doppler ambiguity。

最大无模糊距离：

$$
R_{\text{unamb}}=\frac{c}{2\text{PRF}}
$$

PRF 越高，Doppler 能力越好，但 range ambiguity 更严重。  
PRF 越低，range ambiguity 较少，但 Doppler ambiguity 更严重。

所以真实雷达常用：

- multiple PRF；
- staggered PRF；
- ambiguity resolution。

---

# 17. 真实雷达中必须记住的工程现实

除了理想信号模型，真实雷达还受很多东西影响：

| 现象 | 影响 |
|---|---|
| clutter | 地面、海面、天气等强背景回波 |
| sidelobes | 强目标或杂波可能从副瓣进入 |
| grating lobes | 阵元间距过大导致空间混叠 |
| scan loss | 波束偏离阵面法线时增益下降 |
| calibration errors | 幅相误差破坏相干叠加 |
| dynamic range | 近处强杂波和远处弱目标共存 |
| beam squint | 宽带信号用相移器扫描时，不同频率波束方向不同 |
| jamming / interference | 电磁对抗环境下的干扰 |
| multipath | 多径反射导致虚假目标或测量偏差 |

所以：

> **真实雷达的困难不是只在噪声里找目标，而是在杂波、副瓣、模糊、干扰、动态范围和有限资源中稳定提取目标。**

---

# 18. 最终的 compact mental model

可以把整个相控阵 PD 雷达理解成五层。

## 第一层：系统层

雷达是一个实时任务调度系统：

$$
\text{search}
+
\text{confirm}
+
\text{track}
+
\text{classify}
+
\text{fire-control support}
$$

resource manager 决定下一次 dwell 怎么用。

---

## 第二层：操作层

一个 dwell / CPI 是基本观测单元：

$$
\text{choose beam}
\rightarrow
\text{transmit pulses}
\rightarrow
\text{receive IQ}
\rightarrow
\text{process}
\rightarrow
\text{detect}
$$

完整 scan 是一串 dwell 的 schedule。

---

## 第三层：数据层

原始数据是复数张量：

$$
X[m,p,n]
$$

处理后得到：

$$
Y[R,f_D,\theta,\phi]
$$

再变成：

$$
\text{detections}
\rightarrow
\text{tracks}
$$

---

## 第四层：物理层

目标在数据中表现为：

$$
\text{delay}
+
\text{Doppler phase rotation}
+
\text{array phase slope}
$$

也就是：

$$
(R,\ v_r,\ \theta,\ \phi)
$$

---

## 第五层：数学层

雷达观测可以看成：

$$
X
\approx
\sum_q
\text{complex amplitude}
\times
\text{range template}
\times
\text{Doppler template}
\times
\text{angle template}
+
\text{noise/clutter/interference}
$$

雷达处理就是做匹配投影：

$$
Y(\tau,f_D,u)
=
\sum_m
\sum_p
\int
X[m,p,t]
a_m^*(u)
e^{-j2\pi f_DpT_{\text{PRI}}}
s^*(t-\tau)
dt
$$

---

# 19. 最值得记住的版本

> **相控阵 PD 雷达每次 dwell 用一个发射波束照亮一个有限角域，接收阵列采集多通道复数 IQ 数据。目标回波在数据中表现为 fast-time 延迟、slow-time Doppler 相位旋转和 array-space 相位斜率。雷达处理沿这三个维度做匹配滤波：range compression 得到距离，Doppler processing 得到径向速度，beamforming / angle estimation 得到方向。CFAR 把 radar cube 中的峰值变成 detections，tracking 把多次 detections 变成稳定航迹。扫描整个空域不是一次性看完，而是 resource manager 调度一系列 beam positions，每个 dwell 产生一个局部观测，最后融合成全局 air picture。**

再压缩成一句：

> **发射是在“照亮哪里”，接收是在“听哪个方向”，处理是在“匹配距离、速度、角度模板”，资源管理是在“决定下一次该看哪里”。**
