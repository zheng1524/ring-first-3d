# E2.5失败、不可评价与协议修复

| ID | 对象/步骤 | 失败或限制 | 处理及证据 |
| --- | --- | --- | --- |
| F01 | 新工作树初始化 | Git继承稀疏检出却缺新info目录 | 仅修复新工作树管理目录，旧库未reset/清理；provenance/AUTHORIZATION.json |
| F02 | P1投影预览 | 同B像素多A点最后写入不是首交点显示 | 改为现成A投影Z-buffer，重算P1预览；统计资格/残差规则未变，runtime/P1_DEPTH.log及P1_DEPTH_FINAL.log |
| F03 | 真实对应/H1–H4 | 循环/法向来自HERO，无法认证同一物理点；严格子集可能偏向一致 | 同时公开loose与conditional全分母，未知保留；[图1](figures/Fig1_depth_conflicts.png)、[资格流](metrics/PAIRWISE_QUALIFICATION_FLOW.csv) |
| F04 | D2偏移识别 | 相机/对应/材质混杂；004ref08 Ring偏差超±1mm界，物理偏移不可辨识 | 不clip、不拟合校正、不写HERO；[偏移决定](docs/DEPTH_CORRECTION_DECISION.md)、[图2](figures/Fig2_ring_depth_residuals.png) |
| F05 | 004/B ref13 | 合格HERO0/6命中；其他类别1命中不能补齐 | joint保持FAIL，不更换像素/候选；[初始化表](metrics/NEURAL_INITIALIZATION_AND_HITS.csv)、[图4](figures/Fig4_three_reference_gradients.png) |
| F06 | 005/A三源 | 各0/6命中；采样raw全负，ROI可见段缺前交点 | RGB/Depth保留NaN，三源FAIL；[真实梯度表](metrics/NEURAL_PER_REFERENCE_GRADIENTS.csv)、[图3](figures/Fig3_official_sdf_cpu.png) |
| F07 | 005/B三源 | 各0/6；采样raw全正、opacity0、当前Mask梯度0 | 识别官方密度正尾抵消及BCE clamp；不增第三候选、不训练；[尾部审计](metrics/LAPLACE_TAIL_CANCELLATION.csv)、[图3](figures/Fig3_official_sdf_cpu.png) |
| F08 | 漏命中loss退化 | 固定18观测下覆盖1→1/3，Depth2.087→0.902，joint0.690→0.595 | 明确判有潜在风险；离散选择不是梯度/真实场轨迹；all-miss拒绝不消除partial风险；[反例](metrics/DEGENERACY_SELECTION_COUNTEREXAMPLE.csv) |
| F09 | 稳定BCE首版 | uint8目标取负wrap255，错误负BCE；候选诊断无效 | 原输出及源码归档ATTEMPT001；浮点修复后只精确同种子重建两个B实例，参数SHA一致；[原因](provenance/STABLE_MASK_ATTEMPT001_FAILURE.json)、[复核](provenance/IDENTICAL_NETWORK_DIAGNOSTIC_REPLAY.json) |
| F10 | 选择反例控制 | B没有完整三参考命中，无法充当正常覆盖正控制 | 使用同一个既定legacy A作两个视频的诊断控制，非挑最好模型；005仍全未命中，不制造正常覆盖；实际连续偏移另列 |
| F11 | 官方sampler | CUDA分配及吸收夹持访问，未合法运行 | 仅FIXED_SAMPLER_DIAGNOSTIC_ONLY；两处CPU构造分配显式端口，GPU从未初始化，真实源码不改 |
| F12 | 数值审计辅助脚本 | source重复关键字导致首次解析失败 | 修复字段名为evidence后运行；不影响任何原始数据、主网络结果或科学阈值 |
| F13 | 新物理测量 | G01新重建/测量0/1，未正式训练；严格holdout0、绝对GT位姿未认证 | 误差NaN、历史回退0；没有把CPU模型/图像当高精度重建 |

本轮预注册两候选均保留；未删困难像素、未改变资格或阈值来制造PASS；失败研究Gate不因交付完整性通过而改变。旧资产未删除，HERO/相机/CAD/P0/Dxy未改，GT及目标像素未访问。
