# SOURCE_REUSE_AUDIT

| 历史模块 | 原始位置 / 固定提交 | 原始函数 | 新适配接口 | 实际调用点 | 数学意义是否保持 | 修复前后对照 |
|---|---|---|---|---|---|---|
| `features019.py` | 019 @ `5636aae`（pinned，blob 见 022 provenance） | `features(v)`, `matches`, `match_desc`, `landmarks(ids,label)` | `replay_019_020/code/` 仅改 `common.py` 的 REPO 路径；`core/p3_landmarks.py` 构造 VIEWS | `core/p3_landmarks.py` → `F19.features/landmarks` | **保持**（SIFT 6000/0.01、ratio .72、mutual、MAGSAC、soft_l1、正深度/parallax>0.5°/reproj<2px） | 无（原样运行） |
| `features020.py` | 020 @ `5636aae` | `make(scope,refs,targets,reverse_label,lmname)` | 未端到端接入；用同源的 `F19.match_desc` 做跨视频身份 | `core/p3_objective.py::build_problem` | **部分**（只复用描述子匹配，未复用 PnP/投票/一对一约束） | — |
| `ring020.py` | 020 @ `5636aae` | `RingRenderer`, `CADCurves`（M/I/C/O） | 未接入；Ring 项仍是 021 的 `torus_contours` 距离 | `core/p3_objective.py::losses` | **否**（不是 0.25M+0.35I+0.05C+0.35O） | — |
| `objective020.py` | 020 @ `5636aae` | `SymmetricFeatures`, `Objective.transform` | 数学被重述为 `L_Ring+0.2L_SIFT3D+0.02L_EPI+0.01L_Prior` | `core/p3_objective.py::losses` | **部分**（双向 3D 重投影 + prior 一致；缺轨迹级归一与 2D-only 去重） | 初始 5.244 → 最终 4.042 |
| `optimize020.py` | 020 @ `5636aae` | Adam + deepcopy state + LOCAL_SE3_BOUND | `core/p3_objective.py::optimize`（numpy，逐 10 步 checkpoint） | 同上 | **部分**（Adam 公式与边界一致；缺 state_dict 级回滚） | 80/80 接受 |

**未修改**：`tools/run_w0_camera.py`、`camera_mainline/*`、DXY、HERO、Body、Ring CAD。
`021` 与其 H 保持冻结：023 所有诊断与优化都在自己的目录内完成。
