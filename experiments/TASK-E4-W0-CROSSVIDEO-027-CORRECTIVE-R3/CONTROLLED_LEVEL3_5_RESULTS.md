# CONTROLLED_LEVEL3_5_RESULTS

| Level | 状态 | 原因 |
|---|---|---|
| L3 单相机扰动 | **NOT_EXECUTED** | 时间预算；前置 Gate D 已通过，但本轮未运行 |
| L4 多相机（≥4 台） | **NOT_EXECUTED** | 需要扩展合成场景（当前 004 仅 3 视角）；未执行 |
| L5 噪声/粗差/不同 K | **NOT_EXECUTED** | 同上；且 `K*1.04` 的旧写法需先改为独立 fx/fy/cx/cy |

**没有伪造任何 L3–L5 数值。** 六类图之图 6 明确标注 `NOT_EXECUTED`。
下一轮应先在合成场景中扩展到 6 台 004 视角，再执行 L3/L4；L5 的 K 修改必须满足 `K33=1`。
