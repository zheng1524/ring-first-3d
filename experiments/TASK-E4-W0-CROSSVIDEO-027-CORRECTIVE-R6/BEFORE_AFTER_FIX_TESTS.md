# BEFORE_AFTER_FIX_TESTS

| 测试 | R5 状态 | R6 结果 |
|---|---|---|
| Ring 残差向量 = BA 块能量 | 标量目标，无法比较 | 相对差 <1e-12 |
| 候选最终 H 与精化增量 | 未保存 | 已保存，refine_rot 6.7°–156° |
| H 只应用一次 | 重复应用 | `C == H@T0`，`!= H@H@T0` |
| M2/M3b 分离 | 同一列 | 分阶段记录，H 不同 |
| 参考相机用于极线 | 读 GT | 跟随传入相机（差 >1e-6） |
| HOLDOUT 隔离 | 未测 | 替换 HOLDOUT 不影响选择 |
| M4 局部相机更新 | IndexError | 释放相机 dx≠0，冻结相机 dx=0 |
| 7 图非空 | 图 2 空 | 7 图均由 CSV/NPZ 生成 |

测试：`tests/test_r6_p0.py` **7/7 PASS**。
