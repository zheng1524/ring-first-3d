# HISTORICAL_020_ADAPTER_PLAN

| 问题 | 回答 |
|---|---|
| 020 期望什么输入？ | `R/landmarks/{CROSS_004,INDEPENDENT_005}.npz(+_OBSERVATIONS.json)`、`R/features/CROSS_EPI.json`、`R/matches/<a>__<b>.npz`、模块级 `VIEWS`（含 `id,cache,T,K`） |
| 当前 W0 能提供什么？ | `camera_result.npz`（c2w,K,ids）、`admission.csv`、PREPARED 的 `cache`（RGB/labels/K）、Ring 观测 `q_train` |
| 完全一致字段 | `id`、`cache`、`K`、`T`（c2w）、RGB 像素 |
| 需转换字段 | 角色：历史 `role='FIT'`；本轮把 FIT 视角写入 `VIEWS`，HOLDOUT 视角**不进入** `VIEWS` |
| 禁止使用 | 历史 020 的固定相机、`inputs/G01`、历史 `landmarks/*`、历史 RoMa/Body/HERO |
| 如何保证只用 FIT | `core/p1_020_chain.py` 构造 `views = fit4 ∪ fit5` 后赋给 `F19.VIEWS/F20.f.VIEWS`；SPLIT 在特征提取前写盘 |
| 如何转成 024 一致性输入 | `CROSS_NAMED_3D_TRACK_PAIRS.json` → `HISTORICAL_020_IDENTITIES.csv`（identity_id, landmark_004/005, X004, X005, 支持视角, vote 数） |

## 实际调用顺序（与源码核对）

```
features019.landmarks(fit4,'CROSS_004')           # 317 个
features019.cross(fit4,fit5,lm004,'CROSS')       # CROSS_EPI/PNP
features019.landmarks(fit5,'INDEPENDENT_005')     # 806 个
features020.make('CROSS',fit5,fit4,'REVERSE','INDEPENDENT_005')
        → features/CROSS_NAMED_3D_TRACK_PAIRS.json / CROSS_EPI_2D_ONLY.json
```
`make` 内部还会调用 `features019.cross(fit5,fit4,lm005,'REVERSE')`（反向 PnP/EPI），与源码一致。
