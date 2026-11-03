# 固定M1与版本继承

官方 MonoSDF commit `12513009cd20a08b35ddc2c55a7e42da2c7baf43`。本轮复用上一任务 `e9e79b2`/`f3b2c1a` 的真实官方8×256 ImplicitNetwork、ErrorBoundSampler、RenderingNetwork、LaplaceDensity、有限可见段渲染与官方runner更新块。不是旧E2.7固定单元renderer。

源码改动逐项见provenance/PORT_MANIFEST.json和*.diff。official_adapter.py保持原M1计算不变；训练端口仅固定1万更新、三源循环、场景隔离、恢复/计时和状态输出；几何监测统一阶段网格256³。官方提取增加原场保存并禁用Trimesh自动processing，面和组件全留。

M1：官方RGB/Eikonal/smooth/SSI depth/可靠法向损失，加原生HERO表面SmoothL1、首次正→负深度、真实来源射线前方弱自由空间、稳定正Mask BCE。权重沿上一M1，未因输出修改。跨源前方冲突>.25mm的弱代理权重.25，否则1；后方合法遮挡不是反证，三个来源非统计独立。无GT，不能把HERO当精确真值。

各组1024 rays/update，一次batch即一次Adam，无梯度累积；按源循环，不让大Mask支配。种子20261103，Adam betas(.9,.999)、eps1e-8、lr5e-4，1000步warmup、指数衰减周期200k（不是本轮10k）。比较1000/2000/5000/10000累计步，另外保留0/200/500工程阶段和每1000步完整latest。不按几何质量提前停止或选择好看检查点。

## 当前来源

|物理组/视频|固定来源|当前资格|分区|
|---|---|---|---|
|G01_004|ref08/ref13/ref03|全INSUFFICIENT_EVIDENCE|B3/B5/B2|
|G06_004|ref04/growth_r01/growth_r06|INSUFFICIENT/CONDITIONAL_USABLE/INSUFFICIENT|B2/B1/B3|
|G08_005|ref04/growth_r02/growth_r01|INSUFFICIENT/CONDITIONAL_USABLE/CONDITIONAL_USABLE|B2/B3/B4|

资格依据最新N0对27源统一v0.1结果，已按当前数值规则/required关系/可观测性重算所选9源资格，核查原RGB/Mask/K/c2w/数据SHA，未沿用旧source_camera_qualified布尔认证。G07仅两可入组方向块，另外B3来源NOT_ADMITTED，选择G08不依据神经输出。Camera Gate不重新优化相机，条件入组不等于真实位姿GT。

G01/G06原生/裁剪文件逐字复用当前N0冻结版本；G01神经输入各数组与上一轮完全相同。G08第一次按同一N0/A2固定规则仅一遍派生清理，512候选上限、实际射线/Mask/首CAD/分区负票、全B历史语义；不移植G01人工XYZ定向规则，不搜索阈值。原生ID和被屏蔽记录保留，新增孔洞如实报告，不用补洞隐藏。

各组自己Ring世界坐标，独立域/模型。域G01/G06沿当前N0；G08按同一清理点+实际CAD、margin规则冻结。MonoSDF `x=(X-C)/s`，C=O+L/2、s=L/2；SDF_mm=s*f、轴向Z/s，欧氏ray距离与轴向深度不混。K/旋转不变，c2w平移同转换。Ring实际外径12.4mm，不从文件名猜尺度。公制beta随s换算记录。

## 固定评价与边界

使用所有原始合法native Polyp观测，不以清理或未命中缩分母。CAD后方单列。首层hit/MISS与≤.25mm一致、hit-only误差/含MISS p95、原HERO点与原面保留、Mask越界、≥4次交点、负区代理体积、连通/法向角和观测/推断/未知面分类分别保存。两次交点可为正常壳，不直接叫重复层。

负区体积是模型代理，不是真实体积；HERO误差是有条件一致性，不是物理GT。未知封闭既不自动认证也不删除。展示使用相同视角向量与本组毫米窗口，跨组不混坐标。Raw/Cleaned对照保留原始归档面，cleaned仅按native有效性映射显示原面，存在已知离散化差异；真实SDF均从学习网络提取。

本次历史M0因新任务让位，不是科学失败。可恢复11k完整Adam/调度器/RNG保留；最后日志11200，未写入完整检查点的后续更新不冒充已保全。历史正式M1=0，经研究者确认新建1000基线，不以M0假充M1，也不将别组场作为新息肉初始化。
