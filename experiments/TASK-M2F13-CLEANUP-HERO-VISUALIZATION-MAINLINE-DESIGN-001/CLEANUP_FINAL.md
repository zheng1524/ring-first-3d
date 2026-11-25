# M2F13 退役路线最终清理

本轮授权覆盖旧P和相关废弃3D工作区；不再沿用旧P只读跳过规则。按上轮审计路径刷新141个退役根，保存源码/配置/输入身份/正负结论与代表结果，逐成员核验归档后清理。没有删除Git历史、RAW照片/视频/ZIP、GT/CAD、公共模型或现用Graph/ARAP/Sweep。

## 逐技术闭环

| 技术 | 已处理根 | 删除路径数 | 实际末链接分配字节 | 剩余根库存字节* |
|---|---:|---:|---:|---:|
| Hull_H1_H2 | 2 | 191 | 189657088 | 68145152 |
| M2_retired_runs | 45 | 12805 | 1749250048 | 287002624 |
| MonoSDF_E0_E2 | 35 | 110 | 27414528 | 134508544 |
| NeuralFusion | 11 | 466 | 233398272 | 62070784 |
| Old_Body_structural | 6 | 921 | 170889216 | 6541312 |
| Old_fusion_GICP | 31 | 1705 | 1031036928 | 4097298432 |
| PMGR_FFD | 3 | 8 | 6688768 | 25190400 |
| TSDF | 6 | 28 | 38846464 | 8364032 |
| UNIFIED_002 | 2 | 2613 | 403083264 | 230178816 |

*剩余根库存是逐根去重inode后的目录库存，跨根仍可能共享inode，不相加当物理总量；符号链接别名不重复计体积。精确根路径/删除数量/剩余体积/保留理由见[RETIRED_ROOT_DISPOSITION.csv](evidence/RETIRED_ROOT_DISPOSITION.csv)，逐文件清单在压缩JSON中。未把旧模型已offload的历史空间算成本轮收益。

- TSDF/NeuralFusion：处理旧P及e4_e1e2、pose_depth、e4_a1等废弃树的Mesh/预览/逐轮产物；保留源码、配置、完整失败指标和真实代表。共享硬链接逐路径删除，仅最后链接计块释放。
- MonoSDF/E0/E2与MapAnything：处理已在本地的退役派生输出；所有`FINAL_LAST_SAFE_step000`、`STOP_UNSAFE_step001`、初态检查点保留，因为文件SHA并不等同。保留未完成/停在不安全更新的真实状态，不声称训练充分。MapAnything checkpoint在前次审计已缺失，本轮删除权重0字节；其源码/依赖revision和负结果归档，无专属活动环境可卸载。
- PMGR谱/FFD：清理重复派生显示/产物；主要剩余是小型完整metrics和源码。Graph/ARAP核心独立保留，未按名称误删。
- Hull H1/H2：删参数子集与叠层展示冗余；明确保留两视频完整`H2_nALL.ply`、faces unknown/ROI分类、nALL voxel、Fig2完整视图及Fig9失败见证，不以CONTROL小图替代正式结果。
- 旧补片/GICP/固定主面融合：清理surface_fusion_v1/v2/v3、independent_confidence_fusion及旧phase任务的专属输出。现用导入只需要V2 `inputs/real_camera_0.npz`和replay的`inputs/R10_ring.obj`等明确闭包，未因旧`pack/mesh_for`函数定义而保护全部旧预测。
- 旧Body-E/自由顶点结构更新/失败soft-zbuf：退出SU003训练缓存921个NPZ；保留六个FINAL、INITIAL/GRAPH/GT与源码/失败日志。精确保留SU004三个`{G01,G03,G05}/DEFORM_GROW/FINAL.npz`供SB002历史对照。当前主体核心在独立STRUCTURED-BODY-UPDATE-002的INITIAL、STEP_024 GRAPH/BODY/UPDATES，Sweep在mainline/results，不依赖SU003全缓存。
- UNIFIED-002及M2E/M2F1/2/3/5/8/9：删除剩余冗余派生数据/图集，归档包装代码和身份；保留输入祖先、真正被V6消费的准备代码与R5/R10 CAD。M2F10/11/12全部结果与M2F6保持。

## 唯一共享依赖与例外

`surface_fusion_v1/weights/mvsanywhere_hero_full.ckpt`约2.3GiB是当前官方HERO模型，`ring-first-hero-core/site_config.local.json`明确消费；不是退出TSDF后可删权重。V3 vendor Open3D被本次渲染、M2F12评价和公共入口使用。23个完整SHA相同的Open3D文件已与`.venv/lib/python3.12/site-packages/open3d`权威文件共享inode，原路径不改、无需算法迁移；原本共享的CUDA pybind没有再次计收益。共享Python环境不卸载。

原始输入/真实照片、GT/CAD、旧相机/地标祖先，以及其他runtime/权重的具体剩余路径和理由均列在RETAINED_PATHS；无法确认独占性的少量类型单列`individual unknown file kind`，没有因此阻断整条技术清理。废弃工作区根中残留的Git对象保留；不把几乎空的工作区根声称为整树删除。

## 空间实测

- start_available: `9698865152`
- before_deletion: `9590321152`
- after_deletion: `13428973568`
- deletion_net: `3838652416`
- runtime_dedup_net: `306925568`
- full_archive_bytes: `94516429`
- source_archive_bytes: `5584207`
- final_available: `13721907200`
- whole_phase_net_after_archive_and_evidence: `4023042048`
- df_scope: `same mount /, st_dev=66307`

清理unlink的df净增加 **3.5750 GiB**，公共运行库去重另增加 **0.2858 GiB**；含归档、清单及同期写入后的整个阶段净增加 **3.7467 GiB**。最终普通用户可用 **12.7795 GiB**。同盘移动不计释放。

完整精简证据归档位于`/home/liu/ring_first_3d_workspace/runs/m2f13_hero_all/archives/RETIRED_FINAL_EVIDENCE.tar.gz`，94516429 B、17029成员，SHA `97c894d00be9e93ba9cfdc3471c4a90eb4183a47996039a7527aee68b5fa26c0`；本地保留，不上传整套旧运行。上传源码/报告子包`archive/RETIRED_SOURCE_AND_REPORTS.tar.gz`，5584207 B，SHA `b29c469c1baff1f7a5c64d694ae5b04405542c627d23fcfb536ff541ec49abe9`。归档成员、源路径与SHA随压缩清单上传。

## 保留入口与内容验证

6项清理边界测试通过。清理后30,975个既有工作文件内容SHA、176个科学源码和M2F12冻结2991文件全部一致；7仓库原有修改binary patch已存于本地run/work_protection（仅SHA索引上传，避免把无关工作内容发布）。Open3D0.19真实射线测试得到t_hit≈1；R5/R10 CAD、V2旧相机与Ring标定均校验。旧递归资产目录清单不再代表现用消费闭包，SU003退出项在RETIRED_CLOSURE_EXCEPTIONS逐文件说明，历史清单不回写。未以轻量检查冒称重跑科研主线。

HERO后续只新增69组合的候选预算，按旧单次输出最大体积和顺序执行预留2GiB输出/图表余量；原V6/H004大Mesh直接引用，不整套复制。实际预算须由完整输入身份冻结后生效。
