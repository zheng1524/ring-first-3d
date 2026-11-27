# R1 配准入口和证据复核

本地输出在独立工作树 `TASK-V6-R1-REG-001/experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001/`，中文入口为 `visuals/index.html`。浏览器打开HTML；GitHub可直接浏览PNG。

## 冻结结果

`evidence/RUN_EVIDENCE.tar.gz`以本任务目录为相对根，保存`runs/R1_001/`。含六组原预测T、完整依赖回放、原始自动轨迹、BA held依赖、独立DLT、完整逐观测held、先验、源面采样和状态ID、全视频变换相机/地标、原Raw引用及阶段SHA。不包含视频、模型、重复完整网格或环境。

每组关键文件：

- `PREDICTIONS.json` / `PREDICTION_FREEZE.json`：首次预测和身份，保持冻结。
- `DEPENDENCY_REPLAY.json`：补齐配置/原内核回执后的求解器回放，相同T；不是重跑相机或DLT。
- `interfaces/{M0,M1,M4,M5}.json`：每视频T、公制尺度、相机与HERO同步规则、原Raw SHA与Target/Support。
- `{method}_CAMERAS_{A,B}.npz` / `{method}_LANDMARKS_GLOBAL.npz`：已变换的全视频相机与三维地标。
- `CLEAN_INDEX.json`：M5各源post-registration分类、面ID/状态/UV引用。仅适用于M5共同坐标。
- `EVALUATION.json` / `evaluation/*_HELD.json` / `COMMON_FINITE_DIAGNOSTIC.json`：完整分母与逐观测结果。有限子域辅助对照不替代完整分母。
- `CANDIDATE_SELECTION.json` / `CLEAN_INDEX_M4_CANDIDATE.json` / `interfaces/M4_CANDIDATE_WITH_CLEAN.json`：仅IIa14/R5，主结果审阅后选出的M4候选接口验证，不是新盲测。

Raw顶点始终引用原文件，以`V_world=V_local@R.T+t`重建一次；Clean仅`F[state==0]`。不能把M5的B侧状态用于M4，也不能只移动Mesh而不动对应相机。接口均标为candidate，不启动主体正式更新。

## 重新运行

依赖：本任务基础R1源码f78e854b、真实执行29874fe6；002已提交代码efa0adfb（M4及评价核）、虚拟001已提交代码537c2070（原rigid函数配置），原有venv/OpenCV/SciPy/Open3D和受保护V6科学内核。这里只复用代码；新实验不读历史H004状态。

精确输入路径和SHA在`config/*/ASSETS.json`，保留清单见`evidence/RETAIN_DEPENDENCIES.json`。工作空间迁移时只改路径解析并重新核对SHA，不替换来源版本。实际R1根来自LAUNCH回执，不能改回旧`v6_full_run_001`。

在新的独立worktree中、没有已冻结`runs/R1_001`时：

```bash
bash experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001/run_all.sh
```

脚本按测试→审计→预测/留一→全依赖回放→配准后Clean→评价→候选补充→图示→报告顺序执行。逐源CPU单线程，GPU不可见；资源预算不足则明确失败/让出，不触发上游调度器、HERO或分割重跑。

新增组须先从当前R1状态核验完整双视频身份，再建立新批次/配置；不能改写本批预测或因误差高换组。`candidate_clean.py`复现的是本次已披露的IIa14/R5补充，不是面向新数据的自动选优器。

只复核契约：

```bash
bash experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001/run_python.sh experiments/TASK-V6-R1-CROSS-VIDEO-REGISTRATION-001/code/test_registration.py
```
