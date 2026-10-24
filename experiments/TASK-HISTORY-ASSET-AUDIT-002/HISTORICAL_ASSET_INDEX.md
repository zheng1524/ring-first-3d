# 历史资产索引

本次上传范围：8份原报告、冻结指标转录、4张原PNG、模块/来源索引；未迁移科研源码。源文件路径与SHA完整见[来源清单](provenance/SOURCE_MANIFEST.json)，函数与行号见[模块表](metrics/reusable_modules.csv)。

## 原报告（字节不变）

以下报告按历史原貌归档，不代表当前验收。旧相对图片/模型链接可能仅在原目录有效；本包可直接查看的图片仅[四图索引](FIGURE_INDEX.md)。

| 原报告绝对路径 | 本次归档副本 | 原件/副本SHA256 |
| --- | --- | --- |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/pointcloud_surface_filter_vnext/TECHNICAL_REPORT.md` | [报告](historical_reports/pointcloud_surface_filter_vnext/TECHNICAL_REPORT.md) | `6b815079391edfd24c5a92d9b09fa97bb08106952f6f5b88c8fc0c71157c963e` |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/independent_confidence_fusion_v1/TECHNICAL_REPORT.md` | [报告](historical_reports/independent_confidence_fusion_v1/TECHNICAL_REPORT.md) | `b2048af1d209c18263e85b8b90f94a1716d084a683f146381a3ce6a97c63b824` |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/independent_confidence_fusion_v1/MULTIVIEW_FUSION_REPORT.md` | [报告](historical_reports/independent_confidence_fusion_v1/MULTIVIEW_FUSION_REPORT.md) | `7efeccaa9526d62b160cb57560f700bed300bb829a6128b8c680e5d159c67189` |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/independent_confidence_fusion_v1/FAILURES.md` | [报告](historical_reports/independent_confidence_fusion_v1/FAILURES.md) | `31c53415ef12897040ac88e199baea97a1e87a26151edd98e0988a2f6ffbb822` |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/multigroup_surface_gt_vnext/TECHNICAL_REPORT.md` | [报告](historical_reports/multigroup_surface_gt_vnext/TECHNICAL_REPORT.md) | `a63e8595a71fe59496e41043f6473aead107fc2667ca4b3d8d1d3d8010f60655` |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/TECHNICAL_REPORT.md` | [报告](historical_reports/surface_fusion_v2/TECHNICAL_REPORT.md) | `c8bb39d0806b804d4fb6d866385c9df10e303a113ea43fad1ee26fbd0b657bee` |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v2/FAILURES.md` | [报告](historical_reports/surface_fusion_v2/FAILURES.md) | `e9422822a355e3930285af800423a614a9e302c2a1968e98c5ba5e4a7efda213` |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/surface_fusion_v3/TECHNICAL_REPORT.md` | [报告](historical_reports/surface_fusion_v3/TECHNICAL_REPORT.md) | `3955bfc2a1149c0f7dbc22392d1b42749688e68d4ffcde4b69827cce729d72b3` |

## 已运行、仅有源码、未实施方案

逐方法状态/运行证据见[执行登记](metrics/execution_ledger.csv)。在39个历史目录的有界检索及核心函数逐项检查中，没有找到完整“可信主面＋其他面优化配准融合”的源码或运行链；不将任何名为main的入口函数或最大连通分量统计当作该算法。存在可运行的ICP源码，但它的实际角色是Oracle评价；B3表面重建明确NOT_RUN。

## 小指标表及分母

| 文件 | 内容/分母 |
| --- | --- |
| [点云全部条件](metrics/pointcloud_conditions.csv) | 9视频×6方法=54行RAW；G04/不可评价保留NaN；无B1重复计数 |
| [点云运行登记](metrics/pointcloud_filter_runs.csv) | 原过滤运行/拓扑输出，含失败状态 |
| [组宏均值](metrics/pointcloud_group_macro.csv) | P0/P1/P2/P4共7组Oracle；P3/P5仅1组，不直接横比 |
| [GT控制](metrics/pointcloud_GT_controls.csv) | 干净/注入控制×6方法=12行；GT输入诊断 |
| [置信融合](metrics/fusion_runs.csv) | 2视频×2对象=4行；输出不等于科学验收 |
| [面数量权威计数](metrics/fusion_face_accounting.csv) | 修正早期fusion_runs重复组计数口径，不改原日志 |
| [融合拓扑](metrics/fusion_topology.csv) | 原20个视频×对象×方法组合 |
| [完整射线记录](metrics/fusion_rays.csv) | 60参考×方法×对象行；是模型/候选覆盖非GT |
| [多参考冲突](metrics/multireference_conflicts.csv) | 全部12个有向参考配对，不丢长尾/NaN |
| [拓扑整理](metrics/topology_repair_all_conditions.csv) | 13输入×3分支=39行 |
| [被删面GT审计](metrics/GT_removed_faces.csv) | 原12条可评价输入记录；G04无GT不补 |
| [Ring配准](metrics/ring_registration_attempts.csv) | 5条件：3合成执行、2真实SKIPPED |

## 保留在本地、不上传的几何资产

- `independent_confidence_fusion_v1/meshes/`：004/005各参考A、B直接组合、C置信融合、D_TSDF_RAW_UNKNOWN及open原Mesh。
- `independent_confidence_fusion_v1/provenance/*_fusion.npz`：源像素、source_to_fused、逐面映射、来源位和冲突状态；后续可复用的核心证据。
- `independent_confidence_fusion_v1/scenes/`：原分层与两套UNVERIFIED跨源场景；不得当成认证配准。
- `pointcloud_surface_filter_vnext/points/`、`meshes/`、`provenance/`：原始永久像素身份、P0—P5掩码和RAW/B1来源。
- `multigroup_surface_gt_vnext/meshes/`、`provenance/`：B0/B1/B2及面/顶点映射。`gt_mapping/`内Oracle H仅评价使用。
- `surface_fusion_v2/multiref/`、`registration/`：三参考焊接和有界Ring全场景H；真实identity只是SKIPPED显示。
- 视频、权重、完整深度、GT、PLY/GLB/NPZ、旧实验源码和环境全部LOCAL_ONLY。上述目录相对本索引开头历史根路径；本轮没有打包或移动它们。

## 方法差异与可复用边界

详见[技术报告](TECHNICAL_REPORT.md)。直接可复用的是来源身份/坐标/原开放面、逐点支持诊断、已验证的首表面投影、面来源与拓扑评价。B1仅作几何不变整理；P1/P2/P3/P4/P5删除、C焊接Mesh、TSDF替代、Ring点云配准均未满足默认替换主线的证据要求。可信主面选择与固定、其他表面有界优化、独立验收后附加新面，是与历史方法真正不同且尚未实施的部分。
