# SE3_AND_RING_VALIDATION

## 变换顺序（D2）

`RingRenderer.losses(H_in)` 内部：`C = canonical(H_in @ T0)`。
因此给定**实际相机** `C_actual`，必须传 `H_in = C_actual @ inv(T0)`。

| 检查 | 结果 |
|---|---|
| `canonical(H_in @ T0)` vs `canonical(C_actual)` | 最大差 **1e-12** |
| 旧写法 `inv(T0) @ C` 的偏差 | **>1e-3**（可检出） |
| 与历史 `RingRenderer.losses` 的 M/I/C/O | **1e-12** 内一致 |
| `canonical_np` vs 历史 `canonical`（026 已建） | 0.0 |

## 张成与方向

- `H = H_005<-004`；004 相机 `C = H @ (Exp(δ) T0)`；005 相机 `C = Exp(δ) T0`（δ≡0）。
- 单位变换、平移、一般旋转、混合 6DoF、H/H⁻¹ 双向：继承 026-CORRECTIVE 的 6 项测试（矩阵差 7.1e-15）。

## 未完成

- `x_scale`、解析 Jacobian 与数值 Jacobian 的逐列比对：`NOT_DONE`。
