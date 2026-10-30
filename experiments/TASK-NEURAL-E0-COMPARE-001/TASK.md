> 当前任务已获用户有限P0/P1授权，并完成一次SDF优化及Map M0–M3真实运行；未形成有效双臂科学对照。当前状态见 [TECHNICAL_REPORT.md](TECHNICAL_REPORT.md) 和 [USER_STEERING.md](USER_STEERING.md)。下方为原附件草案。

# TASK-NEURAL-E0-COMPARE-001｜P0 Codex 首轮正式任务草案

**状态：`PROPOSED / NOT_APPROVED / P0_AUDIT_ONLY`**。这是一份可审查的正式任务书，不等于用户批准执行。任务 ID 为未来 E0 竞争总 ID，但**本次拟授权范围仅 P0**；P1 小规模 GPU 烟测及 P2–P4 正式比较需后续逐项批准。

## 0. 新 Codex 启动指令

你是新初始化的单实例 Codex 执行者（EX），项目为 `Reference-Ring Anchored Visible-Surface Reconstruction of Polyps`。首先读取当前仓库 `AGENTS.md`、`COLLAB_STANDARD_v1.3.md`、`README.md` 和 `PROMPT_CODEX.md`，然后读取本任务与 `research/phase_e_neural/{PM_STATUS,E0_COMPETITION_PROTOCOL,CODE_REUSE_AUDIT,RA_REVIEW_REQUEST_E0_001}.md`。只执行研究者明确标记 `APPROVED_TASK` 的工作包；如仍为 `PROPOSED`，只可汇报审阅建议，不运行脚本。本新任务不得声称替代旧实验 Codex 的自动交接。

来源优先使用：

- 边界生长 `fa50f68f27fd1679276e3ac549322cda05fc4191`；`experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/{TECHNICAL_REPORT,RESULT_INDEX,REPRODUCE}.md` 和 provenance。
- 分区 MASt3R `4adfe3aac780bf319aebf9cdd137f42e1e0eb055`；对应三件核心文件、`CODE_REUSE_AUDIT.md` 和 provenance。
- 视角/GT 资格 `432747735aad5df46df32a93f78b3c819c7797ed`。
- 主分支 `02dee8092dce9f89d050bccca35aa51768988645` 是 BOOTSTRAP_ONLY，禁止误作已冻结三维算法 baseline。旧数据/源码保留在本机只读路径，禁止在旧脏 main 工作。

## 1. P0 唯一目标（禁止模型执行）

形成可复算的 E0 输入资格与工程复用证据，回答“在什么单视频/来源/留出帧资格下，两个臂能否合法且低成本地进入 P1 烟测”。不要安装新版本、修改驱动、下载模型权重、跑 HERO/MapAnything、训练 SDF、批量推理或新配准。

### P0-A 仓库与本机资源

1. 创建独立工作树/任务分支（获批准且确认工作树无用户未提交改动后）；只写新任务目录和 Phase E 文档，显式 `git add`，不移动/删除旧缓存。不修改 `Ring-First`、`HERO` 权重、原 P0、相机、Ring CAD、DXY-MID。
2. 只读检查本机历史实际文件、大小、SHA 与依赖闭包：14 历史可读参考、22 新增 HERO 成功参考及 2 个失败输入分别列出；区分可能重叠的源图和同一个 HERO batch 输入。记录总 36 个参考的来源依赖图，不把 36 当独立样本。
3. 复核 `CODE_REUSE_AUDIT.md` 中 `camera_frame_inventory`, `source/target_source`, `load_official`, `unproject/depth_mesh`, `cleaning`, `A→B common_metric`, `cad_audit`, `real_p0_renderer`, GLB 导出；输出函数签名、测试入口、源码 SHA、许可/本地路径状态和“只需 adapter”的方案，禁止自建第二套渲染/反投影。
4. 无系统改动做 GPU 诊断：`nvidia-smi`、`torch.__version__`、`torch.version.cuda`、`torch.cuda.is_available`、一次极小 CUDA tensor、显存/磁盘/驱动；如失败留原始错误和时间，状态 `RUNTIME_BLOCKED`。不得重置驱动、改内核、静默 CPU 跑模型。

### P0-B 四组与视角冻结准备

1. 以 `physical_scene_id` 整理 G01/G06/G08/G07 共 **4 组、5 视频场景**，G01 video004 与 005 的局部 Ring 坐标独立；photo001–003 未认证只作诊断。G07 不合格相机压力；G08 有限；G01/G06 正常条件也仅为候选相机，不是 GT。
2. 每个样本一行清单：`group_id, video_id, source_id, RGB_SHA256, mask_SHA256, K_raw, K_after_resize, distortion, c2w, pose_status, coord_frame, native_depth_SHA, HERO_input_image_SHAs, raw_xyz_SHA, cleaned_flags_SHA, train_or_holdout, leakage_reason, eval_eligibility`。路径可 `LOCAL_ONLY`，完整清单 JSON/CSV 保存在任务 `provenance/`，禁止上传视频、大 NPZ、权重。
3. 复核历史两个不同的“留出”：分区任务 004 旧 ref08/ref13 曾被当 holdout；边界生长有 9 个非本轮新增参考目标但 `whole_pipeline_blind=false`。静态全来源去重后仅**提出** E0 `HOLDOUT_STRICT` 与 `HOLDOUT_RECON_ONLY` 名单；如果无法证实，标 `DIAGNOSTIC_ONLY/NOT_EVALUABLE`；尚不得在训练或结果之后优化选择。
4. 对每组检查 `mm↔m`, K resize, distortion, OpenCV cam2world, positive Z, optical Z-depth vs along-ray, CAD Occlusion 投影。做可人工复核的**静态值/单点投影测试**，不需要调用新模型；源标签任何异常先停止，禁止造 K/pose。
5. GT 文件路径可在排除清单中登记，但 E0 模型输入 loader 必须显式 `GT_ACCESS=DENY`；不读取 GT 网格确定采样/选择帧/对齐。

### P0-C 官方路线可执行性审计

1. MapAnything：固定官方 repo HEAD/版本和要用的合法 checkpoint revision/许可。对照官方 `preprocess_inputs`/`model.infer`，逐项说明 M0/M1/M2/M3 需要的 shape、dtype、相机参考、Z-depth 单位、K resize、输出字段；估计 6GiB 内存风险及权重缓存/下载需求，**不真正加载模型**。
2. SDF：审查 MonoSDF、NeuS2、SparseRecon 的官方许可、依赖和现有代码改造入口；首选候选和明确次选各 1 个，给 6GiB 运行/编译风险及 S0 深度+mask 适配工作量。不要承诺已能训练。
3. 整理 P1 具体最小烟测计划：同一组最小 2–3 合格视角或现有更少可评估输入、固定分辨率、预算上限建议、预计 GPU 峰值、单次成功判定（张量数值有限、坐标/单位/可追溯性通过）。**P1 仍需单独审批，不执行**。

## 2. 必须交付（均不含推理结果）

`experiments/TASK-NEURAL-E0-COMPARE-001/` 内：

- `TECHNICAL_REPORT.md`：唯一中文报告；200–350 字摘要、完整资产分母、来源和不可评价状态、官方路线/风险、失败、下一步 P1 审批范围；不能把读过论文等同运行成功。
- `RESULT_INDEX.md`、`REPRODUCE.md`：静态审计复核说明；命令只检查，不重跑模型。
- `provenance/INPUT_ELIGIBILITY.json`, `SOURCE_LEAKAGE_LEDGER.csv`, `SOURCE_SHA_LEDGER.csv`, `MODEL_DEPENDENCIES.md`, `ENVIRONMENT_CHECK.json`, `FRAME_CONVENTION_TESTS.json`。
- `metrics/FOUR_GROUP_READINESS.csv`、`metrics/SMOKE_TEST_PLAN.csv`（只计划，无 GPU 结果）。
- `figures/` 中 3–4 张**数据来源的核心复合图**：①4组真实 RGB/Mask/可用源 ②相机+Ring/视角与资格 ③36 参考来源、HERO 输入重合及留出污染矩阵 ④两臂数据/坐标接口与失败门禁。若本机无有效图像，图明确 `NOT_AVAILABLE`，不得造图。其他图库仅本地。

G01 图必须标 `SINGLE-VIDEO RECONSTRUCTION — video004` / `SINGLE-VIDEO RECONSTRUCTION — video005` / `CROSS-VIDEO CANDIDATE — NOT FUSED`；P0 没有新重建，图题要写 `HISTORICAL INPUT AUDIT` 避免冒充 E0 模型输出。

## 3. 验收、停机、Git 范围

- 验收 A：每个来源有明确 SHA/缺失原因、36 参考依赖去重和冻结状态；与历史 4 组/5 视频分母一致；旧成果不覆盖；全流程/仅重建留出身份分离。
- 验收 B：至少一条**潜在** SDF 和 MapAnything 官方合法最小调用链通过代码/接口静态审计；权重未下载、模型未运行；不能把可行性预测当 smoke test 成功。
- 验收 C：冻结坐标契约所有例子数值一致；不合格相机和可能泄漏的评估行标 `NOT_EVALUABLE`；GPU 故障单列 `RUNTIME_BLOCKED`。
- 停止：遇到源图身份矛盾、GT 路径进入输入、改变冻结代码要求、需要新增权重下载/运行、新训练、许可不清、硬件故障，保留证据并停止相应工作包，不以用户未批准的 P1 继续。
- Git：仅独立新分支 `exp/TASK-NEURAL-E0-COMPARE-001` 和**本任务新增文件**；禁止 `git add .`、`git clean`、强推、旧 main 写入、全量缓存、模型权重、原视频上传。分阶段推送①审计/测试/配置②小表与3–4图③唯一报告和 SHA。记录任何推送失败；不能假称 GitHub 已同步。

最终回传 PM：Task ID、commit SHA/PR、报告、四组状态、最关键负面证据、需要 P1 审批的确切下载/运行时长/显存/磁盘预算。至此**停止等待 RA/研究者批准**。
