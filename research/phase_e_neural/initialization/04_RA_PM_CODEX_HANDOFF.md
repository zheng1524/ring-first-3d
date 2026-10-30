# Phase E｜RA—PM—Codex GitHub 协作协议（建议版）

## 角色

- **研究者**：批准路线、具体执行范围，验收科学结果。
- **RA（本对话）**：方法和文献设计、竞争公平性审阅、异常结果的独立技术判断；不抢Codex执行权限。
- **PM（新对话）**：持续阅读仓库、维护阶段状态、出Task、完成独立验收、发起RA复审请求；不修改上游算法或替用户批准科学任务。
- **EX（现有Codex）**：唯一实现者；在本地独立工作树执行已批准任务、写日志/核心图/技术报告、增量提交与推送。

## 推荐仓库协作目录

```text
research/phase_e_neural/
  PM_CHARTER.md
  PM_STATUS.md
  E0_COMPETITION_PROTOCOL.md
  RA_REVIEW_REQUEST_E0_001.md
  RA_DECISION_E0_001.md
  DECISION_LOG.md
experiments/TASK-NEURAL-E0-COMPARE-001/
  TASK.md
  TECHNICAL_REPORT.md
  RESULT_INDEX.md
  REPRODUCE.md
  config/
  metrics/
  figures/
  provenance/
```

PM可通过工作树创建这些**新文件**，但不可假设当前仓库已经存在。现有仓库治理规则优先于本建议。

## 有效工作流

**阶段 0（这次）：** 用户批准“组建 PM + 设计E0竞争”；PM先只读审计、查官方实现、起草任务。状态`PM_READY / E0_PROPOSED`。

**阶段 1：** PM将同一份 `RA_REVIEW_REQUEST_E0_001.md` 及协议、Task草案保存/提交 GitHub，或在缺写权限时由现有Codex代为上传**文档，不运行模型**。告知用户/RA 文件链接。

**阶段 2：** RA阅读 PM 的 GitHub 文件，提供 `RA_DECISION_E0_001`：接受、需修改、拒绝，并给出最多3个关键改动。

**阶段 3：** PM按RA意见更新 Task，研究者明确批准具体工作包及GPU预算；状态`APPROVED_TASK`，才可交由Codex执行。若只授权审计，不自动扩成批量训练。

**阶段 4：** Codex单实例执行，分阶段上传核心图、真实指标、failure ledger与技术报告。每次提交路径、SHA与数据版本。

**阶段 5：** PM审计结果并按同一指标比较两臂。争议问题请求RA复审。研究者决定`ACCEPTED/REJECTED/CONTINUE/REVISE`。未通过的候选保留，不擅自删除。

## 让RA与PM减少转发的办法

PM每次把完整研究证据写进固定GitHub路径；RA可以直接用已连接的GitHub工具按路径读取。用户在RA本对话只需要一句：**“审阅 E0 的最新 RA_REVIEW_REQUEST”**，不需要搬运全部表格与图片。

不过，不同ChatGPT聊天不会因为GitHub有新commit自动互发消息、自动创建下一轮Codex任务。没有主动授权的自动化时仍需一次简短消息发起RA审阅或PM工作。若GitHub暂时不能写，先让已有Codex仅上传文档，之后走同样流程。

## PM状态模板

```markdown
# Phase E PM Status
- Last verified ref/commit:
- Scientific state: PM_READY / E0_PROPOSED / APPROVED_TASK / RUNNING / REPORTED / REVIEWED
- Researcher authorization:
- Arm S: repo/weights/input status
- Arm M: repo/weights/input status
- Data groups: G01 normal, G06 normal, G08 limited, G07 unqualified stress
- Heldout identity frozen: YES/NO (with source SHAs)
- GT usage: NONE / POST-FREEZE_EVAL_ONLY
- Hardware status: GPU_AVAILABLE / CUDA_BLOCKED / NOT_CHECKED
- Latest core figures:
- Known failures / NOT_EVALUABLE:
- PM next action:
- Request to RA (maximum 3 questions):
- Researcher decision needed:
```

## 不变的科研边界

来源真实、Ring CAD固定、视觉支持与推测补全区分、毫米单位审计、单视频先于跨视频、相机不合格组单列、GT只可后验、Dxy主线绝不被3D任务修改。展示级、融合级、物理测量级成果严格区分。
