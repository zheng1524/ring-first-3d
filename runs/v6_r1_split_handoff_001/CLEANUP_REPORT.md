# Cleanup report: B001_generated_delivery_duplicates

- Batch status: COMPLETE
- Release SHA256: `6c7a263e58f608bd63173d87c38a6b86a49e3b6c0710de105642f597b85c0d92`
- Protected manifest SHA256: `83def0b29434b131bc4352efb936b30d48d448c401121f0c0670186798ae3872`
- Asset class: exact duplicate generated delivery ZIPs in the old TASK-M2F9 worktree; retained byte-identical archives are in the workspace `experiments/` tree. No RAW ZIPs were included.
- Item counts: {"DELETED": 28}
- Logical bytes deleted: 43637086
- Attributable allocated-space recovery estimate: 43700224 bytes (only items whose pre-delete link count was 1; based on `st_blocks * 512`).
- Available bytes before / after: 2110484480 / 2154164224
- `df` available delta: 43679744 bytes; this is the net change and may include concurrent filesystem writes.
- Health: B worktree exists = True; protected anchors and all retained content hashes recorded in receipt.
- Remaining skipped items: 0; see per-item reasons in receipt.
- Receipt: `receipts/B001_generated_delivery_duplicates.json`

## 当前交接检查（2026-11-27T19:17:59+08:00）

- 暂无可执行清单：releases/ 仅 B001，已为 COMPLETE；cancellations/ 为空。未进行本轮删除。
- B001 核验：清单/保护哈希与回执一致；已删除路径不存在 28/28；保留副本 SHA256 匹配 28/28；保护锚点存在 3/3。
- 当前挂载点 `/dev/nvme0n1p3`（`/`，ext4），可用 2085220352 字节。本轮逻辑删除 0 字节、可归因分配空间回收 0 字节；本轮未执行删除，df 前后差值不适用。
- 有限目录分配空间快照（du -sB1）：

```text
4722688	/home/liu/ring_first_3d_workspace/runs/v6_r1_split_handoff_001
72953856	/home/liu/ring_first_3d_workspace/runs/v6_freeze_storage_cleanup_001
2568085504	/home/liu/ring_first_3d_workspace/runs/v6_full_run_001
```
- 后续需 B 发布新的 READY 批次；不得根据目录大小自行扩大清理范围。

## 新审计交接检查（2026-11-27T19:47:39+08:00）

- 审计通知 `AUDIT_COMPLETE_NOT_READY`；审计提案有 66,520 个候选，但 B 尚未发布新的 READY 释放批次。暂无可执行清单，本轮未删除文件。
- 当前 releases/：B001_generated_delivery_duplicates=READY；现有保护清单 SHA256：`83def0b29434b131bc4352efb936b30d48d448c401121f0c0670186798ae3872`。
- 当前挂载点 `/dev/nvme0n1p3`（`/`，ext4），可用 2061144064 字节。本轮逻辑删除 0 字节、可归因分配空间回收 0 字节；本轮未执行删除，df 前后差值不适用。
- 有限目录分配空间快照（du -sB1）：

```text
4726784	/home/liu/ring_first_3d_workspace/runs/v6_r1_split_handoff_001
72953856	/home/liu/ring_first_3d_workspace/runs/v6_freeze_storage_cleanup_001
2568085504	/home/liu/ring_first_3d_workspace/runs/v6_full_run_001
18329600	/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-FULL-B-001/experiments/TASK-V6-R1-STORAGE-REAUDIT-001
```
- 下一步由 B 将符合依赖与归档条件的精确文件发布为 READY 清单；A 再按锁与回执契约执行。

## A002_old_method_weights_20261127 (2026-11-27T11:57:17.591771+00:00)

- Audit evidence: `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-FULL-B-001/experiments/TASK-V6-R1-STORAGE-REAUDIT-001/TECHNICAL_REPORT.md`
- Status: COMPLETE; counts: `{"DELETED": 12}`
- Logical deleted bytes: 4729025498
- Attributable allocated block recovery: 4681433088 bytes (last-link `st_blocks * 512`).
- df available before/after/delta: 2076340224 / 6757744640 / 4681404416 bytes; concurrent writes may affect net delta.
- Receipt: `receipts/A002_old_method_weights_20261127.json`; release SHA256 `2998113effeed60da2b2a57afc3ad4a60be930c1a761d26a0505b3e7fa708cdd`; protected SHA256 `3bdb559f3fab31da2f603f2c994c8d444d3b00b7e0de41e588142412e563ed47`.

## A003_non_r1_arrays_ge_1m_20261127 (2026-11-27T12:04:42.659156+00:00)

- Audit evidence: `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-FULL-B-001/experiments/TASK-V6-R1-STORAGE-REAUDIT-001/TECHNICAL_REPORT.md`
- Status: COMPLETE; counts: `{"DELETED": 412}`
- Logical deleted bytes: 2173305378
- Attributable allocated block recovery: 2174205952 bytes (last-link `st_blocks * 512`).
- df available before/after/delta: 6756368384 / 8927358976 / 2170990592 bytes; concurrent writes may affect net delta.
- Receipt: `receipts/A003_non_r1_arrays_ge_1m_20261127.json`; release SHA256 `bba9adbabbd8c0e634f992c7a854294210164179cb1ad4e76adff5fc8148c662`; protected SHA256 `3bdb559f3fab31da2f603f2c994c8d444d3b00b7e0de41e588142412e563ed47`.

## A004_non_r1_arrays_ge_100k_20261127 (2026-11-27T12:09:48.308124+00:00)

- Audit evidence: `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-FULL-B-001/experiments/TASK-V6-R1-STORAGE-REAUDIT-001/TECHNICAL_REPORT.md`
- Status: COMPLETE; counts: `{"DELETED": 11431}`
- Logical deleted bytes: 6175069520
- Attributable allocated block recovery: 6200356864 bytes (last-link `st_blocks * 512`).
- df available before/after/delta: 8914825216 / 15051153408 / 6136328192 bytes; concurrent writes may affect net delta.
- Receipt: `receipts/A004_non_r1_arrays_ge_100k_20261127.json`; release SHA256 `e8ac95b6f3b0247569eff0ce89cf020f0f4b5eb76021f02d5b537e15ecf24c1f`; protected SHA256 `922da02561cafc6396e34c7bd5bf0af0fa5ce290a065332298caa3d879155ac8`.

## A005_non_r1_arrays_lt_100k_20261127 (2026-11-27T12:17:43.224357+00:00)

- Audit evidence: `/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-FULL-B-001/experiments/TASK-V6-R1-STORAGE-REAUDIT-001/TECHNICAL_REPORT.md`
- Status: COMPLETE; counts: `{"DELETED": 36663}`
- Logical deleted bytes: 455096842
- Attributable allocated block recovery: 533909504 bytes (last-link `st_blocks * 512`).
- df available before/after/delta: 15008448512 / 15502336000 / 493887488 bytes; concurrent writes may affect net delta.
- Receipt: `receipts/A005_non_r1_arrays_lt_100k_20261127.json`; release SHA256 `2190a4e66c06839f249344a2003394624b73c52499d25f2318f44a5a11568897`; protected SHA256 `922da02561cafc6396e34c7bd5bf0af0fa5ce290a065332298caa3d879155ac8`.

## 审计清理终结摘要（2026-11-27T20:18:55+08:00）

- 新执行批次：A002–A005，全部 COMPLETE；删除 48,518 个精确文件，跳过 0。
- 本轮逻辑删除 13,532,497,238 字节；按末链接分配块可归因回收估计 13,589,905,408 字节；四批 `df` 可用空间净增合计 13,482,610,688 字节。两者差 107,294,720 字节，可能包含同期写入与文件系统元数据变化。旧 B001 收益不计入。
- 当前可用 15496294400 字节；保护清单 v3 SHA256 `922da02561cafc6396e34c7bd5bf0af0fa5ce290a065332298caa3d879155ac8`。
- 剩余候选：旧可视化 4,331、Mesh/点云/场景 7,127、工作树副本 6,544；各自的代表图/消费入口/场景归档/消费者加载条件尚未满足，未执行删除。
- 技术报告：`experiments/TASK-V6-R1-STORAGE-CLEANUP-A-001/TECHNICAL_REPORT.md`；逐项身份和结果见 `releases/A00*.json`、`receipts/A00*.json`。
