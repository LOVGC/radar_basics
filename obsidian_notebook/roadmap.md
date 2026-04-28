
# 2026-04-28

plan:
- 通过 coding 把基本的 matched filtering, doppler processing, digital beamforming 还有常用 filtering 的技术学习一下。


what I learned today：
- 这个 YAML 做得好，基本上就是在概念上描述了一个雷达，方便人类理解。
- obsidian 中是可以直接插入 Mermaid 的图的，这意味着，可以让 AI 在 md 里面生成这种 mermaid 图让人类更容易理解。
- 总结知识的一个方法是画图（图是 intuition 最好的载体）：
	- mermaid 的图：
		- 可以用代码控制， 画简单的逻辑图，框图可以，但是更复杂的就不行。
	- 让 gpt 帮你画图：
		- 可以画很复杂的图，效果还不错。
		- 我的做法：先用文字描述一下自己的 idea, 然后让 gpt 帮我生成画图用的 prompt, 然后再让 gpt 生图。
		- 缺点是：有些细节画得不太对，而且不好控制，花时间也长
- 对于 phased array radar 来讲，这个 3D 空间的 geometry 这个概念还是挺重要的，因为这个东西直接对应的是 Physical 世界的概念。雷达想要测量的也就是这个 physical 世界的物理量。



# 2026-04-27

plan:
- 收集一些 radar signal processing 的好的资料 (contexts)
- learn radar basic signal processing with codex 
	- 基本的 radar operations
	- 基本的信号处理：测角度，测速度，测距离 (learn with coding)
- learn radar tracking 
	- 这个技术的 overall picture 是什么？
	- 然后 walkthrough the details to gain more understanding 


good repos:
- https://www.mathworks.com/help/radar/getting-started-with-radar-toolbox.html?s_tid=CRUX_lftnav : mathworks standard implementations of every signal processing, can be used for verification. 
- radarsimpy: https://github.com/radarsimx/radarsimpy?utm_source=chatgpt.com
- https://github.com/powersthegreat/Advanced_Radar_Processing_Notebooks?utm_source=chatgpt.com

目前可以判断的是，
- 可以用 matlab 来作为 verification 的手段。
- Radarsimpy 是用 python 写的。
- 你自己也可以 implement from scrach


what is done:
- 上午：build mental knowledge framework for 2D phased array radar. 
- 下午：begin design simulation software architecutre with AI

# 2026-04-24

plan:
-  learn tracking by simulation
- then verify data3,4,5 dataset and dataloader (probably next week)



# 2026-04-23

plan: 
- data3, data4, data5, dataset dataloader dev
- basic radar signal processing and tracking simulation

data3, 4, 5 dataset and dataloader finished (By codex)

Next:
- learn tracking by simulation
- then verify data3,4,5 dataset and dataloader


# 2026-04-22

plan:
- review data0, data1 的 dataloader 
- data2 EDA, dataset and dataloader dev

---

what is learned today:
![[ChatGPT Image 2026年4月22日 15_16_25.png]]
- 这个是雷达整个系统的框架。


还有就是相控阵雷达的基本信号处理：
- 一个 2D 相控阵雷达, 在拿到一个 radar datacube 后，接下来的信号处理一般是：
	- 先做 DBF，相当于 apply 一个空域的 filter, 然后再做 matched filtering 和  doppler processing, 在这个过程中会做 detection, 估计出目标的位置，角度，速度，还有 RCS，SNR 这些。
	- 当然 DBF，matched filtering, doppler processiing 这些东西的顺序都无所谓，先 DBF 是为了减少运算量，是工程上的考虑。


Next:
- data2 的 example ipynb, 还有 test code.

# 2026-04-20

todays plan:
- dataset EDA continue




# 2026-04-10


data1 的 EDA，以及 dataloader, dataset 都写好了。

Next, 回顾一下 data0 的 EDA，然后写 dataloader, dataset, 以及测试。
