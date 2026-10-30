# Phase E E0｜RA 审查提交包（仅文档）

创建：2026-10-30，状态 `PROPOSED / NOT_APPROVED / NOT_RUN`。

此包是 `zheng1524/ring-first-3d` 仓库预定新增文件的目录树；**GitHub 写入 403，尚未提交至仓库，也未派发 Codex**。禁止把它误解为科研实验代码或已认证结果。

推荐审阅顺序：

1. `research/phase_e_neural/PM_STATUS.md`——静态仓库审计与权限/硬件状态。
2. `research/phase_e_neural/RA_REVIEW_REQUEST_E0_001.md`——独立 RA 审查要点及最多三个决策问题。
3. `research/phase_e_neural/E0_COMPETITION_PROTOCOL.md`——预注册 SDF/MapAnything 双臂和停机门槛。
4. `research/phase_e_neural/CODE_REUSE_AUDIT.md`——可复用模块及缺口。
5. `experiments/TASK-NEURAL-E0-COMPARE-001/TASK.md`——第一轮正式 **P0 审计任务草案**，尚未授权执行。
6. 同 Task 下 `EVALUATION_PROTOCOL.md`、`ACCEPTANCE.md`、`FAILURE_LEDGER.md`——评估/验收/旧失败登记。

需要将这些文件复制到仓库**相同相对路径**，不要更改已有冻结文件或旧实验分支，不需附上输入视频、权重、XYZ/GLB。上传者必须在独立分支做最小 diff + 显式文件 stage，创建 PR 供 RA 读；不能把 PR 自动合并，也不能把 `PROPOSED` 改成 `APPROVED_TASK`。

参考不可替代的实际证据：边界生长 `fa50f68f27fd1679276e3ac549322cda05fc4191`；MASt3R 分区 `4adfe3aac780bf319aebf9cdd137f42e1e0eb055`；视角/GT `432747735aad5df46df32a93f78b3c819c7797ed`；main治理 `02dee8092dce9f89d050bccca35aa51768988645`。
