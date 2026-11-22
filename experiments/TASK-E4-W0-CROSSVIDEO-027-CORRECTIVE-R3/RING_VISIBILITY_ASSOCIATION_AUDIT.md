# RING_VISIBILITY_ASSOCIATION_AUDIT

用 GT / 3° / 12° 偏差的相机选择 CAD 可见边，**始终在 GT 相机上**计算 Ring 能量（`runs/controlled/VISIBILITY_ASSOCIATION.csv`）：

| 边缘来源 | E_Inner（GT 相机处） | E_Outer | E_Centerline | 内/外边段数 |
|---|---:|---:|---:|---|
| GT | **5.6e-14** | 5.6e-14 | 5.6e-14 | 245–248 / 294–298 |
| 3° 偏差 | 2.4e-06 – 3.1e-06 | 7.0e-06 – 1.4e-05 | 5.6e-14 | 244–247 / 294–298 |
| 12° 偏差 | 1.3e-03 – 1.4e-03 | 9.4e-04 – 1.0e-03 | 5.6e-14 | 247–251 / 294–297 |

- 边段集合的重叠比例见 `VISIBILITY_EDGE_OVERLAP.csv`（12° 时 inner 仍约 95% 重叠）；
- 即便用 12° 相机选边，GT 处的 Ring 能量仅 **~1e-3**（相对典型值 0.1 仍可忽略）；
- 因此**冻结初始可见边不是 12° 失败原因**（Q4）；
- 若某相机无有效边段，代码返回 `RING_EDGE_NOT_EVALUABLE`（当前数据未触发）。
- 外层更新策略（重选边 → 局部 BA）本轮**未启用**（`NOT_NEEDED`，由上述数值支持）。
