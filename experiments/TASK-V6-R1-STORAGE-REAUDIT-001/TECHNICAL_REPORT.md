# R1主线保留策略下的新一轮存储审计

日期：2026-11-27（北京时间）。任务：TASK-V6-R1-STORAGE-REAUDIT-001。

**发现66,520个精确文件候选，逻辑体积19.78 GiB；按inode去重且要求全部硬链接均在候选中，最多可回收约19.84 GiB文件分配空间。** 这不是已经释放的空间，也不是所有文件已满足删除前置条件。当前可用约1.92 GiB。本轮新增删除为0；此前A批次28个交付重复包、43,700,224字节回收没有混入这里。

结论是：可以从“整棵旧工作区保护”改为“保留R1实际依赖、源码/参数/结论/身份；旧大产物按记录退休”。问题的主要体积来自旧方法权重、旧数组与旧几何，而不只是少量W/runs文件。范围覆盖`ring_first_3d_workspace`、`polyp_research`（其中重点为`ring_anchor_3d`）及相关工作树副本。未进入DXY独立项目修改或删除数据。

## 1. 空间去了哪里

以下现占用按普通文件分配块去重，未包含目录块；候选列为逻辑大小。`ring_anchor_3d`是`polyp_research`的子集，不能重复相加。

| 根/子集 | 当前文件分配空间 GiB | 候选逻辑大小 GiB |
|---|---:|---:|
| workspace | 24.87 | 9.94 |
| polyp_research | 33.92 | 7.88 |
| worktree_copies | 6.49 | 1.96 |
| ring_anchor_3d (subset of polyp_research; do not sum again) | 14.49 | 7.87 |

全审计扫描406,715个文件/链接，跨全部根去重后的文件分配空间65.28 GiB。`.git`历史、原素材、GT/标注、运行环境占用了明显空间；这些不是本轮清理收益来源。

## 2. 具体候选类别

| 类别 | 精确文件数 | 逻辑 GiB |
|---|---:|---:|
| 非R1旧观测/匹配/BA/相机/native等数组 | 48,506 | 8.20 |
| 旧Mesh/点云（独立文件类别） | 7,127 | 4.19 |
| 旧路线模型权重 | 6 | 4.28 |
| 旧权重下载分片 | 6 | 0.12 |
| HEAD和权威副本内容均核验的工作树副本 | 6,544 | 1.96 |
| 旧渲染/图集等派生可视化 | 4,331 | 1.03 |

上述类别互斥。Mesh指标表也覆盖工作树副本中的几何，因此不能把Mesh表体积再加到候选总量。6个旧模型文件加6个下载分片共4.40 GiB；其中MASt3R官方旧权重约2.57 GiB，V13的DINO/RoMa/CoTracker/LightGlue系列约1.72 GiB。它们不在当前R1官方HERO/INIT依赖清单中；相关方法源码、来源、配置和真实结论继续保留。

## 3. 优先处理的大目录

这是定位表，**不是父目录递归删除指令**。精确文件和SHA在候选CSV里。当前分配空间与候选逻辑大小口径不同，不用于直接相减。

| 目录 | 当前分配 GiB | 候选逻辑 GiB |
|---|---:|---:|
| `/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v9_ring_guided_recovery` | 2.80 | 2.79 |
| `/home/liu/ring_first_3d_workspace/runs/v6_frontend_photo_pilot_001` | 2.74 | 2.54 |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v13_multisource` | 2.52 | 2.48 |
| `/home/liu/ring_first_3d_workspace/runs/v6_full_run_001` | 2.39 | 1.70 |
| `/home/liu/ring_first_3d_workspace/runs/m2f10_v6_multiview` | 2.00 | 1.69 |
| `/home/liu/ring_first_3d_workspace/runs/v6_raw_to_hero_001` | 1.39 | 1.04 |
| `/home/liu/ring_first_3d_workspace/runs/m2f6_unified` | 1.01 | 0.97 |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/ring_first_v11a_native_pointmaps` | 0.72 | 0.54 |
| `/home/liu/ring_first_3d_workspace/experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001` | 0.50 | 0.44 |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/surface_benchmark_v1` | 0.44 | 0.36 |
| `/home/liu/ring_first_3d_workspace/runs/m1_final_39` | 0.28 | 0.26 |
| `/home/liu/polyp_research/ring_anchor_3d/experiments/ring_depth_v4` | 0.27 | 0.25 |

- `ring_first_v9_ring_guided_recovery`、`ring_first_v13_multisource`的旧模型与中间产物是主要新增空间来源。V13报告日期为2026-10-20，结论是共同坐标验收失败；V9报告也未批准替换原始开放曲面。不是仅凭目录名或mtime判定过期，见[METHOD_LINEAGE](evidence/METHOD_LINEAGE.json)。
- `m2f10_v6_multiview`的FORMAL-02与M2F11按文件分别清点。新的保留政策允许其旧大数组/几何进入候选；当前真正使用的M2F10适配器、V5/V6源码、必要下游输入仍保留。M2F11未完成的运行状态和失败日志不改写为完成。
- 原R0、R1、R2的旧Mesh/native/分类大数组可在指标与身份归档、消费者处理后退休；原105、R1的205、R0全量795三个有重叠的基线记录分别保留，不相加。R1冷/热工程等价所需的相机、完整轨迹和选帧输入另行保护。

## 4. Mesh已记录什么

[MESH_METRICS.csv.gz](MESH_METRICS.csv.gz)覆盖**7,487个文件、6,376种不同内容**，每项保留SHA、文件字节、顶点数、面数、有限顶点数、原坐标包围范围与面积；相同内容只解析一次，全部来源路径仍保留。

- 7,374个文件完成几何指标记录。
- 113个场景文件（约0.28 GiB）只记录对象顶点/面计数，仍需归档节点变换及外部材质引用；不会冒称已完成完整指标归档。
- 单位未独立认证时写`native_units_not_independently_certified`；不把所有旧坐标强称为毫米。几何范围/面积不是GT误差、准确率或跨源一致性。
- 保留所有现存科研JSON/CSV、配置、源码和失败记录。后续执行时还须建立退休回执，指向这些指标；旧HERO_COMPLETE或链接不能继续被解释为大产物仍在。历史图页中被退役的文件应明确标记，而不是留下无解释的失效入口。

## 5. 明确保留与暂不计入的项

1. 官方HERO权重`surface_fusion_v1/weights/mvsanywhere_hero_full.ckpt`约2.25 GiB、共享`.venv`约1.96 GiB、INIT模型、实际公共库、真实Ring CAD仍是当前主线依赖。不能因为父目录方法退役就删除这些文件。实际配置与保护文件见[ACTIVE_DEPENDENCIES](evidence/ACTIVE_DEPENDENCIES.json)。
2. RAW ZIP/视频/照片、标注/GT/标定、全部Git历史保留。`.git`体积不会通过清历史来腾空间。
3. **6,714个旧预处理/轨迹输入，约0.46 GiB，等待R1规范缓存冷/热验证及消费者加载证明；未计入19.84 GiB候选。** B入口工程仍是草稿，两例验证和全量启动尚未完成，见[B_ENGINEERING_STATE](evidence/B_ENGINEERING_STATE.json)。
4. 现用配准/clean/下游依赖按其RETAIN_DEPENDENCIES逐文件排除，而不是让历史代表闭包继续保护整个旧目录。独有工作树产物、已修改文件和无权威同内容副本者保留。
5. 9–10月旧2D候选帧、密集重采样、邻帧/缓存等约3.62 GiB单列待核验，其中9月21日选帧、10月7日风险重采样及sharp5再采样为大项。它们与DXY早期数据流程有关，须完成原始标注及冻结消费者核验，**没有计入当前候选释放上限**。另有来源未认证图片、未知资产也逐项列明，不能把它们统称为可删缓存。

## 6. 空间可行性与下一步批次

原R1全量静态预算约12.11 GB（约11.28 GiB），还需补计规范冷缓存和实测阶段峰值。当前约1.92 GiB，按该旧预算仍缺约9.36 GiB，不能立即启动。

若候选全部满足保留与归档条件，静态相加可将可用空间提高到约21.76 GiB，具备解决空间缺口的规模。**这只是上限推算**：需扣除新增指标包/缓存、保留代表图、113个未完成场景归档及同期写入；实际释放以A逐批回执和现场df为准。

执行建议按四批收束：先旧路线权重/下载碎片；再无R1消费者的旧数组与已核验重复副本；再指标齐全且消费入口已退休的旧几何；最后处理通过冷/热迁移验证的旧预处理副本。只要真实空间已满足更新后的预算，就可继续已授权R1流程，不必为了凑清理批次延迟。

本次清单状态为**AUDIT_ONLY_NOT_READY**。没有新增READY释放批次，没有改变共享目录当前保护清单。后续由B根据本审计生成新版本精确READY批次，由A持maintenance.lock执行；不让A重新判断科学价值，也不要求研究者重复批准已授权R1路线。

## 7. 审计文件与验证

- [PROPOSED_FILES.csv.gz](PROPOSED_FILES.csv.gz)：66,520条精确绝对路径、文件类型、字节、SHA256、inode/nlink、理由、重复副本与指标状态。
- [DIRECTORY_AUDIT.csv](DIRECTORY_AUDIT.csv)：逐目录现占用、候选量及分类体积；[ROOT_SUMMARY.json](ROOT_SUMMARY.json)为根统计。
- [MESH_METRICS.csv.gz](MESH_METRICS.csv.gz)：旧几何指标；[RETENTION_POLICY.md](RETENTION_POLICY.md)：新保留规则与分批执行条件。
- [SUMMARY.json](SUMMARY.json)、[DELIVERY_CHECK](evidence/DELIVERY_CHECK.json)、[空间快照](evidence/SPACE_AT_DELIVERY.json)。候选数量/总量、唯一精确路径、SHA覆盖、Mesh指标连接及核心保护排除校验通过。
- 完整406,715项库存留本地：`/home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-FULL-B-001/experiments/TASK-V6-R1-STORAGE-REAUDIT-001/FILE_AUDIT.csv.gz`，SHA256 `fd95e00383f5dd87640b86340bca697e5099b0d0ac248337497a44e89a180ed5`；为避免重复上传大量保留文件路径，仅上传候选清单与必要审计证据。

所有新候选仅做读取、哈希和指标记录，未改动原Mesh/坐标，未运行科研优化/HERO，也未删除原数据。R1缓存工程草稿保留在独立B工作树；本轮报告提交与尚未冻结的科学工程代码分开。
