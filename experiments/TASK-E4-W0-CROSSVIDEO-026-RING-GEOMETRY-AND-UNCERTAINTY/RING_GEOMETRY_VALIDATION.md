# RING_GEOMETRY_VALIDATION

历史 `features020` 的 Ring 目标在 **22 个当前 G03 ACCEPT 视角** 上端到端运行（`core/p1_ring_io.py`）。

| 指标 | 中位 | 说明 |
|---|---:|---|
| E_M | 0.093 | mask 软轮廓 |
| E_I | **0.099** | Inner（Huber(d/3)） |
| **E_O** | **0.257** | Outer |
| E_C | 1.834 | 中心线（椭圆拟合辅助，非独立三维真值） |
| **E_Ring = .25M+.35I+.05C+.35O** | **0.242** | 历史定义 |

## CAD 与数据来源核对

- CAD：`TASK-E4-HERO-BODY-ADAPT-018/inputs/G03/RING.npz`（G03 专用，非 G01）；R=5.6, r=0.6 与冻结物理尺寸一致。
- NORMALIZATION：`FREE_VERTEX_013/inputs/G03/NORMALIZATION.json`（真实文件，非悬空 symlink）。
- 观测：011 `DXY_OBSERVATIONS` 的 inner/outer 椭圆点，经 `evidence()` 的 2.5 px mask 支持过滤。
- 可见弧：由历史 `segments()` 的 CAD 自遮挡 + 光栅可见性决定；不可见弧不参与。

## 受控验证（本轮）

| 检查 | 结果 |
|---|---|
| 真实 I/O 观测来源 | 22/22 视角均有 I/O adapter 与真实 mask 支持 |
| 明显错误位姿被拒绝 | **H025 使 E_Ring 0.242 → 178.7**（严格拒绝） |
| 单自由度可辨识性 | 见 `RING_POSE_IDENTIFIABILITY.md` |
| 真实 RGB 叠加 | `FIGURES/02_cad_inner_outer_overlay.png` |

**`RING_GEOMETRY_VALIDATED = PASS`**（历史实现 + 真实 G03 CAD + 真实 I/O 观测 + 受控拒绝能力）。
