# 12照片配准

| 照片 | 数值 | 条件入组 | 留出N | 主要原因 |
| --- | --- | --- | ---: | --- |
| G01_photo001 | 是 | 是 | 8 |  |
| G01_photo002 | 是 | 是 | 8 |  |
| G01_photo003 | 是 | 否 | 2 | RGB_6DOF_INSUFFICIENT,INDEPENDENT_RGB_FEATURES_TOO_FEW |
| G03_photo001 | 是 | 是 | 22 |  |
| G03_photo002 | 是 | 否 | 3 | INDEPENDENT_RGB_FEATURES_TOO_FEW |
| G03_photo003 | NaN | 否 | 0 | NO_NUMERIC_POSE |
| G05_photo001 | 是 | 否 | 0 | RGB_6DOF_INSUFFICIENT,INDEPENDENT_RGB_FEATURES_TOO_FEW |
| G05_photo002 | 是 | 是 | 6 |  |
| G05_photo003 | NaN | 否 | 0 | NO_NUMERIC_POSE |
| G06_photo001 | 是 | 否 | 3 | INDEPENDENT_RGB_FEATURES_TOO_FEW |
| G06_photo002 | 是 | 否 | 0 | RGB_6DOF_INSUFFICIENT,INDEPENDENT_RGB_FEATURES_TOO_FEW |
| G06_photo003 | 是 | 否 | 0 | RGB_6DOF_INSUFFICIENT,INDEPENDENT_RGB_FEATURES_TOO_FEW |

G01三张旧数值位姿是命名历史对照，结果与同图新Ring/RGB评价另存metrics/G01_HISTORICAL_PHOTO_SAME_DATA_EVALUATION.json。没有把历史3–5px残差自动当完全认证，也未仅凭旧3px门槛终止研究。Ring-only yaw未定位的照片只在列表展示，不画入共同世界。仅4张有条件入组资格；是否被最大覆盖选中另由同一规则决定。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个独立物理组；8视频+12照片；7650原始视频帧，实际处理884候选 |
| 本算法独立成功 | 877/884产生数值相机（含弱/留出）；550/884条件性验证；4/4组完成新HERO；47/47真实推理+分类 |
| 本算法失败 | 7/884相机无数值（NaN）；其余弱候选和25留出不作正式目标；新增几何未达到可直接Body适配结论 |
| 历史测量值回退 | 0；新HERO推理47次均reused=false；历史相机/原生几何为明确授权的输入及对照 |
| 失败组及具体原因 | 全四组逐来源/逐相机见FAILURE_LEDGER.md与metrics/FAILED_OR_EXPLORATORY_CAMERAS.csv；G03错层、G06支持图反例见Figure6/E4 |
| 最终统计样本 | 全体分母保留：4组、884候选、47推理；几何共同有效N和固定native-pair像素N分别列出，不能以条件MAE代替覆盖 |
| 是否使用 GT 选择算法 | 否；无GT/Oracle数据读取；各组相机和HERO计划freeze早于首次新HERO；旧相机/地图/Body的历史留出依赖不宣称独立 |
