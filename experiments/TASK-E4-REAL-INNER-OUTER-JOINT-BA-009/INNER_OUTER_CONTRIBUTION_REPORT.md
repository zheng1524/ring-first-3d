# INNER_OUTER_CONTRIBUTION_REPORT

| 臂 | 使用的 DXY 曲线 | 名义权重 | 实测 held |
|---|---|---|---:|
| B0 | 无（冻结边界） | — | 2.38 |
| C1 | 仅 inner | 与 C3 相同 | 51.45 |
| C2 | 仅 outer | 与 C3 相同 | 2.38 |
| C3 | inner+outer | 同上 | 未完成 |

## 判断

- Outer 单独使用与冻结基线等价 → **outer 没有带来新信息，也没有破坏**。
- Inner 单独使用破坏相机 → **inner 的当前加权方式有害**，而不是 inner 无用。
- 在 `w/Σw` 归一化下，可信弧越短约束越强，这是方向性错误。

## 下一步必须验证的假设

修成"覆盖率加权"后，inner 的 held 应回到 2.4 附近；若仍显著差于 C2，才能说 inner 与 RGB 存在实质冲突。
