# QUICK-BA-SOLVER-REVIEW 结果摘要

**已完成三条成熟求解器实际续优化，以及同批12张独立照片恢复与G01三张实际配准。未开展主体训练或曲面融合。**

**主要结论：目前不能将021停滞归因“观测已经达到极限”。** 平滑SIFT/先验分支的AD–FD吻合，而Ring可微渲染分支在多方向出现大幅、甚至符号相反的AD–FD偏差。成熟L-BFGS-B没有使A2获得可信的联合几何改善；它仍使用这个未经验证的完整梯度，因此不能据其终止判定BA数据无解。

| method | initial_loss | loss | initial_gradient_norm | final_gradient_norm | nit | nfev | solver_success | solver_message | translation_change_mm | rotation_change_deg | max_point_change_mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 0.071305 | 0.071137 | 0.094559 | 0.069316 | 3 | 41 | False | ABNORMAL:  | 0.029396 | 0.048900 | 0.000000 |
| A2 | 0.067097 | 0.067097 | 0.054995 | 0.054995 | 1 | 11 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.000000 | 0.000000 | 0.000000 |
| A3 | 0.071589 | 0.071587 | 0.055252 | 0.055242 | 2 | 33 | True | CONVERGENCE: RELATIVE REDUCTION OF F <= FACTR*EPSMCH | 0.000006 | 0.000013 | 0.000000 |

Loss无量纲、平移/点位移mm、旋转deg。A1部分下降但线搜索ABNORMAL；A2实际移动约3e−10mm，目标变化约1e−7，处于重复渲染波动量级。A3同样只发生微小变化。`solver_success=True`的相对函数变化终止，不等于低梯度或科学收敛。完整先验仍相对原始RoMa与联合三角化X0，没有在021终点重置正则中心。

## 独立几何结果

| method | before_HOLDOUT_IoU | after_HOLDOUT_IoU | before_held_SIFT_F | after_held_SIFT_F | before_HERO_support | after_HERO_support | exact_common_N | exact_common_before_MAE_mm | exact_common_after_MAE_mm | gained_N | lost_N |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | 0.897414 | 0.897762 | 1.018993 | 1.031965 | 0.347308 | 0.347013 | 2108144 | 0.803705 | 0.801912 | 12068 | 15820 |
| A2 | 0.895871 | 0.895871 | 1.044274 | 1.044274 | 0.343268 | 0.343268 | 2113712 | 0.801347 | 0.801347 | 0 | 0 |
| A3 | 0.897173 | 0.897173 | 1.057115 | 1.057114 | 0.343117 | 0.343117 | 2114074 | 0.801193 | 0.801193 | 4 | 7 |

全部候选冻结后统一评价。HERO分母固定2,893,126个重复原生源–目标观测，21来源/208有向跨视频配对；共同/新增/丢失严格依据同一原Pixel ID。共同误差仍含单列的后方/合法自遮挡代理，不是物理表面GT。A1只有微小代理变化；A2/A3没有实质独立收益。没有按这些HOLDOUT/HERO数值再调参，也未选择新终点。

## 独立照片与输入恢复

初次默认`rg --files`遵守Git忽略规则，遗漏raw20260805，曾误选旧picture/new picture目录中的同名照片。检查v4/v13原始来源SHA后发现不同采集批次；错误输出与源码完整保留在`provenance/WRONG_CAPTURE_COHORT_QUARANTINE/`，不计入正式结果、不回填。随后显式读取raw20260805：四组12/12原始JPG及对应原生分割缓存均找到，G01三张原SHA与同视频采集记录完全一致，640×360工作图也与历史原始输入逐像素一致。**同名不是同一采集身份。**

旧20260415 `missing_inner_ellipse`只是旧同名记录，不能当作本批照片缺失；当前本批三张都实际运行成熟DXY Ring流程。当前Mask是同批保留UNet3Plus多类缓存，非旧LabelMe，也不是本轮新分割推理。旧记录只取stem/status/reason，未使用旧测量值。不同采集批次旧失败与本批新拟合不构成严格同Mask算法对照。

| id | SIFT_FIT_PnP_inliers_N | PHOTO_HELD_error_px | Inner_MAE_px | Outer_MAE_px | minimum_direction_difference_deg | camera_status | current_gate_reasons |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G01_photo001 | 50 | {'N': 23, 'MAE': 3.848546935850043, 'median': 3.5031501334628685, 'p95': 5.389826876204722, 'maximum': 15.226761263373561} | 2.732995 | 1.581214 | 7.102866 | NUMERIC_RING_SIFT_POSE_WEAK_HELD_VALIDATION | ['PHOTO_HELD_MAE_GT3PX'] |
| G01_photo002 | 44 | {'N': 10, 'MAE': 3.058128769198525, 'median': 2.7588613791387075, 'p95': 4.792421246013733, 'maximum': 5.34816185493797} | 1.229349 | 1.478709 | 1.532473 | NUMERIC_RING_SIFT_POSE_WEAK_HELD_VALIDATION | ['PHOTO_HELD_MAE_GT3PX'] |
| G01_photo003 | 15 | {'N': 14, 'MAE': 5.049078482157553, 'median': 4.555628088699338, 'p95': 9.823293916274409, 'maximum': 10.643531513637912} | 6.337944 | 7.359407 | 9.985451 | NUMERIC_RING_SIFT_POSE_WEAK_HELD_VALIDATION | ['PHOTO_HELD_MAE_GT3PX', 'PHOTO_HELD_P95_GT6PX', 'RING_CONTOUR_GATE'] |

三张均有独立Ring-First初始化、真实SIFT/PnP与Ring约束精修，未复制任何视频外参。photo001/002的004/005独立种子精修结果分别只相差约0.028/0.010mm、0.019/0.012°，但PHOTO_HELD MAE分别3.849/3.058px；photo003单侧种子、held MAE5.049px/p959.823px及Ring误差更大。它们均未通过事前固定3px MAE/6px P95门槛；该结论来自本轮新观测，非继承V13旧UNREGISTERED标签。photo002接近阈值，不等于物理无价值，更不能事后改阈值。

真实2D匹配另做固定16个视频FIT视角×3照片、复用缓存SIFT，Essential/Ring有限候选仅作显式2D-only补充；不虚构3D同名点，不称其为PnP，不根据留出或主体挑选。完整候选保留。独立照片不是短视频，彼此无已知相对轨迹。

## HERO与全视角适配

现有审计原生目标均是视频帧；V13照片历史记录亦为NOT_RUN。本轮核验了018官方HERO加载器和完整权重SHA、原017清理规则，准备了每张目标及三个同组FIT支持的RGB/K/统一世界相机清单。由于三张未通过新照片相机门禁，本轮实际新HERO推理0次，TRUSTED子集、面积、与已有曲面相容性、主体未覆盖和新增可信面积均为MISSING/NOT_EVALUABLE，不能用视频深度投影假装照片原生深度。

71是68视频+3独立照片的候选资产数，不是71份已合格三维监督。保留原8个HOLDOUT，现有60个FIT视角可提供条件性Mask观测，其中16个具有已登记原生TRUSTED HERO；三照片当前不进入强监督FIT。新增方向最小差约7.10°/1.53°/9.99°为数值候选条件估计，不等于新增可见表面积；photo002方向接近已有视角。

**下一轮坐标建议：暂时沿用事前固定的021 B3共同坐标基准，保留其已知局限；不自动将A1/A2/A3升级为新主线，也不按本轮HOLDOUT重新选择020候选。** 优先隔离修复Ring梯度一致性；对照片核对光学模式、误差来源及有限真实对应，001/002可优先进一步核验，003需更多Ring/位姿证据。真实独立照片的数值候选不是绝对位姿认证。

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | BA为G01同一视频对的3条续优化；照片为4组×3=12个原始采集，G01三张做实际相机尝试 |
| 本算法独立成功 | 3/3实际成熟求解器输出，12/12同批RGB和Mask定位，G01 3/3独立数值相机候选；强照片监督资格0/3，不混为正确率 |
| 本算法失败 | 完整Ring梯度门禁失败；A1线搜索异常，A2/A3主要在数值波动附近终止；3照片新门禁均未过，照片HERO/可信新增面积NaN/NOT_EVALUABLE |
| 历史测量值回退 | 0；021终点是本轮明确授权的续优化初值/A0参考；没有旧Dxy或其他算法测量值补齐 |
| 失败组及具体原因 | G01三照片当前held误差门禁失败，photo003还存在Ring/尾部问题；错误采集批次已隔离。见失败台账及真实RGB/三维候选图 |
| 最终统计样本 | BA全部18轨迹/553FIT像素、全部52FIT+3HOLDOUT目标帧及固定21HERO来源；全部12照片保留，包括未运行HERO的三张 |
| 是否使用GT选择算法 | 否；原BA不含照片/body/HERO/HOLDOUT；候选先冻结再独立评价。照片只用PHOTO_FIT选初值与拟合，PHOTO_HELD/主体不参与 |

[四张核心图与补充RGB证据](RESULT_INDEX.md) · [复现](REPRODUCE.md)。本轮结束，等待人工审核。
