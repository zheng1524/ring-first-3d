# G03 位姿研究记录

**正式P1：NOT_RUN_JACOBIAN_GATE。** 原坐标及源相机保持不变。

| group | video_scope | target_video_views_N | FIT_N | HOLDOUT_N | P1_actual_solver_runs | P1_success | P1_status | P1_translation_mm | P1_rotation_deg | P1_Ring_improvement_px | P1_SIFT_improvement_px | P1_HERO_improvement_mm | FIT_P0_Ring_IoU | FIT_P0_body_IoU | FIT_P0_Inner_MAE_px | FIT_P0_Outer_MAE_px | HOLDOUT_P0_Ring_IoU | HOLDOUT_P0_body_IoU | HOLDOUT_P0_Inner_MAE_px | HOLDOUT_P0_Outer_MAE_px | P0_HERO_fixed_N | P0_HERO_known_N | P0_HERO_MAE_mm | absolute_pose_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G03 | 004_only | 9 | 6 | 3 | 0 | 0 | NOT_RUN_JACOBIAN_GATE | NaN / NOT_RUN | NaN / NOT_RUN | NaN / NOT_RUN | NaN / NOT_RUN | NaN / NOT_RUN | 0.8662485 | 0.903606 | 1.387384 | 1.667889 | 0.8346754 | 0.9187554 | 2.051481 | 0.8565003 | 1791112 | 1715304 | 1.064599 | NOT_EVALUABLE_NO_GT |


## 实际输入与可计算指标

| id | role | map_points | RGB_matches | fit_PNP | held_features | fallback_epi_N |
| --- | --- | --- | --- | --- | --- | --- |
| G03_key04_raw00554 | FIT | 424 | 111 | 87 | 24 | 0 |
| G03_key00_raw00100 | FIT | 424 | 83 | 62 | 20 | 0 |
| G03_v004_raw00834 | FIT | 424 | 109 | 90 | 19 | 0 |
| G03_v004_raw00161 | FIT | 424 | 74 | 60 | 14 | 0 |
| G03_v004_raw00406 | FIT | 424 | 116 | 93 | 22 | 0 |
| G03_v004_raw00651 | FIT | 424 | 113 | 94 | 17 | 0 |
| G03_key06_raw00782 | HOLDOUT | 424 | 128 | 107 | 20 | 0 |
| G03_v004_raw00263 | HOLDOUT | 424 | 66 | 47 | 17 | 0 |
| G03_v004_raw00589 | HOLDOUT | 424 | 68 | 56 | 10 | 0 |


原生HERO固定代理：

| sources_N | native_TRUSTED_pixels_N | cumulative_source_area_mm2 | fixed_source_target_N | known_N | depth_mm | visibility_categories |
| --- | --- | --- | --- | --- | --- | --- |
| 9 | 223889 | 3249.539 | 1791112 | 1715304 | {'N': 1715304, 'MAE': 1.0645988276522815, 'median': 0.9284681546181908, 'p95': 2.517695040614573, 'maximum': 5.018055038034952} | {'fixed': 1791112, 'known': 1715304, 'supported': 482676, 'front': 633017, 'behind': 599611, 'cad_occluded': 23, 'target_Ring_order_unreliable': 16, 'unknown': 75785} |

累计来源面积不是去重解剖面积；已知深度误差是可见性代理、非GT精度，更深层可为正常自遮挡。完整逐视角Ring I/O P95、Mask轮廓与SIFT残差见ALL_VIDEO_P0_METRICS.csv。

## 故障定位与八项判断

| group | local_J_max_rel_h1e4 | local_J_max_rel_h1e5 | data_only_J_rank | condition_J | yaw_invariance_error |
| --- | --- | --- | --- | --- | --- |
| G03 | 3.203607e-07 | 3.223858e-09 | 6 | 69.55113 | 1.65635e-15 |

该组已定位4条在登记微扰中切换的实际CAD边，原始vertex ID/XYZ/投影/射线状态完整保留。

1. 成熟求解器正式执行成功：NOT_RUN。
2. 合理位姿更新：NOT_RUN，无派生矩阵。
3. Ring边界改善：NaN，只有P0。
4. SIFT几何改善：NaN，真实输入匹配计数已给。
5. 独立观测退化：NOT_TESTED，不用基线数值替代。
6. 不合理漂移：NOT_TESTED；当前未产生相机更新。
7. 弱自由度：本组代表视角局部数据J秩6，条件数见表；Ring自身yaw无约束。其余视角未逐个做完整J审查。
8. 后续研究资格：原P0可作为明确标注的研究输入；本轮新方法不升级，先修复共同Ring可见性缺陷。

G01使用既有B3统一004世界，其他三组仅004；未虚构额外视频姿态。冻结HERO和主体只用于上述P0独立评价。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 4个物理组；98个canonical视频视角（81FIT/17HOLDOUT），照片阶段12张仅条件授权 |
| 本算法独立成功 | 正式P1派生相机输出0/98；四组正式精修完成0/4；98/98原始输入审计、4/4代表视角数值探针完成不算优化成功 |
| 本算法失败 | 3/4代表视角局部J多步长门禁失败；全局门禁FAIL，全部4组P1未运行，结果NaN。12照片NOT_RUN_STAGE_A_GATE |
| 历史测量值回退 | 0；用户指定021B3与旧相机仅作P0/初始化，不冒充新P1输出 |
| 失败组及具体原因 | G01/G05/G06在1e-4的Outer残差跨clamp分支；G03局部J通过但重线性化可见边也切换。四组均发现CAD边射线可见性切换，详见逐组报告和真实图 |
| 最终统计样本 | P0全部98视角和51个原生TRUSTED来源；新P1独立输出0，改进指标NaN；绝对GT误差MedARE/MAE/P95/max均NOT_EVALUABLE |
| 是否使用GT选择算法 | 否；未读取GT。原相机/Mask/HERO/主体/CAD/DXY未修改，未用HERO或主体生成位姿 |
