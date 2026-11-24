# DISK_SPACE_AUDIT — TASK-CLEANUP-SPACE-AUDIT-002

**Status:** `DISK_AUDIT_COMPLETE`
**Cleanup:** `CLEANUP_CANDIDATES_READY`
**Deletion:** `DELETION_EXECUTED = false`
**Human approval:** `WAITING_FOR_HUMAN_APPROVAL`

审计时间：2026-11-24（Asia/Shanghai）。本轮只读：未删除、未移动、未清理、未改 Git 历史。

## 1. 核心汇总

| 项目 | 实际结果 |
|---|---:|
| 根文件系统 | `/dev/nvme0n1p3` ext4, mounted `/` |
| 容量 / 已用 / 可用 | 211.43 GB / 196.05 GB / **4.56 GB**（可用 4.25 GiB） |
| 使用率 | 98% |
| inode | 1,620,624 / 13,180,928 = 13%；**未耗尽** |
| 当前工作空间 | 12.61 GB allocated（11.74 GiB） |
| 近期主要增长目录 | `/tmp` 3.8–4.1 GB；workspace protected raw 3.7 GB；Git 临时 pack 1.48 GB；历史工作树约 11.3 GB；pip cache 0.96 GB |
| 已确认重复文件 | open3d pybind 802 MB，SHA256 完全相同 |
| 可重建缓存 | 约 0.06 GB（M1 pilot/aborted prepared 等） |
| 历史实验候选 | 约 11.3 GB 工作树 + 0.82 GB old cleanup + 0.80 GB duplicate |
| Git 数据 | workspace `.git` 953 MB；polyp `.git` 6.2 GB；其中 tmp packs 1.48 GB |
| 方案 A 预计释放 | **6.02 GiB** |
| 方案 B 预计释放 | **19.66 GiB** |
| 方案 C 预计释放 | **43.58 GiB（高风险，未建议直接执行）** |
| 推荐安全余量 | **≥ 25–30 GiB 可用**，完整三臂 HERO 建议 ≥ 35 GiB |

## 2. 近期约 16 GB 下降的原因

**没有历史 `df` 快照，不能精确证明“哪 16 GB 全部是近期新增”。** 根据文件 mtime 与当前大小，以下是最可能的主要贡献，合计约 13–15 GB：

| 路径/对象 | 当前占用 | mtime 证据 | 备注 |
|---|---:|---|---|
| `/tmp/dsh-workspace-changes-*` | 3.8–4.1 GB | 2026-11-24 10:08 / 11:36 | 当前 DSH 工作区变更快照；最大的近期临时对象 |
| `workspace/assets/protected_raw_data` | 3.7 GB | 2026-11-18 | P0 原始数据保护；不可清理 |
| `polyp_research/.git/objects/pack/tmp_pack_*` | 1.48 GB | 2026-11-17～18 | 无对应 `.idx` 的 Git 临时包；未发现活动 git 进程 |
| `.cache/pip/http-v2` | 0.96 GB | 2026-11-22 | 普通 pip 下载缓存 |
| `workspace/.git` pack | 0.65 GB | 2026-11-24 | 当前提交对象；不是普通临时文件 |
| `ring_first_3d_forensic_audit_002` | 1.15 GB | 2026-11-18 | 历史审计工作树 |
| `ring_first_3d_structural_update` | 1.87 GB | 2026-11-17 | 历史 body/structural 实验 |
| `workspace/smart_endoscope_20260805 (1)` | 4.03 GB | 2026-08-16 | 不是近期新建；duplicate 未确认，不可据此删除 |

`runs/m1_final_39` 286 MB、`m2a` 53 MB、`m2b` 168 MB、`m2c` 59 MB；**当前 W0 结果与 prepared/work 不是 16 GB 下降的主因**。

## 3. 重点目录

| 路径 | allocated | 角色 |
|---|---:|---|
| `/home/liu/polyp_research` | 40.1 GB | 历史项目、raw data、HERO/模型 |
| `/home/liu/miniconda3` | 25.3 GB | 5 个 conda 环境 + 2.5 GB 包缓存 |
| `/home/liu/ring_first_3d_workspace` | 12.6 GB | 当前正式工作空间 |
| `/home/liu/.local` | 7.7 GB | 旧 Python 3.8 site-packages |
| `/home/liu/文档` | 6.7 GB | 用户文档，非本轮科研 |
| `/home/liu/continuum_robot_hardware_bringup` | 7.6 GB | 其他项目，未判断 |
| `/home/liu/ring_first_3d_*` 历史工作树 | 约 11.3 GB | 历史 source/outputs |
| `/tmp` | 4.05 GB | DSH 临时对象 |

## 4. 已确认重复

`surface_fusion_v3/vendor/open3d/.../pybind...so` 与当前 `.venv` 同文件 SHA256：

```text
b2be62326991e9d84b5db4aab1f449ddc4e2c02f22055c0cefe0860bbbcca525
```

大小 802,242,736 bytes。**只建议在人工确认 historical F3 不再使用后删除 vendor 副本；保留 `.venv` 副本。**

`/tmp` 两个快照不是硬链接共享（抽样 nlink=1），但完整 inode 关系未逐文件证明；实际释放以删除后 `df` 为准。

另有一条 **未完全证明的树级重复**：workspace `smart_endoscope_20260805 (1)` 与 polyp original tree 的一个 108 MB 文件 SHA256 相同；全树未逐文件哈希，因此 `estimated_reclaimable_bytes=0`，只列为 C3/C5 人工决策，不进入方案 A/B。

## 5. 保护资产（不可列入直接删除）

P0：原始 ZIP、original raw tree、`assets/protected_raw_data`、DXY frozen repo、workspace raw copy（去重前保护）。

P1：当前 workspace、`.venv`、MVSAnywhere HERO checkpoint、DINOv2 weights、MVS vendor source、HERO/body code、当前 Git 对象。

P2：M1/M2-A/M2-B/M2-C 正式表、W0 相机、M2B 本地 review、prepared/clean labels、retained sources、关键可视化。

完整的 `PROTECTED_ASSETS.csv` 共 18 条。**当前 `.venv` 2.12 GB、HERO checkpoint 2.42 GB、DINO 1.22 GB 不能为了释放空间而删除。**

## 6. 三级方案

| 方案 | 新增候选 | 估算释放 | 清理后可用 |
|---|---|---:|---:|
| A 保守 | /tmp 快照 + pip/npm/mozilla/torch 缓存 | 6.02 GiB | 10.27 GiB |
| B 推荐 | A + Git 临时 pack + 历史工作树/旧清理 + open3d 重复 | 19.66 GiB | 23.91 GiB |
| C 深度 | B + raw 工作副本 + MASt3R + v13 + conda/legacy site-packages | 43.58 GiB | 47.83 GiB |

方案 B 达到 **23.91 GiB** 可用，刚超过 20 GiB 目标，但不足以覆盖完整 3 臂 HERO + body + 可视化峰值；需要分组验收后释放临时深度/网格，或采用方案 C 的严格子集。

## 7. 释放空间最大的 20 个候选

| # | 路径 | 类 | 估算释放 | 风险 | 建议 |
|---:|---|---|---:|---|---|
| 1 | `/home/liu/miniconda3/envs/息肉检测` | C3 | 9.19 GiB | HIGH | HUMAN_DECISION |
| 2 | `/home/liu/.local/lib` | C3 | 5.89 GiB | HIGH | HUMAN_DECISION |
| 3 | `/home/liu/ring_first_3d_workspace/smart_endoscope_20260805 (1)` | C3 | 3.75 GiB | HIGH | HUMAN_DECISION |
| 4 | `/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v9_ring_guided_recovery/weights/MASt3R_official.pth` | C3 | 2.57 GiB | HIGH | HUMAN_DECISION |
| 5 | `/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v13_multisource` | C3 | 2.52 GiB | HIGH | HUMAN_DECISION |
| 6 | `/home/liu/ring_first_3d_contour_guided_init_a` | C3 | 2.44 GiB | HIGH | HUMAN_DECISION |
| 7 | `/tmp/dsh-workspace-changes-GGsTeP` | C1 | 1.89 GiB | LOW | REMOVE_AFTER_APPROVAL |
| 8 | `/tmp/dsh-workspace-changes-m3e6pM` | C1 | 1.89 GiB | LOW | REMOVE_AFTER_APPROVAL |
| 9 | `/home/liu/ring_first_3d_structural_update` | C3 | 1.74 GiB | HIGH | HUMAN_DECISION |
| 10 | `/home/liu/ring_first_3d_boundary_growth` | C3 | 1.13 GiB | MEDIUM | HUMAN_DECISION |
| 11 | `/home/liu/ring_first_3d_forensic_audit_002` | C3 | 1.07 GiB | MEDIUM | HUMAN_DECISION |
| 12 | `/home/liu/ring_first_3d_mainline` | C3 | 0.99 GiB | MEDIUM | HUMAN_DECISION |
| 13 | `/home/liu/polyp_research/.git/objects/pack/tmp_pack_83NVwI` | C1 | 0.92 GiB | MEDIUM | HUMAN_DECISION |
| 14 | `/home/liu/.cache/pip/http-v2` | C1 | 0.89 GiB | LOW | REMOVE_AFTER_APPROVAL |
| 15 | `/home/liu/ring_first_3d_harness` | C3 | 0.79 GiB | MEDIUM | HUMAN_DECISION |
| 16 | `/home/liu/ring_first_3d` | C3 | 0.79 GiB | MEDIUM | HUMAN_DECISION |
| 17 | `/home/liu/research_storage_cleanup` | C3 | 0.76 GiB | MEDIUM | HUMAN_DECISION |
| 18 | `/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/vendor/open3d/cuda/pybind.cpython-312-x86_64-linux-gnu.so` | C3 | 0.75 GiB | MEDIUM | REMOVE_VENDOR_COPY_AFTER_APPROVAL |
| 19 | `/home/liu/.npm/_cacache` | C1 | 0.53 GiB | LOW | REMOVE_AFTER_APPROVAL |
| 20 | `/home/liu/.cache/mozilla` | C1 | 0.50 GiB | LOW | REMOVE_AFTER_APPROVAL |

完整 30 条见 `CLEANUP_CANDIDATES.csv`。**所有“REMOVE/APPROVE”仅为建议，不执行。**

## 8. 结论

- **最推荐**：先执行方案 A（/tmp 快照、pip/npm/browser/torch 缓存），可恢复到约 **10.3 GiB** 可用。
- **推荐但需人工批准**：方案 B 的 Git 临时 pack、历史工作树、旧 cleanup、open3d vendor 重复；可恢复到约 **23.9 GiB**。
- **必须保留**：原始数据/ZIP、DXY、当前 workspace、`.venv`、HERO/DINO 权重、M1–M2C 正式结果、当前 Git。
- **需人工进一步判断**：`smart_endoscope_20260805 (1)` 副本、MASt3R 权重、conda 环境、`.local/lib`、历史 body/structural 工作树。
- **不能支持完整 M2-C 三臂 HERO**：若按 39 组 × 79 视频 × 4 目标 × 3 策略估算，峰值可能需要 25–45 GiB 额外空间；方案 B 仅勉强进入下限。必须先完成方案 A/B，并在 HERO 前按组分包清理临时 XYZ/Mesh。

## 9. 证据限制

- 没有历史磁盘快照，无法精确证明 16 GB 的逐日增量；
- `du` 对硬链接/稀疏文件的估算以当前目录遍历为准，删除后实际释放可能略小；
- 许多历史目录同时包含“源码 + 结果 + 可能的运行时依赖”，不能按目录名直接删除；
- Git 临时 pack 的删除应使用 Git 安全流程，或人工确认后再做；本轮未执行 `git gc/prune`；
- `/tmp` 快照可能影响当前 DSH 会话撤销，不建议在无人监督时删除。
