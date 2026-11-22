# HISTORICAL_SOURCE_AUDIT

历史源码取自固定提交 `5636aaebd61a3d53b69f528692c4c7095df46508`（经 022 的 `collect_pinned_sources.py` 以 Git blob 校验，29/29 PASS）。

| 文件 | 用途 | 本轮修改 |
|---|---|---|
| `019/code/features019.py` | `features/matches/cross/landmarks` | **未改**（仅在其外部 `common.py` 中把 REPO 指向当前仓库） |
| `020/code/features020.py` | `make()` 身份投票/一对一/2D-only | **未改** |
| `020/code/common.py` | `R`/`REPO`/IO | 仅 `REPO` 一行（路径适配），见 `ACTUAL_CALL_GRAPH.md` |
| `020/code/ring020.py` | M/I/C/O Ring | **未运行**（本轮 Ring 检查仍用 `torus_contours`；已在 `RING_COORDINATE_VALIDATION.md` 标注不等价） |
| `020/code/objective020.py` / `optimize020.py` | 目标/优化器 | **未运行**（本轮不执行 H 优化） |

`replay_019_020/code/` 内为逐字节副本（`common.py` 除外）。实际调用记录见 `IDENTITY_BUILD_TRACE.md`。
