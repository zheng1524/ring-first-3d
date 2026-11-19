# 标准流程补全 002

工作空间：`/home/liu/ring_first_3d_workspace`。基线提交：`2fe2c3cbda40bd4d0f8a15a3d71dad3f494a1c7f`。

唯一入口为 `code/standard.py`，顺序为：冻结输入 → 成熟 Ring/RGB 原生参考库 → Ring-First → 正式 HERO → EXACT013 → B1/B2 → 冻结预测 → GT/HOLDOUT → 报告/验收。

从工作空间根目录使用现有环境：

```bash
bash mainline/scripts/python.sh experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/standard.py check
bash mainline/scripts/python.sh experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/standard.py run --stage all
```

可单独指定 `--stage audit|banks|cameras|hero|body|evaluate|report|check`，以及 `--group G02 --video 005`。输入未冻结时，`audit/all` 会执行来源审计；首次科学执行前需通过测试门禁。回归入口为 `code/run_tests.py`，结果位于本任务 `logs/`。

已有输出直接复用，失败阶段保留状态；同一输入不会静默覆盖重跑。`audit/CLI_RESUME_VALIDATION.json` 实测已完成实例的 HERO/Body 恢复调用不触发新推理/训练，且冻结文件 SHA 不变。更换输入或算法需要独立任务版本。

参考库不足时，入口调用已有 V6 RGB 跟踪、yaw 初始化和**同视频**局部标定，再调用原 `features019.landmarks`。`code/frozen_calibration/` 是原成熟函数的逐字节副本，原位置和 SHA 在 `MATURE_CALIBRATION_SOURCE_LOCK.json`。最终相机仍使用原 native `recover`、RF_ONLY 来源过滤和 3px 门禁。原数值参数未调整，没有跨视频 BA。

REF_BUILD_REV1 补齐了先前遗漏的成熟构库步骤；REF_DENSITY_REV2 对仍缺乏完整 FIT 相机的实例，仅补充现成的同视频历史 FIT 图像。所有当前 HOLDOUT 以像素 SHA 排除，原八个 Body FIT、顺序、权重和全部 HOLDOUT 不变。历史结果在 `runs/BEFORE_REF_BUILD_REV1/`、`runs/REF_BUILD_REV1_RESULTS/`，当前实例在 `runs/RF_ONLY_V1/Gxx/00x/`。

001 中成功的四个 004 作为冻结引用，不重复训练。G03/004 仅对失败 HOLDOUT 做同参数诊断。新实例使用相同的 36 次外循环、Graph/Smooth ARAP/Sweep、Ring/投影保护及 HeroDepth018；B1/B2 仅切换深度项。原深度为相机轴向 Z，单位毫米，保存原生像素、有效性、Raw XYZ 和完整开放 Mesh。

GT 在 `ALL_PREDICTIONS_FROZEN_BEFORE_GT.json` 生成后才进入新实例评价，尺度固定 SE(3) 仅作用于评价副本。`body/*/FINAL.npz` 和 `exported/` 保留未对齐的公制世界结果。严格实体 IoU 不可评价时保留 NaN，条件占据和表面指标分别标注。

阅读 `report/FINAL_REPORT.md`、`report/PIPELINE_COMPLETENESS.csv`、`RESULT_CARD.md`、`FAILURE_REGISTRY.json`。静态图片入口为 `visualization/README.md`，没有 HTML。失败视角不删除，观测/匹配问题可通过 `visualization/FAILURE_DIAGNOSTICS/` 检查。

本机共享依赖沿用工作空间 `manifests/LOCAL_DEPENDENCIES.json` 和现有 venv；未安装新包或创建环境。原视频、ZIP、权重和历史数据保持原位。Git 只提交源码、报告、指标及精选证据；全部本机运行产物由 `RUN_MANIFEST.json` 的实际路径与 SHA 绑定。
