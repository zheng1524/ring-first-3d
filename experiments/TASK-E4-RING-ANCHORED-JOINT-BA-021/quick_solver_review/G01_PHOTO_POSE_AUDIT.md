# G01 独立照片数值位姿与资格

| id | Ring_boundary_px | Ring_hard_balanced_MSE | Inner_MAE_px | Outer_MAE_px | SIFT_FIT_PnP_inliers_N | PHOTO_HELD_error_px | seed_pose_spread | minimum_direction_difference_deg | nearest_existing_video_view | frozen_independent_photo_pose_body_IoU | current_gate_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G01_photo001 | {'N': 1684, 'MAE': 0.8270635355319632, 'median': 0.0, 'p95': 3.1622776601683795, 'maximum': 5.0990195135927845} | 0.050470 | 2.732995 | 1.581214 | 50 | {'N': 23, 'MAE': 3.848546935850043, 'median': 3.5031501334628685, 'p95': 5.389826876204722, 'maximum': 15.226761263373561} | [{'seed_video': '004', 'camera_center_distance_mm': 0.0, 'rotation_difference_deg': 1.768626761220885e-15}, {'seed_video': '005', 'camera_center_distance_mm': 0.02840554537394477, 'rotation_difference_deg': 0.018550881164667708}] | 7.102866 | G01_004_growth_r06 | 0.888981 | ['PHOTO_HELD_MAE_GT3PX'] |
| G01_photo002 | {'N': 1906, 'MAE': 0.792691660385558, 'median': 0.0, 'p95': 2.8284271247461903, 'maximum': 7.0} | 0.043040 | 1.229349 | 1.478709 | 44 | {'N': 10, 'MAE': 3.058128769198525, 'median': 2.7588613791387075, 'p95': 4.792421246013733, 'maximum': 5.34816185493797} | [{'seed_video': '004', 'camera_center_distance_mm': 0.0, 'rotation_difference_deg': 6.990210361282175e-16}, {'seed_video': '005', 'camera_center_distance_mm': 0.010447825388765262, 'rotation_difference_deg': 0.012189235182323253}] | 1.532473 | G01_v005_raw00262 | 0.887744 | ['PHOTO_HELD_MAE_GT3PX'] |
| G01_photo003 | {'N': 1952, 'MAE': 2.1582304790765927, 'median': 1.0, 'p95': 9.433981132056603, 'maximum': 17.0} | 0.091859 | 6.337944 | 7.359407 | 15 | {'N': 14, 'MAE': 5.049078482157553, 'median': 4.555628088699338, 'p95': 9.823293916274409, 'maximum': 10.643531513637912} | [{'seed_video': '004', 'camera_center_distance_mm': 0.0, 'rotation_difference_deg': 4.4615294894585786e-15}] | 9.985451 | G01_video004_004_15 | 0.772268 | ['PHOTO_HELD_MAE_GT3PX', 'PHOTO_HELD_P95_GT6PX', 'RING_CONTOUR_GATE'] |

原照片/同批Mask路径与SHA见INDEPENDENT_PHOTO_ASSET_MANIFEST.csv；每张Ring初值、两个PnP分支及精修、真实UV/描述子ID/原视频featureID均保留于results/photos和photo_features。原始PnP与2D-only Essential候选不混用；所有位姿在照片held/body评价前冻结。当前数值yaw由真实特征支持，但未满足强监督门禁；不能称Ring单独认证6DoF。内参K490沿用同设备工作图假设，不能称独立标定。照片对主体IoU仅为冻结后代理，不用于选姿态。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | BA为G01同一视频对的3条续优化；照片为4组×3=12个原始采集，G01三张做实际相机尝试 |
| 本算法独立成功 | 3/3实际成熟求解器输出，12/12同批RGB和Mask定位，G01 3/3独立数值相机候选；强照片监督资格0/3，不混为正确率 |
| 本算法失败 | 完整Ring梯度门禁失败；A1线搜索异常，A2/A3主要在数值波动附近终止；3照片新门禁均未过，照片HERO/可信新增面积NaN/NOT_EVALUABLE |
| 历史测量值回退 | 0；021终点是本轮明确授权的续优化初值/A0参考；没有旧Dxy或其他算法测量值补齐 |
| 失败组及具体原因 | G01三照片当前held误差门禁失败，photo003还存在Ring/尾部问题；错误采集批次已隔离。见失败台账及真实RGB/三维候选图 |
| 最终统计样本 | BA全部18轨迹/553FIT像素、全部52FIT+3HOLDOUT目标帧及固定21HERO来源；全部12照片保留，包括未运行HERO的三张 |
| 是否使用GT选择算法 | 否；原BA不含照片/body/HERO/HOLDOUT；候选先冻结再独立评价。照片只用PHOTO_FIT选初值与拟合，PHOTO_HELD/主体不参与 |
