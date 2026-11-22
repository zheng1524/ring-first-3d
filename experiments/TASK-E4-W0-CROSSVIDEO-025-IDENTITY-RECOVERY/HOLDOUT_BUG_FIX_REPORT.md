# HOLDOUT_BUG_FIX_REPORT

## 024 的两个错误

1. **单描述子查询**：`d = Ds[k][None]` 只有 1 行，而 `match_desc` 的 mutual 需要反向 `knnMatch(...,k=2)`，
   单行查询永远无法通过 mutual → **0 匹配**（024 的 `n=0` 是程序缺陷，不是"无证据"）。
2. **反向变换传 None**：`holdout_eval(..., inv=None)` 分支里对需要矩阵的代码传 `None`，反向从未真正执行。

## 025 修复

- **批量匹配**：`match_desc(all_landmark_descriptors, view_descriptors)`，一次匹配一张 HOLDOUT 图，
  再把 `(query_idx)` 映射回地标 ID（`p2_validate.py::batch_map`）。
- **双向**：`004->005` 用 `H`，`005->004` 用 `H^{-1}`，两侧都真实执行（`tests/test_025_contracts.py::TestDirections`）。
- **分类**：`MATCHED_VALID` / `MATCHED_HIGH_ERROR`(>10 px) / `NO_DESCRIPTOR_MATCH` / `NEGATIVE_DEPTH`；
  未匹配不记 0，也不判身份错误。
- **只读**：HOLDOUT 视角不进入 `VIEWS`、不参与 020 投票、不参与 RANSAC、不参与门限选择
  （`TestSplitIsolation` 断言身份证据视角与 HOLDOUT 无交集）。

## 结果

| 类别 | 004→005 | 005→004 |
|---|---:|---:|
| MATCHED_VALID | 12 | 16 |
| MATCHED_HIGH_ERROR | 0 | 4 |
| NO_DESCRIPTOR_MATCH | 64 | 16 |
| NEGATIVE_DEPTH | 0 | 0 |

有效合计 **28**，中位 **6.08 px**，p90 **7.63 px**。逐身份结果见 `IDENTITIES/HISTORICAL_020_IDENTITIES_STATUS.csv`。
