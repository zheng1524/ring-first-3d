# CLEANUP_EXECUTION_REPORT — TASK-CLEANUP-SPACE-EXECUTION-002

**Status:** `CLEANUP_EXECUTED_SELECTIVE`
**Deletion:** selective deletion executed for approved safe candidates
**Human review:** required; no further automatic cleanup

## Headline

| 项目 | 结果 |
|---|---:|
| 清理前可用 | 4.56 GB（4.25 GiB） |
| 清理后可用 | **18.18 GB（16.93 GiB）** |
| 实际释放 | **13.62 GB（12.68 GiB）** |
| 使用率 | 91% |
| 当前目标差距 | 距 20 GiB 仍差约 3.1 GiB；未为凑数删除活跃/唯一资产 |

`df` 前后为同一根文件系统 `/dev/nvme0n1p3`。实际释放按 `df` 计，不按逻辑目录大小相加；部分历史目录存在硬链接/共享块，删除后实际值可能低于 `du` 估算。

## Execution batches

| Batch | Candidate IDs | `df` before | `df` after | Actual delta |
|---|---|---:|---:|---:|
| LOW_CACHE | CAND_014, CAND_019, CAND_025 | 4,561,326,080 | 6,431,772,672 | +1,870,446,592 |
| GIT_TEMP | CAND_013, CAND_024, CAND_028 | 6,431,772,672 | 7,911,219,200 | +1,479,446,528 |
| HISTORY | CAND_005,009,010,011,012,015,022,023,026,027 | 7,911,219,200 | 16,532,492,288 | +8,621,273,088 |
| HISTORY_CAND16 | CAND_016 | 16,532,492,288 | 17,377,280,000 | +844,787,712 |
| DEDUPE | CAND_018 vendor hardlink | 17,377,280,000 | 18179383296 | +802103296 |

`CAND_016` 的未提交 `maintenance/` 8.3 MB 已先保留到：

```text
docs/audit/space_cleanup_execution_002/preserved_CAND_016_maintenance/
```

## Deleted / deduplicated

- Caches: pip HTTP, npm `_cacache`, torch download cache.
- Git temp packs: three `tmp_pack_*` files under `polyp_research/.git/objects/pack`.
- Historical roots: contour_guided_init_a, structural_update, boundary_growth, forensic_audit_002, mainline, harness, multisurface_stress, g01_multisurface, structured_body_002, incremental, and old `ring_first_3d` checkout.
- CAND_018: **not deleted**; vendor Open3D binary was replaced by a hardlink to the current `.venv` copy. `same_inode=true`, current import path is `.venv`; no dependency path removed.
- CAND_016: old checkout deleted after preserving its unique untracked maintenance evidence.

Exact paths, pre-sizes and batch info are in `DELETED_FILES_MANIFEST.csv`; raw batch log in `CLEANUP_BATCH_LOG.json`.

## Not deleted / skipped

| Candidate | Path | Reason |
|---|---|---|
| CAND_001 | conda `息肉检测` | explicitly not authorized |
| CAND_002 | `.local/lib` | explicitly not authorized |
| CAND_003 | workspace raw copy | **explicitly prohibited; current prepare input** |
| CAND_004 | MASt3R weight | explicitly not authorized |
| CAND_006 | ring_first_v13 | **explicitly prohibited; DINO weights** |
| CAND_007/008 | DSH snapshots | current session, not ended; undo dependency |
| CAND_017 | old cleanup | unique `.ply.gz` archives; no verified backup |
| CAND_020 | Firefox cache | active Firefox open files |
| CAND_021 | e4_a1 | current frozen_registry absolute path reference |

See `SKIPPED_CANDIDATES.csv`.

## Protected assets verified after cleanup

- DXY HEAD `75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`.
- INIT weight SHA256 matches `981aa596...`.
- HERO checkpoint SHA256 matches `00878bab...`; DINO exists.
- 79 prepared manifests / 790 views; 79 M2C A1 W0 files exist.
- Ring CAD R5=3.1/0.6, R10=5.6/0.6; `torus_contours` returns 2 curves.
- Torch 2.7.1, CUDA available, Open3D 0.19.0 imports from `.venv`, OpenCV 4.11.0.
- PyTorch3D direct `.venv` import is false, but the current body path `runtime/p3d/pytorch3d` imports successfully (0.7.9); this was not a cleanup regression.
- `hero_stage.py`, `body_stage.py`, `body_hooks.py`, `hero.py`, `camera.py`, `contour_metrics.py` all present.

Full JSON: `POST_CLEANUP_DEPENDENCY_CHECK.json`.

## Remaining disk risk

At 16.93 GiB free, M2-C A2 and a staged HERO arm may be possible, but **full 3-arm HERO + body + visualization is not safely funded**. If more space is required, the next human decision should consider one of:

1. CAND_007/008 current snapshot cleanup after ending/settling this session (~4 GB);
2. CAND_017 old cleanup only after verifying unique `.ply.gz` backups;
3. CAND_020 after closing Firefox;
4. moving `CAND_003`/`CAND_006` to external storage, not deletion.

No further automatic cleanup was performed.
