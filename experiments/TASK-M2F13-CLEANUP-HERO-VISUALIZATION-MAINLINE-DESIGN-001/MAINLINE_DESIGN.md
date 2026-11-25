# 下一代统一 Ring-First 主线：设计提案，未实施

建议采用**统一观测、有限多候选初始化、同一 Ring/RGB 联合 BA、冻结地图新 query 验证**的单入口方案。保留 Ring 对真实尺度、环平面/中心及物理合法性的约束，用 RGB 确定轴内 yaw 和完整相对位姿。当前证据不足以决定“V6整体保留”或“004整体替换”；更不支持在两条最终深度之间事后择优。这里推荐的是可被下一轮小试验推翻的架构，不是已经取得覆盖或精度提升的结论。

本轮仅完成既有 H004 的冻结相机下 HERO 补齐和原输出评价，没有实现下述求解器、重新优化相机、运行39组、训练Body或跨视频融合。

## 证据与边界

基准：M2F12报告提交 `1d561f251cf1dc74ae94245d13daf1851c7fef1f`；V6正式算法运行身份为RUN_STATE中的 `a38d4c822daf9a9b3cd88e1cd0edebdc70b9bfad`，报告提交 `2cd9822e1fbd3841a6151abc54acdc6ffe1d5a6c`不是算法执行身份。早期V6诊断尝试另有执行身份，逐源保留。M2F13新增69次HERO在 `c08ef3d292469e33469589f5268b0a0c283c42fd` 下执行，未重算相机。

[全部图集](HERO_ALL_VIDEOS_INDEX.html)、[204条来源清单](SOURCE_MANIFEST.csv)、[20条路线×视频统计](VIDEO_SUMMARY.csv)是本轮主要几何证据。174个唯一完整输入组合=H004 76+V6 98；V6的128条已有来源中30条是同输入别名，全部保留自己的输出、指标和别名图。五条跨CORE/V6记录原生深度逐元素相同，但Mesh定义不同，不能把别名原输出丢弃。32个诊断深度原先无打包Mesh，本轮按原V6转换函数生成几何，不是新增推理。

**观察事实 F1：数量不等于共同标准下的有效覆盖。** H004有76个原合法Target、7/10视频；V6有66个原正式面源、5/10视频。H004 seed基本精度通过0/10（包括2个seed失败）；V6的66个正式成员中，只有14个Target自身VALIDATED，52个Target未VALIDATED，三Support均通过。固定视频分母为10，物理组为5，不能把同组004/005当10个独立物理组做显著性结论。

76与0/10并不矛盾：H004 seed独立整轨迹测试采用原2px基本门槛，而后续原MAX资格看物理有效、FIT至少10点/4格/秩6、FEATURE_HELD至少4点且median≤8px/P95≤20px、Ring IoU≥.35及有观测边界median≤10px。FEATURE_HELD按landmark索引mod5，只从PnP拟合排除，没有从上游建库和seed排除；建库与query使用同一16帧池。其准入是**给定地图的条件资格**，不是全链路独立验证。两条指标既阈值不同，又评测对象/独立性不同。H004两线共同独立RGB结果仍NOT_EVALUABLE。

**机制推断 I1：** H004的地图匹配/PnP能在已有可用几何地图上恢复额外数值相机，连续LK与外观SIFT也可能补足彼此观测；这是合理的新增覆盖机制。但本轮76之中多少来自此机制、多少来自宽门槛及同帧建库回估，不能分离。H004共128个数值相机来自8个成功seed视频，V6固定池共167个数值相机且选帧不同；点数3463与3910还受V6每视频500点上限影响。禁止用这些非配对数量推断因果改进。

**观察事实 F2：** [H004 Ip12/004同一坐标规范近景](figures/H004_RAW_BASELINE__GP_Ip_12.0mm_closed_R10_single_refY_004__NEAR_GAUGE_00.png)显示环附近多个曲面及向下/侧向延伸的分离薄面；全范围和逐源图保留长尾。[V6 Ip12/005正式成员六视角](figures/V6__GP_Ip_12.0mm_closed_R10_single_refY_005__FORMAL__SOURCE.png)也有明显分层、不同方向的下延面与缺口，不能用环口附近视觉接近宣称整个面一致。它们都是各自同一次相机解算内的面源，不依赖跨尝试叠加解释。

**观察事实 F3：** H004 Ip20/004与005的各源Ring MAE分别约7.65–13.32mm、4.35–10.97mm，源P95最大约68.91mm、74.20mm。[Ip20/005全范围](figures/H004_RAW_BASELINE__GP_Ip_20.0mm_closed_R10_single_refY_005__ALL_NUMERIC__SOURCE.png)显示分离片段与长尾。[R5 Ip8.8/005代表图](figures/H004_RAW_BASELINE__GP_Ip_8.8mm_closed_R5_single_refY_005__REPRESENTATIVES.png)中一个源46.7%的共同Ring像素误差超过5mm。所有超色标比例、max、P95已单列；裁切近景不能取代完整范围。

**机制推断 I2：** Ring是轴对称物体，约束尺度/环法向/中心并不能独立确定yaw；局部环带深度好也不能保证远离环带的Polyp曲面好。相机相对旋转/平移误差会影响多视图三角化；连续位姿的系统漂移可让各自的局部Ring误差较小而全视频分层。以上解释符合几何可观测性，但本轮没有独立位姿真值，不能认定唯一成因。

**待验证 H1–H3：** H1是初始化/轨迹几何不稳定而被同帧建库回估掩盖；H2是相机尚可但特定Target/Support基线、遮挡、反光或纹理导致HERO深度不一致；H3是内参假设及输出离散化放大误差。H004原生352×640 Mesh与V6深度线性回360×640、三顶点轴向Z极差≤.75mm的拓扑合同不同。两者HERO入口均采用work K主点+.5、内参缩放后-.5、毫米平移转米、352×640/refine1/fast_cost_volume=False，因此不能笼统归因为“.5像素一定错”；仍需同输入合同试验。跨V6尝试yaw规范未经认证的总览仅用于展示原坐标，不能用其重影诊断单次运行误差。

## 三个候选

| 候选 | 统一入口的计算顺序 | 可能收益与主要风险 | 代价与判断 |
|---|---|---|---|
| A：改造004的顺序建图 | LK视觉初始化→Ring公制锚定→同一Ring/RGB BA→019地图→新query Ring/PnP→统一准入 | 长轨迹与可复用地图可补覆盖；但单seed错误进入地图后会自洽传播，同帧回估必须退出最终验收 | 复用最多、改动较小。保留为低成本对照，不作为默认推荐 |
| B：统一观测、多候选初始化、单一联合图优化 | 观测身份/划分先冻结→LK与SIFT轨迹去重→有限初始化假设→同一Ring/RGB BA→按开发观测统一选一个→冻结地图→独立query/评价→HERO | 不依赖某路线的原门槛或成品；能在推理前识别弱连接/法向/yaw歧义，并用共同质量标准检验覆盖。风险是候选选择过拟合、跨提取器泄漏、单刚体模型失配 | 中等工程与CPU代价；最多3初始化/视频，只有统一相机/支持通过才运行HERO。推荐 |
| C：直接全视频联合稠密优化 | Ring公制初始化→相机/场景深度及光度联合优化→独立评价→HERO或重新审定深度出口 | 稠密证据有机会约束局部错位，但反光、遮挡、非刚性及曝光使光度目标不可靠；焦距—深度耦合可能被优化“解释” | 实现/调试/计算成本最高，本轮无证据证明优于B；暂不进入最小试验 |

B不是“A输出或V6输出择优”，而是同一观测图上的少量**初始状态假设**进入同一优化器。禁止读取既有预测深度、历史成品地图、组名或GT形状来选择候选。失败时记录明确原因，不以另一条隐藏流程补齐。

## B的接口及Ring约束

所有组使用一个未来入口 `ring_first_3d reconstruct --registry ... --protocol ...`（拟设计，尚不存在新实现）。输入物理参数只含真实Ring内径与管半径、已知标定及RAW身份；R10主半径5.6mm、R5为3.1mm，管半径均.6mm。组名只用于日志，不参与求解分支。

1. **观测合同。** RAW SHA、顺序解码PTS/无损BGR SHA绑定帧；记录native/work/native-HERO图像、Mask、K的像素中心变换。统一右手C2W、毫米、camera axial-Z，显式Ring CAD版本。所有阶段传递同一个FrameRecord/TrackGraph，不再以任务目录里的`reference=8`、`459/516`等隐式编号推断RAW身份。内参已标定则固定；仅有F980假设则全组同一假设与不确定性声明，不能称已标定。焦距敏感性另设开发实验，不能用GT或最终TEST反选。
2. **初始化。** 每视频最多三种预先列定的初值：一份连续视觉E/PnP初值经Ring锚定，两份Ring法向候选配合RGB极几何yaw初值。只用FIT轨迹，统一ref RAW帧规范；Ring尺寸在建立公制状态前生效，Ring候选非正尺度/非物理解直接拒绝。三种初值都进入同一个残差、变量和预算的BA，不能原样运行两套完整流程再比较HERO。
3. **轨迹与地图。** 合并LK连续观测与SIFT长基线匹配，在像素/时间关联层保守去重；同一物理track只分配一个FIT/DEV/TEST身份，身份模糊者整连通组归TEST或排除拟合。去重不能依据已拟合几何的好坏挑TEST。地图仅用BUILD帧FIT观测建立；Ring始终以真实CAD投影残差进入BA，RGB约束yaw/6DoF，点正深度和可观测性同时记录。归一化各残差项按观测噪声与有效样本数定义，避免多加SIFT点就压倒Ring。初始提案固定K，不在第一轮同时释放焦距。
4. **位姿/BA和选择。** 复用V6稀疏相机+XYZ优化结构，Ring轮廓项、RGB重投影、正深度保留；平滑项是弱先验，不能替代观测。固定一个reference yaw gauge，Ring中心/平面/毫米尺度作为公共坐标约束；记录正规方程奇异值、连接分量和初值间位姿分散。只按独立DEV的预定质量门槛、可观测性、误差词典序选一次，固定平局次序；TEST、HERO深度、GT完全不参与。若无候选达到DEV门槛，保留数值诊断而不宣称有效覆盖。
5. **新query和相机准入。** 建图结束冻结地图和描述子SHA；新query图像此前不参与track、三角化、BA、候选选择。只用query FIT匹配做PnP/Ring约束恢复，query TEST仅评价。评价需要的TEST三维点单独由BUILD TEST观测与已冻结相机三角化，存为只供评测读取的eval地图，绝不进入求解地图或PnP；query TEST不参与测试点三角化、几何筛选或任何拟合；BUILD TEST不足基线/正深度失败逐项保留，计为不可评价而不从40-query分母删除。DEV也使用评价侧独立地标；候选选择只读BUILD DEV，绝不读query DEV/TEST。query阶段不再选择初始化候选。因此它验证新query观测泛化，仍不是绝对相机真值。保留004的map-PnP与Ring恢复能力，取消“回估建库帧可证明泛化”的解释。目标与三个Support必须同一资格标准；所有无可观测/失败帧仍在固定分母。
6. **HERO出口。** 按预先固定的观测重合、基线/视角和相机不确定性选择唯一3-Support元组；不看深度选元组、不做失败后换组。官方模型与native深度保持，统一用CORE原生Mesh合同；旧V6仅作为历史对照按旧合同保存，不能在新主线长期维护两种默认定义。Ring深度指标与非参与视图的独立诊断同时输出，任何融合必须另立任务。

## 模块来源表

路径前缀：`E=/home/liu/polyp_research/ring_anchor_3d/experiments`；`H=/home/liu/polyp_research/ring-first-3d/experiments`；`C=/home/liu/ring-first-hero-core/src/ring_first_hero`；`P12=本仓库experiments/TASK-M2F12-CLEANUP-AND-HISTORICAL-004-CAMERA-RESTORATION-001`；`W=/home/liu/ring_first_3d_workspace`。下列SHA为源码完整SHA256前12位，完整路径、完整哈希和函数名见[DESIGN_MODULE_IDENTITIES.json](evidence/DESIGN_MODULE_IDENTITIES.json)。旧P未有可代表脏文件的可靠单commit，不能用报告commit冒充源码版本。

| 阶段 | 确切模块/函数、版本 | 输入 → 输出 | 保留 / 拟改、证据与代价 |
|---|---|---|---|
| RAW/观测 | P12/code/frame_identity.py `bind_frames` `9115a0a3d069`；historical004.py `prep` `15e4351be029` | RAW+PTS/nativeRGB+INIT → 实际帧/观测/K合同 | 保留无损身份与物理Ring观测；把任务IO适配收敛到公共FrameRecord。M12已检出seek/JPEG歧义；解码成本小 |
| 初始化：视觉 | E/ring_first_v5_real_validation/scripts/visual_initialize.py `pair_initial/triangulate/main` `4d42560da502`；run_real.py `normalize_visual_gauge/align_ring` `e97e9b02e103` | FIT tracks、Ring观测/K → 公制初始C/XYZ | 保留视觉初始化与Ring尺度锚定，取消原固定历史repeat成品语义；seed0/10提示必须独立检查，不能直接作为可靠地图 |
| 初始化：Ring/RGB | 同V5/ring_candidates.py `configure/main` `6e21f79e1c91`；E/ring_first_v6_local_reconstruction/scripts/local_ring_sfm.py `pair_data/canonical_reference/initialize` `673b57af12fc` | 同一FIT图、Ring法向候选 → 另外两份初值 | 保留物理候选/RGB消歧，候选清单推理前固定；断连不能偷偷以自由SfM补齐。最多三次统一优化 |
| 轨迹 | E/ring_first_v3_static_ba/scripts/track_scene.py `main` `5d31e1bbe302`；V6/scripts/track005.py `main` `c912da0713a3` | BUILD图像、Mask → 统一2D tracks及全链路split | 保留双向LK与SIFT互检/camera-disjoint并查集；新写身份去重和联合观测接口，禁止复制两份流水线。主要新增工程成本 |
| 地标 | H/TASK-E4-RING-POLYP-REGISTRATION-019/code/features019.py `landmarks` `50cd25fd8df8`；V6/local_ring_sfm.py `triangulate_training` | FIT轨迹+相机 → XYZ/描述子/来源 | 保留最长基线、正深度/视差/拒绝记录；统一过滤规则并只在BUILD FIT建图。019的known-pose匹配不是独立证据 |
| 位姿/BA | V6/local_ring_sfm.py `BA` `673b57af12fc`；C/camera.py `recover/residual` `0168b331808d`；C/rgb.py `pnp` `29bd1d25e2b0` | 初值+同一图/Ring → 联合C/XYZ，冻结地图后query C | 保留稀疏BA、Ring物理项与map-PnP；不引入旧MAX跨视频Bundle。统一残差/预算/坐标规范；增加不确定性与观测秩审查 |
| 相机准入 | V6/validate_select.py `main` `bdfb607de4c3`；H/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/code/register.py `qualification` `a5f04bbb5ec9` | 冻结C+独立观测 → numeric/quality/原因 | 保留whole-track排除、Ring/正深度/初始化分散与秩证据；淘汰把FEATURE_HELD称全链路独立、不同门槛直接计胜。统一门槛见下 |
| Target/Support | V6/select_supported_views.py 顶层脚本 `f8439f53565b`；同MAX/coverage.py `support_pairs/main` `156b183d0faa` | 同标准合格相机/观测 → 唯一元组 | 复用观测共视/视角计算；取消未合格Target作为“有效”来源。困难帧保留失败分母，不能仅删难例 |
| HERO/Mesh | C/hero.py `load_official/infer` `9a83c565a563`；geometry.py `native_rgb_labels/depth_mesh` `b6622afb2450` | 1+3固定输入 → 352×640轴向毫米深度/原生开放Mesh | 官方模型SHA `00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d`，不训练、不尺度调参。该出口已完成76组合；新主线只保留一种合同 |
| 共同评价 | W/src/ring_first_3d/mainline/lineage/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py `render/evaluate` `0171f5a56d08`；P12 seed whole-track evaluator；本轮evaluate_sources.py | 冻结输出+观测角色 → 覆盖/质量/尾部/失败 | 保留实际三角形渲染、全源表及NaN；新增独立TEST身份验证和统一分母。A→B只在B未参与时才可列为非输入视图诊断；无部署poseGT不报绝对形状精度 |

实现时先将上述实际函数提取为一份带版本的公共模块，旧任务入口成为只读重放适配器；公共函数只接受显式输入，不读历史任务全局目录。以原冻结fixture验证未改内核的一致性，再对明确批准的算法变更单独版本化。运行身份包含代码commit、模块SHA、协议SHA、RAW/模型SHA；不再叠M2F14包装脚本而让旧全局变量继续隐式决定主线。

## 固定分母与最小验证计划（下一轮拟议，本轮未执行）

先完成“相机和证据是否可信”的廉价阶段，再决定是否花HERO预算。建议仍使用本轮固定5组10视频和按RAW顺序固定的每视频16帧，全部方法用同一帧，不能沿用V6/H004各自不同抽帧。16帧按序号预分：query为3、7、11、15，其余12帧BUILD（0起）；在任何建图前冻结名单。所有query图像/特征从BUILD建库、候选选择和BA隔离。真正同RAW同Support试验如需新增推理，须另建任务预算，不属于本轮69次。

| 试验与预算 | 冻结和评价 | 支持 / 推翻推荐的判据 |
|---|---|---|
| P0：身份/接口/独立性，零HERO | 5组10视频共160固定RAW帧；FIT/DEV/TEST整track划分及跨LK/SIFT重叠表先冻结。query4帧/视频，未读入建库进程；比对像素中心往返、C2W单位、CAD尺度与源码SHA | TEST或query泄漏则该结果无效，不进入质量比较；既有旧H/V结果仅作背景，不混称新同输入实验 |
| P1：相机-only，最多3初值/视频=30候选 | B三初值同一BA；DEV选择一次，TEST最后开封；同时保留A型单视觉初值和V6型首Ring初值作为预定义消融，复用候选计算。每候选固定相同迭代/点数上限，记录耗时和失败 | 若B只提高FIT而40个新query TEST不改善，或增益仅来自放宽门槛/剔除不可测query，则不支持B；本计划三候选共享同一LK+SIFT图，只检验初始化选择收益；不能归因新增观测，轨迹贡献需另立预算的观测消融 |
| P2：冻结地图新query | 每视频4个query各自只用FIT匹配PnP/Ring恢复；TEST整track不进入求解地图/姿态拟合，仅BUILD DEV用于建图候选选择。统计每query正深度、测试重投影、Ring边界、可观测性、初值分散 | 至少一个旧失败视频在原固定分母下产生合格新query，且既有通过视频不掉出共同质量标准，才算覆盖收益证据；如果同帧回估好而新query差，支持H1并否定当前扩展方式 |
| P3：同RAW Target/3Support、最多30次HERO | 每视频预选一个query Target和三个BUILD Support，共10个固定元组，按时间/观测覆盖规则在深度前确定；三条预定相机消融各最多一次，无合法组合计失败不换元组。选择另一未参与的query B作独立观测，B相机同样受独立检验 | 报10视频共同可运行交集并同时报10视频全分母缺失。相机改善但相同元组深度Ring尾部和非输入B一致性未改善，则不支持“HERO收益”假设；不能用未配对均值赢过缺失方法 |
| P4：覆盖—一致性关系，复用P1/P3输出 | 冻结主门槛外，预注册RGB阈值{2,3,4}px、P95{4,6,8}px作为描述曲线，不能据最终TEST再选发布门槛；逐视频/物理组显示数值、合法、有效覆盖与误差分布 | 曲线仅靠降低质量换覆盖则不接受“同时提高”；有效覆盖增加且共同可测样本质量不下降才支持继续，不声称全局最优 |

建议主门槛在实现前由研究者确认并冻结：独立TEST不少于8个观测、覆盖至少4个空间格、正深度比例≥.95、RGB MAE≤3px且P95≤6px、Ring边界MAE≤3px且P95≤6px。沿V6初值中心分散≤2mm作为稳定性门槛，同时报告旋转分散而不伪装已校准误差。若只有一个数值候选，分散不可估计，标NOT_EVALUABLE并保留在分母；可观测秩不足不能靠平滑伪造。TEST只做最终接受/拒绝，不为已经选定的候选重排；部署准入应使用可获取的DEV/观测不确定性，实验TEST用于检验其可靠性。

深度阶段暂拟共同合格要求：Ring共同像素覆盖≥.5且MAE≤2mm/P95≤5mm；与非输入B的前景覆盖≥.7、RGB MAE≤20/255，同时报告亮度敏感性和遮挡。它们是需研究者批准的工程判据，**不是本轮已证明的精度真值或通用物理标准**。非输入B投影仍依赖估计相机，须与独立几何观测结合；无独立poseGT时绝对表面误差仍NOT_EVALUABLE。若阈值对真实反光显著失真，只能在DEV上修订并重新冻结新的实验，不能看TEST调门槛。

分母分四层逐视频公布：①数值相机/预定160帧；②同标准相机合格/160；③唯一合法固定元组/预定10个元组（以及有合法元组视频/10）；④共同质量标准合格的深度/预定10元组和视频/10。40个新query另有固定40分母，不能混入160得到较漂亮比例。正式独立统计以5物理组为单位报告组内004/005，不把174相关曲面当174个独立样本。

继续条件建议为：新增至少1/10有效视频，原先有效视频不回退；共同配对元组的独立RGB误差及Ring P95无超过10%的恶化，同时逐例揭示最大尾部；若仅有不足3个物理组的共同元组，结论限定为可行性，不能宣称普遍优越。这个10%是预注册容差提案，需要与测量噪声在DEV上检查后冻结。下一步最值得先批准的是P0–P2；只有其通过，才批准P3的≤30次HERO。设计讨论前不启动任何阶段。
