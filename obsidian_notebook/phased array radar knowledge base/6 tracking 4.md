
Radar 每个 dwell 输出一批 detections。

每个 detection 是某个时间点上的一个 measurement，
通常包含位置，有时还包含速度、多普勒、强度、协方差等信息。

这些 detections 没有身份。
Tracker 维护一组 tracks。
每条 track 是 tracker 对某个目标状态的估计，
比如位置、速度、历史、置信度、miss 次数等。

每个新 dwell 到来时，tracker 会：

1. Predict:
   用运动模型把已有 tracks 预测到当前时间。

2. Associate:
   把当前 detections 和已有 tracks 做匹配。
   也就是判断哪个 detection 属于哪个 track。

3. Update:
   用匹配到的 detection 修正 track 的位置和速度。

4. Initiate:
   对没有匹配到任何 track 的 detections，可能创建新 track。

5. Delete:
   对连续 miss 太多次的 tracks，删除。