# E2.7 失败记录

状态TRAINING_STOPPED / NO_LEARNING。本轮A/B各仅1次真实Adam更新，最后安全模型都是step0。所有失败保留。

| ID | 类别 | 对象 | 原因/事实 | 证据 | 处置 |
| --- | --- | --- | --- | --- | --- |
| F01 | 科学硬停止 | A/B raw00745 extra | 首步均14/32<50%；原31/32 | metrics/COVERAGE_HISTORY.csv / Fig1–4 | 立即停止，累计各1步；不等3次、不改阈值 |
| F02 | 可信学习未实现 | 全部3源及small | extra87/96→A50/B51；small18/18→A10/B11 | metrics/PER_REFERENCE_METRICS.csv | 下降均标潜在失败；不剔除困难射线 |
| F03 | 几何收缩 | 完整真实网络 | 负区体素体积−66.7%/−65.7%；头部/下缘退缩，严格支持顶点0 | metrics/SURFACE_DIAGNOSTICS.json / Fig1/3 | 保存实际失败场；不是只输出偏移或解析球 |
| F04 | Anchor未获益 | B与A匹配首步 | B少量命中优势，仍同样硬失败，Anchor Loss较初始大幅升高 | metrics/A_B_COMPARISON.json | ANCHOR_NOT_BENEFICIAL，本轮配方限定 |
| F05 | 评价退化 | 12个实际source warp | 条件RGB更低，但解释覆盖全部下降 | metrics/LOW_COVERAGE_LOW_RGB_ERROR.csv / Fig4 | 全部POTENTIAL_FAILURE；不宣称photometric几何改善 |
| F06 | 未运行预算 | steps25/50/75/100 | 两组首步已停止，后续均NOT_RUN | checkpoints/ + metrics/A_RUN.json/B_RUN.json | 图明确留空；final-last-safe=0，unsafe1另存 |
| D01 | 只读诊断失败保留 | component-gradient sum→Adam | FP32分项线性和预测误差约1.31e−6，未达2e−7 | provenance/COMPONENT_SUM_ADAM_CHECK.json | 原FAIL保留；另按原backward累积核验1.49e−8，阈值未改，无追加更新 |
| D02 | 已修复分母表述 | post mesh CAD supported_N=0 | 零分母曾记录0比例，不能当无穿插 | provenance/POST_SURFACE_CAD_ZERO_DENOMINATOR_ORIGINAL.json / POST_SURFACE_CAD_CORRECTION.json | 改null/NOT_EVALUABLE；不改模型、训练判定或已有有分母检查 |
| I01 | 已解决上传事故 | 第一次增量push | HTTP408，客户端同时显示Everything up-to-date不能当成功 | provenance/GIT_UPLOAD_INCIDENT.json / 最终远端核验 | 原分支同提交正常重试，无force，无训练重启 |
| I02 | 已修复交付检查脚本 | validate.py首跑 | 条件表达式else缺空格导致SyntaxError；未进入数值检查 | runtime/VALIDATION_ATTEMPT001.log | 仅修语法后重跑只读完整性检查，未运行任何神经更新 |

图证：[零水平集](figures/Fig1_SDF_learning.png)、[三参考拟合](figures/Fig2_three_reference_fit.png)、[可见表面](figures/Fig3_visible_surface.png)、[多视角和覆盖](figures/Fig4_multiview_validation.png)。固定审计表、完整分母与八问答见[唯一技术报告](TECHNICAL_REPORT.md)。严资格支持面为空时CAD比例NaN，不能以0制造PASS。
