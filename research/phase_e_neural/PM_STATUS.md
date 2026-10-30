# Phase E 项目状态（PM 只读审计）

- 日期：2026-10-30（Asia/Shanghai）
- 状态：`PM_READY / E0_PROPOSED / CODEX_NOT_DISPATCHED / RA_REVIEW_PENDING`
- 科研授权：允许审计、制定协议和任务书；**不授权执行 GPU、下载权重、训练或修改冻结算法**。
- 仓库：`zheng1524/ring-first-3d`；主分支 `main` SHA `02dee8092dce9f89d050bccca35aa51768988645`，仍为 `BOOTSTRAP_ONLY`，未认证独立三维正式 baseline。
- 最新边界生长：`exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001` SHA `fa50f68f27fd1679276e3ac549322cda05fc4191`；状态 `REPORTED / EXPERIMENTAL_RUNTIME_LIMITED`，非科学验收。
- 前次 MASt3R 分区：`exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001` SHA `4adfe3aac780bf319aebf9cdd137f42e1e0eb055`；状态 `COMPLETED / EXPERIMENTAL`，非科学验收。
- 相机/GT 资格补充：`exp/TASK-VIEW-OBSERVABILITY-GT-EVAL-001` SHA `432747735aad5df46df32a93f78b3c819c7797ed`。
- 数据：4 个物理组 / 5 个单视频场景。G01（Ip/R10）004 与 005 先独立；G06（IIa/R10）正常条件；G08（IIa/R10）有限条件；G07（Is/R5）不合格相机压力测试，不计正常成功率。
- 真实输入：仓库中有来源/相机/哈希登记和小型表、代码/核心图；原视频、完整深度、完整 XYZ/GLB、模型权重仍为实验机 `LOCAL_ONLY`，当前 PM 无法校验它们在执行机的物理存在或哈希。
- 留出帧：`NOT_FROZEN_FOR_E0`。历史分区任务发现 G01_004 两帧与旧 HERO/P0 源重合、G08 无预冻结独立留出；边界生长的 9 个目标为非本轮新增参考，但均标 `whole_pipeline_blind=false`，旧 HERO 来源可能不完整。不得无审计复用为真正盲测。
- GPU：`CUDA_BLOCKED_IN_LAST_GROWTH_RUN / CURRENT_STATUS_NOT_CHECKED`。video005 两次 `cur_image.to(device)` unspecified launch failure；新进程 `torch.cuda.is_available=false`、CUDA arange 失败；`nvidia-smi` 可见 RTX 3060 Laptop 6 GiB 不等于 GPU 可用。任务执行机需重新只读检测。
- Arm S：SDF 成熟开源实现可调查，但尚未确定兼容 6 GiB、Torch/CUDA 的基座，更未完成烟测；`NOT_RUN`。
- Arm M：官方 MapAnything 支持 RGB、K、`depth_z`、OpenCV cam2world `camera_poses` 等；当前版本/权重在实验机未固定、GPU 可行性未知；`NOT_RUN`。
- GT：仅允许方法和配置冻结后的独立评价；Blender 形状 GT 真实部署变换未知，绝对三维表面精度 `NOT_EVALUABLE`，不得 GT-ICP 选择赢家。
- GitHub 写权限：当前连接可以读取，但 2026-10-30 创建 `pm/phase-e-e0-review-001` 返回 `403 Resource not accessible by integration`；**本方案未上传、未创建 PR/Issue，也未通知 RA 或 Codex**。待权限修复或由有权 Codex 只上传这些文档。

## 审计后的关键结论

1. 边界生长工程输出覆盖 4/4 物理组与 5/5 视频，300 次接纳及 22/24 次成功新增 HERO；不是 300 个独立样本，也不是物理三维正确率。G01 的共同像素 RGB 恶化，004/005 旧 S0 点经 Joint 后分别额外产生 19/21 个 Ring CAD 内点；跨视频仍 `NOT FUSED`。
2. MASt3R 分区任务已经实跑 18 次 MASt3R、5 次新增 HERO；G01_005 非自投影覆盖约 +5.21 个百分点，但共同 RGB MAE 略恶化；G01 跨视频双向轴向冲突 65.90%/70.40%，不能联合认证。
3. 对神经方法的首要风险是相机与深度不一致、真正独立留出不足、GPU 运行阻塞和本地大数据未上 Git。E0 必须先过静态数据资格与运行门禁。

## 下一交接

请 RA 阅读 `RA_REVIEW_REQUEST_E0_001.md`、`E0_COMPETITION_PROTOCOL.md` 与 `TASK.md`，写 `RA_DECISION_E0_001.md`。研究者批准某一明确定义的 Task 和预算之前，Codex 不开始执行。PM 在报告到仓库且获独立审计后更新状态。
