# TASK-MAINLINE-ASSET-CONSOLIDATION-001

**工程验收：PASS。原247项回归0失败/0跳过，Preflight、Contracts、Reuse Audit、Smoke通过，8/8关键模块从新路径重放并与冻结结果比较通过。科研状态仍为ACTIVE_RESEARCH_MAINLINE，绝非CERTIFIED_SCIENTIFIC_BASELINE。**

统一入口：/home/liu/ring_first_3d_mainline/mainline/README.md。实际代码在src/ring_first_3d（mainline/lineage版本隔离、native相机/HERO、frozen_registry原SHA数学来源）。完整配置、真实输入、编译库及checkpoint身份均有清单；执行audit拒绝从原实验工作区运行Python代码。

## 16项验收问题

1. 整理前：df显示197G文件系统已用187G、可用0；扫描276183资产、逻辑53,135,662,730字节（含重复，不等同物理占用）。环境/.git与其科研资产分别记录，原始命令见INITIAL_COMMANDS。
2. 阶段1实测释放15,808,393,216字节，即14.722713GiB。最终净变化另见FINAL_STORAGE，包含新工作区及完整清单开销。
3. 清理了可再生成缓存及22611个独立重复payload；硬链接去重保留每条历史路径、完整内容和引用。操作级分配块与实际文件系统空闲分别统计。没有删除唯一Mesh或官方权重。
4. TSDF/NeuralFusion/MonoSDF等冗余副本已去重；唯一中间checkpoint/负证据及依赖不明资产保留。两份大归档各含124个无独立副本成员，未删。MonoSDF仍是未完成充分训练，不能称充分训练后失败。
5. 保留Ring-First源码、官方HERO加载/推理/回投影、E1/E2九参数/完整Mask参考、013/014/015、Graph/SmoothARAP、Sweep/RMF/Union、T28旧深度与T30原生深度独立实现、A→B、P0、跨视频BA、重要负结论与代表图。原完整历史由commit及原路径追溯，不迁入所有运行目录。
6. 集中到/home/liu/ring_first_3d_mainline，README/PROJECT_HOME/mainline README/PIPELINE/MAINLINE_ASSET_MAP构成五个入口文件。mainline仅组织配置/运行/结果，代码继续在既有包。
7. Ring-First真实固定输入重放PASS，相机矩阵max abs=0；不是独立pose GT。
8. HERO一次新官方原生推理PASS，深度逐bit相同，Raw顶点/面/PixelID相同；未用历史深度冒充推理。checkpoint未复制，官方源码实际核验commit为5bd49bba0992aa56060e1aa3bb40b2150b04726f；旧4483…是父项目身份误记，保留原纠正记录。
9. 初始化真实原013容器SHA相同、五类Mesh数组一致；Graph保存状态通过原函数实际生成Body，最大误差1.7763568394e-15mm，SARAP能量实际计算。没有重新优化36轮或按病例改算法。
10. G01保存样条由新路径重建，真实Blender Union顶点误差0、面索引相同、全FIT投影变化误差0。总弧长2.530961、嵌入0.804116、外露1.726844mm；Ring双向不恶化，自交0。但近端截面0.047185mm局部露出及固定INITIAL→GT框架MAE恶化保持。
11. G03同样真实生成Union并重投影；PER_VIEW_PROTECTION拒绝被复现，005两视角下降0.023444/0.012446，正式柄长NaN，失败尝试/根审计保留。
12. A→B实际源面与原A RGB重投影PASS，RGBA/z/FaceID/重心/CAD深度/有效域逐bit相同；B颜色和Mask仅后评价，原位姿是条件性状态。
13. 原018 T30 PyTorch3D/native-depth前向、损失、梯度PASS；加权loss误差0，历史梯度相对误差7.89843173677e-08（原阈值1e-4）。T28旧观察模型另存，未混成一个模块。
14. 对比明细如下；全部预冻结容差未放宽。路径适配通过逆变换AST比较，科学公式不变。
15. 外部依赖仍包括受保护原始观测/Mask/GT/相机缓存、官方MVS/DINO源码与checkpoint、既有venv、Open3D等官方库；本项目.runtime中的编译包已复制并核验，不依赖删掉的旧实验源码。逐资产大小、SHA和用途见EXTERNAL_INPUTS/RUNTIME_FILES；受控数据原位保留。
16. 跨机器尚需受控数据授权提供/路径重绑定、原HERO权重、Python/CUDA/PyTorch3D ABI及官方第三方源码；不能宣称空机器开箱即用。新科研优化还需新TASK/Policy授权，本轮仅checkpoint continuation和固定模块重放，未新接入HERO反向更新Body。

|模块|状态|与冻结结果比较|
|---|---|---|
|ring-first|PASS|相机矩阵max abs=0；分支身份相同|
|hero|PASS|新官方原生推理；深度逐bit一致，Raw FaceID/PixelID/顶点一致|
|body-initialization|PASS|G01/G03原始013容器SHA相同，V/F/F_solid/cap/boundary逐元素一致|
|body-update|PASS|保存的32节点变换经原Graph真实生成Mesh；最大误差1.7763568394002505e-15mm|
|stalk-growth-g01|PASS|新Boolean并集顶点误差0、面索引相同、投影变化误差0；自动门禁仍通过|
|stalk-growth-g03|PASS|新Boolean并集及投影同历史；PER_VIEW_PROTECTION仍拒绝，正式柄长NaN|
|a-to-b|PASS|RGBA、轴向深度、FaceID、重心、CAD深度和有效域逐bit一致|
|depth-supervised-pytorch|PASS|实际T30加权loss差0；梯度相对误差7.89843173677e-08|

## 工程故障、复现版本与清理边界

新协议修订1保留了共享ARM.json错绑G03的失败；修订2保留了把后期重序列化cache当原013容器的SHA失败；修订3全部8项通过。两次均只修复输入身份/接口，没有改变数学参数或数值容差。源码/配置快照与失败JSON在REPLAY_PROTOCOL_REVISIONS，不覆盖原历史。

COPY_VERIFICATION逐文件记录原路径/任务/commit/原SHA/新路径/新SHA/是否适配/依赖。EXACT_COPY字节完全一致；ADAPTED_COPY只改路径，逆适配AST与原算法一致。完整原始Git历史、远端分支、其他项目及DXY保留。原工作区含唯一输入/证据和LOCAL_ONLY绑定，未冒险移除。新维护树仅保留规范算法、冻结协议与精选证据，新增冗余中间副本经PHASE7 manifest清除；原报告与原源目录未清理。

静态引用图没有声称覆盖任意动态调用；实际8项执行轨迹和旧源码执行拒绝补充了运行核验。所有原数据/权重仍可用，失败台账不自动晋升永久规则。硬链接历史资产禁止原地写入，新任务必须独立输出。

## 科研审计表

|审计项目|必须汇报|
|---|---|
|目标组数|物理组G01/G03共2；固定重放模块8；新科学训练0|
|本算法独立成功|本轮为维护，不产生新的科学预测；工程8/8重放通过。原G01只有自动门禁通过|
|本算法失败|保留原G03正式NaN及G01根部/固定框架缺陷；维护接线故障已留证修复|
|历史测量值回退|0；显式历史参数是重放输入与对照，不伪称新的独立测量|
|失败组及具体原因|mainline/results/FAILURE_REGISTRY.json及本任务FAILURE_REGISTRY.json|
|最终统计样本|8固定模块、2物理组；未新增科学精度统计或将8模块当8病例|
|是否使用GT选择算法|否；没有新优化/训练/GT调参，原科学GT评价原样保留|

入口与关键可视化：mainline/visualization/index.html；原完整G01/G03画廊在mainline/visualization/stalk_growth/index.html。全部使用实际图像和三角Mesh。工程通过不修改原科学结论。

## 最终验收补充

最终修订4额外锁定全部继承API和小型冻结输入，共824项；数学参数与容差未变。实际串行checkpoint流水线8/8通过，见PIPELINE_RESULT.json；最终247项回归0跳过。全部873项复制资产SHA核验通过，复制Python源码的声明commit均含原字节，所有路径适配经逆变换AST验证。可视化56张图像解码成功、两个首页66个本地链接存在。

主线目录：/home/liu/ring_first_3d_mainline

可视化：/home/liu/ring_first_3d_mainline/mainline/visualization/index.html

原始完整盘点按逐实验汇总见EXPERIMENT_STORAGE_SUMMARY.csv。目录别名仅整理维护分支当前树，原4110个Git文件仍在固定基线和原工作树；没有重写历史或移除远端分支。原工作树保留是因为仍有唯一资产及LOCAL_ONLY绑定，不冒险删除。跨机器、全新训练收敛或新的HERO→Body耦合均未认证。
