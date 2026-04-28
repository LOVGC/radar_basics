# 二维相控阵雷达物理世界示意图作图 Prompt

## 详细中文 Prompt

画一张**科学插图 / 技术示意图 / 学术论文风格**的高质量三维物理场景图，主题是“二维相控阵雷达对空间目标的观测几何关系”。整体风格要求**简洁、专业、清晰、带数学标注、适合教材或研究报告插图**。背景干净，建议白底或浅灰底，线条清楚，标注规范。

### 1. 画面主体与构图

- 采用**三维透视视角**或**isometric engineering illustration（等轴测工程示意风格）**。
- 画面中心放置一个**二维平面相控阵天线（2D phased array）**，由许多个阵元组成，阵元均匀排列成一个**矩形网格**。
- 阵列位于三维坐标系中的某个平面上，推荐放在 **x-y 平面**，法向朝向 **+z 方向**。
- 阵列中的每个阵元可画成小方块、圆点或小贴片天线单元，规则排列，体现“二维阵列”的空间分布。
- 不需要把每个阵元都写编号，但至少要清楚地标出一个代表性的阵元 **m-th element**，并标注它的位置向量 **$r_m$**。

### 2. 必须包含的物理元素

#### 2.1 三维坐标系

- 明确画出 **x, y, z** 三个坐标轴。
- 坐标轴从阵列参考原点出发。
- 原点可标为 **array phase center** 或 **origin**。

#### 2.2 阵元位置向量 $r_m$

- 从原点画一根箭头指向阵列中的某一个阵元，标注为：

  $$
  r_m
  $$

- 旁边可加说明文字：

  ```text
  position vector of the m-th array element
  ```

- 让观者一眼看出 $r_m$ 是**从坐标原点到第 m 个阵元的位置向量**。

#### 2.3 目标方向向量 $u$

- 从阵列原点向空间中某个远处方向画一根明显的箭头，标注为：

  $$
  u
  $$

- 该箭头表示从雷达到目标的**单位方向向量**。
- 在箭头旁边标注：

  $$
  u(\theta,\phi)=
  \begin{bmatrix}
  \cos\phi\cos\theta \\
  \cos\phi\sin\theta \\
  \sin\phi
  \end{bmatrix}
  $$

- 同时用弧线清楚标出：
  - **$\theta$** = azimuth
  - **$\phi$** = elevation

#### 2.4 Look / steering direction $u_l$

- 再画一根与 $u$ 接近但不完全相同的箭头，使用不同颜色或虚线，标注为：

  $$
  u_l
  $$

- 表示当前波束指向 / steering direction。
- 可在阵列前方画一个浅色的波束主瓣或锥形波束，沿 $u_l$ 方向延伸，表示 transmit beam。

#### 2.5 目标

- 在远处空间中，沿 $u$ 方向放置一个简化的目标点或小目标图标，标注：
  - target
  - range $R$
- 从原点到目标画一条虚线或细线，标注距离：

  $$
  R
  $$

#### 2.6 入射波 / 平面波概念

- 为了表现方向 $u$ 对应的来波，可以在目标方向附近画几条**平行波前**（plane wavefronts），朝阵列传播。
- 波前可用浅蓝色半透明线面表示。
- 旁边可标注：

  $$
  a_m(u)=\exp\left(j\frac{2\pi}{\lambda}r_m^T u\right)
  $$

- 表达“方向 $u$ 在阵列上形成空间相位斜率”。

### 3. 推荐的数学标注与说明框

在画面边上增加几个小型公式说明框，风格像论文图中的 annotation callout：

#### Steering vector element

$$
a_m(u)=\exp\left(j\frac{2\pi}{\lambda}r_m^T u\right)
$$

#### Transmit field gain

$$
B_t(u;u_l)=\left|\frac{1}{M}\sum_{m=1}^{M}\exp\left(j\frac{2\pi}{\lambda}r_m^T(u-u_l)\right)\right|
$$

#### Round-trip delay

$$
\tau=\frac{2R}{c}
$$

#### Doppler relation

$$
f_D=\frac{2v_r}{\lambda}
$$

这些公式不需要占太大面积，但要像“解释性标注”一样融入图中。

### 4. 图像风格要求

- 风格：**scientific illustration, engineering diagram, high-end textbook figure, clean academic visualization**
- 色彩：干净克制，建议蓝色、青色、灰色为主；方向箭头可用红色/橙色突出。
- 线条：精准、简洁、清楚。
- 字体：清晰可读，像论文图或教材图。
- 画面不宜过于花哨，重点是**结构清晰、空间几何直观、物理含义明确**。

### 5. 重点表达

整张图要让人一眼看出：

- 这是一个**二维相控阵雷达阵列**。
- 阵元在空间中的分布是规则的二维网格。
- 每个阵元有自己的位置向量 $r_m$。
- 空间中存在目标方向 $u$。
- 雷达当前波束指向是 $u_l$。
- 三维坐标系 $x,y,z$ 用来描述几何关系。
- 这个图是在解释公式：

  $$
  x_m[p,t]\approx \alpha B_t(u;u_l)a_m(u)s(t-\tau)e^{j2\pi(f_D p T_{\mathrm{PRI}})}
  $$

  所对应的物理世界。

### 6. 附加约束

- 不要卡通风格。
- 不要概念艺术风格。
- 不要复杂背景。
- 不要过多无关装饰。
- 保持学术插图风格。
- 数学符号必须正确且清晰。
- 重点突出二维阵列、$r_m$、$u$、$u_l$、x-y-z 坐标系。
