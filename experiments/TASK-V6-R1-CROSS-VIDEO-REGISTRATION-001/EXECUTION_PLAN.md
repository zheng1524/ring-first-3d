# R1 跨视频配准执行计划

用户明确授权自主选择方法、薄适配和小规模诊断；本计划直接执行，不另等上游。基础提交 f78e854bdbb6487cc946f4543250b8432dbfc779；真实前半段执行29874fe61f59c429fb83d2377ab707c847992ef8。旧v6_full_run_001仅用来发现迁移，正式输入为启动回执指向的v6_r1_full_b_001。输出仅本任务目录。科学实验CPU单进程单线程、nice19/ionice idle、GPU禁用；磁盘预留5GiB，本任务256MiB，资源不足让出，不改全量。

## 组合表（先于实现）
|阶段|现有入口|输入→输出|处理|
|---|---|---|---|
|R1身份审计|R1 RUN_IDENTITY/CAMERA_COMPLETE/PLAN_FROZEN/HERO_COMPLETE与INPUT_IDENTITY|完整父子链、RGB真实帧/相机/Target+Support/native/Raw→冻结ASSETS|薄读取；不调用full_run/route运行入口|
|匹配/独立DLT|002 real2.make_tracks/triangulate；原V6 track005.main/triangle|8帧/视频，自动RGB轨迹→FIT/HOLDOUT、各侧3D|复用；帧池全对，与R1相同SIFT函数；R1新增媒体/temporal适配对本轮纯视频全对无影响|
|M0/M1/M4|002 solver2.solve_methods及Ring先验real2.ring_prior|同一帧池、FIT轨迹、两侧Ring不确定度→T|原算法复用，只接R1已核验输入|
|M5|旧投影/SE3、SciPy least_squares、002 Ring残差/二次先验|多帧2D–2D Sampson残差→一个6自由度T|用户授权小型新目标；无相机变量、无形变；不重写上游|
|配准后Clean|原mapped_input_for_source / classify_native / trusted_subset|冻结T后同步相机/原V，固定共同CAD→state0原面子集|薄global坐标适配；临时PLY仅为原分类器入口；不读Clean选FIT|
|评价/图|002 bidirectional/ring_pixels/真实三角scene、mesh_sections|冻结预测→全分母双向留出、固定CAD、曲面一致性与中文图|复用评价内核，独立报告；无真实GT|

现有registry已存在；docs/architecture.md不存在，以上基于原源码与真实运行收据，不据缺文档认定缺实现。历史002方法为候选、科学表现mixed，用户明确批准作基线；不升格已普遍验证。

## 冻结实验协议

首批6组：Ip8.8/R5、Ip4/R10、IIa14/R5（历史对照）；IIa14/R10（HERO不平衡）、Ip20/R10（大）、Ip2.9/R10（小）。均以当前DONE、native/renderable>0为条件，完整case排序取A/B前两段。三视频组不按效果选两段。若身份失败保留失败，不以结果替换。首次审计19组双视频合格；完成前可只读检查新增Is完整组，独立记补充批次，不回写初批选择。

每侧按真实ledger顺序等间隔8帧，全对SIFT6000/ratio .72，原连通整轨迹mod5留出。保留原BA held依赖标记。M4原FIT：≥2视图/侧、视差≥.5°、正深度、最大同侧重投影≤6px、≥6条。M5同一FIT原轨迹池，要求≥2观测/侧，不因独立DLT误差筛选2D点；显式报告有效约束集差异。不强制息肉纹理，不另建类别筛选体系。

M5每条FIT轨迹的全部跨侧帧对使用像素Sampson残差，sigma=1.5px，逐残差soft_l1；每轨迹总权重相同，归一化在鲁棒损失外。与M4共用5维Ring covariance与lambda1/5sigma宽界限，Ring独立二次损失。72格yaw仅用FIT计算目标，与M4初始化共同竞争，固定最多100函数评价。没有GT、held或Clean参与搜索/排序/调参。极线有符号/近零基线退化，须诊断正深度与FIT支持，不把低Sampson当成功。

固定评价：相同完整HOLDOUT，不按Clean/误差删点。双向独立源DLT→目标图像，报告所有失效/越界/负深度、全分母与有限条件MAE/P95；新增held极线仅辅助。至少8双侧独立轨迹、两侧≥2帧为最低支持；3/6px沿用诊断，不事后放宽。六次首/中/末FIT留一敏感性。原相机内部几何不变，轴Z/投影不变性测试；不得把不变性当跨视频改善。固定每源96个原面采样，只评跨视频三角面距离/覆盖诊断，无GT不可称准确率。全部来源、失败与缺面保留。

主输出M5为研究候选，配准冻结后再分类全部来源，T不随Clean改变。输出T+相机+原面ID/状态+原Raw引用；变换后V由同一T重建，Clean不另动V。每组真实六视图（M0/M4/M5 Raw与M5 Clean）、固定CAD、真实RGB/held、双固定切面，中文HTML。评价状态区分验证/初步/待研究/不可完成，不自动启动主体。

## 执行步骤
- [ ] 只读审计和冻结来源；记录运行根差异、R1实际模块/版本、相机与native一致性。
- [ ] 契约红测→M5最小实现→无GT控制坐标/纯旋转/退化测试；冻结源码和参数。
- [ ] 顺序跑六组自动匹配、M4/M5及FIT留一；冻结T。
- [ ] 先同步几何，再调用原Clean；冻结原面映射与分类证据。
- [ ] 全分母评价、真实图、报告七个研究问题和候选接口；独立静态审查。
- [ ] 输入后哈希复核、显式提交、小型证据上传、核验远端SHA。
