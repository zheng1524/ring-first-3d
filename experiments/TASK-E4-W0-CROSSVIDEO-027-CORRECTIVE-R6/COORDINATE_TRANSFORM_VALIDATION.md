# COORDINATE_TRANSFORM_VALIDATION

统一约定（c2w）：

```
T004_world = H · ΔT_i · T004_W0      (H = H_005<-004)
T005_world = ΔT_j · T005_W0
```

- BA 内部：`cameras_from(H, dx)` = `H @ (Exp(dx) @ T0)`（004），`Exp(dx) @ T0`（005）。
- **`make_problem` 只接收 W0/扰动后的基准相机，H 只出现在 BA 内部** → 不可能重复应用。
- 测试 `test_H_applied_once`：对 12° + 0.4 mm 的 H，实际相机与 `H@T0` 差 <1e-12，且与 `H@H@T0` 差 >1e-6。
- Ring 评价走 026-CORRECTIVE 的 `ring_adapter`（`C@inv(T0)`）路径，本轮未改。
- 所有三维点与相机均在 005/Ring 公制世界；`X0` 由 005 相机三角化，坐标一致。
