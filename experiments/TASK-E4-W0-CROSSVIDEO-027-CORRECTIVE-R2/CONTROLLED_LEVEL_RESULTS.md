# CONTROLLED_LEVEL_RESULTS

| Level | 内容 | 结果 | 状态 |
|---|---|---|---|
| **L0** | GT 代入残差（RGB + I/C/O） | RGB 0.0；I 1.2e-13；C 1.7e-14；O 1.2e-13 | **PASS** |
| **L1** | GT 相机 + 三角化地标，全变量释放（锚点/005 冻结） | 相机 **2.7e-6°**、H **1.2e-6°**、地标 **6.5e-15 mm**、`success=True`、nfev 10 | **PASS** |
| **L2a** | 只优化 H + 地标，H 初值=I，GT yaw 12° | H 旋转 **7.06°**、平移 0.53 mm、地标 1.03 mm、`success=False`（40 次） | **FAIL** |
| **L2b** | 同上，GT yaw 3° | H 旋转 **0.022°**、平移 **0.0025 mm**、地标 **0.0029 mm**、`success=False`（40 次达上限） | **PASS（误差）/ NOT_CONVERGED（状态）** |
| L3 | 单相机扰动 | — | `NOT_EXECUTED`（时间预算） |
| L4 | 多相机扰动 | — | `NOT_EXECUTED`（时间预算） |
| L5 | 噪声/粗差/不同 K | — | `NOT_EXECUTED`（时间预算） |

## L2 的解释

- 12° yaw 初值偏差时，004 侧所有 RGB 残差都在 Huber 线性区（远大于 3 px），梯度被压制 → H 无法从 identity 收敛；
- 3° yaw 时可恢复到 **0.022°**，说明**模型与求解器正确**，失败是**收敛域/初始化**问题（Q7）。
- 两次 L2 都是 `success=False`（`max_nfev` 上限），因此状态标 `NOT_CONVERGED`，不宣布"优化成功"。

## 判据（事前冻结）

无噪声非退化场景：相机 ≤0.1° / 0.2 mm、H ≤0.2° / 0.2 mm、地标 ≤0.2 mm。
L1 与 L2b 满足；L2a 不满足。

**总结状态：`CONTROLLED_BA_PARTIAL`。**
