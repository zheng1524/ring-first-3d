# FREEZE_TABLE_DECOUPLING_AUDIT

- R6 入口的 `if a.group != 'G03': BLOCKED_BY_W0_ADMISSION` 已**删除**；本轮入口 `core/u028.py` 无任何组名分支。
- 组名只用于选择：prepared 目录、`camera_mainline/<G>`、`assets/.../inputs/<G>/RING.npz`、任务输出目录。
- 历史冻结/准入表（`camera_mainline/CAMERA_ADMISSION_POLICY.yaml`、`admission.csv`）只作为**资产状态**读取：
  ACCEPT 视角优先；无 ACCEPT 时仍运行并标记 `NOT_ADMITTED_DIAGNOSTIC`，不阻断。
- G06 未出现在 `camera_mainline`，本轮**按其正式 W0 入口重算**（004: 8 ACCEPT, 005: 0 ACCEPT），未改主线资产。
- G01 全 QUARANTINE 但仍完整进入同一流程（Ring 1.014，identities 0）。
- 测试证据：`tests/test_u028_contracts.py`（组名替换不影响路径；无组分支；冻结表缺失不阻断）。
