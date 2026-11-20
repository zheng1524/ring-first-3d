# BUGFIX_AUDIT

| # | 缺陷 | 状态 | 验证 |
|---|---|---|---|
| 1 | `_TREE` id() 全局缓存 | 已删除 | `test_no_cache_pollution` |
| 2 | A1/A2 模式字符串不匹配 | 已改显式臂名 | 代码审查 + A1 指标变化 |
| 3 | `K0=None` | 已修 | 007 修复复用到 008 |
| 4 | 采样数不足/重复 | 弧长重采样恒 m 点 | `test_fixed_length`, `test_arc_length_uniform` |
| 5 | 退化返回零残差 | 显式惩罚 | `test_degenerate_not_zero` |
| 6 | 1px 离散化距离 | 精确点到线段 | `test_distance_matches_bruteforce` |
| 7 | DXY 真实可见弧点未导出 | **未修复**（记录偏差） | — |
| 8 | counts 调制 Ring 权重 | **未修复**（记录） | — |

测试：`5/5 通过`。

## 007 异常数值复查

- G03/005 `raw00128` outer 42.52 px、G05/005 `raw00099` outer 31.59 px、`raw00082` inner 16.64 px：
  用修复后的无缓存精确距离重算 A0 相机，G03/005 的 inner/outer 均值从 007 的 1.02/1.66 变为 0.97/1.68（差异 <0.05 px）。
  **说明这些几十像素的异常不是缓存导致的**，而是**个别视角的真实投影偏差**（CAD 与 DXY 在该视角确实不吻合），需图 B 局部放大进一步定性。
