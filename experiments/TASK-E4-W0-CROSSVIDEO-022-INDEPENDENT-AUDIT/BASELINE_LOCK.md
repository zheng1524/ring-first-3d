# BASELINE_LOCK

| 项 | 值 |
|---|---|
| 仓库 | `/home/liu/ring_first_3d_workspace`（remote `https://github.com/zheng1524/ring-first-3d`） |
| 审计对象分支 | `exp/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE` |
| 审计对象 commit | `bfd9c622bb2660b4a2e4c2ffdbadbb72b19971fd` |
| 历史参考 commit | `5636aaebd61a3d53b69f528692c4c7095df46508`（本地存在，`git cat-file -t` = commit） |
| 本审计分支 | `audit/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT`（自 021 commit 创建） |
| 工作树 | **dirty**：22 项未提交（其余实验的 log/CSV 自动产物 + `TASK-E4-DXY-CONIC-PRIOR-PILOT-002/runs/`）；未触碰 |
| 固定源码收集 | `tools/collect_pinned_sources.py` → `VERIFIED_PINNED_SOURCES: 29/29 pinned, 2 extra, 0 failures`；副本在 `provenance/pinned_sources/`（244 KB） |
| 物理快照校验 | `tools/verify_snapshots.py` → 3/3 PASS（020 features020.py、021 se3.py、021 cross_video_matches.py） |
| Python | 3.12（`/home/liu/polyp_research/ring_anchor_3d/.venv`），torch 2.7.1+cu128，pytorch3d 0.7.9（`runtime/p3d`，非 pip 安装） |
| 不可获得项 | 020 legacy 逐视角缓存 `/home/liu/ring_first_3d_e4_sdf_localization/...`（目录已删除，020 内为悬空软链）；G01/G05 的跨视频实验（W0 无 ACCEPT） |

## 021 关键文件 blob（示例，完整见 `provenance/pinned_sources`）

| 文件 | git blob SHA1 |
|---|---|
| `core/se3.py` | `6103e467afaadba35de35404b5b1c1333d7dca5c` |
| `core/cross_video_matches.py` | `8df7c78ce50f94b58c2a2107c299cf9e682d9d23` |
| `core/run_corrective.py` | `498a253a80d870cc6e38c6e4bf943252afe71049` |

## 运行时刻证据（解释 code_sha 不一致）

| 文件 | mtime |
|---|---|
| `experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/runs/G03/RUN_STATE.json` | 2026-11-22 15:46:48.560989001 |
| `experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/runs/G01/RUN_STATE.json` | 2026-11-22 15:45:04.180615890 |
| `experiments/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE/config/UNIFIED_PROTOCOL.json` | 2026-11-22 18:20:22.669418517 |
