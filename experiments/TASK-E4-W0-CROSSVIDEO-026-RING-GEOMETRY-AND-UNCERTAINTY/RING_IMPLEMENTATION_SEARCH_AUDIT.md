# RING_IMPLEMENTATION_SEARCH_AUDIT

## 1. 历史 020 是否真的运行过 Inner/Outer？

**是。** 固定提交 `5636aae` 的 020 运行目录中存在真实 gate 产物：

- `metrics/RING_VISIBLE_EVIDENCE_COUNTS.json`
- `metrics/RING_CURVE_PROJECTION_GRADIENT_GATE.json`
- `metrics/REFERENCE004_FIXED_RING_ERRORS.{csv,json}`
- `gate.log`：`RING020_GATE G01_005_raw00057 True {'I': 0.0, 'O': 0.000178, 'C': 0.000216} 8.1e-08`

即历史确实在 G01 上调用过 `RingRenderer.losses` 并记录了 I/O/C 数值与梯度门。

## 2. 当前主线

`src/ring_first_3d/mainline/native/camera.py::torus_contours` 只给出两条轮廓，
它不区分真实 Inner/Outer 语义、不做 CAD 自遮挡、不提供 M/I/C/O 分解；
`013` 的 `contour_metrics` 只是最近轮廓距离（R0）。

## 3. 本轮决策

**方案 A（复用历史 020）成功**，因此没有创建新算法。
适配方式（不改匹配/投票/优化规则，仅数据与路径）：

| 历史依赖 | 026 适配 |
|---|---|
| `inputs/G01/RING.npz` | 环境变量 `RING_CAD` → G03 `RING.npz`（018 retained source） |
| `inputs/G01/NORMALIZATION.json` | `RING_NORM` → G03 `NORMALIZATION.json`（FREE_VERTEX_013 retained source） |
| `config/VIEWS.json` | 由当前 W0 ACCEPT 视角生成（22 个） |
| `v['cache']` 需含 `T` | 生成适配 cache（RGB/labels/K + W0 `T`），位于 `replay_020/runs/inputs/G03/` |
| `ring/<view>.npz/.json` | 由 011 `DXY_OBSERVATIONS` 生成 inner/outer 椭圆采样点 |

代码差异见 `RING_IMPLEMENTATION_DECISION.md`（仅两行路径替换）。
