# Technical change record

## v1.0 — 2026-11-03，正式新实验前

- 研究者确认无现成总技术MD，首次根据实际G01_004脚本创建docs/KEY_TECHNICAL_VERSION_v1.0.md。
- 新薄适配将Camera Gate相同规则扩至本轮候选，保留INSUFFICIENT_EVIDENCE并独立记录条件性入组。未修改冻结相机。
- 从旧F0适配层移除仅属于旧任务的几何质量提前停机；本轮完整正序与严格逆序。
- 按研究者新任务对每组独立冻结物理域；不复用旧固定27.959mm。
- 旧规范3px细柄硬门槛已撤销；不作为本轮门禁。
- 不修改历史代码/报告/输入。后续工程差异将在此追加。

## 工程修正（首次GPU之前）

- AST复用函数最初绑定到common命名空间，Camera Gate在任何测试前触发NameError；改为显式传入调用模块globals。原失败日志保留，无阈值变化。
- G06 ref04像素身份NPZ使用pixel_uv且没有重复存faces；适配层改为读取原Raw Mesh faces并逐顶点/像素反投影验证，仍完全使用原三角面。已完成G01固定清理通过SHA复用，没有再删一轮。
- prepare静态语法检查修正else空格；未影响数据结果。
- 当前全量输入/域已冻结：G01八源、G06五源。G01域20.106mm/128，G06域17.664mm/128；各组所有保留XYZ及实际CAD均入域。

## 仅评价与显示修正（26次推理之后，无GPU重跑）

- 面片类别最初仅以距清理输入<=0.25mm标记邻近；正式结果进一步要求真实相机投影Polyp有效深度、轴向差<=0.25mm、CAD不遮挡。旧近邻类别结果保留runtime/pre_visibility_label_metrics。固定射线分母和深度误差不变，全部Mesh不变。
- Figure 3按冻结输入中位XYZ定位局部放大，便于检查主体/侧面；仅显示窗口变化，flat/smooth使用同一几何。

## 复现交付修正（无新推理）

- 导出4145个累计屏蔽原生ID（含历史V6与本轮A/B），restore_inputs.py从原生HERO逐ID恢复13来源/26份native和crop文件，实测全部SHA精确一致。不依赖隐藏的V6缓存才能恢复输入。
- 当前infer/verify的冻结输入SHA核查改为相对于各自任务根解析文件，便于隔离复跑；数值SHA、输入、网络和26次既有运行不变。实际用于26次前向的infer代码SHA保存在各SEQUENCE_START/BEFORE_GPU中（b9711c8）。
- Figure 1缩短面板标题避免重叠；只改文字，所有几何/数据不变。
