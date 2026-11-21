# EXECUTION_ERROR_REPORT

详见 `EXECUTION_ERROR_LEDGER.csv`（6 项：2 high / 2 medium / 1 low / 1 verified-ok）。

## 摘要

| ID | 严重度 | 内容 | 状态 |
|---|---|---|---|
| E1 | high | `020/landmarks/CROSS_004.npz` 悬空软链接，指向已删除工作区 | WORKAROUND（用 019 副本），已记录 |
| E2 | high | 保存的 `H` 是 `H_004←005`；直接左乘 004 点会得到 45 mm 误差 | DOCUMENTED + 测试 |
| E3 | low | `features019.py` 三处副本 | VERIFIED_SAME（SHA 相同）|
| E4 | medium | `optimize020` 的 Adam 回滚逻辑 | VERIFIED_OK（实现正确）|
| E5 | high | Ring-only 无法定 yaw（θ=0 比 47° 差 5 倍）| CONFIRMED（G03 实测）|
| E6 | medium | 留出残差 14.45 px vs 训练 11.7 px | DOCUMENTED（yaw 泛化、精度受限）|

## 没有发现的问题（也要说）

- 未发现 `c2w/w2c` 混用：`coordinate_adapter` 的方向测试与 7 个单元测试全部通过。
- 未发现 K 传递缺失：所有投影/对极都显式使用 `K`。
- 未发现 Ring 圆心/法向被优化破坏：纯 yaw 下 `|C|` 与法向保持。
- 未发现历史 `features019.py` 版本分叉。
