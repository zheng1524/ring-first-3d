# 002 独立审阅记录

审阅范围：common、observations_revision、pipeline_revision、consume_revision、visibility_revision、registration、dxy_full、visualize_revision。未修改科学或可视化实现；正式全量仍在执行，以下帧检查是当前快照，不冒充最终1700帧验收。

## 已关闭的 Important

1. 原消费者仅校验 INDEX 未检查所读子文件。现 validate_inputs 递归核验相机、CAD、RGB/Mask、完整 DXY 回执、曲线、二维 NPZ、源 OBS 和 source_files。IIa14/R5/004 实际调用追踪为281次校验，原遗漏类别全部覆盖。
2. 原 revision_key 漏掉实际复用001外层科学模块。现5个模块先与 BASE_INIT 的 git show 字节SHA比对，再纳入缓存键，每次使用重验。未发现实际源漂移。

## 科学与接口核验

- 实测单视频恢复LOCAL后首相机与原相机最大差0；源射线/坐标使用同一逆历史T，再按合格组件T转换。
- IIa22/R10、Is7/R5、IIa9.5/R5、Is14/R5的联合组件均为空；Ip4/R5仅005+006合格子集，007独立；全组JOINT_FULL_GROUP明确NOT_RUN。
- P/Q及法向/区间使用相同确定索引采样；P来自所选A/B真实集合，X不进入边界等式；合格子集不引入排除视频观测。
- CAD固定anchor；多起点固定同一p0先验/观测/权重；cap不当深度，invalid保持fixed_N分母。

## DXY实际数据检查

输入清单1700个唯一(case, frame)、79视频、39组；逐视频ledger索引与对应相机c2w长度一致，source_id和原帧ID一致。

已完整扫描218个具有COMPLETE回执的帧：210 OFFICIAL、8 PIXEL_ONLY。其中52帧有实际no-Q exact-V2候选池，158帧保留identifiability profiles，13帧为zero-P/Q-interval分支。逐帧核查selected ID唯一、未选profile或当前拒绝项；P/Q/X原global索引严格指回原像素；Q单位法向与有向区间合法；未发现错误。

另在后续301帧快照逐项比较PROCESS默认池与官方geometry_candidates.csv行数（排除新增pixel与no-Q补录项），全部一致、无遗漏。

no-Q过程通过真实pipeline._measure返回局部量current捕获，未由variants摘要伪造候选；默认A/B池从ObservedMeasurement.results读取。PIXEL_ONLY复用observable_P与exact_V2下层circle/ellipse求解，ring.valid与正式测量状态不伪造，候选不产生新的毫米量测。

## 可视化检查

源码全部RGB绘制仅为原图、紫色实际二维曲线、绿色当前三角主体可见投影；没有Mask线/填色、P/Q/X散点或独立CAD叠加层。绿色可见域自然包含Ring遮挡边界，不是额外画CAD。

实际目视检查IIa14/R5/005：RGB三幅纵排(990×1913)，三维及真实三角面剖面四幅纵排(1050×2625)，标题/图例位于图外。JOINT RGB为6×1，HTML/SVG均block单列。过程候选各图单条真实曲线且保留ID。

结论：当前无未关闭Critical/Important。全量结束仍需按最终冻结键核验1700帧回执和全部拟合/可视化，不能仅以FRAME文件存在数宣称完成。

审阅时源码SHA：

- code/common.py: `5eff8e27ab17acf4300d6021a1ab543b8e1b0b7f53601d5c3d7b7a4d982cce30`
- code/consume_revision.py: `c73656432c0132d93f141f8e3180f515a7cd116ae25aa1384202875c93c6abfc`
- code/dxy_full.py: `4fe42bc5fbe60b9a679cfff69f72e9134682b96c070ea0ac65c4482ed252701f`
- code/visualize_revision.py: `6e1ce9362bdb94eb4062c9d75065c40497aa16be87c49078f73d2c7da6452db1`
