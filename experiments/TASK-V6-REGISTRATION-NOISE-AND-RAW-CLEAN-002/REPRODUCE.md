# 复核与重跑

本任务只消费既有HIST、虚拟001及获准Clean依赖，不调用上游调度器。

## 直接复核已执行结果

- 中文图集：`visuals/index.html`（下载后浏览），各组PNG可直接在GitHub查看。
- 表：`evidence/CONTROL_RESULTS.csv`、`REAL_BIDIRECTIONAL.csv`、`REAL_CATEGORIES.csv`、`SURFACE_CONSISTENCY.csv`、`RAW_CLEAN_SOURCES.csv`、`FIT_LOO.csv`。
- 小型运行证据：`evidence/RUN_EVIDENCE.tar.gz`，相对本任务目录包含`runs/R002_001/`。含完整T、自动轨迹、逐条held、先验、逐源state/原面ID/UV、原面采样和阶段源码SHA。无视频、模型、重复网格或虚拟环境。
- 运行时源码：最初提交`de7351cd2b066534684b5025df3a68f7075706d9`、`evidence/EXECUTED_CODE_BEFORE_REVIEW.tar.gz`和本提交。按每个`*_START.json`的SHA选择，不以最终源码冒充早期执行版本。
- 大资产保持原位置，精确路径/哈希见`config/*/ASSETS.json`和`evidence/RETAIN_DEPENDENCIES.json`。不得清理这些保留依赖。虚拟001公开保护包位于其537c2070提交的`evidence/RUN_EVIDENCE.tar.gz`。

## 单进程重新执行

必须在**新的独立worktree**执行；不覆盖已冻结的`R002_001`，不改变现有全量目录。已选来源配置保持不变，不再次按效果选组。工作空间依赖路径已在`common2.py`列明；迁移只按SHA解析路径，不替换科学来源。运行环境为已有venv，入口统一通过`run_python.sh`限制CPU、线程、优先级和GPU。若无相应依赖，报缺失，不触发上游重跑。

在新worktree根目录：

```bash
bash experiments/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002/run_all.sh
```

此命令依次执行契约测试、受控prepare/predict/evaluate、真实track/clean/predict/evaluate、图示与汇总。每源都会重新检查≥3GiB余量与任务256MiB预算。先验和方法不随留出结果调整。复核现有包时只运行测试，不重算：

```bash
bash experiments/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002/run_python.sh experiments/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002/code/test_contracts2.py
```

`interfaces/<method>.json`保存每组T、尺度1、原Raw引用、Clean选择引用和同步相机/地标/曲面规则。均标为candidate_only，不代表质量批准或已启动主体拟合。
