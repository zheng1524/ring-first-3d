# 020 完整结果索引

根目录`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-SIFT-SYMMETRIC-REGISTRATION-020`。

| 产物 | 路径 |
| --- | --- |
| 核心报告/方法/失败 | TECHNICAL_REPORT_SUMMARY.md、TECHNICAL_REPORT.md、METHOD_AND_INPUT_AUDIT.md、FAILURE_LEDGER.md |
| 冻结输入 | INPUT_MANIFEST.json/csv、config/VIEWS.json、config/PROTOCOL.json、config/HERO_EVALUATION_SOURCES.json |
| RoMa原始及R0–R4全部矩阵 | results/*.json（含seed_T、共享T、物理尺度、实际更新次数） |
| R3派生相机及显式方向 | derived/T004_from005_R3.json、derived/VIDEO005_CAMERAS_R3.json |
| Ring原证据/原像素映射 | ring/、ring_evidence_v2/（xy对应原640×360Pixel ID=y*640+x）、metrics/RING_VISIBLE_EVIDENCE_COUNTS.json |
| 独立004/005地标 | landmarks/CROSS_004.npz、INDEPENDENT_005.npz及*_OBSERVATIONS.json |
| 双向真实匹配 | features/CROSS_PNP.json、REVERSE_PNP.json、CROSS_NAMED_3D_TRACK_PAIRS.json、matches/ |
| 完整FIT/HOLDOUT指标 | metrics/REGISTRATION_COMPARISON.csv、ALL005_FRAME_METRICS.csv、SIFT_READABLE_SUMMARY.csv |
| 梯度和拒绝日志 | optimization/每路线/HISTORY.json、metrics/ENDPOINT_GRADIENT_RELATIONSHIPS.json、REJECTION_REASONS.csv |
| 优化状态 | optimization/每路线/ITER_001/010/020/040/080.pt，q/Adam/iteration/seed |
| 同视频负对照 | metrics/NEGATIVE_CONTROL.json/csv、NEGATIVE_PER_VIEW.csv、results/NEGATIVE_R3.json |
| HERO逐源固定分母 | metrics/HERO_INDEPENDENT_PER_PAIR.csv、HERO_INDEPENDENT_AGGREGATE.csv、HERO_CENTROID_AREA_PROXIES.csv |
| 固定原生射线多层/CAD内部样本 | metrics/HERO_MULTILAYER_NATIVE_RAY_PROXY.csv、HERO_RING_SAMPLE_COLLISION_AUDIT.csv、HERO_MULTILAYER_COLLISION_SUMMARY.csv |
| 固定004相机与逐帧SIFT | metrics/REFERENCE004_FIXED_RING_ERRORS.csv、SIFT_PER_VIEW.csv |
| 核心6图和55帧详细图 | figures/Fig*.png、figures/details/All005_01..08.png |
| 诊断GLB | derived/G01_R3_DIAGNOSTIC_NOT_FUSION.glb，原Mesh独立组件，黑色Ring，非融合 |
| 大文件本地索引 | assets_index/LOCAL_RESULTS.json；完整绝对路径、字节、SHA，不上传大型原视频/深度/权重 |

R3为预指定主候选，未由HOLDOUT/GT/HERO选出；R4只是固定body对照。全部失败和未采用3D候选保留。最终等待人工审阅，不推进融合。
