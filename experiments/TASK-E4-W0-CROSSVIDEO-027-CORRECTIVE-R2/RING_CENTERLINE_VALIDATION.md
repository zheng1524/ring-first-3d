# RING_CENTERLINE_VALIDATION

- 中心线几何来源：历史 `RingRenderer.curves.mid`（720 点闭合圆，R=5.6 mm），与 026-CORRECTIVE 修复后的 `centerline` 定义一致。
- BA 中作为**独立通道**（`V_mid/E_mid`），不与 Mesh 顶点索引混用。
- Level 0：`ring_C = 1.7e-14`（GT 相机下为零）→ C 的观测与 CAD 投影严格一致。
- 关闭 `use_centerline` 时，`ring_C` 项不产生残差；启用时残差数量 = 每相机 180 个（720/4 子采样）。
- **BA Ring 目标 = I + C + O（ICO）**；Mask 仍在独立评价层，未进入 BA。不宣称完整 MICO 已进入 BA。
