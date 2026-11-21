# ERROR_FIX_LEDGER (018 → 018-REPAIR)

| # | 018 的问题 | 根因 | 修复 | 验证 |
|---|---|---|---|---|
| 1 | 合成相机含镜像反射 | `rig()` 用 `np.diag([1,-1,1])*[1,1,-1]` 拼接，det=−1 | `geometry.look_at()`：R=[x_c,y_c,z_c]，x=z×up、y=z×x，**det=+1** | `test_camera_rotation_validity`（3 组随机位姿），S0 err=0 且所有点 Z_c>0 |
| 2 | S5 观测生成后才改相机位置 | 控制变量顺序错误 | `make_pairs` 先按 bz 放置 B 组相机，**再**投影生成观测 | 基线 0.078–3.0 mm 均重生成；见 S5 表 |
| 3 | 同视频角度误差符号 | 应比较 θ̂ 与 −α | `err=|wrap(θ̂+α)|`，由 `reproduce`/控制脚本真实计算 | 0/30/−120/179 全部 0.055° |
| 4 | 多解判断把同一极小值判成多个 | 只看最低几个网格点 | 周期曲线 + 圆形聚类(merge 12°) + 分离判据(sep 20°) + **rise_away** 平坦度判据 | `test_single_minimum_not_ambiguous` / `test_two_separated_minima` / `test_periodic_boundary` |
| 5 | 损失上限说法不一致 | Huber 均值上界 = clip = 5 | 在 `metrics()` 中同时输出 median/MAE/p90/p95/inlier3/saturation/loss | `test_loss_bounds` |
| 6 | 交付缺真实匹配提取源码 | 只有 CSV | `code/real_matches.py`（SIFT→ratio→背景 mask→坐标） | 本次 B/A 全部由该脚本重建 |

## 仍未闭环（如实记录）

- **S5 的退化设计仍不成立**：绕 Ring 圆心的旋转本身产生弦长基线，缩放基线不会让 yaw 退化；
  真正退化条件是"相机中心位于旋转轴上"（纯旋转）。本轮未重构该用例，标为 `DESIGN_FLAW`。
- 004 ACCEPT↔005 的一致性判据是"per-pair yaw 的 MAD"，它与 Gate 的 `inlier3` 门限并不等价，
  两者同时报告，不互相替代。
