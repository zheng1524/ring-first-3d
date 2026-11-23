# HISTORICAL_CODE_REUSE_AUDIT

| 功能 | 复用的历史模块 | 用途 | 修改 |
|---|---|---|---|
| W0 相机 | `tools/run_w0_camera.py`（正式入口） | G06 重算（004: 8 ACCEPT） | 仅 `--output` 到本实验目录 |
| Ring 证据 | `dxy_mid._engine.ring_component.recover`（019/020 同例程） | 每组每视角 I/O/C | 无 |
| Ring 渲染 | `ring020_026.py`（020 + 026-CORRECTIVE 2 行路径补丁） | M/I/C/O 数值 | 仅模块级 `R` 指向本组 replay |
| 特征/轨迹 | `features019.features/landmarks` | 单视频地标 | 无 |
| 跨视频身份 | `features019.match_desc`（ratio .72 + mutual） | 身份候选 | 无 |
| SE(3)/BA | R6 `r6_core`/`ba_core_r4` | 后续阶段（未执行） | 无 |
| 评价 | R6 同一 Ring/RGB 定义 | 资产层 | 无 |

未新建第二套 W0、Ring、SIFT 或 BA。
