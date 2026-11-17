# Failure ledger — 2026-11-03

失败保留，未修改历史Gate A/A2/F0记录，未按输出结果重选参数、来源或域。完成全部26前缀后停止。

|ID|范围/状态|原因、证据及处置|
|---|---|---|
|E01|总技术版本，RESOLVED|原先无总MD。研究者明确授权调研建立首版，见../../docs/KEY_TECHNICAL_VERSION_v1.0.md。没有伪造旧版本。|
|E02|Camera Gate启动，RESOLVED|AST函数绑定默认common命名空间导致NameError，发生在第一项数值检查前。显式globals修复，日志runtime/camera_gate.log保留；阈值未变。|
|E03|prepare静态语法，RESOLVED|else0缺空格，静态检查阻止运行后修复，无数据结果受影响。|
|E04|G06原始面接口，RESOLVED|ref04身份NPZ无original_faces，使用pixel_uv。适配读取原Raw Mesh faces，逐顶点和原归档像素反投影验证同一几何。已完成G01清理按SHA复用，未重删。日志runtime/prepare.log保留。|
|C01|G01八源，UNRESOLVED|八源均保留INSUFFICIENT_EVIDENCE身份；有充分RGB关系但仍缺指定参考关系/部分关系未通过。条件性研究入组不是严格认证，见metrics/CAMERA_QUALIFICATION.csv。无GT相机结论。|
|C02|G01 growth_r01，NOT_ADMITTED|Ring p95=12.4px，超过明确矛盾12px。未以放宽规则恢复，不参与八源。|
|C03|G01 new_r00，CONDITIONAL_RISK|Ring p95=6.708px，不满足6px通过线；没有达明确矛盾线。本轮按允许制度有风险使用，不能负向投票，不假装合格。|
|C04|G06八源迁移，NOT_AVAILABLE|只有5份真实原生HERO，只能完成正/逆F0–F4。没有新HERO，也没有复制重复源凑8。|
|I01|清理孔洞，POTENTIAL_SURFACE_LOSS|G01额外屏蔽1072点，净新增闭合孔洞463像素；r14其中362像素位于最大Mask组件并成孔。G06额外屏蔽29点，新增4孔洞像素。原r14历史507头部缺口仍在。不能声明清理无损，见metrics/*_CLEANUP_SUMMARY.json、HEAD_STALK_SIDE_INPUT_PROXIES.csv。|
|I02|G01原始帧号，UNRESOLVED|004_XX精确绑定缓存RGB SHA，不等价于独立核验原视频解码帧号。历史帧元数据不一致，不据缓存序号编造真实raw帧。增强方案须先解决身份映射。|
|S01|G01可信首源退化，OBSERVED|ref08首次深度一致率9742/13250=73.52%→62/13250=0.47%；p95约2.50mm。总体一致率提高不能掩盖。见Fig4及各前缀*_RAYS.csv。|
|S02|G01多层/多壳，OBSERVED_PROXY|≥4次真实射线交点比例6.44%→66.43%，组件113→273。闭合壳前后两次并非自动错误；四次以上是重复/多层代理，不等价解剖GT。见MULTILAYER_RAY_DIAGNOSTICS.csv。|
|S03|未知边界封闭，RETAINED|官方式unknown正哨兵使全部网格watertight；G01/G06最终约40.34%/57.02%面邻接unknown。全部原样保留并标记，不删面制造结果。|
|S04|封闭不是唯一原因，OBSERVED|G01 ref08的13065个bad首交点中12895位于all8-known MC单元，仅170为unknown边界代理。G06对应1114/1173。几何误差不能只归咎渲染或unknown设置。|
|S05|相互冲突的输入，UNRESOLVED_PROXY|多份G01清理源投影至ref08存在约0.5–1.6mm的中位轴向提前，跨源/相机不确定性未校正。官方局部窄带融合不强制本项目单层自由空间一致性，可能保留多个深度层；没有为获得单层而私改网络。见INPUT_CROSSVIEW_DEPTH_DIFFERENCES.csv。|
|S06|G06浅表面/台阶，OBSERVED|首次一致率46.65%→61.39%，但F3后下降、growth_r03最终仅约6.9%一致。坐标轴法线约53%，图见台阶/封闭环带，平滑法线仅显示差异，不能算几何修复。|
|S07|逆序局部差异，MEASURED|最终总体接近但不相同，G01双向面距p95约0.040/0.048mm，极值0.336/0.776mm。均保留，不挑好顺序。|
|M01|历史Open3D非配准消融，LIMITATION|同一固定观测分母可作描述比较，但旧6源/原生清理前/.1mm，和新8源/.157mm不同。不能解释为纯算法性能差；G06历史Open3D未核验可用，记NOT_AVAILABLE，未新跑TSDF。|
|M02|评价标签修正，RESOLVED_WITH_RECORD|初版仅用最近点距离标记邻近；正式版增加真实相机有效深度及CAD未遮挡要求。旧版结果保留runtime/pre_visibility_label_metrics；射线误差/分母/Mesh未改，变更记TECHNICAL_CHANGELOG.md。|
|P01|20–30视角，PLAN_ONLY|现有资源24份分属G01 16/G06 8，不能合成一组；G01单组不够20。待补真实帧、身份、当前Gate及新HERO，详见增强方案，本轮没有增强推理。|

所有结论是HERO和候选相机条件下的几何证据；未将Mask、最近距离、闭合性、支持标签当物理GT。失败不是通过删掉困难源、只报命中均值、缩小分母或Mesh修复隐藏的。
