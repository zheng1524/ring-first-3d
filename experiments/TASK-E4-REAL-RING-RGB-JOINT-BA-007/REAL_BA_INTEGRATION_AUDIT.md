# REAL_BA_INTEGRATION_AUDIT

## 残差装配

```
r_ring_new = [ r_DXY_inner(256), r_DXY_outer(256), r_p, r_b ]
```
- `r_q`（原始离散边界）被**替换**，未与 DXY 项同时保留（避免重复计算）。
- `r_p`（材料区）/`r_b`（背景区）原样保留。
- 长度由 BA 内部 `rglen = len(ring_residual(...))` 自适应，稀疏矩阵行数同步。

## 失败与修复记录

| 现象 | 根因 | 修复 |
|---|---|---|
| `NO_BA_VERSION`，`cam @ K.T` 维度错误 | BA 调用 `ring_residual(pose, ob)` 只传 2 参，`K0=None` 被传给 `torus_contours` | 闭包捕获 `ns['K']` 作为默认内参 |

## 采样密度

`ring_vector` 逐点残差 + `sqrt(w/Σw)` 归一化，
`test_joint_loss.py::test_ring_vector_density_invariance` 证明 128/512 点结果一致。

## 退化保护

若某视角缺 DXY 观测，`make_residual` 回退到原始 `b` 并**记录**（不返回零向量）。
