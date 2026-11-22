# CONTROLLED_GT_LEAKAGE_AUDIT

## 027 的泄漏

```python
P = BA.Problem(..., pts0=scene['X'].copy())      # GT 三维点
theta0 = [..., scene['X'].ravel() + 0.5]         # GT + 0.5 mm
```

GT 同时进入**初值**与**地标先验**。因此 0.03° 只证明"从真值附近能回到真值"，不证明可用性。

## 本轮隔离

```
GT(cameras, H, X)  -> 生成 2D 观测                [GT 出场 1]
观测 + 初始相机    -> fixed_track_tri (历史 019)   -> X_init   [无 GT]
X_init + 观测 + Ring -> BA                         [无 GT]
结果 vs GT (独立文件 GROUND_TRUTH.json)            [GT 出场 2]
```

自动检查：`core/controlled2.py` 只把 `X_init` 传给 `BAProblem`；`GROUND_TRUTH.json` 不参与任何残差。
`X_init` 与 GT 的中位差（`X_init_err`）随场景为 **0.81–6.47 mm** —— 证明初值不是 GT。

## 对照结果

| 初始化 | 相机旋转误差（S1 无噪声） |
|---|---:|
| 027 的 GT+0.5 mm（泄漏） | 0.030° |
| **三角化初值（本轮正确）** | **7.03°（80 次迭代）/ 3.04°（400 次迭代）** |

⇒ 027 的"成功"主要来自真值初始化。
