# IDENTITY_BUILD_TRACE（每级过滤数量）

| 阶段 | 数量 | 说明 |
|---|---:|---|
| 004 FIT 三维轨迹（`CROSS_004`） | **317** | `features019.landmarks(fit4)`，历史质量门 |
| 005 FIT 三维轨迹（`INDEPENDENT_005`） | **806** | 同上 |
| CROSS 跨视频 EPI 对 | 21 对 / **220** 观测 | `features019.cross(fit4,fit5)` |
| CROSS 正向 PnP 成功 | **1 / 8** 目标视角 | 004 地标投到 005 视角 |
| REVERSE 反向 PnP 成功 | **3 / 3** 目标视角 | `make` 内部 `cross(fit5,fit4)` |
| 020 投票候选（多视角证据） | 24 对 | `votes[(a,b)]` 由真实 RGB-RANSAC 内点累积 |
| **020 选中身份**（≥2 视角/侧 + 一对一） | **12** | `CROSS_NAMED_3D_TRACK_PAIRS.json` |
| 020 拒绝 | **12** | 全部 `INSUFFICIENT_DISTINCT_VIEW_SUPPORT` |
| 2D-only EPI（去重后） | 见 `CROSS_EPI_2D_ONLY.json` | 已排除被三维身份使用的端点 |

24 → 12：12 个因两侧不同视角支持不足被拒，一对一键约束未产生额外拒绝。
