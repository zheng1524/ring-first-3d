# TASK-PHASEC-SPARSE-STRETCH-CLEAN-VIS-001｜结果索引

状态：ENGINEERING_COMPLETE / C档人工复核预览 / NO_STABLE_AUTOMATIC_THRESHOLD / STOPPED_FOR_REVIEW。

- [唯一技术报告](TECHNICAL_REPORT.md)：原风格恢复证据、全部参数、8组9视频13参考、三档39结果、失败与复现命令。
- [固定真实P0渲染入口](../../visualization/real_p0_renderer.py)及[来源配置](../../visualization/real_p0_renderer_provenance.json)。
- [参数](parameters.json)、[运行前协议](PROTOCOL.md)、[输入身份](metrics/input_identity.csv)、[输入哈希](provenance/INPUT_MANIFEST.json)。
- [39行逐参考结果](metrics/reference_results.csv)、[24行逐组](metrics/group_results.csv)、[正常/压力/形态/Ring分层](metrics/stratified_results.csv)、[来源区域风险](metrics/region_risks.csv)、[失败清单](metrics/failure_ledger.csv)。
- [推荐C与限制](metrics/recommendation.json)：spacing_ratio≥3且stretch_ratio≥3；无全自动推荐。
- [13项小检查](metrics/small_tests.json)、[197项核验](metrics/validation.json)、[143份本地派生资产哈希](provenance/OUTPUTS_FROZEN.json)。
- [可独立重放的新目录入口](code/reproduce.py)，依赖[requirements.txt](requirements.txt)与现有冻结本地数据，不重跑上游模型。

| 四张真实PNG | 内容 |
| --- | --- |
| [Fig1](figures/Fig1_004_Raw_Marked_Cleaned.png) | 004三个原参考、Raw/标记/Cleaned C，同原三维相机与尺度 |
| [Fig2](figures/Fig2_005_Raw_Marked_Cleaned.png) | 005三个原参考，恢复认可原侧视与Ring线点 |
| [Fig3](figures/Fig3_multigroup_C_cleanup.png) | Ip、Is、IIa及R5正常/压力条件与C档 |
| [Fig4](figures/Fig4_threshold_failures_and_stalk_risk.png) | C/M/A细柄代理放大、残留与主连续片切断反例 |

完整Raw/候选/三档Cleaned PLY与来源NPZ留在本任务`local_results/`，未上传；每个Cleaned均指向原点/原面索引。原P0与上轮D0/D1保持不变，GT未使用，DXY未修改。公开[文件清单](provenance/PUBLICATION_MANIFEST.json)不包含完整资产。

实际实现提交`f86ebfd09c182d5002d55e834185f42a6738e7eb`；指标/四PNG提交`428bd42f25cbcaa3ef61fc44e6c4a7dc8f20c357`；最终报告SHA以本文件所在提交及交付消息为准。远端读回后保存本地`provenance/REMOTE_RECEIPT.json`。本任务已停止，等待人工验收。
