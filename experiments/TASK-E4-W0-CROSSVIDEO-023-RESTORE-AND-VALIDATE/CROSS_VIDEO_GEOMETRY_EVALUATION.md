# CROSS_VIDEO_GEOMETRY_EVALUATION

## 正式目标与数据

`L(H) = L_Ring + 0.2·L_SIFT3D + 0.02·L_EPI + 0.01·L_Prior`，`H = H_(005<-004)`，
种子 `Rz(45.62°)`（1-DoF 求解器，状态 `AMBIGUOUS_MULTIMODAL`）。

| 项 | FIT 初始 | FIT 最终 | HOLDOUT 最终 |
|---|---:|---:|---:|
| L_Ring | 0.092 | 0.094 | — |
| L_SIFT3D fwd / rev | 31.58 / 17.85 | 25.34 / 12.18 | 26.33 / 13.42 |
| L_EPI（24 对） | 10.45 | 9.64 | — |
| L_Prior | 0 | 0.38 | 0.38 |
| **Total** | **5.244** | **4.042** | **3.978** |
| 观测数 fwd/rev | 121 / 50 | 121 / 50 | 113 / 55 |
| 修正量 | — | **0.589 mm / 5.73°** | — |

## 判定

- Huber 值 18.8 ⇒ 平均残差 **≈56 px**；FIT 与 HOLDOUT 几乎相同（18.76 vs 19.87），说明**不是过拟合，而是身份本身错**。
- 参与优化的 24 个跨视频身份中，`match_desc` 只做描述子 ratio+mutual，没有 3D 一致性验证；
  `features020` 的一对一约束/双向 PnP/投票均未接入。
- `L_SIFT3D` 权重 0.2 远大于 `L_EPI` 的 0.02，错误身份把 H 拉偏：EPI 均值 ~29 px，
  比 021（中位 4.6 px）明显恶化。

**`CROSS_VIDEO_GEOMETRY_ACCEPT = NO`**；不进入 HERO/Body。

## 需要的下一步（不是调权重）

1. 用 3D 一致性 RANSAC（历史 `named_candidate020` 做法）筛身份，而不是描述子 ratio；
2. 接入 `features020.make` 的完整身份构建（双向 PnP + 一对一）；
3. 地标三角化只用 FIT 视角，消除本轮的部分泄漏；
4. 补受控 GT 与 resume/梯度测试后，再跑一次评分。
