# DEFECT_TO_TEST_MATRIX

| 缺陷 | 位置 | 修复前表现 | 修复 | 测试 | 结果 |
|---|---|---|---|---|---|
| D7 极线索引 | `epipolar_score` | `epi=None`、`score=1e6+ring` | 按 CSV 行位置选 FIT；返回状态字典 | `H_CANDIDATES.csv` 的 `epi`/`n_fit_ids`；`SUMMARY.epi_available` | **PASS**（G03/G06 true） |
| A2 F 方向/K 顺序 | `epipolar_score` | `K_ref`/`K_other` 互换 | `F=K_other^-T [t]× R K_ref^-1` | `T02`（真实对应<1e-8；5° 错 H>1px；交换顺序一致） | **PASS** |
| A3 HOLDOUT 泄漏 | `main` | 全部身份进优化 | FIT-only + 独立 holdout 路径 | `SPLIT.json` + `REPROJ_HOLDOUT_*.csv` | **PASS**（代码级） |
| A4 旧路线顺序 | `main` | H=I 下先共同三角化 | 参考 FIT 三角化 → H-only → 共同三角化 | `triangulation/X_REF_ONLY.csv` | **PASS** |
| A5 Ring I/C/O | `ring_vector` | 仅 I/O | 加 Centerline；空边返回 None | `T05` | **SKIP（D11）** |
| H 一次 | `solve_pipeline` | 角色判断错误 | role 映射 + 仅 W0 相机 | `T07` | **PASS** |
| D10 U 路径 | `u028c.py` | 写入旧目录 | U 指向 FINAL，结果迁移 | 清单/manifest | 已修 |
| D11 测试路径耦合 | T05 | 找不到 R6 VIEWS | — | — | **未修（skip）** |
| D14 W0 重放 | `w0_ensure` | 未演练 | — | — | **NOT_EXECUTED** |
