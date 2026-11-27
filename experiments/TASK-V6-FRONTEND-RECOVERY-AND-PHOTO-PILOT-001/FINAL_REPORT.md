# V6前端修复与照片小试：最终交付

固定6组12视频18照片的R1/R2全部执行完成，科学快照 `dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e`。原39组79视频基线未替换。

| 小试 | 有视频输出 | 视频Target Raw/Trusted | 原105目标保留 | 独立照片Raw/Trusted |
|---|---:|---:|---:|---:|
| R0基线 | 5/12 | 105 / 本轮未重评 | 105/105 | 未接入 |
| R1前端修复 | 11/12 | 205/205 | 105/105 | 未接入 |
| R2加入照片 | 10/12 | 181/181 | 84/105 | 12/18，均非空Trusted |

R1覆盖改善来自真实Ring边界恢复、保留原锚分量及零计划时有界初始化回退。Is7/R5/005仍只有至多2台准入相机，无法形成三Support。R2照片有17次注册输出但只对应12张物理照片；仅1次照片注册通过准入并用于2个Support元组，不能把照片出面当作姿态精度通过。

R2令Ip8.8/R5/004原21个视频Target全失。固定相机诊断显示，照片参与留出三角化和新增留出轨迹改变了验证/准入证据。**R2当前不推广全量。** R1虽保留105/105，但共同投影深度P95逐对差中位数+0.0256 mm，不能宣称一致性全面提升；请结合Raw图审阅这项代价。

- [中文三栏可视化](index.html)，本地服务：<http://127.0.0.1:8960/index.html>。
- [技术报告、完整机制与实际模块组合](TECHNICAL_REPORT.md)、[逐视频对照](VIDEO_COMPARISON.csv)、[全部源身份](SOURCE_MANIFEST.csv)、[共同105目标](COMMON_105_TARGETS.csv)。
- [真实Ring旧新点](figures/RING_BEFORE_AFTER.png)、[断连分量](figures/GRAPH_GP_Is_7.0mm_closed_R5_single_refY_005.png)、[独立照片输入](figures/PHOTO_INPUTS.png)。
- 单源Raw/四态/Trusted：[新恢复](figures/SINGLE_1.png)、[R10对照](figures/SINGLE_2.png)、[R5对照](figures/SINGLE_3.png)、[照片Target](figures/SINGLE_4.png)。
- [39项测试](evidence/TESTS.txt)、[产物审计PASS](evidence/FINAL_ARTIFACT_AUDIT.json)、[照片退化归因](evidence/R2_ZERO_ATTRIBUTION.json)。
- [复现与本地服务命令](REPRODUCE.md)、[受保护的全量启动/恢复方案](FULL_RUN_PLAN.md)。

正式403次HERO，开发尝试44次完整保留，合计447次低于540次预检预算。全部新Raw完成固定clean，原始面与Trusted子集校验通过。磁盘剩余约2.15 GB；实测外推全量保守需约13.72 GB，当前不足。RAW、模型及全量Mesh只留本地准确路径/哈希，未重复上传。

源码、报告、图表及必要日志交付分支：`exp/TASK-V6-FRONTEND-RECOVERY-AND-PHOTO-PILOT-001`。科学提交与报告提交分开；最终远端报告SHA由交接消息给出。本轮按附件停在小试审阅，不启动39组全量或照片优化变体。
