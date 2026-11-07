# 原始Blender来源、单位与指标定义

所有匹配在PREDICTIONS_FROZEN_BEFORE_GT和SCALE_LOCK_BEFORE_GT之后。根据冻结物理身份/确切源目录，G04/G07另有历史人工确认别名和原始SHA绑定，不按预测相似性挑选。所有原始.blend仅读取，未保存、清理或修补。

|病例|冻结物理身份|原始文件|主体对象|单位转换|作者基底|
|---|---|---|---|---|---|
|G01|spec_01p-12-|/home/liu/polyp_research/01p型/01p-12-/息肉.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G02|spec_01p-4-|/home/liu/polyp_research/01p型/01p-4-/息肉.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G03|spec_01p-20-|/home/liu/polyp_research/01p型/01p-20-/息肉.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G07|spec_01s-14|/home/liu/polyp_research/experiments/geometric_validation_v1/assets/Is14.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G04|catalog_family:FROZEN_PHYSICAL_GROUP:G04|/home/liu/polyp_research/experiments/geometric_validation_v1/assets/IIa6.5.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G05|spec_01s-18-6.99|/home/liu/ultralytics-main/polyp_detection/息肉建模/01s-18-6.99/息肉.blend|棱角球|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G06|spec_02a-14-1.6|/home/liu/ultralytics-main/polyp_detection/息肉建模/02a-14-1.6/息肉.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G08|spec_02a-22-4.4|/home/liu/ultralytics-main/polyp_detection/息肉建模/02a-22-4.4/息肉.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|
|G09|spec_02a-4.5-1|/home/liu/ultralytics-main/polyp_detection/息肉建模/02a-4.5-1/息肉.blend|球体|METRIC m ×1000→mm|世界XY、最低真实平面三角面，条件参考|

G04数据标签Is来自用户既有分类，但CAD源是明确绑定的IIa6.5别名，不视为干净的类型辨识实验。G07恢复源同样有SHA绑定。其余按完整spec_物理目录关联，不仅凭直径。所有源场景单位METRIC、scale_length=1且主体无动画/形状键；毫米转换只作用GT，不影响已锁定预测。

Dxy为作者XY方向投影凸包最大Feret，统一作用于GT和每个刚性对齐后的预测，非文件名直径。条件Hmax以同一作者平面为参考；主报告H95用预测完整实体和GT完整实体各8192面积采样，同算子、推断盖明确计入模型假设。观测可参与面H95另列，不能与完整实体H95混用。Hmax数值接近不证明到达真实基底或恢复细柄。

原生世界相机2D指标不使用GT对齐改善投影。3D注册严格6DoF、无尺度，矩阵及全部24初值残差保留。GT自交/开口不修补，严格体积IoU缺失保留NaN；含推断底盖仅占据代理。固定Sobol采样给数值估计而非精确布尔体积或严谨置信区间。

源SHA、场景/物体矩阵和最低平面证据见assets_index/GT_SOURCE_LOCK、GT_SOURCE_INSPECTION、GT_IDENTITY_UNIT_EVIDENCE；GT_VALIDITY逐例列自交和闭合状态。原始.blend和GT主体缓存保留本地索引，不上传大型源模型。
