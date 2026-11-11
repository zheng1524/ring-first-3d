# G01 位姿研究记录

**正式P1：NOT_RUN_JACOBIAN_GATE。** 原坐标及源相机保持不变。

| group | video_scope | target_video_views_N | FIT_N | HOLDOUT_N | P1_actual_solver_runs | P1_success | P1_status | P1_translation_mm | P1_rotation_deg | P1_Ring_improvement_px | P1_SIFT_improvement_px | P1_HERO_improvement_mm | FIT_P0_Ring_IoU | FIT_P0_body_IoU | FIT_P0_Inner_MAE_px | FIT_P0_Outer_MAE_px | HOLDOUT_P0_Ring_IoU | HOLDOUT_P0_body_IoU | HOLDOUT_P0_Inner_MAE_px | HOLDOUT_P0_Outer_MAE_px | P0_HERO_fixed_N | P0_HERO_known_N | P0_HERO_MAE_mm | absolute_pose_accuracy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01 | 004+005_shared004world | 68 | 60 | 8 | 0 | 0 | NOT_RUN_JACOBIAN_GATE | NaN / NOT_RUN | NaN / NOT_RUN | NaN / NOT_RUN | NaN / NOT_RUN | NaN / NOT_RUN | 0.879017 | 0.8985859 | 1.47084 | 1.449352 | 0.8620444 | 0.9022904 | 2.441277 | 2.239524 | 5991640 | 4867316 | 0.7789459 | NOT_EVALUABLE_NO_GT |


## 实际输入与可计算指标

| id | role | map_points | RGB_matches | fit_PNP | held_features | fallback_epi_N |
| --- | --- | --- | --- | --- | --- | --- |
| G01_004_ref08 | FIT | 153 | 37 | 29 | 7 | 0 |
| G01_004_ref13 | FIT | 153 | 48 | 41 | 7 | 0 |
| G01_004_ref03 | FIT | 153 | 19 | 14 | 4 | 0 |
| G01_004_new_r00 | FIT | 153 | 12 | 10 | 1 | 0 |
| G01_v004_raw00412 | FIT | 153 | 24 | 20 | 4 | 0 |
| G01_v004_raw00852 | FIT | 153 | 36 | 27 | 9 | 0 |
| G01_video004_004_15 | FIT | 153 | 50 | 40 | 10 | 0 |
| G01_v004_raw00152 | FIT | 153 | 15 | 12 | 3 | 0 |
| G01_004_growth_r04 | HOLDOUT | 153 | 35 | 29 | 5 | 0 |
| G01_004_growth_r06 | HOLDOUT | 153 | 46 | 37 | 8 | 0 |
| G01_004_growth_r10 | HOLDOUT | 153 | 46 | 40 | 6 | 0 |
| G01_video004_004_09 | HOLDOUT | 153 | 36 | 30 | 5 | 0 |
| G01_v004_raw00334 | HOLDOUT | 153 | 18 | 13 | 4 | 0 |
| G01_005_raw00057 | FIT | 980 | 56 | 44 | 10 | 0 |
| G01_005_raw00459 | FIT | 980 | 43 | 34 | 9 | 0 |
| G01_005_raw00745 | FIT | 980 | 52 | 41 | 11 | 0 |
| G01_005_new_r04 | HOLDOUT | 980 | 37 | 29 | 6 | 0 |
| G01_005_growth_r03 | FIT | 980 | 62 | 47 | 15 | 0 |
| G01_005_growth_r20 | FIT | 980 | 42 | 33 | 8 | 0 |
| G01_005_growth_r12 | FIT | 980 | 52 | 43 | 9 | 0 |
| G01_005_growth_r15 | FIT | 980 | 66 | 61 | 5 | 0 |
| G01_005_growth_r11 | FIT | 980 | 65 | 54 | 11 | 0 |
| G01_video005_v005_00000 | FIT | 980 | 28 | 26 | 2 | 0 |
| G01_video005_v005_00115 | FIT | 980 | 73 | 57 | 16 | 0 |
| G01_video005_v005_00287 | FIT | 980 | 77 | 61 | 16 | 0 |
| G01_video005_v005_00326 | FIT | 980 | 37 | 26 | 8 | 0 |
| G01_video005_v005_00344 | FIT | 980 | 53 | 48 | 5 | 0 |
| G01_video005_v005_00401 | FIT | 980 | 31 | 25 | 4 | 0 |
| G01_video005_v005_00427 | FIT | 980 | 63 | 46 | 17 | 0 |
| G01_video005_v005_00611 | FIT | 980 | 68 | 50 | 18 | 0 |
| G01_video005_v005_00631 | FIT | 980 | 34 | 33 | 1 | 0 |
| G01_video005_v005_00688 | FIT | 980 | 64 | 49 | 15 | 0 |
| G01_video005_v005_00785 | FIT | 980 | 63 | 51 | 11 | 0 |
| G01_video005_v005_00803 | FIT | 980 | 42 | 31 | 11 | 0 |
| G01_video005_v005_00860 | FIT | 980 | 43 | 36 | 6 | 0 |
| G01_v005_raw00086 | FIT | 980 | 55 | 44 | 10 | 0 |
| G01_v005_raw00104 | FIT | 980 | 50 | 35 | 13 | 0 |
| G01_v005_raw00121 | FIT | 980 | 66 | 52 | 14 | 0 |
| G01_v005_raw00139 | FIT | 980 | 33 | 26 | 7 | 0 |
| G01_v005_raw00157 | FIT | 980 | 31 | 27 | 4 | 0 |
| G01_v005_raw00174 | FIT | 980 | 76 | 64 | 12 | 0 |
| G01_v005_raw00192 | FIT | 980 | 47 | 37 | 10 | 0 |
| G01_v005_raw00209 | FIT | 980 | 12 | 9 | 3 | 0 |
| G01_v005_raw00245 | FIT | 980 | 37 | 31 | 6 | 0 |
| G01_v005_raw00262 | FIT | 980 | 37 | 32 | 5 | 0 |
| G01_v005_raw00280 | FIT | 980 | 70 | 59 | 10 | 0 |
| G01_v005_raw00298 | FIT | 980 | 78 | 66 | 12 | 0 |
| G01_v005_raw00315 | FIT | 980 | 38 | 34 | 2 | 0 |
| G01_v005_raw00333 | FIT | 980 | 19 | 17 | 2 | 0 |
| G01_v005_raw00351 | FIT | 980 | 54 | 47 | 7 | 0 |
| G01_v005_raw00368 | FIT | 980 | 42 | 35 | 7 | 0 |
| G01_v005_raw00386 | FIT | 980 | 45 | 36 | 9 | 0 |
| G01_v005_raw00421 | FIT | 980 | 58 | 43 | 15 | 0 |
| G01_v005_raw00439 | FIT | 980 | 47 | 35 | 12 | 0 |
| G01_v005_raw00456 | FIT | 980 | 49 | 39 | 10 | 0 |
| G01_v005_raw00474 | FIT | 980 | 56 | 39 | 16 | 0 |
| G01_v005_raw00492 | FIT | 980 | 52 | 43 | 8 | 0 |
| G01_v005_raw00509 | HOLDOUT | 980 | 53 | 41 | 10 | 0 |
| G01_v005_raw00527 | FIT | 980 | 59 | 47 | 12 | 0 |
| G01_v005_raw00545 | FIT | 980 | 61 | 47 | 14 | 0 |
| G01_v005_raw00562 | FIT | 980 | 53 | 40 | 13 | 0 |
| G01_v005_raw00598 | FIT | 980 | 70 | 53 | 17 | 0 |
| G01_v005_raw00651 | FIT | 980 | 52 | 43 | 9 | 0 |
| G01_v005_raw00668 | HOLDOUT | 980 | 49 | 37 | 12 | 0 |
| G01_v005_raw00703 | FIT | 980 | 73 | 61 | 12 | 0 |
| G01_v005_raw00721 | FIT | 980 | 60 | 49 | 11 | 0 |
| G01_v005_raw00756 | FIT | 980 | 46 | 37 | 9 | 0 |
| G01_v005_raw00774 | FIT | 980 | 60 | 52 | 8 | 0 |


原生HERO固定代理：

| sources_N | native_TRUSTED_pixels_N | cumulative_source_area_mm2 | fixed_source_target_N | known_N | depth_mm | visibility_categories |
| --- | --- | --- | --- | --- | --- | --- |
| 21 | 299582 | 2323.897 | 5991640 | 4867316 | {'N': 4867316, 'MAE': 0.7789458980970698, 'median': 0.5300011496963197, 'p95': 2.432122547941317, 'maximum': 22.977308791581656} | {'fixed': 5991640, 'known': 4867316, 'supported': 2328490, 'front': 1339770, 'behind': 1199056, 'cad_occluded': 2240, 'target_Ring_order_unreliable': 186, 'unknown': 1122084} |

累计来源面积不是去重解剖面积；已知深度误差是可见性代理、非GT精度，更深层可为正常自遮挡。完整逐视角Ring I/O P95、Mask轮廓与SIFT残差见ALL_VIDEO_P0_METRICS.csv。

## 故障定位与八项判断

| group | local_J_max_rel_h1e4 | local_J_max_rel_h1e5 | data_only_J_rank | condition_J | yaw_invariance_error |
| --- | --- | --- | --- | --- | --- |
| G01 | 0.01131766 | 2.633795e-09 | 6 | 43.10851 | 1.605047e-16 |

该组已定位1条在登记微扰中切换的实际CAD边，原始vertex ID/XYZ/投影/射线状态完整保留。

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
