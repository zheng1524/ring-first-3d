# Phase E｜统一神经几何重建项目经理启动资料包

状态：`PM_READY / E0_PROPOSED / CODEX_NOT_DISPATCHED`（2026-10-30）

## 用法

1. 在一个**新的 ChatGPT 对话或 ChatGPT Work 任务**中，将 `01_PM_INITIALIZATION.md` 全文作为第一条消息。若使用 Work，应授权访问已经连接的 GitHub；普通对话也可使用连接的 GitHub 查看仓库。
2. 同时提供本包其余文件，或让 PM 依据启动提示词读取。PM 必须**独立从 GitHub 读取**最新报告与治理规范，不以本包作为仓库事实的替代品。
3. PM 先提交项目状态审计和 `E0` 竞争实验草案，交由研究者与顶层设计者（本对话）审阅。**不得把创建 PM 视作允许 Codex 立即运行 GPU 实验的额外授权。**
4. 经用户批准任务书后，转交现有单实例 Codex。Codex 在独立分支执行、增量提交结果；PM根据 GitHub 报告验收；顶层设计者审查路线与方法选择；用户决定采纳。

## 仓库

- https://github.com/zheng1524/ring-first-3d
- 最新边界生长实验：https://github.com/zheng1524/ring-first-3d/tree/exp/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001/experiments/TASK-BOUNDARY-GUIDED-SURFACE-GROWTH-001
- MASt3R 视角分区实验：https://github.com/zheng1524/ring-first-3d/tree/exp/TASK-VIEW-PARTITION-MAST3R-FUSION-001/experiments/TASK-VIEW-PARTITION-MAST3R-FUSION-001
- 冻结规则：`AGENTS.md`、`COLLAB_STANDARD_v1.3.md`，优先以实际仓库版本为准。

## 文件

- `01_PM_INITIALIZATION.md`：独立 PM 的启动系统提示词。
- `02_E0_COMPETITION_PROTOCOL.md`：Neural SDF 与 MapAnything 的公平竞争设计。
- `03_E0_CODEX_TASK_DRAFT.md`：供 PM 核对、修订、送审的 Codex 第一轮任务草案，尚未批准执行。
- `04_RA_PM_CODEX_HANDOFF.md`：三角色异步协作、项目状态和报告交换规范。

## 权限状态

本次助理可读取仓库，但 GitHub 连接尝试新建分支、Issue 均返回 `403 Resource not accessible by integration`；因此**没有修改远程仓库、没有建立 GitHub Issue，也没有启动独立 PM 或 Codex 执行任务**。用户可以将本包交给具备 GitHub 写权限的 PM / Codex。若 PM 没有写权限，使用 Codex 通过其既有本地仓库工作树增量上传。

## 科研授权边界

Ring-First、HERO权重、冻结相机与原始 P0、Ring CAD、Dxy 主线保持不变；新学习路线是**派生候选分支**。GT 只可在方法和超参冻结后用于独立评价，不能用于选帧、拟合或选择模型。G07 不合格相机仅作为压力测试。Neural SDF 的网络只优化**单场景统一表示**；MapAnything 第一阶段只调用预训练权重推理，不要混淆两者的训练成本。
