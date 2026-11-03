# 官方复用与最小适配记录

所选实现：[autonomousvision/monosdf](https://github.com/autonomousvision/monosdf)，commit `12513009cd20a08b35ddc2c55a7e42da2c7baf43`。未选择 SDFStudio，未读取其他路线模型权重。原始 Git blob 而非历史脏文件作为复制来源，清单见 [OFFICIAL_SOURCE_MANIFEST](provenance/OFFICIAL_SOURCE_MANIFEST.json)。历史 clone 只读。

## 已实际执行的官方计算链

`rend_util.get_camera_params → MonoSDFNetwork.forward → ErrorBoundSampler.get_z_vals → implicit_network.get_outputs → RenderingNetwork → MonoSDFNetwork.volume_rendering → 官方 Eikonal/normal/RGB/SSI 组件 → backward → Adam`。

四组资源运行每组各 25 次，上述四个主要组件都有实际计数，不是仅构造类。全体 loss 和参数梯度有限，采样未越出有限可见区间。最新原生射线防护后的单次不更新核查亦通过。这只证明短程计算合同，**不证明长程训练完成、几何可靠或官方 Mesh 提取已经执行**。

## 与官方配置和入口的差异

|项目|官方代码/配置|本项目必要适配与限制|
|---|---|---|
|网络|官方同时实现 plain MLP 和 Grid 分支；DTU MLP conf 仍令 Grid_MLP=True 且关闭 grid feature|选真正的官方 plain ImplicitNetwork，8×256、PE6、skip4、feature256，共 670395 参数；不实例化无用 hash encoder。此选择明记为配置差异，不声称逐字复现原 conf|
|Python 导入|模块顶层导入 hashencoder，runner 用已移除的 imp 及 DDP/日志依赖|仅将未使用 hash 导入移入 Grid 构造器；utils.general 只读复用官方 get_class。原网络计算未重写；[import diff](provenance/OFFICIAL_IMPORT_PORT.diff)|
|数据集|DTU 路径、相机缩放矩阵、Omnidata cues|新输入读取已冻结的三个真实来源、RGB、HERO 轴向深度、原生 ID 和已有独立等比 crop；没有 Omnidata 推理或伪预训练深度|
|模型单位|官方归一场景|沿当前 N0 同一物理立方域，MonoSDF 用中心化 [-1,1]³，s=10.053 mm/unit；K/旋转不变，c2w 平移、深度、SDF 严格统一换算|
|射线区间|球/固定 near/far，末尾 extra samples 又使用固定 near/far|相同官方 Algorithm1、自适应迭代、beta 上界搜索及 PDF/CDF；仅将入段和最后 extra samples 的 near/far 换成逐射线 cube 首入/出段及固定 CAD 首交点前 .05mm|
|末段密度|terminal interval=1e10，plain 分支可用吸收球 SDF|末段 interval=0，禁用虚假吸收球，保持 Polyp-only 有限可见段；不学习 Ring 或背景几何。修改见 [finite visibility diff](provenance/OFFICIAL_FINITE_VISIBILITY_PATCH.diff)|
|深度 cue|官方 target*50+.5，scale-and-shift invariant，32×32 分组|移除 Omnidata 特有数值变换，输入真实 HERO Z/s；保留 SSI 数学目标、权重和本来的随机 1024 射线分组，并公开其不能锁定绝对公制壳的局限|
|法向 cue|官方 normal map|由当前真实 HERO XYZ 四邻中心导数估计；四邻有效、轴向跳变≤.75mm、距原生 Mask 边缘>2px；朝实际相机、变换至相机系。无效 cue 不入法向损失，不生成 all-ones 法向|
|Mask/背景|原例可有场景背景|M0 仅在真实合法 Polyp+HERO 射线取 RGB/depth，Mask 用于范围资格；不把 Ring/未知 Mask 当待学习背景。M1 正 Mask 使用稳定有限光学 BCE，身份与范围相同|
|学习率|5e-4 及官方指数调度|保持终值比 .1；两臂共同增加预注册 1000 步线性 warmup，初步幅为 baseLR/1000。这是稳定性改动，不冒称原 conf 原样|
|训练入口|MonoSDFTrainRunner.run（epoch 驱动）、DDP 等|目前只有一次性资源入口；正式长程/恢复入口未完成，因此当前不能宣称完整官方训练与提取已完成|
|表面提取|官方 utils.plots.get_surface_trace、浮点 MC|已阅读、已登记128³检查点/512³最终计划，尚未执行。未来须调用官方提取、保留全部组件和原始面，不以新简化 mesher 替代|

上述表格记录资源预检时点的适配。研究者批准先单参考后，新增 `train_full.py`：实际复用官方 `MonoSDFTrainRunner.run`，原 zero_grad→model→loss→backward→step 更新块逐字保留，仅接入恢复步数和检查点回调。`OFFICIAL_RUNNER_PORT.diff` 展示全部方法改动。官方 `get_surface_trace`/`get_grid_uniform` 已对真实初始化执行，保存原场与27976原面；提取仅增加原场保存、明确Trimesh process=False，无组件删除。`OFFICIAL_EXTRACTION_PORT.diff` 记录该端口。完整200k状态仍必须由运行日志/检查点证明，不能用接线或初始化代替。

## M0 与 M1

M0：官方 RGB L1、Eikonal .1、smooth .005、SSI depth .1、normal L1/cos 各 .05，cue 权重保留官方 `exp(-step/12800*10)`。深度/法向保留官方预测过零 gate，覆盖退化须持续监测，不能因 gated loss 降低声称表面改善。

M1：相同骨干、采样、渲染、种子、预算，额外使用 HERO 原生 XYZ 处 `SmoothL1(f_mm/.25,0)` 权重1、真实首次正→负过零的公制残差权重.1、来源实际射线上 HERO 前 .5mm 的弱正 SDF 权重.1、有限段正 Mask BCE 权重.1。首次交点项本身仍无空场交点梯度；独立于预测 hit 的表面锚点承担恢复候选作用，尚未证明长程有效。

锚点来自原始 Pixel ID 的真实 XYZ，不用 crop 连续射线假装原生点；原生射线单独检查真实 Mask、ROI 与 CAD 次序。crop 最近邻量化误差单列。前方自由空间仅依合格来源的首次 HERO 观测作弱代理，HERO/相机可能出错，不把 ROI 入口假定为外部，不约束 Ring 后或未知区域。

跨源前方矛盾>.25mm 的候选权重.25，其余1；后方可被合法遮挡，不直接判负。该代理未校准，对三个来源不对称，并非物理真假标签。三个来源有共同上游 RGB 家族，按来源循环等权，不宣传为三个统计独立观测。全部已冻结来源保留，不修原生 HERO、不加逐像素校正参数。参数以 [PREREGISTERED](config/PREREGISTERED.json) 为准。
