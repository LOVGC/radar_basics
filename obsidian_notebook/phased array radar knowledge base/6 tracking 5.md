# 概率模型,具体讲

## 1. 状态空间模型(state-space model)

整个 tracking 的概率结构由两个分布定义。设 $x_k$ 是 $k$ 时刻的真实状态(比如 $[x,y,v_x,v_y]$,隐藏),$z_k$ 是 $k$ 时刻的测量(雷达给的位置,可见):

**运动模型(状态转移)** —— 给定上一时刻状态,这一时刻状态的分布: $$p(x_k \mid x_{k-1})$$

**测量模型(似然)** —— 给定真实状态,测量值的分布: $$p(z_k \mid x_k)$$

整个 tracking 推断只用到这两个东西。

## 2. 先验和后验在哪一步出现 —— 递归贝叶斯滤波

每来一个 dwell,做两步:

**Predict(算先验)**: $$ p(x_k \mid z_{1:k-1}) ;=; \int p(x_k \mid x_{k-1}), p(x_{k-1} \mid z_{1:k-1}), dx_{k-1} $$

人话:用**上一时刻的后验**沿运动模型推一步,得到**还没看本次测量时**对 $x_k$ 的信念。这就是本时刻的先验。

**Update(算后验)**: $$ \underbrace{p(x_k \mid z_{1:k})}_{\text{后验}} ;\propto; \underbrace{p(z_k \mid x_k)}_{\text{似然}} \cdot \underbrace{p(x_k \mid z_{1:k-1})}_{\text{先验}} $$

就是贝叶斯定理。

⚠️ 关键认识:**先验和后验不是固定的两个分布,而是每个 dwell 滚动更新的概念**:

- 本 dwell 的"先验" = 上 dwell 的"后验" 经运动模型推一步
- 本 dwell 的"后验" = 本先验 × 本似然(归一化)

这就是为什么叫 _recursive_ Bayesian filter。

## 3. 线性高斯假设下,这就是卡尔曼滤波

最常用的假设:运动和测量都线性高斯。

$$ x_k = F,x_{k-1} + w_k, \quad w_k \sim \mathcal{N}(0, Q) $$ $$ z_k = H,x_k + v_k, \quad v_k \sim \mathcal{N}(0, R) $$

- $F$:状态转移矩阵(CV 模型就是把位置加上 $v\cdot dt$)
- $Q$:过程噪声协方差(代表"目标可能微微加减速、转向"的不确定性)
- $H$:把状态映射到测量(只测位置 → $H=[I,0]$)
- $R$:测量噪声协方差

这套假设下,所有分布都保持高斯,只用维护**均值 + 协方差**两个量:

|量|含义|
|---|---|
|$\hat{x}_{k\mid k-1},, P_{k\mid k-1}$|先验均值 / 协方差|
|$\hat{x}_{k\mid k},,, P_{k\mid k}$|后验均值 / 协方差|

Predict / Update 都有闭式解,就是经典 KF 公式。直觉:

- $Q$ 大 → 认为目标乱动 → 先验宽 → 多信测量
- $R$ 大 → 测量糟 → 似然宽 → 多信预测
- $P$ 越大 → 越不确定 → 更新时 Kalman gain $K$ 越大,越倾向跟随测量

**协方差 $P$ 这条线,正是 α-β 滤波丢掉的关键信息**(下一节)。

## 4. α-β 滤波 = KF 收敛到稳态后的简化

代码里的更新式: $$ x_{\text{new}} = (1-\alpha), x_{\text{predicted}} + \alpha, x_{\text{measured}} $$

对照 KF 在 $H=I$ 时的更新: $$ \hat{x}_{k\mid k} = (I - K_k),\hat{x}_{k\mid k-1} + K_k, z_k $$

可见 **α 就是把 Kalman gain $K_k$ 写死成常数**。KF 每步根据 $P_{k\mid k-1}$ 自适应算 $K_k$;α-β 直接给一个固定值——便宜,但不再追踪不确定性,出错了也不会"知道自己更不确定"。

α-β 在系统达到稳态(P 收敛)时和 KF 几乎等价,这也是它能用的理论依据。

## 5. 多目标:多出一层"关联"隐变量

上面都是**单目标**。多目标时,本 dwell 给出一组 detections $Z_k = {z_k^1, z_k^2, \dots}$,但你不知道哪个 $z_k^i$ 属于哪条 track。引入关联变量 $\theta_k$:

$$ \theta_k(i) = j ;\Leftrightarrow; \text{detection } i \text{ 属于 track } j\text{(或虚警 } j=0\text{)} $$

完整的多目标后验是**状态和关联的联合后验**: $$ p!\left(x_k^{1:M},, \theta_k ;\middle|; Z_{1:k}\right) $$

不同 tracker 的本质差异 = **怎么处理 $\theta_k$ 这个离散隐变量**:

|算法|对 $\theta_k$ 的处理|
|---|---|
|**GNN**|取最大后验(硬决策),问题退化成 $M$ 个独立 KF|
|**JPDA**|对所有可能的 $\theta_k$ 取加权期望(软关联)|
|**MHT**|维护多个 $\theta$ 假设的树,延迟决策,后期剪枝|
|**PHD / PMBM**|连目标数 $M$ 也视为随机变量|

代码里的 gating + nearest neighbor 是 **GNN 最朴素的实现**:在 gate 内挑一个最近的 detection 硬关联,然后用(简化版的)KF——也就是 α-β——更新每条 track。

---

总结成一张图:

```
            运动模型 p(x_k|x_{k-1})         测量模型 p(z_k|x_k)
                    │                              │
                    ▼                              ▼
   上一后验 ──Predict──▶ 本先验 ──Update(×似然)──▶ 本后验 ──▶ 下一 Predict ...
                                  ▲
                                  │
                              本次测量 z_k

   多目标:测量是一个集合 {z_k^i},中间多一步"关联"隐变量 θ_k 的推断
```

KF / α-β / GNN / JPDA / MHT 这些名字看着唬人,但都套在这个骨架上,只是在不同地方做了不同近似。