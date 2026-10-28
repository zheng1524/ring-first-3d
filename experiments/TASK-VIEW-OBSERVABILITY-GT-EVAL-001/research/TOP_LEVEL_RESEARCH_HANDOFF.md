# 顶层研究设计者文献调研交接

本文件是实验事实与问题清单，不是文献综述，不替代RA独立审查，也不采用未经审查的新路线。Codex本轮未以关键词搜索决定重大科研路线。

实际主线：Ring-First冻结相机候选→HERO冻结轴向深度→有源像素XYZ/开放Mesh→既有Type-2候选（因结构损伤未采用，Applied仍Raw）→主面优先条件补片/证据分层→背景代理基底H95和独立3D Feret原型。正式Dxy独立冻结。旧源码与大资产只读、本地；无正式认证baseline。

上轮G01的004/005分别只有0.73701/0.83996mm²模型条件补片，冲突约207.5514/110.0452mm²、重复约46.1037/78.5382mm²（多参考面暴露，非解剖面积）。其余三组单参考，不能声称跨组融合通用性。

| 物理组 | GT H95 mm | 有效预测H95范围 mm | 有效条件 / 全条件 | 相机条件 |
| --- | --- | --- | --- | --- |
| G01 | 15.8791 | [12.476040867638016, 12.630082542578124] | 4/18 | NORMAL_CONDITIONAL |
| G06 | 1.5917 | [1.4703098303730098, 1.5801444247722118] | 3/3 | NORMAL_CONDITIONAL |
| G07 | 4.6575 | NaN / NOT_EVALUABLE | 0/3 | UNQUALIFIED_STRESS |
| G08 | 4.3773 | [4.0376495253133715, 4.23875789774408] | 3/3 | LIMITED_STRESS |

| 组 | GT Feret mm | 全部数学候选范围 mm | 数学候选数 | 全条件数 | 正式成功 | 主要限制 |
| --- | --- | --- | --- | --- | --- | --- |
| G01 | 12.0000 | [10.211078014025192, 11.57021784919287] | 54 | 54 | 0 | 基底/表面支持/端点条件失败 |
| G06 | 14.0000 | [12.62254466532105, 12.623883982220798] | 9 | 9 | 0 | 两端点独立支持均失败 |
| G07 | 14.0000 | NaN / NOT_EVALUABLE | 0 | 9 | 0 | 相机不合格，候选也NaN |
| G08 | 22.0000 | [21.350058761860222, 21.357873727356992] | 9 | 9 | 0 | 一端点独立支持失败 |

真实GT底盖可定义作者形状标量；真实部署姿态/组织切面未知，不能独立表面精度评价。27高度条件10有效，81正式Dxy全部失败。三照片有真实RGB/Mask与历史匹配，但光学模式K未知且正式位姿失败。五个G01来源必须分别看待，视频004/005共一物理组，不是两个病例。

| 来源 | 原始资产 | 现成P0数 | 相机/关联状态 | 限制 |
| --- | --- | --- | --- | --- |
| G01_photo001 | GP_Ip_12.0mm_closed_R10_single_refY_001.jpg | 0 | UNREGISTERED | NO_VERIFIED_K_OR_POSE_OR_DEPTH; matches exist but fail independent geometry |
| G01_photo002 | GP_Ip_12.0mm_closed_R10_single_refY_002.jpg | 0 | UNREGISTERED | NO_VERIFIED_K_OR_POSE_OR_DEPTH; matches exist but fail independent geometry |
| G01_photo003 | GP_Ip_12.0mm_closed_R10_single_refY_003.jpg | 0 | UNREGISTERED | NO_VERIFIED_K_OR_POSE_OR_DEPTH; matches exist but fail independent geometry |
| G01_video004 | GP_Ip_12.0mm_closed_R10_single_refY_004.mp4 | 3 | LOCAL_ONLY |  |
| G01_video005 | GP_Ip_12.0mm_closed_R10_single_refY_005.mp4 | 3 | LOCAL_ONLY |  |
| G06_photo001 | GP_IIa_14.0mm_closed_R10_single_refY_001.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G06_photo002 | GP_IIa_14.0mm_closed_R10_single_refY_002.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G06_photo003 | GP_IIa_14.0mm_closed_R10_single_refY_003.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G06_video004 | GP_IIa_14.0mm_closed_R10_single_refY_004.mp4 | 1 | LOCAL_ONLY |  |
| G06_video005 | GP_IIa_14.0mm_closed_R10_single_refY_005.mp4 | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G07_photo001 | GP_Is_14.0mm_closed_R5_single_refY_001.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G07_photo002 | GP_Is_14.0mm_closed_R5_single_refY_002.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G07_photo003 | GP_Is_14.0mm_closed_R5_single_refY_003.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G07_video004 | GP_Is_14.0mm_closed_R5_single_refY_004.mp4 | 1 | LOCAL_ONLY |  |
| G07_video005 | GP_Is_14.0mm_closed_R5_single_refY_005.mp4 | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G08_photo001 | GP_IIa_22.0mm_closed_R10_single_refY_001.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G08_photo002 | GP_IIa_22.0mm_closed_R10_single_refY_002.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G08_photo003 | GP_IIa_22.0mm_closed_R10_single_refY_003.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G08_photo004 | GP_IIa_22.0mm_closed_R10_single_refY_004.jpg | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |
| G08_video005 | GP_IIa_22.0mm_closed_R10_single_refY_005.mp4 | 1 | LOCAL_ONLY |  |
| G08_video006 | GP_IIa_22.0mm_closed_R10_single_refY_006.mp4 | 0 | UNREGISTERED | RAW_SOURCE_ONLY; no traced frozen camera/depth/P0; not reconstructed this task |

| 来源 | 冻结帧/元数据合格 | 光轴对本地Ring法向倾角 min/median/max° | 同视频最大光轴夹角° | 同视频最大基线mm | 条件 |
| --- | --- | --- | --- | --- | --- |
| G01_video004 | 16/16 | [43.99839685254667, 47.14935995003443, 48.32653294347] | 27.5646 | 26.8071 | NORMAL_CONDITIONAL |
| G01_video005 | 22/15 | [24.17704315683897, 26.489352566787176, 28.2380535222396] | 14.8121 | 27.2407 | NORMAL_CONDITIONAL |
| G06_video004 | 8/4 | [51.07415945699602, 52.45707125402782, 56.79819213209264] | 33.4398 | 14.3886 | NORMAL_CONDITIONAL |
| G07_video004 | 8/0 | [38.63669812717897, 39.55523526389749, 41.95879045315902] | 3.3262 | 17.6403 | UNQUALIFIED_STRESS |
| G08_video005 | 8/2 | [48.90593736558385, 57.440427079129556, 64.4783858377767] | 23.5187 | 24.0969 | LIMITED_STRESS |

请独立从原论文、arXiv、正式开放全文和官方代码核查下列问题。每项方法均填写：数据前提、相机/坐标假设、公制尺度来源、静态/刚体条件、遮挡和高光处理、成功/失败条件、真实内镜证据、GT身份、代码版本/许可证、与本冻结资产的最小兼容改动；不得仅列方法名或漂亮Demo。

1. 内镜多视图几何：在反光/弱纹理/部分遮挡、近似平面组织条件下，怎样独立诊断相机误差与深度错层？全局联合优化需要哪些真实约束？
2. 跨视频注册：圆环中心/法向/尺度之外，如何识别剩余旋转自由度？静态近端背景需要何种非对称/非共面结构，怎样判定退化而不是用ICP低残差宣布成功？
3. 已知标志物辅助位姿：环的对称性、双分支、内参不确定性和遮挡如何进入不确定性评价？独立物理校准的最小数据是什么？
4. 静态照片接入：手机/内镜光学模式及分辨率变化时，现有K490假设何时失效？哪些有界验证能够使用现存资产，不需要再跑完整HERO？
5. 多视角深度/可见表面融合：哪些成熟机制能保留主面、处理系统深度差、保留细蒂且不平均冲突层？何时需要修深度，何时只需改显式表面连接？
6. 遮挡/镜面高光/弱纹理：RGB残差有多大程度可解释为几何，哪些鲁棒或光照不变量有独立证据，而非事后挑选可见区域？
7. 新增表面评价：如何分离重叠点、条件重复面、真实新面、未注册冲突和未知区？需要何种可见GT、留出观测和面积分母？
8. 物理指标：可见点P95与完整GT顶点/面积P95如何匹配定义？作者底盖与真实组织切面需要什么独立证明？Feret极值端点支持应与数学直径、临床直径怎样分开？

待审候选仅两项：①已有相机/静态照片内参模式和跨源几何的独立认证；②在可信相机前提下，研究能解释参考间深度差的成熟多视图联合约束。均交PM/RA评审，不是本轮自动执行计划。停止无界清理阈值搜索、对称环+平面背景的盲目多初始化ICP、GT/Oracle修正正式预测、把点数/平滑/低同帧RGB误差当精度。
