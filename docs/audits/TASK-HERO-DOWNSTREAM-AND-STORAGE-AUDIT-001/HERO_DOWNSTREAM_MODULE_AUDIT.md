# HERO 下游模块与完整路线审计

任务：`TASK-HERO-DOWNSTREAM-AND-STORAGE-AUDIT-001`。审计日期：2026-11-26，Asia/Shanghai；机器 `liu-INVALID`。本轮只读取科学资产、写审计文本；没有执行 M2F11/M2F12、训练、推理、重渲染、算法修改或修复。任务书指定的两份主报告取代通用规范要求的第三份 `TECHNICAL_REPORT.md`，避免重复交付。

## 1. 可以据此作出的决定

**保留三条有明确用途的组合：固定输入八块工程回归（R-REPLAY）、M2F10 的 V6 多目标开放曲面候选（R-V6）、EXACT013→Graph/SmoothARAP→Sweep/Boolean 的主体/柄部研究组合（R-BODY）。同时保留历史004相机/参考库恢复链（R-004）及 M2F6 对照（R-M2F6）。目前没有可认证为“RAW→可靠完整主体与柄部”的成熟端到端路线。**

- M2F10 的数量收益不能改写成融合精度收益：5个物理组/10视频中，4组/5视频有接纳曲面，共66面源；Ip20两视频为零。198/198 A→B 是有接纳输出的支持相机对上完成评价，不是198个独立样本，也不是全体视频质量通过。
- 当前 README 的默认入口确实消费历史主体 checkpoint，且相机/HERO块和Body块彼此独立。这是源码明确声明的工程回归；如果称为从新HERO全链重建，就是错误解释。
- 旧TSDF、NeuralFusion、PMGR-FFD、旧重写Body-E及大部分重复实验包装退出日常主线维护，保留独有算法与正负结果。MonoSDF停止默认推进、保留未完成训练状态；不能把4000步解释成充分训练失败。Hull H1/H2已执行但未通过PM验收，保留研究候选身份。
- 不拆掉历史004的相机、RGB参考库、019/021构建源码、原始标定/Mask、冻结图像身份；004和005有不同血统，不能把V6 local005替换称为004恢复。

详表：[MODULE_VERSION_MATRIX.csv](MODULE_VERSION_MATRIX.csv)；资产与恢复：[第二份报告](EXPERIMENT_STORAGE_AND_REPAIR_REPORT.md)、[EXPERIMENT_STORAGE_MAP.csv](EXPERIMENT_STORAGE_MAP.csv)。模块编号沿用 T01–T43、CG/SU/SB/GR 等原注册号，新增 Nxx；版本编号包含本次真实文件SHA前缀。同SHA不自动等同运行行为，配置/输入/AST适配另列。Bxxx为只有某本地分支保存的源码字节版本，**不是已认证算法模块**。

## 2. 范围、真实HEAD与核查边界

| 位置 | 实测HEAD/分支 | 开始审计时状态 | 判断 |
|---|---|---|---|
| `/home/liu/ring_first_3d_workspace`（W） | `8e59081600db2739ab183325bbe5354c4d1d2b4c`，M2F8 | 18 tracked修改、28,075 untracked文件；包含运行产物 | 当前工作区，未切换其分支 |
| `.config/superpowers/worktrees/ring_first_3d_workspace/TASK-M2F10`（W10） | `2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c` | 3 untracked | 最新已发布V6候选源码；不是W当前HEAD |
| 同父目录 `TASK-M2F9` | `b791c9affa74e848f04792cb600f8b95040bba3a` | `tools/m2f8_render_v6.py`修改、2 untracked | 脏修改单独保护 |
| 同父目录 `TASK-M2F11` | 同W10，M2F11分支 | clean | 无独立M2F11源码提交不等于磁盘上无执行 |
| `/home/liu/polyp_research`（P） | `4483e25ede3eee1b6eaf96254d2544152f935c0d`，main | 14 tracked修改、2,602 untracked | 只读，未提交或清理 |
| `P/ring-first-3d`（H） | `fa649fa1cf20b111bfdb8489e8af20ba90339bba` | clean，技术注册分支 | 大量E3/E4源码、指标与图；不能漏审 |
| `/home/liu/ring-first-hero-core`（C） | `72f30e7f1a2edfc4b0dcd270da217ae65c07f516`，main | clean | 固定样本/原生HERO与viewer |

W共有73个本地分支，逐分支 `git ls-tree -r` 盘点到1,414个源码路径/blob组合，64个只出现在单个分支的版本进入Bxxx表。H的3个本地分支也已列举，重点源码按现存文件哈希核查。共扫描373,305条文件/链接元数据，无遍历错误；14,017个排除vendor/runtime的大部分Python源码有完整SHA，2,800个不同SHA，其中1,016个在该扫描集合仅一份，全部进入Uxxxx保护行。此“单副本”不排除Git对象或其他未扫描位置的副本，更不等于独有算法。

已读W/P/旧树AGENTS、`docs/cleanup_003/WORKSPACE_DEPENDENCIES.json`、`manifests/LOCAL_DEPENDENCIES.json`、PATH_BINDINGS、清理003及2026-10-13/16/30/31报告。32个相关ZIP/tar仅列目录，241个Python成员被识别；ZIP源码成员流式读入计算SHA，未整包解压。独有分支、归档和非Git文件的存在阻止“主分支未引用即可删除”的推断。

多处 `ring_first_3d_*` 旧目录的 `.git` 仍指向已不存在的 `/home/liu/ring_first_3d/.git/worktrees/...` 或harness宿主。`/tmp/rf019`被登记但路径不存在。它们的HEAD未核实；不能将旧清理报告的“对象仍在原位”当作当前事实。原文件仍可审计，详情见第二份报告。

远端只读 `git ls-remote` 实测M2F8/M2F9/M2F10与上述SHA相同；未返回M2F11分支。其他全部分支的远端完整性未逐一认证；本地upstream信息只作线索，Git远程不覆盖未跟踪数据/权重。

### 背景纠正：M2F11有历史部分运行

实际存在 `W/runs/m2f10_v6_multiview/M2F11-FULL-20261125-01`、`M2F11-PAR-20261125-A/B/C`及日志，并非“从未执行”。`runs/m2f11_partial_visualization/M2F11_PARTIAL_SUMMARY.json`记录8/102视频、4/39组有记录，2组3视频45接纳曲面；其`RUNNING_PARTIAL`是历史状态，审计开始时进程快照没有对应科研任务。日志含实际DXY/HERO前向完成记录；本轮没有启动/续跑它们。汇总滞后与每阶段最终状态仍需下一任务核查，不能把8条记录称为全量完成。M2F12没有本轮执行；未找到其独立运行证据不等于断言任何地方都不存在。

## 3. 完整路线：入口、真实组合与实际终点

路径简写：W/P/H/C/W10见上表，E=`P/ring_anchor_3d/experiments`。下面所有“执行”指已有记录，本轮不重跑。

| 路线ID | 入口 → 实际模块版本 | 输入 → 输出；代表实验 | 实现/科研/复现边界 | 处置 |
|---|---|---|---|---|
| R-REPLAY | `W/scripts/run_pipeline.sh`→`mainline/scripts/run_pipeline.py`→`replays.FUNCTIONS`（N02）；N01、EXACT013、SB/GR、T43/T30 | C/G01_demo + retained_sources + STEP024/Sweep →8块回归结果；cleanup003 | 已执行8/8历史回归；相机/HERO与Body为独立块；固定输入可复现证据，非RAW优化闭环 | 继续维护工程回归 |
| R-V6 | `W10/tools/m2f8_v6_general.py`（N10）→`m2f5_unified.prepare_one_m2f6`→V5 Ring→V6 track005/local_ring_sfm/validate_select→全target支持调度→原HERO/独立packager | RAW、分割权重、CAD、配置 →native深度/开放Mesh/A→B；M2F10-FORMAL-20261125-02 | 5组10视频；66面源；尚无可靠多面融合/跨视频认证；RAW执行有身份链，非新独立重复实验 | 下一轮V6候选基线，不能宣称正式精度通过 |
| R-M2F6 | `W/tools/m2f5_unified.py --m2f6`及M2F6配置（N03）→既有W0/选择/原生HERO/评价 | RAW→相机/曲面；`runs/m2f6_unified/formal_002` | 5组10视频已有输出；scientific_incomplete；M2F7与V6帧集交集为0，不作配对提升统计 | 独立对照/失败回归 |
| R-004 | N04 `features019.landmarks`、019/021原相机池→`reference_banks`→native RF5DoF/SIFT-PnP yaw→HERO | 冻结004公制相机/RGB map→原生HERO；001和C/demo | 找到构建核心与成品，但初始相机→所有参考库构建的精确日志闭包尚不完整；不是local005 | M2F12恢复必须保护；暂不重建替代链 |
| R-MIXED-002 | `experiments/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002/code/bootstrap_references.py` + `cameras.py`→native recover→HERO/Body | 004冻结库、005 V6建库、G02第三来源→同A线recover | 实际运行过的混合组合；旧per-frame验证/support消费者遗漏，不能用M2F10已修订状态反推002正确 | 负结果归档，不作默认组合 |
| R-BODY | EXACT013输入→SB02 DeformationGraph、SB03 SmoothARAP、SB01/07门控→STEP024→GR03 EmbeddedSweep/GR04–09 Boolean与门控 | G01/G03冻结相机/Mask/初体→主体/柄部；STRUCTURED-BODY-002/GROWTH-RECOVERY | 两病例研究链；G01接受，G03 PER_VIEW_PROTECTION/正式NaN；当前默认仅重放保存状态 | 继续主体/柄部研究，保持原版本组合 |
| R-ELLIPSOID | T04–09：9参数、解析椭圆投影、E1二维椭圆/E2完整Mask→多初值TRF/资格检查 | 4主004组→候选体；BODY-GUIDED-HERO-DXY-REPAIR | 数值4/4，各臂完整资格0/4；不能替代EXACT013 frozen初体 | 数学模块保留，完整路线归档研究候选 |
| R-DEPTH018 | T24可见性修复renderer+T27自由顶点+T30原生首交深度+T33/34门控 | 4组43来源（29FIT/14held）→018更新 | 有实际执行与梯度证据；G03 miss无有效梯度、nearest背面；不能把loss下降当覆盖改善 | 原生深度目标可复用，路线仅研究候选 |
| R-PMGR | 谱基/渐进/FFD与trust_region（N07，独立旧实现） | 冻结主体/HERO→PMGR变形 | 4组80臂MIXED；FFD两组6臂，G06同尺度FD失败、无独立holdout | 退出默认维护，留负结果/提案组件 |
| R-CLEAN/FUSION | Type-2/跨视角Mask证据→选择性补片/TSDF T39/NeuralFusion T40 | 同视频多HERO→融合/筛面；E3、PHASED系列 | TSDF、官方NeuralFusion均实跑，第一层/孔洞/叠层退化；多面叠加不是认证融合 | 无成熟融合版本；分源Raw保留为首选证据 |
| R-CROSSVIDEO | 019 RGB/Ring→020对称SIFT→021共同地标BA；MASt3R/固定主面分支独立 | 004/005来源级变换→共同场景候选 | 共同地标背景、held/深度支持退化；GICP越Ring/NOT_FUSED；不能默认为统一坐标 | 历史基准及失败证据；暂不作为正式下游输入 |
| R-HULL | N05 H1/H2遮挡雕刻 | G01两视频各自坐标/Mask/CAD→体素/包络 | H2保护环后未知区；倾斜锥、ROI墙；真实端到端精度NE；新PM未验收 | 归档候选，不当可信完整主体 |
| R-IMPLICIT | T41官方MonoSDF adapter→MLP/体渲染/iso0；早期E0/E2受限学习另存 | 已冻结metric域和清理HERO→SDF Mesh | G01 M1真实4000步；目标G06/G08 NOT_RUN；层数恶化；NeuS2提案，其他术语未核实有效接线 | 停默认推进，保留可续状态/负结果；无成熟全局隐式版本 |
| R-MAP | N13 MapAnything，另有MASt3R/native pointmap/RoMa支线 | RGB/匹配→点图或配准候选 | 有旧执行记录，非HERO后处理同一方法；Map权重本地缺失 | 竞争路线归档，恢复成本另算 |

`mainline/scripts/run_pipeline.py`逐块启动新进程，明确写出`new_optimization_steps=0`与`scientific_certification=False`。`replays.body_update`直接读取 `STEP_024/GRAPH.npz` 的rotation/translation；`growth`读取`FINAL_SWEEP_PARAMETERS.npz`。**没有证据表明默认脚本偷偷将历史深度冒充新HERO；但它根本没有实现新HERO反馈到Body的训练闭环。** 这比笼统说“全链已跑通”更准确。

M2F10通过RAW准备子进程避免历史同名Python模块污染；`source_modules`及AST适配仍依赖V5/V6旧脚本。支持相机要求VALIDATED且共享≥15 tracks/3个不同真实来源；target本身不保证VALIDATED。原表中Is14/004、Ip8.8/004的`validated_raw_count=0`却有接纳曲面，不能误报“所有接纳target相机已验证”。独立packager移除了历史“两case比较尾部”假设，保留几何体；这是版本行为改变，不能仅凭冻结V6源码SHA相同认定相同路线。

### 3.1 主体引导路线中还应独立保留的版本

这些版本在新整理目录外也有实际实验，不能合并成同一“主体拟合”或只按是否包含mainline命名判断成熟。CSV的MF/SR/IA/CG/SU版本已补到现存迁移报告/冻结记录并计算证据SHA；只有DV01的单独执行证据仍未核实。

| 路线 | 实际链路与输入输出 | 当前证据/相对变化 | 保留条件 |
|---|---|---|---|
| R-DUALVIDEO | `src/ring_first_3d/dualvideo/audit.py`等DV01–07：004/005原生相机/RGB/Mask/CAD→场景身份门控→合成注册控制 | 场景资格是后续实验前提；真实绝对pose没有独立GT，不把合成成功迁移成真实认证 | 单独留真实性门控与失败，不直接替代019/021 |
| R-MULTISURFACE | `multisurface.handlers/scene/registration/fusion` MF01–05：冻结多面→低维Body引导来源变换→保来源场景 | 已执行G01-like单seed控制；科学为MIXED/局部定位负结果，不是成熟全局融合 | 保留算法/原面来源；停止把新场景外观当增益 |
| R-STRESS | `stress.handlers/real` SR01–04：原MF链+单独CTF适配→压力控制/真实最小接口 | 34/34仿真条件、3/3真实组有数值；C4/E1分散下降但GT MAE .294137→.308335mm，真实绝对精度NE | CTF与原阈值结果分开；34条件不是34独立真实组 |
| R-INIT-A | `inita.train` IA01–05：EXACT013→015原顶点训练，多视频均衡→HERO定位 | 目标11组，10/11共同数值；严格实体IoU仅3/11组有效，.746908→.767866；HERO完整多曲面4/11组，定位收益不稳定 | 保留Exact013初值与原trainer；不能用E1/E2或单005补G08缺004 |
| R-CONTOUR | `contour_guided.correspondence/experiment` CG01–05：固定Body/相机/预算→显式2D对应→冻结后H4 HERO定位 | A2D→A3公平无深度对照6/10 Chamfer改善，平均−.001373mm；H4对H3同视频0/4、跨视频1/3改善。新Body收益未稳定传递 | 作为SB对应证据组件保留；H1/H2/H3/H4这里是重定位对照，不是Visual Hull H1/H2 |
| R-STRUCTURAL | SU01–06：显式轮廓→自由顶点+局部面片挤出→冻结后HERO像素重定位 | C0 MAE .380925→.278727mm；真实G01 .351000→.398401退化，G03/G05位移约1e−5mm停滞；没有ARAP | 归档旧结构更新负结果；SB02/03替换参数化/正则后才是Graph+SmoothARAP，不能改名混同 |
| R-BODY前段 | SB01–11：32节点Graph+SARAP→共享边界Sweep提案；三组×两臂 | G01 MAE .35100→.33491但P95变差；G03无可靠改善，G05停滞；**此002阶段没有任何Sweep获准** | GR后续仅恢复G01/G03被拒参数并改为embedded/Boolean链；不能把后续G01接受追记为002已接受 |

直接证据：`references/mvs/TASK-E4-MULTISURFACE-STRESS-AND-REAL-PILOT-001/RESULT_CARD.md`、`references/multiview_alignment/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001/RESULT_CARD.md`、同目录CONTOUR任务RESULT_CARD，以及`assets/retained_sources/{ring_first_3d_structural_update,ring_first_3d_structured_body_002}/experiments/<各自TASK>/TECHNICAL_REPORT.md`。这些既有报告给出指标定位，完整源码与实际调用符号/哈希见CSV；没有把注册表状态直接当新实测。

## 4. 分技术环节推荐与明确缺口

| 环节 | 推荐保留版本/理由 | 适用条件、退化与剩余缺口 |
|---|---|---|
| HERO公制原生输出 | N01 native/hero.py + geometry.py；V6路线仍绑定原adapter3 | 4帧、3supports、共同K；352×640原生Z/mm；world=`(K^-1 uv Z)R^T+t`。pose送模型前mm/1000、深度出模型后×1000；轴向Z不是射线长度；RGB/Mask用half-pixel映射；Raw面原本已有0.75mm跳变门槛，不能算后续清理收益 |
| 清理/标签 | T21/T22 017证据与T23路径适配版；T30/018只消费明确原生观测 | 017最终18来源×两表示，0删面；TRUSTED也可能自解释错平面。不得混NATIVE_GRID与ARCHIVE_RAW FaceID；保留Unknown/uncertain；Type-2定向空间规则与全B-Mask规则只能在其原协议内使用 |
| 多参考/重复面 | 分源Raw+来源ID+首次命中一致性；N10只调度更多独立target | 目前无成熟融合版本；TSDF/NeuralFusion和“选择性融合”不可用较漂亮Mesh替代第一层误差与覆盖分母 |
| 跨视频 | N04/019–021及匹配审计作为回归材料 | 没有可普遍认证的共同坐标版本；每视频Ring gauge独立。来源级SE3/Sim3、ICP/GT对齐与真实公制共同坐标必须分开 |
| 初始化 | R-BODY必须EXACT013原输入+同initialize；T05–09保留独立研究 | E1/E2只改变2D loss/输入，不自动比冻结Mesh更成熟；4组均未完全合格。H1/H2是可行包络，不能补隐藏形状 |
| 主体更新 | SB02/03/07 Graph+SmoothARAP与原gate组合；T24可见性修复renderer/T31轮廓 | Graph限制的优化不是原论文无约束全顶点线性求解；ARAP正则不提供独立形状真值。旧soft-zbuf梯度失败版本退出；014/015/016留回归，不混装018 |
| HERO深度监督 | T30首次命中/barycentric轴向Z，保留未命中项 | T28/T29旧相对稀疏深度是不同观察模型，不能换名冒充018；018 G03固定miss无梯度，nearest背面不能当有效监督 |
| 对应/重定位/生长 | CG/SU的2D对应用于证据；SB/GR原组合用于柄研究 | HERO重定位不能改变原像素/来源身份；主体冻结后低维修正不是全局融合。5控制点、16站Sweep/RMF/EXACT Boolean需原配置与Blender；G03正式NaN继续保留 |
| 全局SDF | T41作为唯一有较清楚官方接线/真实训练记录的研究档案 | 4000步≠充分训练；SDFStudio/BundleSDF/独立VolSDF未核实项目执行，不以名称补实现。NeuS2明确NOT_RUN |
| 评价/测量 | T43真三角面A→B + T35预测冻结后固定scale最佳SE3 GT；正式Dxy用T01独立API | A→A回放只测自洽；A→B的support相机不是独立相机GT；最佳GT位姿只Oracle形状评价。开放面面积不可当唯一解剖面积，开放/人为封底体积不能称真实体积；高度基底定义与环平面分开 |
| 展示 | N10既有六视角/原观察图，R-BODY切面/失败图 | 标注mm、原Mask/GT状态；PLY/NPZ/mm与GLB/m区分；不重渲染。根目录M2F10 HTML有路径故障，图文件本身仍在 |

### 4.1 可直接复核的负结果

- 017：`H/experiments/TASK-E4-HERO-GEOMETRY-CLEAN-017/metrics/FINAL_SOURCE_SUMMARIES.csv`、`GROUP_SUMMARY.json`及`FAILURE_LEDGER.md`。4组18来源，G01 11来源不算11独立组；原Raw 570,176面（各组计数见原表），最终0删面。
- E1/E2：`H/experiments/TASK-E4-BODY-GUIDED-HERO-DXY-REPAIR-001/metrics/NEXT_STAGE_ELIGIBILITY.json`直接记录`advance_to_HERO=false`、多初值不稳/留出不一致/Ring穿透；不能仅据numerical_available=true称通过。
- TSDF：`H/experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/TECHNICAL_REPORT.md`及其`TSDF_CONFIG.json`/逐来源CSV：ref08首层50.22%→27.98%，mm/m等价最大0.0020026695mm超过0.002mm；未命中的完整分母p95为∞，不能仅用有限命中的p95。
- NeuralFusion：`H/experiments/TASK-E3-N0-NEURALFUSION-EIGHT-VIEW-001/TECHNICAL_REPORT.md`和metrics/清理决定：G01八参考/G06五参考，官方完整链已执行；G01 ref08首层73.52%→0.47%，多层6.44%→66.43%。输入清理还会失去细部，不能用“接线完成”做科研验收。
- MonoSDF：`H/experiments/TASK-E3-SDF-RTX4090-M1-10X-MULTIPOLYP-001/TECHNICAL_REPORT.md`，2000→4000首层43.78%→43.49%、≥4层7.89%→22.80%；固定分母48,641可见原观测。历史4000步checkpoint记录SHA `63a1b05b681fd47929afe2b05437f18bc5ccb9ad28c63056179315cb00859985`；本轮未核实远端或该checkpoint全部可恢复。
- G01/G03：`mainline/results/G01`、`mainline/results/G03`中的参数、CHOSEN_GATES、FINAL/FAILED_ATTEMPT；`docs/cleanup_003/MODULE_REPLAY_DETAILS.json`。原报告G01独立SE3 MAE 0.334906→0.303623mm，固定INITIAL→GT 0.335972→0.356988mm，不能只报改善的一列。

### 4.2 M2F8→M2F9→M2F10的真实差别

三个版本同名`tools/m2f8_v6_general.py`，CSV N08/N09/N10分别保存当前字节SHA。M2F8用统一R5/R10 adapter得到13曲面，缺共享输入因果交换与完整续跑身份；M2F9改RAW准备进程、Ring按ID关联、参考/留出索引绑定与状态链；M2F10增加所有目标调度、支持tuple重试和每case包装，66个接纳面源。以上数量变化受输入/选择/调度共同影响，不能归因为单一核心算法更准确。

N10的正式状态写的是代码提交`a38d4c822daf9a9b3cd88e1cd0edebdc70b9bfad`，W10 HEAD `2cd9822e...`是后续报告提交。实际重哈希16份RUN_STATE、1,720条引用（1,247个唯一文件）全部匹配；并未调用原科研runner。报告写“15 attempts”与实际16（10 attempt0 + 6 attempt1）不符，应按记录修正文档而非更改历史状态。

`W10/experiments/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001/evidence/final/VIDEO_METRICS.csv`重算：160 target记录、86 native输出记录、66独立packaged；独立target数还需按`independent_*`列，不把重试记录当独立样本。A→B使用已接纳target的3个support，198对来自4个有结果物理组；目标组分母仍5，视频仍10。15–16 HERO/组的M2F6对照与该选择不是共同样本，不报告配对改善。

## 5. 源身份、当前依赖与保护边界

99条原注册模块逐文件对照，其中98条与原登记SHA相同；T23 `clean_native.py`只增加`historical_path`导入并重绑定旧`/home/liu/ring_first_3d/experiments`，diff已确认。它必须另记运行适配版本；不能静默抹掉字节差异，也没有证据说明其科学阈值被改动。

HERO官方加载器实际锁定upstream `5bd49bba0992aa56060e1aa3bb40b2150b04726f`并逐文件核验；旧注册卡末尾写的`4483e25...`是P父仓库提交，不能当官方MVSAnywhere commit。HERO ckpt完整SHA本轮与外部清单再匹配。DINO源码是离线backbone构建依赖；`E/ring_first_v13_multisource/weights/dinov2_vitl14_complete.pth`另被`roma13_verified.py`直接加载，不因HERO的`pretrained=False`就认定它无用。

动态加载实证：`replays.activate`插入指定lineage code；`definitions`抽取AST；`paths.historical_path`重定位；N10 `source_modules`、V6 `v6_common`→V5 `g5_common`→V4 `v4_common`→surface_fusion_v3/v2/v1共用project/反投影/Open3D。脚本`python.sh`把P的vendor和本地runtime放入PYTHONPATH。**这些入口运行环境是组合依赖，不是仅拷贝一个py即可恢复。**

绝不能丢失：

1. **004恢复**：C `.local_data/G01_demo`全样本（尤其`REFERENCE_RGB_MAP.npz`、`historical/CAMERA_INITIAL.json`与DATA_MANIFEST）；W 001 `audit/reference_banks/{G01_004,G01_005,G03_004,G05_004,G06_004}.npz`及OBSERVATIONS；019/021 `features019.py`/相机池/图像身份；W `assets/retained_sources`中013/014/015/018/MAX来源、原RGB/Mask/K/T。构建源码已找到，全部初始相机生成命令/祖先日志未闭合，不能称“已从RAW恢复004”。
2. **V6/M2F11**：W10 N10脚本及其父源码，E V5/V6/V4、surface_fusion_v1–v3必要源文件；原RAW（包括W `smart_endoscope_20260805 (1)`）、INIT分割权重/配置、官方HERO checkpoint及MVS/DINO源码；W全部RUN_STATE/RUN_TRACE/input身份、失败与M2F11部分状态。RAW有同名但不同覆盖范围，不能整目录按副本删除。
3. **主体/柄部**：EXACT013输入身份、INITIAL、STEP024 GRAPH/BODY、SB/GR原code、原始相机/Mask/split/权重、FINAL_SWEEP_PARAMETERS、G03 FAILED_ATTEMPT/拒绝gate、GT原形状及评价变换、运行库/Blender。未纳入Git的这些资产需要独立备份，远端代码不是备份证明。
4. **公共保护**：DXY冻结库、原视频/照片/ZIP、GT/标注/标定、Ring CAD、必要权重/环境及独有未提交源码；保护清单优先于重复哈希。

## 6. 退出维护时必须留下什么

| 路线/版本 | 可退出的维护范围 | 最小证据与可考虑收敛的大产物 |
|---|---|---|
| M2F8/M2F9、M2F1/2/3/5等阶段包装 | 不再各维护一份新默认runner；保留旧入口原样 | exact commit/配置/RAW身份、命令日志、选择与失败、指标、代表原生深度/曲面和版本差异。仅哈希确认重复的诊断输出进入Dxxxx；不按run目录整删 |
| 旧Body-E T42、未修复soft-zbuf | 不作为默认拟合/renderer | 损失差异、梯度失败与修复对照、源码、输入、失败表；旧唯一mesh仍先归档 |
| TSDF/NeuralFusion、选择性补片 | 停默认融合推进 | 所有源ID/输入协议、mm/m测试、顺序与逆序、首层/孔洞/覆盖指标、解释错层的图和至少一原输出。未闭合输入/权重时不能声称可重算 |
| PMGR/FFD/014–016 | 停重复重写与非必要大规模参数分叉 | FD失败、拒绝轨迹、共同样本与独立组表、最终/关键失败mesh、确切源码及配置；不能只保留最后“最好”图 |
| MonoSDF/神经E2系列 | 停默认全局隐式主线 | checkpoint含optimizer/scheduler/RNG/step；原native分母；配置/官方源版本、训练和未运行台账。远端checkpoint未核实，暂不能删除本地唯一训练证据 |
| Hull H1/H2、跨视频失败支线 | 保留候选，不再宣称完成重建/配准 | 正式完整unknown/ROI域、对照子集区别、逐视频失败、GT状态/变换及源身份；显示用GLB不是全部科学证据 |

本轮没有确认一个独有算法被完整替代且可无条件丢弃。能够进入清理选择的是**具体相同字节副本**，而不是整个研究路线的全部资产；第二份报告给出空间收益和恢复前提。

## 7. 已核查、未核查与交付边界

已核查：实际HEAD/工作树、模块源码哈希及关键函数调用、归档目录、原始指标/负结果、主输入/运行库闭包、N10状态引用、候选大文件完整SHA、主要展示路径。固定输入清单5759/5759、外部126/126、runtime1045/1045匹配属于文件身份验证，不是本轮247项测试重跑。

未核查/阻塞：所有旧分支的每个函数语义；全部档案成员与Git blob的全组合比较；旧工作树失效Git宿主的完整对象来源；004初始相机→所有库的完整构建日志；全部旧HTML/图链接；云端SDF/checkpoint与外部存储可用性；全部运行环境ABI实际导入；M2F11各历史worker停止时点与后续完成状态。以上统一标“未核实”，不补写不存在/成功/备份完成。

审计结论是可据现存证据选择路线和清理前置工作的目录，不是新的科学验收。第二份报告给出真实磁盘、恢复步骤、M2F11峰值估算与提交上传回执。

## 附录B：本地分支快照

以下是本地refs及缓存upstream关系，只有正文列出的3个M2F远端HEAD做了本次联网验证；其余不能据空ahead字段宣称上传成功。

```text
audit/TASK-CLEANUP-SPACE-AUDIT-002 deed4b045411452e3efef620ca94ea358930726b origin/audit/TASK-CLEANUP-SPACE-AUDIT-002
audit/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT af90667787f268a93769b8916f16e452e7ce25ba origin/audit/TASK-E4-W0-CROSSVIDEO-022-INDEPENDENT-AUDIT
audit/TASK-E4-W0-CROSSVIDEO-022R-RESIDUAL-FORENSICS b114ac45a217f05e0df6130dc2fd5aa39e4b5530 origin/audit/TASK-E4-W0-CROSSVIDEO-022R-RESIDUAL-FORENSICS
exp/TASK-E4-CAMERA-ADMISSION-013 f3665e138ead158851889ffb04ce9b44d54d62cb origin/exp/TASK-E4-CAMERA-ADMISSION-013
exp/TASK-E4-CAMERA-ADMISSION-013-PATCH 10e9175b1837fddc82fcb27450f57e088da6e15c origin/exp/TASK-E4-CAMERA-ADMISSION-013-PATCH
exp/TASK-E4-CROSS-VIDEO-CAMERA-014 ed956d2d23a3f5b28c3a28ce6ca9c455b2fa6460 origin/exp/TASK-E4-CROSS-VIDEO-CAMERA-014
exp/TASK-E4-DXY-CONIC-PRIOR-PILOT-002 6f9007af2bdb0f5e96515bc6c0d41cac306f4b54 origin/exp/TASK-E4-DXY-CONIC-PRIOR-PILOT-002
exp/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001 a87eac085193b7af56e363bf8fe86d675b3e6c0e origin/exp/TASK-E4-DXY-CONIC-RING-OBSERVATION-REUSE-001
exp/TASK-E4-G01-PIPELINE-AUDIT-003 c5a6be7c991bdb843ac27aeee7eb7a2045fec277 origin/exp/TASK-E4-G01-PIPELINE-AUDIT-003
exp/TASK-E4-HISTORICAL-CROSSVIDEO-REPAIR-019 2cfc4dbeca0766f0390f0c830af81b7cf84a72d1
exp/TASK-E4-HISTORICAL-CROSSVIDEO-REPRODUCTION-019 2cfc4dbeca0766f0390f0c830af81b7cf84a72d1 origin/exp/TASK-E4-HISTORICAL-CROSSVIDEO-REPRODUCTION-019
exp/TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004 732a8d73f2c256529c8671b5167aa64244d3e399 origin/exp/TASK-E4-PIPELINE-VALIDATION-AND-RING-MASK-AUDIT-004
exp/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004 ca8fa3856e26566e18563de1b07eaae0f6257f2d origin/exp/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004
exp/TASK-E4-REAL-INNER-OUTER-JOINT-BA-009 c4fb171836e83b9bc4be354b7e73a2e8e0c333cb origin/exp/TASK-E4-REAL-INNER-OUTER-JOINT-BA-009
exp/TASK-E4-REAL-JOINT-BA-008 251f760d75aa9b3d48a11e6c3dcc1bfebb988347 origin/exp/TASK-E4-REAL-JOINT-BA-008
exp/TASK-E4-REAL-RING-GEOMETRY-010 72719a58a9118e6736f69f48e0652f0e390a6100 origin/exp/TASK-E4-REAL-RING-GEOMETRY-010
exp/TASK-E4-REAL-RING-RGB-JOINT-BA-007 c81850aba0aaf83cb8b2c36eecbffb667e3116a2 origin/exp/TASK-E4-REAL-RING-RGB-JOINT-BA-007
exp/TASK-E4-RING-CROSS-VIDEO-017 fd9d3f186071f686f28c80380a0e706158cd9cd2 origin/exp/TASK-E4-RING-CROSS-VIDEO-017
exp/TASK-E4-RING-CROSS-VIDEO-018 918efb13c3efd7958513ad81afc030ea993e47d4 origin/exp/TASK-E4-RING-CROSS-VIDEO-018
exp/TASK-E4-RING-CROSS-VIDEO-018-REPAIR 969bc565928f5da2797298a0d76ad38424b7816b origin/exp/TASK-E4-RING-CROSS-VIDEO-018-REPAIR
exp/TASK-E4-RING-RGB-J2-CORRECTION-012 ba70f3402db0bc9ad0436b7fa3991c9ed0a9804e origin/exp/TASK-E4-RING-RGB-J2-CORRECTION-012
exp/TASK-E4-RING-RGB-JOINT-BA-011 d4cecc7266d848df0da443083cd0a0206a963e39 origin/exp/TASK-E4-RING-RGB-JOINT-BA-011
exp/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR ae05d1fcf9178215f982ea5d930153b1e74560d5 origin/exp/TASK-E4-RING-RGB-JOINT-BA-011-REPAIR
exp/TASK-E4-RING-RGB-JOINT-BA-012 98ffa3b25c19348838e8799851455ebde943dc24 origin/exp/TASK-E4-RING-RGB-JOINT-BA-012
exp/TASK-E4-RING-RGB-JOINT-CONTOUR-BA-006 2abbfe8ac406637c5e2678b80e08618ca3a8626e origin/exp/TASK-E4-RING-RGB-JOINT-CONTOUR-BA-006
exp/TASK-E4-RING-RGB-JOINT-CONTOUR-BA-006-FIX 094f11ea5adefe7cb727f2f6ed1762a9f04e7d81 origin/exp/TASK-E4-RING-RGB-JOINT-CONTOUR-BA-006-FIX
exp/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002 ff242954b10624840ade9e711078625cd4f9232e origin/exp/TASK-E4-UNIFIED-PIPELINE-COMPLETION-002
exp/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005 b3cf5e0ffb270dd053ccdcb6893dcbf722078215 origin/exp/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005
exp/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001 2fe2c3cbda40bd4d0f8a15a3d71dad3f494a1c7f origin/exp/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001
exp/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005 ba6c4dc256281f9eae4a3fe92ec62522a9cccaf8 origin/exp/TASK-E4-UNIFIED-RING-RGB-CAMERA-MAINLINE-005
exp/TASK-E4-VIEW-DENSITY-SWEEP-003 78d93b67a53ac6df335ce645053598e1bc8f6971 origin/exp/TASK-E4-VIEW-DENSITY-SWEEP-003
exp/TASK-E4-W0-CROSS-VIDEO-016 fefe3695681385ecb5cdae2a6af0cbd855da5d0d origin/exp/TASK-E4-W0-CROSS-VIDEO-016
exp/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE bfd9c622bb2660b4a2e4c2ffdbadbb72b19971fd origin/exp/TASK-E4-W0-CROSSVIDEO-021-CORRECTIVE
exp/TASK-E4-W0-CROSSVIDEO-021-REPAIR 98812c74dc67497e893e475579dc546a387dc67a origin/exp/TASK-E4-W0-CROSSVIDEO-021-REPAIR
exp/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE cf31e232ad692956bc69cb2c0164e2edcdd7e4e3 origin/exp/TASK-E4-W0-CROSSVIDEO-023-RESTORE-AND-VALIDATE
exp/TASK-E4-W0-CROSSVIDEO-024-LANDMARK-IDENTITY-AND-REPAIR 4c7f01594c7aad86f5246daf8b53cd06dc1f80a6 origin/exp/TASK-E4-W0-CROSSVIDEO-024-LANDMARK-IDENTITY-AND-REPAIR
exp/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY 22987a619e39ea01a0b81e4573facfb3f831def4 origin/exp/TASK-E4-W0-CROSSVIDEO-025-IDENTITY-RECOVERY
exp/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE 4d6104d915ba8462ec9e42231cb2348100870ae1 origin/exp/TASK-E4-W0-CROSSVIDEO-026-CORRECTIVE
exp/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY f6fdd9e99a8036bb7b82cacdfcf04e867848aa57 origin/exp/TASK-E4-W0-CROSSVIDEO-026-RING-GEOMETRY-AND-UNCERTAINTY
exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE 5a0251a6c6d2de94f95a753d207ab57ba921c56a origin/exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE
exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2 ad5d09fcf82e49a4d9cb67e71ae273a3e0773af3 origin/exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R2
exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3 48f886e7ca00805ae11b90c82ddb117228d95a02 origin/exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R3
exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4 b92d717d567963126d380151aa5895c641f6f8c3 origin/exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R4
exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5 625ddbfc153bde030dfb5b95dd9e06c551c6885e origin/exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R5
exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6 23b3fb0e9da17ce54f79654d13ea8c9b0869cb73 origin/exp/TASK-E4-W0-CROSSVIDEO-027-CORRECTIVE-R6 [ahead 1]
exp/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT 42525c72bfaa75cf921a7563db6ab3ecedc179c3 origin/exp/TASK-E4-W0-CROSSVIDEO-027-RING-ANCHORED-BA-PILOT
exp/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE 194cbbbaa483d8bad30c38d7f067d58f03aaa65d origin/exp/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE
exp/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL 45e19c440c9c72efd5f5acf73851bf9909fb45ee origin/exp/TASK-E4-W0-CROSSVIDEO-028-CORRECTIVE-FINAL
exp/TASK-E4-W0-CROSSVIDEO-028-REAL-UNIFIED 23b3fb0e9da17ce54f79654d13ea8c9b0869cb73 origin/exp/TASK-E4-W0-CROSSVIDEO-028-REAL-UNIFIED
exp/TASK-E4-W0-CROSSVIDEO-UNIFIED-020 8d4936ad9bc49fc32f687b3635ee2ffac79ae27b origin/exp/TASK-E4-W0-CROSSVIDEO-UNIFIED-020
exp/TASK-E4-W0-MAINLINE-CONSOLIDATION-015 e455b9a8661d60beddfe87cc7f40612c3d87570f origin/exp/TASK-E4-W0-MAINLINE-CONSOLIDATION-015
exp/TASK-E4-W0-REGISTRATION-STAGE-020 ea4b4479ff13422443c2b7c0cf978251d5617eea origin/exp/TASK-E4-W0-REGISTRATION-STAGE-020
exp/TASK-M2A-W0-OBSERVABILITY-GRAPH-RECOVERY-001 aff1d40f885f27cfc9d07ee661e7dabd215e0f2b origin/exp/TASK-M2A-W0-OBSERVABILITY-GRAPH-RECOVERY-001
exp/TASK-M2B-RING-OBSERVATION-AND-GLOBAL-BRANCH-001 888503ab8d6ad7064b4c83961185475ebc2348d1 origin/exp/TASK-M2B-RING-OBSERVATION-AND-GLOBAL-BRANCH-001
exp/TASK-M2C-CORRECTIVE-COMPLETION-001 e08eafc28858ef5a41288b35b476802fc4ebc5f6 origin/exp/TASK-M2C-CORRECTIVE-COMPLETION-001
exp/TASK-M2C-W0-TRAJECTORY-AND-DOWNSTREAM-ADMISSION-001 14a790a4fbd54f59cfc50869e597a3ff13f6a6ed origin/exp/TASK-M2C-W0-TRAJECTORY-AND-DOWNSTREAM-ADMISSION-001
exp/TASK-M2D-HISTORICAL-MVS-REPRODUCTION-AND-VISUAL-CORRECTION-001 f3d95166c22ce0918418d76aeecca3bd732e8052 origin/exp/TASK-M2D-HISTORICAL-MVS-REPRODUCTION-AND-VISUAL-CORRECTION-001
exp/TASK-M2D-W0-REPAIR-AND-MVS-VALIDATION-001 d66bf8a3f4766c546353d6aca662c95e7fcba09f origin/exp/TASK-M2D-W0-REPAIR-AND-MVS-VALIDATION-001
exp/TASK-M2E-HISTORICAL-METHOD-INTEGRATION-001 7934553be9981ecaf0d3d0baad9217810d21c999 origin/exp/TASK-M2E-HISTORICAL-METHOD-INTEGRATION-001
exp/TASK-M2F-ADMISSION-RESTORATION-AND-METRIC-DEPTH-DIAGNOSIS-001 abd760fca8fa834fbe9bc93d1e9038413d2bacd4 origin/exp/TASK-M2F-ADMISSION-RESTORATION-AND-METRIC-DEPTH-DIAGNOSIS-001
exp/TASK-M2F1-STRICT-PIPELINE-RESTORATION-002 1b81bc5fa1c60a0093f3b261782bcfa48d0d23b5 origin/exp/TASK-M2F1-STRICT-PIPELINE-RESTORATION-002
exp/TASK-M2F1-W0-ADMISSION-AND-VIEW-SELECTION-RESTORATION-001 41a96c57209ba507ca953073d6e09c02683f1747 origin/exp/TASK-M2F1-W0-ADMISSION-AND-VIEW-SELECTION-RESTORATION-001
exp/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001 2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c origin/exp/TASK-M2F10-V6-MULTIVIEW-HERO-EXPANSION-001
exp/TASK-M2F11-V6-FULL-DATASET-VALIDATION-001 2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c
exp/TASK-M2F2-ROOT-CAUSE-CORRECTIVE-003 ef4a57c091293883c38f4aa3e2a8a2830052bbfe origin/exp/TASK-M2F2-ROOT-CAUSE-CORRECTIVE-003
exp/TASK-M2F3-W0-AND-ADMISSION-CONVERGENCE-001 907076543a24fa78a45b57c9eab3452457d8eb42 origin/exp/TASK-M2F3-W0-AND-ADMISSION-CONVERGENCE-001
exp/TASK-M2F5-UNIFIED-ROUTE-COMPOSITION-001 3d2f6fada8fc04d80c6af160ebc9d8741da7bcd9 origin/exp/TASK-M2F5-UNIFIED-ROUTE-COMPOSITION-001
exp/TASK-M2F5-UNIFIED-ROUTE-EXECUTION-001 8e58892074e103c33e00dc63a9ea480782d8c32b origin/exp/TASK-M2F5-UNIFIED-ROUTE-EXECUTION-001
exp/TASK-M2F6-UNIFIED-OBSERVATION-GEOMETRY-001 1a06461a91790ac1a115444434e176b6dabffb7c
exp/TASK-M2F7-HIST-G01-CAUSAL-001 5c061e0b0d511f07215cf0c4b128fc3385be5906 origin/exp/TASK-M2F7-HIST-G01-CAUSAL-001
exp/TASK-M2F8-V6-GENERALIZATION-001 8e59081600db2739ab183325bbe5354c4d1d2b4c origin/exp/TASK-M2F8-V6-GENERALIZATION-001
exp/TASK-M2F9-V6-GENERALIZED-PIPELINE-CORRECTION-001 b791c9affa74e848f04792cb600f8b95040bba3a origin/exp/TASK-M2F9-V6-GENERALIZED-PIPELINE-CORRECTION-001
local/workspace-003-baseline 5b36aba0c51d09e5d9403cad6c80bed251e15424
```

## 本轮收尾核验

2026-11-26T01:22:04+08:00：两份报告与两张CSV已交付准备；178个版本源码/可用证据SHA复核、2947条唯一资产ID、跨表模块关联、净释放求和、保留副本不与候选重叠、报告相对链接均通过。四文件合计约3.7MiB。全部原有效Git工作树的tracked/untracked状态与起始快照一致；本轮未运行科研测试或算法。仅本任务四文件将以临时Git索引提交到指定新分支，原分支和索引保留。上传是否完成以最终远端SHA实测回执为准。
