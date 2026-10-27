# 本轮结果索引

[完整技术报告](TECHNICAL_REPORT.md) · [复现入口](REPRODUCE.md) · [逐组指标](metrics/F_group_summary.csv) · [所有本地文件SHA](provenance/LOCAL_ASSET_INDEX.csv)

4物理组、5视频场景、9参考；仅G01有多参考。GT=NONE；清理候选未采纳，三维Dxy均不可评价。

[打开本轮可视化文件夹](/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations) · [直接打开 index.html](/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/index.html)

四张公开组级核心图（每场景含清理、增量融合和高度/Dxy三类完整面板）：

- [G01 三阶段审查图](figures/G01_three_stage_review.png) — SHA256 `cb2222dace1f9b69b160824e816386a4896a57683d99afbc5a47453d40dd7a3c`
- [G06 三阶段审查图](figures/G06_three_stage_review.png) — SHA256 `f52cbe8b6cc88b4a01f24323935992b04c684462e2609991921d698ee8440156`
- [G07 三阶段审查图](figures/G07_three_stage_review.png) — SHA256 `7236236f9ebb77bbeca6aab4b758ea9e21e3f2567e7ea39b5ea7763028199b1d`
- [G08 三阶段审查图](figures/G08_three_stage_review.png) — SHA256 `9cf172bec4b3a947238d39af77e1f742e82b2facb2b5a78e0c78930fc9ff4f47`

全部单独核心图和27个完整基底条件图在本地HTML中；完整XYZ、Mesh和GLB未公开上传。

| 场景 | 两类本地GLB | 字节 | SHA256 |
| --- | --- | ---: | --- |
| G01_004 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G01_004_primary_priority.glb` | 7196480 | `0261209d16fd71f81f16c519188e69f0a9aa2f2d76f6a8a3b4c778bd57f13901` |
| G01_004 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G01_004_evidence_preserved.glb` | 12958932 | `500d44f159f4e0da556d086167bd178a625ff8d9dc625177bd5e7083eb0968e7` |
| G01_005 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G01_005_primary_priority.glb` | 6872468 | `ba8ab80a47443897cd58328d2f82e02f03e4934bd5eb84d00e8a07afcc0e2a3a` |
| G01_005 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G01_005_evidence_preserved.glb` | 10686376 | `0bbf23fdb5e5507a5c1192534c42796d35501e1420ca668146ddc9ad930c33c1` |
| G06_004 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G06_004_primary_priority.glb` | 3387288 | `26f7feaa55eaa461c2e4db4a302264862b05dd8c3b37c43fd63702180935601a` |
| G06_004 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G06_004_evidence_preserved.glb` | 3387288 | `d9604eccaef08593d2b535eb9a2a9a17cb2bf3c0a16fe5ce4398798cb587b988` |
| G07_004 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G07_004_primary_priority.glb` | 5761460 | `5adcc40caa2a95ac4df0accfd502e4a831a8fb648041bbf04fc9fcec2ee9bd7a` |
| G07_004 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G07_004_evidence_preserved.glb` | 5761460 | `eacfca64d875d1abe1f8f946589eacc4640ce491ecaba21325873258550e5d00` |
| G08_005 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G08_005_primary_priority.glb` | 6056252 | `505b010b586833f71d7d00df955776f48e53f33aa061664467d4ba6f9d2ef3c6` |
| G08_005 | `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/local_results/GLB/G08_005_evidence_preserved.glb` | 6056256 | `ca70027475a4aa865a4461f4bfaf5c3abb6890306fd184f607ed4e9f67580938` |

每场景真实可视化文件夹：

- `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/G01_004`：三类核心PNG及全部ROI条件。
- `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/G01_005`：三类核心PNG及全部ROI条件。
- `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/G06_004`：三类核心PNG及全部ROI条件。
- `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/G07_004`：三类核心PNG及全部ROI条件。
- `/home/liu/ring_first_3d_incremental/experiments/TASK-PHASED-INCREMENTAL-FUSION-MULTIGROUP-001/visualizations/G08_005`：三类核心PNG及全部ROI条件。
