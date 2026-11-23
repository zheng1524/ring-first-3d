# FIX_VERIFICATION

| 项 | 证据 |
|---|---|
| D7 极线评分 | `runs/G03/h_initialization/H_CANDIDATES.csv`：`epi` 非空（0.5–10 px 量级）、`epi_status=OK`、`n_fit_ids=7`；`SUMMARY.epi_available=true` |
| A2 F 公式 | `tests/test_final_math.py::T02` 3 项断言全部通过 |
| A3 隔离 | H/BA 输入仅 `rows_fit`；holdout 由 `holdout_stats` 独立生成 |
| A4 旧路线 | `runs/G03/triangulation/X_REF_ONLY.csv` 存在，且 M2 用该结构 |
| A5 Ring | `ring_vector` 含 mid 分支（代码）；`b` 项在 `RING_SCORES.csv` 的 M/I/C/O 中 |
| H 一次 | `T07` 通过 |
| 测试 | 4 tests：**3 PASS / 1 SKIP** |
