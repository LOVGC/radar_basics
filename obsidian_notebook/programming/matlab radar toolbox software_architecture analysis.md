下面是对 **MathWorks Radar Toolbox 公开文档体系**做出的软件架构分析。这里的“软件架构”不是 MathWorks 内部源码结构，而是从官方文档、产品页、函数分类、示例和支持包边界推导出的**功能架构、模块边界、数据流和工程生命周期架构**。

---

# Radar Toolbox 软件架构分析

## 1. 总体判断

Radar Toolbox 是一个面向雷达工程全生命周期的 MATLAB/Simulink 工具箱。它的核心定位不是单一仿真器，而是把**雷达系统设计、指标评估、场景建模、合成数据生成、信号处理、跟踪、AI 数据生成、代码生成和硬件联调**组织成一个模型驱动的工程平台。官方文档明确说明它支持单基地、双基地、多功能雷达的设计、仿真、分析与测试，并覆盖从需求、链路预算、合成数据到实测数据分析的工作流。([MathWorks][1])

从架构上看，它由几类组件共同构成：**交互式 App、MATLAB 函数、System object、Simulink block、场景对象、数据对象、加速/代码生成能力、硬件支持包**。这意味着 Radar Toolbox 的软件架构不是传统单体应用，而是典型的 MATLAB 生态内的**分层工具箱架构**。([MathWorks][1])

---

## 2. 顶层软件架构图

```text
┌────────────────────────────────────────────────────────────────────┐
│  应用任务层                                                         │
│  Automotive Radar | Bistatic Radar | Multifunction/Cognitive Radar │
│  SAR | AI for Radar | Hardware-in-the-loop / Field Data Workflows   │
└────────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────────┐
│  系统工程与需求评估层                                               │
│  Radar Designer | Radar Equations | ROC/TOC | Link Budget           │
│  Detection/Tracking Statistics | Loss Models | SAR Metrics          │
└────────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────────┐
│  场景、平台与环境建模层                                             │
│  radarScenario | platform | trajectories | emitters | surfaces      │
│  atmosphere | propagation | clutter | weather | theaterPlot         │
└────────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────────┐
│  多保真度数据合成层                                                 │
│  Power-Level → Measurement-Level → Waveform-Level                   │
│  radarDataGenerator | radarTransceiver | radarChannel | RCS models  │
│  detections | tracks | IQ signals | micro-Doppler | clutter/jammer  │
└────────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────────┐
│  信号处理、检测与跟踪层                                             │
│  Waveform libraries | matched filter | pulse compression | CFAR      │
│  range/angle/Doppler estimation | DBSCAN | radarTracker | Kalman     │
└────────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────────┐
│  加速、代码生成与部署层                                             │
│  Parallel | GPU | MEX | C/C++ code generation | HDL | RFSoC          │
└────────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────────┐
│  硬件与实测数据接口层                                               │
│  TI mmWave sensors | DCA1000EVM | ADC/IQ acquisition | deployment    │
└────────────────────────────────────────────────────────────────────┘
                                │
┌────────────────────────────────────────────────────────────────────┐
│  MATLAB 生态依赖层                                                  │
│  MATLAB | Simulink | DSP System Toolbox | Phased Array System       │
│  Toolbox | Signal Processing Toolbox | Sensor Fusion and Tracking   │
│  Toolbox | Mapping Toolbox | Embedded/HDL/SoC/Parallel products      │
└────────────────────────────────────────────────────────────────────┘
```

Radar Toolbox 的安装依赖也反映了这种架构边界：官方系统需求列出它依赖 MATLAB、DSP System Toolbox、Phased Array System Toolbox 和 Signal Processing Toolbox，并可结合 MATLAB Compiler SDK、Parallel Computing Toolbox 等产品使用。([MathWorks][2])

---

# 3. 相关官方网页对应的架构模块分析

| 官方文档模块                                     | 架构含义      | 关键作用                                                     |
| ------------------------------------------ | --------- | -------------------------------------------------------- |
| Radar Toolbox 首页                           | 总体入口与能力总览 | 定义工具箱边界：系统设计、仿真、数据合成、处理、硬件、代码生成                          |
| Getting Started                            | 入门工作流层    | 通过测量级数据生成、目标可探测性、传播、RCS、扫描雷达、`radarScenario` 等教程建立主流程    |
| Applications                               | 应用层       | 将底层能力组合成双基地、AI、多功能雷达、SAR、汽车雷达等工程场景                       |
| Radar Systems Engineering                  | 系统工程层     | 用雷达方程、检测统计、损耗、环境、SAR 指标做需求评估和链路预算                        |
| Scenario Generation                        | 场景层       | 建立平台、轨迹、发射机、接收机、场景记录和可视化                                 |
| Data Synthesis                             | 数据生成层     | 以 power-level、measurement-level、waveform-level 三种保真度生成数据 |
| Signal and Data Processing                 | 算法层       | 完成匹配滤波、脉冲压缩、CFAR、距离/角度/多普勒估计、聚类、跟踪                       |
| Algorithm Acceleration and Code Generation | 工程化层      | 支持 GPU、MEX、C/C++、HDL、RFSoC 等部署或加速                        |
| Supported Hardware                         | 硬件接口层     | 通过 TI mmWave 支持包连接真实传感器和采集板                              |

官方首页本身已经把这些模块分成 Applications、Radar Systems Engineering、Scenario Generation、Data Synthesis、Signal and Data Processing、Algorithm Acceleration and Code Generation、Supported Hardware 等顶层分类，这基本就是该工具箱对外呈现的软件模块边界。([MathWorks][1])

---

# 4. 分层架构详解

## 4.1 应用任务层

应用层负责把基础建模、仿真、处理和部署能力组合成面向行业或雷达体制的工作流。官方 Applications 文档覆盖汽车雷达、双基地雷达、多功能/认知雷达、SAR 和 AI for Radar 等方向，并说明可模拟波形、回波、目标几何体、微多普勒、天线、信道以及实时或录制信号。([MathWorks][3])

### 主要应用子模块

| 应用子模块                           | 架构角色                                      |
| ------------------------------- | ----------------------------------------- |
| Automotive Radar                | 面向车载雷达，支持概率模型、物理模型、MIMO、I/Q、微多普勒、检测、聚类和跟踪 |
| Bistatic Radar                  | 面向发射机和接收机分离的双基地/被动雷达建模                    |
| Multifunction / Cognitive Radar | 面向闭环雷达，动态选择波形、波束、频率、PRF，支持搜索/跟踪模式切换       |
| SAR                             | 面向合成孔径雷达，分析天线足迹、距离/方位分辨率、模糊、SNR、杂波和几何约束   |
| AI for Radar                    | 面向机器学习/深度学习的数据标注、合成数据生成、分类和目标识别           |

车载雷达模块明确支持概率模型和物理模型，能够生成 I/Q、微多普勒、检测、聚类和跟踪，并可使用 `radarDataGenerator` 与 `radarTransceiver` 建模；多功能雷达模块则强调闭环控制，仿真中可以动态改变频率、波束方向和波形选择。([MathWorks][4])

AI for Radar 不是独立深度学习框架，而是把 Radar Toolbox 的合成数据、波形、回波、微多普勒和 Signal Labeler 等能力作为 AI 数据工程入口，用于训练机器学习或深度学习模型。([MathWorks][5])

---

## 4.2 系统工程与需求评估层

这一层是 Radar Toolbox 的“前端系统设计层”。它解决的问题不是先写信号处理算法，而是先回答：

* 雷达需要多大发射功率？
* 天线孔径和增益是否足够？
* 目标在某个距离上的 SNR、Pd、Pfa 是否满足需求？
* 环境、雨雪、地球曲率、地物杂波会造成多大损耗？
* SAR 几何约束、分辨率和模糊是否满足任务要求？

官方 Radar Systems Engineering 文档说明该层包含雷达方程、检测与跟踪统计、天线/接收机损耗、环境与杂波、SAR 等类别，用于评估雷达系统性能、SNR、最小可检测信号、目标属性精度、ROC、搜索跟踪和 SAR 指标。([MathWorks][6])

### Radar Designer 的角色

Radar Designer 是这一层的关键交互式 App。它用于高层设计和早期评估，可比较多个设计，配置雷达、环境和目标，考虑地球曲率、大气、地形、降水、自定义 RCS、天线和损耗，并能导出结果、模型、绘图或 MATLAB 脚本。([MathWorks][7])

更重要的是，Radar Designer 体现了该工具箱的“需求驱动设计”特征：它支持设置指标和约束，进行 tradeoff 分析，并在结果中查看 SNR、CNR、Pd、环境损耗、detectability factor 以及类似 stoplight chart 的通过/警告/失败状态。([MathWorks][7])

### 系统工程层内部模块

```text
需求 / 指标
   │
   ├─ Radar Designer App
   │    ├─ 场景几何
   │    ├─ 链路预算
   │    ├─ 环境损耗
   │    ├─ SNR / CNR / Pd 曲线
   │    └─ 设计约束与指标检查
   │
   ├─ Radar Equation Functions
   │    ├─ radareqsnr
   │    ├─ radareqrng
   │    ├─ radareqpow
   │    └─ SAR / search radar equation variants
   │
   ├─ Detection / Tracking Statistics
   │    ├─ ROC / TOC
   │    ├─ detectability
   │    ├─ Albersheim / Shnidman
   │    └─ track probability metrics
   │
   └─ Loss / Environment / Clutter Models
        ├─ antenna and scanning loss
        ├─ receiver/noise/matching loss
        ├─ atmosphere/rain/snow/fog attenuation
        ├─ land/sea/custom surface clutter
        └─ propagation factor / terrain / grazing geometry
```

雷达方程页面列出的函数覆盖最大探测距离、SNR、峰值功率、功率孔径积等计算；检测与跟踪统计页面覆盖 ROC、TOC、Blake chart、最小 SNR、Swerling 模型、MDS、Pd/Pfa 和跟踪概率；损耗页面则覆盖波束、扫描、遮挡、噪声、匹配、脉冲积累、CFAR 和 MTI 损耗。([MathWorks][8])

环境与杂波模块提供大气、气体、雾、雨、雪、自由空间损耗、雷达传播因子、land/sea/custom surface、杂波 RCS 和反射率等建模能力，说明这一层不是理想雷达方程，而是把实际传播环境纳入系统评估。([MathWorks][9])

---

## 4.3 场景、平台与环境建模层

这一层是 Radar Toolbox 的“世界模型”或“仿真场景内核”。它负责描述时间、空间、平台、轨迹、姿态、发射源、接收源、目标、地表和可视化。

Scenario Generation 文档说明它支持空中、地面、舰船平台和目标，支持航路点、轨迹对象和惯性导航对象描述运动与姿态，并可可视化或记录场景演化。([MathWorks][10])

### 核心对象和接口

| 对象/函数                                                          | 架构作用                      |
| -------------------------------------------------------------- | ------------------------- |
| `radarScenario`                                                | 雷达场景容器，管理仿真时间、平台、传感器、发射源等 |
| `platform`                                                     | 场景中的移动实体，例如飞机、车辆、舰船、目标    |
| `geoTrajectory` / `waypointTrajectory` / `kinematicTrajectory` | 描述目标或平台运动                 |
| `radarScenarioRecording`                                       | 记录场景演化，用于复现和后处理           |
| `coverageConfig`                                               | 描述传感器覆盖范围                 |
| `theaterPlot`                                                  | 场景和结果可视化入口                |
| `detectionPlotter` / `trackPlotter` / `platformPlotter`        | 检测、航迹、平台可视化               |

官方 Scenario Creation 页面列出了 `radarScenario`、`platform`、`radarScenarioRecording`、`radarEmitter` 相关对象，Visualization 页面列出了 `theaterPlot`、`coveragePlotter`、`detectionPlotter`、`platformPlotter`、`trackPlotter` 等可视化对象。([MathWorks][11])

这一层的设计关键是：**先建立真实世界的 ground truth，再在此基础上生成不同保真度的数据**。换句话说，场景层是 power-level、measurement-level 和 waveform-level 三种数据生成方式的共同上游。

---

## 4.4 多保真度数据合成层

这是 Radar Toolbox 架构中最核心的一层。官方 Data Synthesis 文档明确把数据合成分为三个抽象层级：

```text
Power-Level       ：链路预算 / SNR / RCS / 环境损耗 / Pd
Measurement-Level ：检测、虚警、杂波、目标航迹、测量误差
Waveform-Level    ：发射波形、传播、目标回波、I/Q、通道、杂波、干扰
```

官方文档说明，Radar Toolbox 可在概率模型和物理模型两个层级生成雷达数据：低保真概率模型可快速生成检测和航迹以支持跟踪/融合，高保真物理模型则模拟发射波形经环境传播、目标反射再接收的过程，并支持多径、杂波、干扰和目标回波。([MathWorks][12])

### 4.4.1 Power-Level 数据合成

Power-Level 主要用于系统设计和早期性能评估。它关注 SNR、RCS、环境传播损耗、预测检测概率等，不直接生成完整 I/Q 波形。官方页面说明该层可分析环境效应、目标 RCS、SNR 随距离变化和检测概率。([MathWorks][13])

适用场景：

* 概念设计；
* 链路预算；
* 天线、功率、频率、距离 tradeoff；
* 快速评估“这个雷达大概能不能看见目标”。

### 4.4.2 Measurement-Level 数据合成

Measurement-Level 用于在较高抽象层生成检测、虚警、杂波、目标航迹、SNR、增益/损耗和测量误差。该层的典型对象是 `radarDataGenerator`，用于在动态场景中模拟雷达和目标，并生成检测或航迹。([MathWorks][14])

适用场景：

* 多目标跟踪算法开发；
* 传感器融合算法测试；
* 大规模 Monte Carlo；
* 快速生成 detection / track 级别数据；
* 不需要完整电磁波形细节的系统仿真。

### 4.4.3 Waveform-Level 数据合成

Waveform-Level 是最高保真度的数据生成层。官方文档说明它用于模拟雷达信号、回波、目标回波、微多普勒和算法测试，典型对象是 `radarTransceiver`，可建模波形级信号和数据处理链，生成 I/Q 数据，并测试检测和微多普勒算法。([MathWorks][15])

这一层还包含 RCS 几何体、`radarChannel`、`twoRayChannel`、`widebandTwoRayChannel`、`barrageJammer`、`constantGammaClutter`、行人/骑车人 backscatter 模型和脉冲波形库等组件。([MathWorks][15])

适用场景：

* 波形设计；
* 信号处理算法验证；
* I/Q 数据生成；
* 微多普勒识别；
* 干扰和杂波建模；
* 与真实硬件采集数据对比。

### 多保真度架构的核心价值

```text
同一个雷达任务
   │
   ├─ 用 Power-Level 快速做链路预算和指标可行性分析
   │
   ├─ 用 Measurement-Level 大规模生成检测/航迹，验证跟踪和融合算法
   │
   └─ 用 Waveform-Level 生成 I/Q 和回波，验证信号处理、波形和硬件相关算法
```

这说明 Radar Toolbox 的数据层不是单一仿真精度，而是**分辨率可调的仿真架构**。工程上可以先用低成本模型快速搜索设计空间，再在关键方案上提升到波形级仿真。

---

## 4.5 信号处理、检测、聚类与跟踪层

这一层负责把雷达原始或合成数据变成工程上可用的目标信息。官方 Signal and Data Processing 文档列出了一条典型处理链：匹配滤波、stretch-processing 脉冲压缩、相干/非相干积累、CFAR、距离/角度/速度估计、聚类、关联、多目标跟踪和闭环认知雷达。([MathWorks][16])

### 典型处理流水线

```text
I/Q 或回波数据
   │
   ├─ 波形处理
   │    ├─ matched filtering
   │    ├─ pulse compression
   │    ├─ stretch processing
   │    └─ integration
   │
   ├─ 检测
   │    └─ CFAR / thresholding
   │
   ├─ 参数估计
   │    ├─ range estimation
   │    ├─ angle / DOA estimation
   │    └─ Doppler / velocity estimation
   │
   ├─ 聚类
   │    └─ DBSCAN
   │
   ├─ 航迹管理
   │    ├─ track initiation
   │    ├─ association
   │    ├─ prediction / correction
   │    └─ deletion
   │
   └─ 输出
        ├─ objectDetection
        └─ objectTrack
```

Detection、Range、Angle、Doppler 页面列出 CFAR、Range-Doppler response、Range estimator、Doppler estimator、matched filter、stretch processor 等函数和 block；Clustering 页面提供 DBSCAN 聚类；Multi-Object Tracking 页面提供 `radarTracker`、`objectDetection`、`objectTrack`、track history 等对象。([MathWorks][17])

跟踪滤波层还支持常速度、常加速度、协调转弯等运动模型，以及 alpha-beta、Kalman、EKF、UKF 等滤波器初始化和状态转换函数。([MathWorks][18])

---

## 4.6 加速、代码生成与部署层

Radar Toolbox 的工程化层支持把仿真和算法从 MATLAB 原型推进到更高性能或部署环境。官方文档将这一部分分为并行/GPU 加速、C/C++ 与 MEX 代码生成、HDL 代码生成和 RFSoC 工作流。([MathWorks][19])

### 工程化能力

| 能力                    | 架构作用                                    |
| --------------------- | --------------------------------------- |
| Parallel / GPU        | 加速大规模场景、扫描仿真、杂波仿真                       |
| MEX                   | 将 MATLAB 算法编译为本机代码，提高仿真速度               |
| C/C++ code generation | 生成可嵌入或集成的 C/C++ 算法代码                    |
| HDL code generation   | 面向 FPGA 的硬件实现工作流                        |
| RFSoC deployment      | 结合 SoC Blockset，把模型部署到 Xilinx RFSoC 开发板 |

官方代码生成页面说明可生成 C/C++ 和 MEX，并可从 Simulink 模型生成 HDL；RFSoC 页面说明可将 Simulink 模型部署到 Xilinx RFSoC 开发板。([MathWorks][20])

这一层体现了 Radar Toolbox 的定位：它不只是离线仿真工具，也支持**原型验证、加速仿真和硬件部署链路**。

---

## 4.7 硬件与实测数据接口层

官方 Supported Hardware 页面列出 TI mmWave Sensors 支持包，说明 Radar Toolbox 可通过支持包连接硬件。([MathWorks][21])

TI mmWave 支持包页面进一步说明，它可以与 TI mmWave 雷达通信、配置设备、采集数据，并支持读取 EVM 的检测/测量结果，通过 DCA1000EVM 获取实时 I/Q 数据，还可借助 Embedded Coder 将 Simulink 独立应用部署到 TI 板卡的 ARM Cortex 处理器上。([MathWorks][22])

硬件工作流大致如下：

```text
TI mmWave EVM / DCA1000EVM
   │
   ├─ 设备配置
   ├─ 检测结果读取
   ├─ ADC / I/Q 数据采集
   ├─ MATLAB / Simulink 算法验证
   ├─ 与仿真数据对比
   └─ 嵌入式部署 / 参数调优 / PIL
```

硬件支持包文档还列出了硬件 setup、读取 detections、读取 ADC/IQ、建模与部署等工作流，并对 Windows、DCA1000、TI UniFlash、MMWAVE-STUDIO、MMWAVE-SDK 等外部软件有要求。([MathWorks][23])

---

# 5. Radar Toolbox 的核心数据流架构

Radar Toolbox 的完整工程数据流可以抽象为下面这条主链：

```text
需求与指标
  ↓
系统工程设计
  ↓
场景与环境建模
  ↓
多保真度数据合成
  ↓
信号处理 / 检测 / 估计
  ↓
聚类 / 跟踪 / 融合 / AI
  ↓
性能评估与闭环调参
  ↓
加速 / 代码生成 / 硬件验证
```

展开后如下：

```text
1. 需求输入
   - 探测距离
   - 分辨率
   - Pd / Pfa
   - 搜索区域
   - 平台运动
   - 频段 / 功率 / 天线约束

2. 系统级设计
   - Radar Designer
   - radar equation
   - ROC / TOC
   - loss models
   - environmental effects

3. 场景构建
   - radarScenario
   - platform
   - trajectory
   - transmitter / receiver
   - land / sea / custom surface
   - atmosphere / weather / clutter

4. 数据生成
   - power-level: SNR, Pd, link budget
   - measurement-level: detections, false alarms, tracks
   - waveform-level: waveform, echoes, I/Q, channel, clutter, jammer

5. 算法处理
   - pulse compression
   - matched filtering
   - CFAR
   - range / angle / Doppler estimation
   - clustering
   - tracking filters
   - radarTracker

6. 应用闭环
   - automotive radar perception
   - SAR image/geometry analysis
   - bistatic/passive radar
   - multifunction radar scheduling
   - AI dataset generation

7. 工程实现
   - GPU / parallel simulation
   - MEX / C/C++
   - HDL
   - RFSoC
   - TI mmWave hardware acquisition and deployment
```

多功能雷达场景中，数据流还会形成反馈闭环：处理结果会影响下一时刻的波束方向、频率、PRF、波形选择或搜索/跟踪模式切换。官方 Multifunction Radar 文档明确描述了闭环仿真、波形选择、搜索/跟踪模式、PRF/频率捷变和干扰缓解能力。([MathWorks][24])

---

# 6. 关键软件对象与接口契约

Radar Toolbox 的架构中有一批关键对象，起到了“模块接口”的作用。

| 对象/接口                                                          | 所在层    | 作用                             |
| -------------------------------------------------------------- | ------ | ------------------------------ |
| `radarScenario`                                                | 场景层    | 管理雷达场景、平台、时间推进和场景实体            |
| `platform`                                                     | 场景层    | 表示目标、雷达平台、发射平台、接收平台等移动实体       |
| `waypointTrajectory` / `geoTrajectory` / `kinematicTrajectory` | 场景层    | 表示平台运动和姿态                      |
| `radarDataGenerator`                                           | 测量级数据层 | 生成检测、杂波、虚警、目标航迹等测量级数据          |
| `radarTransceiver`                                             | 波形级数据层 | 建模发射、传播、反射、接收和 I/Q 数据生成        |
| `radarEmitter` / `radarEmission`                               | 发射源建模  | 表示雷达发射机、干扰源或电磁辐射事件             |
| `objectDetection`                                              | 算法接口   | 检测结果标准数据结构                     |
| `objectTrack`                                                  | 跟踪接口   | 航迹标准数据结构                       |
| `radarTracker`                                                 | 跟踪层    | 管理雷达目标航迹                       |
| `theaterPlot`                                                  | 可视化层   | 统一显示平台、覆盖、检测、航迹和场景             |
| CFAR / Range-Doppler / Matched Filter blocks                   | 信号处理层  | MATLAB/Simulink 中的处理算法组件       |
| TI mmWave support package interfaces                           | 硬件层    | 连接真实 TI mmWave 设备，读取检测或 I/Q 数据 |

这些接口说明 Radar Toolbox 的模块之间不是简单函数调用关系，而是通过**场景对象、检测对象、航迹对象、波形对象和 Simulink block**进行松耦合组合。

---

# 7. 架构中的三条典型工程路径

## 路径 A：系统设计与链路预算

```text
需求 → Radar Designer / radareq* → SNR/Pd/Range/Power tradeoff
     → 环境损耗/杂波建模 → 设计方案比较 → 导出脚本或模型
```

适合雷达概念设计、指标分配、功率/孔径/频率 tradeoff。

---

## 路径 B：检测与跟踪算法验证

```text
radarScenario
   → platform / trajectory / target truth
   → radarDataGenerator
   → objectDetection
   → clustering / association
   → radarTracker / filters
   → objectTrack
   → theaterPlot / metrics
```

适合跟踪算法、传感器融合、车载雷达和大规模 Monte Carlo 验证。

---

## 路径 C：波形级信号处理验证

```text
waveform library
   → radarTransceiver
   → channel / clutter / jammer / RCS target
   → I/Q data
   → matched filter / pulse compression
   → CFAR
   → range-angle-Doppler estimation
   → detections / tracks / AI features
```

适合 FMCW、脉冲雷达、微多普勒、干扰、杂波和真实硬件采集数据对比。

---

# 8. 横切架构特性

## 8.1 多保真度建模

Radar Toolbox 的一个重要架构特征是允许用户在不同保真度之间切换：

| 保真度               | 计算成本 | 输出                             | 用途          |
| ----------------- | ---: | ------------------------------ | ----------- |
| Power-Level       |    低 | SNR、Pd、链路预算                    | 快速设计探索      |
| Measurement-Level |    中 | detections、false alarms、tracks | 跟踪/融合算法验证   |
| Waveform-Level    |    高 | I/Q、回波、数据立方体                   | 信号处理和硬件相关验证 |

这使得同一个雷达项目可以从粗到细逐步推进，而不是一开始就进入高成本波形级仿真。

## 8.2 模型驱动与闭环仿真

通过 `radarScenario`、`radarDataGenerator`、`radarTransceiver`、`radarTracker` 等对象，Radar Toolbox 支持从 ground truth 到 detection/track 的完整仿真闭环。多功能雷达场景进一步把算法输出反馈到雷达控制策略中，实现波形、波束、频率和模式的动态调整。([MathWorks][24])

## 8.3 MATLAB/Simulink 双接口

该工具箱同时面向脚本化 MATLAB 工作流和 Simulink 模型工作流。许多能力既有 MATLAB 函数/System object，也有 Simulink block，并且代码生成、HDL、RFSoC 和硬件部署主要依赖 Simulink 生态延伸。([MathWorks][20])

## 8.4 真实硬件闭环

通过 TI mmWave 支持包，Radar Toolbox 可以把仿真链路延伸到真实传感器，读取检测数据或 ADC/IQ 数据，并进行参数调优、PIL 和部署。([MathWorks][22])

---

# 9. 软件架构优点

## 9.1 全生命周期覆盖

从需求、链路预算、场景建模、合成数据、信号处理、跟踪、AI、代码生成到硬件联调，Radar Toolbox 覆盖了雷达工程从概念到验证的大部分阶段。([MathWorks][1])

## 9.2 多抽象层统一

Power-Level、Measurement-Level、Waveform-Level 三层数据生成使它既能做快速系统评估，也能做高保真 I/Q 级仿真。([MathWorks][12])

## 9.3 与 MATLAB 生态深度集成

Radar Toolbox 与 Phased Array System Toolbox、DSP System Toolbox、Signal Processing Toolbox、Sensor Fusion and Tracking Toolbox、Mapping Toolbox、Simulink、Embedded Coder、HDL Coder、SoC Blockset 等形成组合能力。官方系统需求和 MATLAB Radar 解决方案页面都体现了这种生态型架构。([MathWorks][2])

## 9.4 适合算法原型和工程验证

它既能用 MATLAB 快速写算法，也能用 Simulink 做模型化系统设计，再进一步生成 C/C++、MEX、HDL 或部署到 RFSoC/硬件平台。([MathWorks][19])

---

# 10. 架构局限与注意点

1. **强依赖 MathWorks 生态**
   Radar Toolbox 本身依赖多个基础工具箱，复杂部署还可能需要 Simulink、Embedded Coder、HDL Coder、SoC Blockset、Parallel Computing Toolbox 等产品。([MathWorks][2])

2. **硬件支持范围不是无限扩展**
   官方 Supported Hardware 页面主要列出 TI mmWave Sensors 支持包，说明硬件接口层当前以特定厂商/板卡工作流为主。([MathWorks][21])

3. **波形级仿真计算成本高**
   Waveform-Level 能生成 I/Q、回波、杂波、干扰和微多普勒，但这类高保真仿真天然计算成本较高，因此官方单独提供并行、GPU、MEX 和代码生成相关工作流。([MathWorks][15])

4. **代码生成能力需要按函数/对象确认**
   Radar Toolbox 支持 C/C++、MEX、HDL 等工作流，但在实际项目中通常需要逐个确认所用函数、System object 或 Simulink block 是否支持目标代码生成路径。官方代码生成页面本身也以特定函数和示例方式组织支持范围。([MathWorks][20])

---

# 11. 最终抽象架构

可以把 Radar Toolbox 总结为下面这个软件架构模式：

```text
Radar Toolbox = 
    雷达系统工程层
  + 场景/环境数字孪生层
  + 多保真度数据合成层
  + 雷达信号处理与目标跟踪算法层
  + AI 数据生成与标注支撑层
  + 加速/代码生成/硬件部署层
  + MATLAB/Simulink 生态集成层
```

它的核心架构思想是：

```text
用统一的场景模型承载雷达任务，
用多保真度数据合成连接系统设计和算法验证，
用标准 detection / track / I-Q 接口连接处理链，
用 MATLAB/Simulink 生态完成从仿真到部署的工程闭环。
```

因此，如果要画成企业级软件架构，可以归纳为：

```text
需求与指标管理
       ↓
雷达系统设计与链路预算
       ↓
场景 / 平台 / 环境 / 目标建模
       ↓
多层级仿真数据生成
       ├─ power-level
       ├─ measurement-level
       └─ waveform-level
       ↓
信号处理、检测、估计、聚类、跟踪
       ↓
应用任务闭环
       ├─ 汽车雷达
       ├─ 双基地/被动雷达
       ├─ 多功能/认知雷达
       ├─ SAR
       └─ AI for Radar
       ↓
性能评估、加速、代码生成
       ↓
硬件采集、原型验证与部署
```

这个架构的本质是一个**面向雷达工程的模型驱动仿真与验证平台**，而不是单一算法库。它通过 Radar Designer、`radarScenario`、`radarDataGenerator`、`radarTransceiver`、信号处理 block、跟踪对象、代码生成和 TI mmWave 支持包，把雷达从系统指标到真实硬件验证的链路串成了一个完整软件工程体系。

[1]: https://www.mathworks.com/help/radar/index.html?s_tid=CRUX_lftnav "Radar Toolbox Documentation"
[2]: https://www.mathworks.com/support/requirements/radar-toolbox.html "Product Requirements & Platform Availability for Radar Toolbox - MATLAB & Simulink"
[3]: https://www.mathworks.com/help/radar/applications.html?s_tid=CRUX_lftnav "Applications - MATLAB & Simulink"
[4]: https://www.mathworks.com/help/radar/automotive-radar.html?s_tid=CRUX_lftnav "Automotive Radar - MATLAB & Simulink"
[5]: https://www.mathworks.com/help/radar/ai-for-radar.html?s_tid=CRUX_lftnav "AI for Radar - MATLAB & Simulink"
[6]: https://www.mathworks.com/help/radar/radar-system-analysis.html?s_tid=CRUX_lftnav "Radar Systems Engineering - MATLAB & Simulink"
[7]: https://www.mathworks.com/help/radar/ref/radardesigner-app.html "Radar Designer - Model radar gains and losses and assess performance in different environments - MATLAB"
[8]: https://www.mathworks.com/help/radar/group_function.html?s_tid=CRUX_lftnav "Radar Equations - MATLAB & Simulink"
[9]: https://www.mathworks.com/help/radar/environment-and-clutter.html?s_tid=CRUX_lftnav "Environment and Clutter - MATLAB & Simulink"
[10]: https://www.mathworks.com/help/radar/radar-scenario-generation.html?s_tid=CRUX_lftnav "Scenario Generation - MATLAB & Simulink"
[11]: https://www.mathworks.com/help/radar/scenario-generation.html?s_tid=CRUX_lftnav "Scenario Creation and Recording - MATLAB & Simulink"
[12]: https://www.mathworks.com/help/radar/radar-data-synthesis.html?s_tid=CRUX_lftnav "Data Synthesis - MATLAB & Simulink"
[13]: https://www.mathworks.com/help/radar/power-level-simulations.html?s_tid=CRUX_lftnav "Power-Level Simulations - MATLAB & Simulink"
[14]: https://www.mathworks.com/help/radar/measurement-level-simulations.html?s_tid=CRUX_lftnav "Measurement-Level Simulations - MATLAB & Simulink"
[15]: https://www.mathworks.com/help/radar/waveform-level-simulations.html?s_tid=CRUX_lftnav "Waveform-Level Simulations - MATLAB & Simulink"
[16]: https://www.mathworks.com/help/radar/radar-signal-and-data-processing.html?s_tid=CRUX_lftnav "Signal and Data Processing - MATLAB & Simulink"
[17]: https://www.mathworks.com/help/radar/detection-range-angle-and-doppler-estimation.html?s_tid=CRUX_lftnav "Detection, Range, Angle, and Doppler Estimation - MATLAB & Simulink"
[18]: https://www.mathworks.com/help/radar/tracking-filters-and-motion-models.html?s_tid=CRUX_lftnav "Tracking Filters and Motion Models - MATLAB & Simulink"
[19]: https://www.mathworks.com/help/radar/algorithm-acceleration-and-code-generation.html?s_tid=CRUX_lftnav "Algorithm Acceleration and Code Generation - MATLAB & Simulink"
[20]: https://www.mathworks.com/help/radar/code-generation.html?s_tid=CRUX_lftnav "Code Generation - MATLAB &amp; Simulink"
[21]: https://www.mathworks.com/help/radar/supported-hardware.html?s_tid=CRUX_lftnav "Radar Toolbox Supported Hardware - MATLAB & Simulink"
[22]: https://www.mathworks.com/help/radar/mmwaveradar-support-package.html "TI mmWave Radar Sensors - MATLAB & Simulink"
[23]: https://www.mathworks.com/help/radar/ug/install-support-for-ti-mmwave-hardware.html "Install Support and Perform Hardware Setup for TI mmWave Hardware - MATLAB & Simulink"
[24]: https://www.mathworks.com/help/radar/multifunction-and-cognitive-radar.html?s_tid=CRUX_lftnav "Multifunction Radar - MATLAB & Simulink"
