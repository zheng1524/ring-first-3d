# UNIFIED_PIPELINE_CONTRACT

| 阶段 | 输入 | 实现 | 输出 | 状态 |
|---|---|---|---|---|
| 数据发现 | `prepared/{G}_{v}`, `camera_mainline/<G>` | `videos_of`, `Ctx` | `input_manifest/` | 已执行（三组） |
| W0 | 正式 `camera_mainline` 或 `tools/run_w0_camera.py` | `w0_ensure` | `w0/` | 读取已执行；自动补算未演练（D8） |
| 视角选择 | W0 + RGB + Ring 证据 | `select_views`（Ring/RGB 独立 + 角度覆盖） | `view_selection/SELECT_*.csv` | 已执行（三组） |
| Ring | CAD + 真实轮廓 | DXY `recover` + `RingRenderer` | `ring/RING_SCORES.csv` | 已执行（三组） |
| 特征/地标 | 选中视角 | `features019` | `rgb_features/replay` | 已执行（三组） |
| 跨视频身份 | 二维轨迹 | `features019.matches` + 地标映射 + 投票 + 一对一 | `identities/IDENTITIES.csv` | 已执行（G01 0 / G03 10 / G06 6） |
| H 初始化 | Ring + 极线 | `ring_candidates` | `h_initialization/H_CANDIDATES.csv` | 已执行（G03/G06）；epi 缺陷 D7 |
| 三角化 | 固定相机 + 2D | 019 逐轨迹 | `triangulation/` | 已调用，结果未落盘（进程终止） |
| BA | H + X | `ba_core_r4` M2/M3b | `ba/` | **未完成** |
| 评价 | 独立观测 | reproj + Ring | `evaluation/` | **未完成** |
