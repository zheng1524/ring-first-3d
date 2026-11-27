# V6 前端恢复与照片混合小试

**状态：固定6组12视频的R1/R2小试、固定clean和证据核验全部完成；未启动全量。R1增加覆盖且保留原105个Target；R2出现原成功视频退化，不满足全量推广条件。** 完整计数见 [逐视频表](VIDEO_COMPARISON.csv) 与 [中文三栏可视化](index.html)。本轮不启动39组全量。旧全量、clean、配准任务及外部源码均保留。

本地地址：<http://127.0.0.1:8960/index.html>。输出根 `/home/liu/ring_first_3d_workspace/runs/v6_frontend_photo_pilot_001`；科学快照 `dfc13a01cbbc5d57af99f2cb38a0c6aee3f0fd8e`，已核验远端同SHA。后处理和报告提交与科学执行身份分开记录。

## 最终结果与剩余失败

| 指标（固定分母） | R0旧结果 | R1统一前端修复 | R2修复＋照片 |
|---|---:|---:|---:|
| 有视频Target Raw的视频 | 5/12（41.7%） | 11/12（91.7%） | 10/12（83.3%） |
| 有视频Target Raw的物理组 | 3/6 | 6/6 | 6/6 |
| 视频Target Raw | 105/252（41.7%） | 205/252（81.3%） | 181/252（71.8%） |
| 视频Target非空Trusted | 本轮未重评 | 205/252 | 181/252 |
| 原105个成功Target保留 | 105/105 | 105/105 | 84/105 |
| 照片Target Raw/Trusted，独立物理照片 | 未接入 | 未接入 | 12/18（各12） |
| 照片Target Raw/Trusted，分视频注册 | 0 | 0 | 17（各17） |

R1共205、R2共198次正式HERO，403个Raw均非空、固定clean后Trusted均非空。两轮24个队列状态均DONE；DONE包括合法计划为0的正常结束，不等于出面。每视频精确链条见[VIDEO_COMPARISON.csv](VIDEO_COMPARISON.csv)，每候选见[INITIALIZATION_COMPARISON.csv](INITIALIZATION_COMPARISON.csv)。没有通过删除失败视频缩减12视频或252视频Target分母。

- **IIa4.5/R10/005**：原21+1断连保留21视图锚分量；R1实际13个视频Target出面。排除B后的20个候选不是20个合法输出。R2为12个视频Target＋1次照片Target。
- **Is18/R5/004、005**：默认版本合法计划均0，第二版本分别Q1=9、3，实际21、7个视频Target出面。005不仅恢复了真实Ring边界，也在本轮相机和完整合法调度下产出7个Raw。
- **Is7/R5/004**：R1第二版本Q1=11、实际17个视频Target；R2为15个视频Target＋2次照片Target。
- **Is7/R5/005**：原15+6+1仅保留原锚15视图；两候选Q1分别0、2，均不足形成合法三Support，实际HERO为0。照片未建立进入该分量的有效匹配路径。断连异常被消除，但观测/准入不足仍真实存在，不制造相机以补齐。
- **IIa9.5/R10/004、005**：修正后的默认版本已各有21个合法视频Target，不再沿用旧协议“必须选备选”的结论。
- **Ip8.8/R5/005**：R1默认版本计划0，第二版本Q1=12且实际21个视频Target；体现有界回退也保护了原成功对照。

### 照片收益与R2退化定位

18张物理照片分别加入两个视频，形成36次输入注册；19次进入保留分量并获得数值相机，17次成为Target输出，对应12张物理照片。**仅IIa9.5/R10/004的照片001通过Q1并实际作为2个元组的Support**。其他照片有Raw不表示自身相机已通过Support准入，原协议允许Target自身不设同样准入门。完整排除、准入和Support使用见[VIEW_MANIFEST.csv](VIEW_MANIFEST.csv)、[照片匹配诊断](PHOTO_MATCH_DIAGNOSTICS.csv)。许多003照片只有1–8条最大训练配对，未达到建图所需12条。

R2令原成功的**Ip8.8/R5/004从21个视频Target降为0**。其24台数值相机仍存在，但默认/第二版本Q1仅1/0，完整计划均0，阻断在HERO之前。没有用其他组的照片输出抵消这21个损失。

以下归因表展示version 0：首行用R1原相机作为对照，其余三行固定同一套R2相机，只读调用原验证内核并限制三角化观测（没有重跑BA/HERO，没有更改正式准入或元组）：

| 验证观测 | 视频Q1数 | 视频RGB留出MAE中位数/px | 留出评估数 |
|---|---:|---:|---:|
| R1原轨迹、视频观测 | 5 | 7.587 | 1694 |
| R2正式：全部轨迹、全部观测 | 1 | 14.730 | 1737 |
| R2相机：仅原轨迹、全部观测 | 2 | 9.205 | 1694 |
| R2相机：仅原轨迹、仅视频观测 | 5 | 7.515 | 1694 |

事实是：固定R2相机、恢复原视频验证观测后Q1回到5；照片参与的留出三角化及新增留出轨迹显著改变了门控证据。由此推断，**混合验证证据的变化是该零输出的重要原因，不能简单归咎于整体相机尺度崩溃**。这不是R2已恢复的证据，也不能证明所有照片姿态可靠；正式R2仍计0。完整数值见[evidence/R2_ZERO_ATTRIBUTION.json](evidence/R2_ZERO_ATTRIBUTION.json)。下一轮若继续照片方向，应先保护固定原视频验证队列，单独验证新照片query姿态，再决定其能否参与其他视图的验证三角化；本轮不实施此变体。

### 原105个Target的回归与一致性

R1保留105/105，其中55个Support元组改变。原Mesh面积比最小0.983、中位1.059、最大1.234；共同方向/毫米范围图未见成功对照整体翻转或明显整体缩小，仍可见分层和碎片。面积与人工图检不是精度证明。R2只保留84/105，这84个Support均改变，面积比0.946/1.061/1.288；21个缺失逐一保留NOT_EVALUABLE。

按固定R0有向Target对评价，R1共105对可评，跨源深度P95中位数由0.503变为0.548 mm，逐对差的中位数为**+0.0256 mm**；R2在共同84对上由0.524变为0.585 mm，逐对差中位数**+0.0389 mm**，另21对不可评。R1个别对差可达+0.641 mm；R2可达+1.683 mm。因此只能说R1覆盖改善且原目标全部保留，**不能说一致性全面提升或所有质量回归均通过**。条件性Ring MAE的逐Target差中位数分别−0.0236/−0.0941 mm，也不能抵消跨源一致性退化或用不同共同集宣布路线胜负。证据见[COMMON_105_TARGETS.csv](COMMON_105_TARGETS.csv)、[配对汇总](evidence/PAIRED_REGRESSION_SUMMARY.json)。

## 最终核验、空间与交接

[最终产物审计](evidence/FINAL_ARTIFACT_AUDIT.json)为PASS：复核264个基线文件、24份原track/pair文件、806个新native/mesh哈希、403个合法元组、197,723条pair身份、564条输入视图注册和11,410,825张原始分类面；Trusted严格为原V/F的F[state==0]，三份clean实现/协议与冻结提交逐字节相同。

正式403次HERO之外，两次工程尝试保留44次，合计447次，未超预检540次预算。中途进程中断使用同一dfc13快照恢复；两段中断相机尝试原样保留，已完成视频未重跑，无暗换Support资源重试。见[恢复回执](evidence/RESOURCE_RESUME_001.json)、[归档位置映射](evidence/ARCHIVE_RELOCATION.json)。RAW、模型、大Mesh和所有失败证据留在本地精确路径；Git只上传代码、配置、表格、必要日志与图。

空间详见[STORAGE_FINAL.json](evidence/STORAGE_FINAL.json)。小试前可用4,962,279,424字节，结束约2.15 GB（约2.00 GiB）；本轮运行树约2.92 GB，包含工程尝试。该变化受同盘其他活动影响，不当作逐文件净消耗证明，更不把同盘归档计为释放。全量所需空间明显不足。

推荐研究者先审阅R1覆盖收益及一致性代价；R2当前不具备全量推广条件。保留统一入口、全79/120清单及受保护启动模板，但不以解除审批标记代替科学回归解决。[全量方案](FULL_RUN_PLAN.md)与[复现命令](REPRODUCE.md)均已准备；本轮到此停止，不自动启动全量。

## 输入、边界与实际调用链

固定6组12视频、18张照片。R0为冻结全量原结果（5视频105个面源）；R1不加照片；R2以相同补丁加入同组独立照片。两轮均真实重新解相机、选元组、运行HERO，原每视频22视图、非诊断Target总分母252保留。照片Target和视频Target分开；同一照片在两视频注册不增加独立照片数。

执行仍为 `v6_raw/route.py` → M2F10 `tools/m2f8_v6_general.py` → 外部V5/V6。M2F10文件SHA `6ad695b0ffd66699a41306d4d38c1853a5d65b6a372d758a54ce284e7a586412`，来源提交 `2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c`。通过局部内存适配修改实际函数，不写外部文件。每运行 `FRONTEND_KERNELS.json` 记录模块 `__file__`、源码位置、磁盘SHA及适配AST SHA；`CAMERA_COMPLETE`、`PLAN_FROZEN`、`HERO_COMPLETE` 冻结实际父子身份，官方HERO模型SHA不变。

实际Ring修正进入 `M2F10.build_ring → V5.ring_observations.ns['adapt'] → g5_common → V6`。复用 `native.camera.observe(all)` 的真实像素边界语义，保持原候选、Ring+RGB BA、公制几何、p/b区域观测及原生HERO。邻息肉只作诊断。边界来自画面内部标签跳变，不封闭图像外边缘、不补绘、不用CAD点冒充观测；原内/外轮廓诊断保留，没有提供独立遮挡证据，所以不新增遮挡排除。

79视频的1,732张旧Mask全部回放：**1,487张实际q点坐标/成员改变，523张最终q数量改变；原33张空q均恢复为非空**。此前过程更新的648是适配器前级轮廓数量变化，不能当作最终q影响范围。最终统计复用了V5的排序、256点上限和每5点留1的划分。Is18/005图中原q为0，新q训练204/留出52；p训练512/留出128，b训练0。恢复观测本身不是相机/HERO恢复。

## 实际组合与边界适配

| 阶段 | 复用入口 | 本轮适配、输出及代价 |
|---|---|---|
| RAW/INIT | `route.prepare`、既有冻结PREPARED、DXY INIT | 原选择与Mask按RAW/模型/代码/文件SHA复用；不复用旧相机。照片独立分割。 |
| Ring | M2F10 `build_ring` → V5 `ring_observations` | 真实全部Ring边界；诊断邻接。非空q区域权重完全不变，空q时区域权重分子用max(1,nq)，防止有区域证据却乘零。 |
| 匹配/地图 | V6 `track005.main`、`pair_data` | 原SIFT阈值/RANSAC不变；照片与全部视频及其他照片实际匹配。原视频track ID、xy、category、train/held前缀和视频pair保留。 |
| 照片轨迹扩展 | `frontend.preserve_video_tracks` | 原缓存只提供不变的SIFT身份；真实新匹配决定照片扩展。SIFT同坐标可对应多个方向关键点，映射用候选ID集合，合并/碎裂/类别歧义拒绝。不会把held改为train；代价是可能丢弃部分真实但不能唯一认证的照片连接。 |
| 分量/时间边 | `frontend.component`、原 `pair_data` | 冻结原16中锚8、B9的真实RAW身份；保留原锚分量，排除B与物理重复后需≥4视图。丢弃视图留在清单/分母。只继承原视频相邻选帧时间边，不跨删除缺口或照片。 |
| 初始化/BA | V6 `local_ring_sfm.initialize/triangulate_training/BA` | 原两候选、原优化器；仅改明确时间边、短轨迹不可三角化保护及空q区域权重。没有新增收敛门槛。 |
| 验证/准入 | 原 `validate_select` + `policy.admit_camera` | None/NaN保持不可评估，不补0；Q0/Q1阈值不改；每候选使用自己的覆盖中心。 |
| Target/Support | 原 `select_supported_views` + `route._schedule` | 默认数值成功版本只要有合法计划就保留，否则检查第二版本。相机/验证/中心/排序/组合整套绑定；未检查备选的合法数为未评估，不伪报0。Target不新增自身准入门槛。 |
| HERO/建面 | 原 `run_mvs005_supported`、`package_surfaces` | 每Target一个冻结三Support元组，官方模型与352×640原生深度、原Mesh定义不变。原B不可用时不取负索引代替，相关指标为NOT_EVALUABLE。 |
| clean | `surface_clean.mapped_input_for_source` → `native.cleaning.classify_native` | 固定017四态+gap，`trusted_restore.trusted_subset`严格取F[state==0]；协议SHA99c00fe5…b56不变。原V/F和四态全留；仅删除本轮可再生的重复PLY导出并记哈希。 |
| 共同评价/展示 | 原 `evaluate.scorer/depth_diagnostic`、`nearviews.make`、`trusted_restore.render` | 同Target比较、Support变化明示；原成功视频的跨源投影对固定为R0 Target身份顺序，缺源保留NOT_EVALUABLE。CAD指标条件于相机，不是独立深度正确率。 |

照片成像依据是研究者明确确认“同镜头、变焦、裁剪、畸变校正，和视频统一处理”，没有独立照片标定。保留原1920×1080尺寸、EXIF/方向检查及原图→640×360像素中心映射；工作K沿视频490/319.5/179.5。每照片自己的Ring/RGB观测共同求解自己的Camera-to-Ring，不借视频姿态，没有照片时间戳或伪视频帧号。该共享K是经采集说明支持的假设，不能当作已标定精度。

`track005.json`保留原混合union阶段统计；最终track计数及保留划分以`TRACK_EXTENSION.json`、`COMPONENT.json`及最终NPZ为准。每张照片的相机准入、Support使用、Target状态见[视图清单](VIEW_MANIFEST.csv)。照片成为Target不等于照片本身通过Support准入。

## 工程核验与尝试保留

39项边界/既有V6测试通过。真实首段离线核验：614个原track、123个held和全部类别/坐标前缀严格保持；7,620条pair行的轨迹ID和两端坐标一致；新轨迹不含任何原track关键点；110条原轨迹有明确照片观测。12段原tracks/pairs共24个SHA经复核符合原冻结回执。

两次开发启动均保留在`engineering_attempts`：714676db在HERO前停止；f5703ca5发现重复SIFT坐标身份问题后停止，已有44次HERO推理/原生结果保留。它们不是资源重试，也不计入正式dfc13a01结果；详见`evidence/ENGINEERING_ATTEMPTS.json`。没有以好坏选择版本或删除异常面源。

## 评价解释与后续边界

- 所有原105个Target逐一对照，Support不同须标记，不能用不同Target均值宣布路线优劣。面积比/高度分布仅提示明显尺度或分层变化，不是GT准确率。
- 固定R0 Target对的跨源深度投影是条件性一致性诊断。B参与A的HERO时明确标记；即使B不参与HERO，其相机仍由同一BA求得，不是全链路独立盲测。
- 单源图按“新恢复、R10成功对照、R5成功对照、照片Target”类别的身份列表中位序号选取，不按质量挑最好结果。各列同Raw完整毫米范围、同观察方向、黑色真实CAD；不修改或融合Mesh。
- 初始化被准入/选择使用的held指标不是独立测试。没有形状/位姿GT，不能报告正确率或宣称全局最优。
- 本轮结束后只交付审阅与[全量启动方案](FULL_RUN_PLAN.md)。全量79视频/120照片启动既需研究者确认回归结果，也需落实足够输出空间；当前配置明确拒绝自动启动。
