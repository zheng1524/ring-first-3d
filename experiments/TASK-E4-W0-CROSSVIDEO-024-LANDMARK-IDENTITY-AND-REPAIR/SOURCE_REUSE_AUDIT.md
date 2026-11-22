# SOURCE_REUSE_AUDIT

| 历史模块 | 提交 | 原始函数 | 本轮调用 | 数学意义 |
|---|---|---|---|---|
| `019/features019.py` | `5636aae` | `features`, `matches`, `match_desc`, `landmarks` | **实际调用**（`core/p1_pipeline.py`），`common.py` 仅改 REPO | 保持（6000/0.01、ratio .72、mutual、MAGSAC、soft_l1、正深度/parallax/reproj 门） |
| `020/features020.py` | `5636aae` | `make(scope,refs,targets,reverse_label,lmname)` | **未接入**（依赖其 scope/PnP 运行包）；本轮用 `match_desc` 作候选，再叠加新的 3D 一致性判定 | 部分（未做双向 PnP/投票/一对一） |
| `020/ring020.py` | `5636aae` | `RingRenderer`, `CADCurves` | **未接入**；Ring 检查用 `torus_contours` 对 `q_train` 的 MAE | 否（不是 M/I/C/O 加权） |
| `020/objective020.py` | `5636aae` | `SymmetricFeatures`, `Objective` | 数学重述（023），本轮**未优化**（一致性未通过） | 部分 |
| `020/optimize020.py` | `5636aae` | Adam + state_dict + LOCAL_SE3_BOUND | 用 `core/optimize.py`（同调度 + 真 checkpoint） | 部分 |

**未修改**：W0、DXY、HERO、Body、Ring CAD、021/022/022R/023 的实验结果。
