# EXECUTION_DEFECT_REGISTER

| # | 问题 | 现象 | 修复 |
|---|---|---|---|
| 1 | R6 入口按组名阻断 | `if group != 'G03': BLOCKED` | 删除；`u028.py` 无组分支（测试） |
| 2 | RingRenderer 模块级 `R` 固定 | G01 KeyError（读 G03/R6 的 VIEWS） | 显式 `ring020_026.R = <本组 replay>` |
| 3 | 适配缓存缺 `RGB_SHA256` | features019 KeyError | 每 VIEWS 条目加 `RGB_SHA256` |
| 4 | DXY 对部分视角无 I/O 椭圆 | `evidence()` KeyError 'inner' | `ring_evidence` 返回有效性；无效视角从 Ring/身份选择中剔除 |
| 5 | 视频编号被写死 | 004/005 固定 | 视频列表由 `prepared/{G}_*` 扫描；参考视频按 ACCEPT 数选（G03→005，G01/G06→004） |
| 6 | JSON int64 | TYPE ERROR | `json.dumps(..., default=int)` + 显式 int() |

均已修复并用 `tests/test_u028_contracts.py`（3/3）验证。
