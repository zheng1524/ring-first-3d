# W0_EVALUATOR_BUG_REPORT

## 发现（实现与语义不一致）

`tools/run_w0_camera.py` 的 `evaluate` 阶段用 **Ring 世界原点**是否在相机前方来填 `positive_depth`：

```python
m['positive_depth'] = float(EV.project(np.zeros((1, 3)), cams[i])[1][0] > 0)
```

这不是"全部真实 RGB 轨迹点的正深度比例"，而是单个点的布尔量。门限
`positive_depth_min: 0.95` 因此在这条路径上退化为"原点在相机前方"。

## 实测（`metrics/POSITIVE_DEPTH_AUDIT.csv`）

用 `runs/<G>_<V>/W0.npz` 的真实三维点 + `tracks005.npz` 的真实观测重新统计：

| 组/视频 | 视角数 | 门控 positive_depth | 真实轨迹点正深度比例 | 真实点总数 |
|---|---:|---:|---:|---:|
| G01/004 | 16 | 1.000 | 1.000 | 1840 |
| G01/005 | 16 | 1.000 | 1.000 | 2945 |
| G03/004 | 16 | 1.000 | 1.000 | 3087 |
| G03/005 | 16 | 1.000 | 1.000 | 5581 |
| G05/004 | 16 | 1.000 | 1.000 | 813 |
| G05/005 | 16 | 1.000 | 1.000 | 419 |

**结论**：实现确实不是声明的语义，但在这六个组/视频上**两者数值恰好一致（都为 1.0）**，
因此对 021 的准入结论**没有实际影响**——G01/G05 被拒是因为 `HELD_P95` / `HELD_TRACKS`，与正深度无关。

## 建议补丁（未应用）

```python
z  = np.einsum('ij,ij->i', pts - C[:3, 3], C[:3, :3][:, 2])
seen = np.isfinite(xy[tids, k, 0])
m['positive_depth'] = float((z[seen] > 0).mean()) if seen.any() else np.nan
```

## 为什么本轮不改

`tools/run_w0_camera.py` 与 `camera_mainline/` 是冻结主线；改动会重新定义 G01/G03/G05 的既有准入结果，
必须作为独立主线修复任务并全组回归。本轮只提交诊断、最小复现（本报告 + CSV）与建议补丁。
