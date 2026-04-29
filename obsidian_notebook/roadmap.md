# 2026-04-29

plan:
继续学习 basic radar signal processing

what I learn today:
- 今天这个学习方法有点意思，i.e. learn a codebase with AI
	- 就是说，目的是学习和理解一个 codebase, 对这个 codebase 建立一个 Mental model (或者说，人类学习任何东西，基本上都是在对这个东西建立一个自己能理解的 Mental model, 这个建立过程，最高效，最直接的方式，就是与这个东西进行 interation。 如果这个东西是个 codebase, 那么这个 interation 就更直接了，你可以直接上手去实验，然后验证自己的理解。)
	- 学习方法是：
		- 把这个复杂的 codebase 先分析其 overall architecture, 然后看看这个 code base 想要 implement 的 concept 是啥，建立一个对这个 code base 的 mental model (mental model 这个概念其实就是，你该怎么去想这个东西). 这个活是让 AI 来干的。
		- 然后让 AI plan 一个教学计划：
			- 这时候，其实可以用 plan.md 那个 idea 了，因为这个 plan 可能会随着学习者的实际的学习进度而改变。所以 plan.md 就因该是一个 Living document。AI 应该在与学习者互动的过程中，不断地去更新这个 plan.md 来修改学习计划。
		- 整个学习过程应该是这样的：AI 按照一开始的教学计划把教学内容给一点一点地呈现给学习者。
			- for each section in the tutorial plan:
				- show the content
				- 学习者会阅读并且尝试理解这个内容，这时候，学习者会追问一些问题.
				- 然后 AI 回答这些问题。
				- 最后，学习者主动总结一下自己对这个 section 的理解。如果 AI 觉得这个理解基本正确，就可以进行下一个 secction 的学习了；如果 AI 觉得这个理解不太对，就要指出来。
	- 我目前还没有 implement 这个 plan.md, 就只是用一个 session 来学习。不过这个学习系统可以探索探索，说不定，在教培机构已经有人这么做了。


技巧 Learned:
![[Pasted image 20260429112243.png]]
- 想要看某个函数的定义，可以用这个 peek
- 也可以直接 go to definition

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
