# 019 失败与限制台账

所有失败保留，不改门槛造PASS。当前研究候选数值成功≠已认证配准/融合成功。

| 项目 | 具体原因与证据 | 处理 |
| --- | --- | --- |
| 未胜过历史基线 | A5 HOLDOUT0.882843，RoMa0.893435；3/3留出均更差；`metrics/PAIRED_FRAME_COMPARISON.csv` | 保留A0与A5，不替换输出、不挑帧 |
| 弱形状方向 | model核心到Ring法向轴的投影短、HERO局部可见中心偏；A1/A2与SIFT相差8–9° | 多候选，不算术平均/唯一真方向 |
| SIFT证据局限 | 147/153背景地标；FIT34/52PnP，HOLD17地标对应；极线p95有长尾 | 不冒称丰富Polyp纹理或充分认证 |
| 初始cv2数值失败 | 退化RGB帧对触发USAC断言；features.log保留 | 捕获cv2.error为无F/无内点，未补对应或放宽阈值；features_resume.log |
| 同视频非零漂移 | t0.016857mm、R0.270117°，3/80接受，FIT IoU轻微下降 | 如实记录分量权衡，不说零漂移 |
| Ring深度不稳定 | 22/22未通过扇区/MAD/留出稳定性；下表逐来源 | 原生深度不变，无来源级全图校正 |
| HERO仍不一致 | H1 known MAE0.867141mm；固定分母前方分歧代理22.003% | 不把自遮挡当自由空间真错误，不融合 |
| 小量CAD内部样本 | 005 growth_r03新增1个引用顶点深入CAD超过.02mm；面中心0，完整三角相交未认证 | 保留原面、不调相机掩盖、不声称无碰撞 |
| 原主体误差 | 冻结body不完全符合005全Mask，柄部仍缺失 | 不开放body自由度补偿配准 |
| HERO不可用帧 | 00546/55无原生深度，但camera/RGB/Mask完整 | 完整参加主配准；深度辅助项NOT_AVAILABLE |
| 准独立留出 | 本轮HOLDOUT不进入选择；018/014祖先可接触部分图像 | 标明更新阶段留出，不说端到端独立 |
| NMS实现偏差 | 文字预注册“局部极小”，实际score+20°NMS | 原证据保留，报告偏差，不扩大本轮搜索 |
| 未独立门禁所有候选正深度 | 实际只罚特征behind，不是全body候选硬约束 | 最终68帧另测正深度，不能追认所有提案 |
| 软Ring数值抖动 | 约1e−6的重复前向浮动>1e−9接受容差 | 小幅接受/拒绝不作严格单调证据，未留出后调参 |
| 性能修复/中断 | naive硬Ring慢，停自身进程、40步q/Adam恢复 | equivalence104组+3梯度通过；秒数仅恢复段，不伪造全程耗时 |
| 子集NPZ无引用V诊断 | 首次显示范围/内部计数误含F未引用顶点 | 仅诊断改为真实引用几何，旧计数另存，预测完全不变 |
| H2未执行 | 内部相对相机变化max1.42e−14，仅坐标规范统一 | 按任务条件不重复HERO；不包装新预测 |

## 全部Ring深度来源：均未通过来源级标定

| view | video | reliable_N | MAD_mm | sector_spread_mm | Ring_held_before_MAE | Ring_held_after_MAE | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G01_004_ref08 | 004 | 2469 | 0.751957 | 2.711239 | 0.868170 | 0.944377 | REJECT_SOURCE_BIAS_TRIAL |
| G01_004_ref13 | 004 | 2217 | 0.242405 | 1.785362 | 0.449226 | 0.448879 | REJECT_SOURCE_BIAS_TRIAL |
| G01_004_ref03 | 004 | 2923 | 0.549440 | 5.159837 | 1.673315 | 1.708189 | REJECT_SOURCE_BIAS_TRIAL |
| G01_004_new_r00 | 004 | 2076 | 0.251521 | 4.170340 | 0.738006 | 0.667266 | REJECT_SOURCE_BIAS_TRIAL |
| G01_v004_raw00412 | 004 | 2583 | 0.448868 | 3.245901 | 1.206219 | 1.324135 | REJECT_SOURCE_BIAS_TRIAL |
| G01_v004_raw00852 | 004 | 2259 | 0.274586 | 0.983154 | 1.110067 | 0.774874 | REJECT_SOURCE_BIAS_TRIAL |
| G01_video004_004_15 | 004 | 2055 | 0.414993 | 2.610046 | 0.810672 | 0.755363 | REJECT_SOURCE_BIAS_TRIAL |
| G01_v004_raw00152 | 004 | 2257 | 0.158001 | 1.283640 | 1.071890 | 1.008879 | REJECT_SOURCE_BIAS_TRIAL |
| G01_004_growth_r04 | 004 | 2532 | 0.355911 | 3.014116 | 0.703188 | 0.652782 | REJECT_SOURCE_BIAS_TRIAL |
| G01_004_growth_r06 | 004 | 2564 | 0.460937 | 3.132032 | 0.993467 | 0.876854 | REJECT_SOURCE_BIAS_TRIAL |
| G01_004_growth_r10 | 004 | 2199 | 0.624870 | 2.332708 | 0.934332 | 1.035192 | REJECT_SOURCE_BIAS_TRIAL |
| G01_video004_004_09 | 004 | 2189 | 0.777172 | 2.545471 | 1.704509 | 0.910595 | REJECT_SOURCE_BIAS_TRIAL |
| G01_v004_raw00334 | 004 | 2501 | 0.616074 | 2.781681 | 2.534606 | 1.827029 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_raw00057 | 005 | 3872 | 0.315060 | 1.355972 | 0.691307 | 0.688212 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_raw00459 | 005 | 3556 | 0.418968 | 1.293732 | 0.407871 | 0.408709 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_raw00745 | 005 | 3613 | 0.557728 | 1.304661 | 0.449326 | 0.448110 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_new_r04 | 005 | 4116 | 0.307602 | 0.947344 | 0.341524 | 0.327811 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_growth_r03 | 005 | 4855 | 0.292791 | 1.407118 | 0.432916 | 0.431805 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_growth_r20 | 005 | 4271 | 0.654507 | 2.249641 | 0.662961 | 0.707630 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_growth_r12 | 005 | 3599 | 0.366325 | 1.209122 | 0.345746 | 0.335059 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_growth_r15 | 005 | 3738 | 0.355104 | 1.175758 | 0.293627 | 0.339287 | REJECT_SOURCE_BIAS_TRIAL |
| G01_005_growth_r11 | 005 | 3570 | 0.280447 | 1.133064 | 0.243052 | 0.233449 | REJECT_SOURCE_BIAS_TRIAL |

## 005 FIT的特征缺口（帧仍保留）

| view | SIFT_epi_available | PnP_available | handling |
| --- | --- | --- | --- |
| G01_005_raw00057 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_005_raw00745 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_005_growth_r03 | False | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_005_growth_r20 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_video005_v005_00000 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_video005_v005_00115 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_video005_v005_00860 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00086 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00104 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00121 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00139 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00157 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00174 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00262 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00315 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00333 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00703 | True | False | Mask and Ring retained; absent feature channel not fabricated |
| G01_v005_raw00721 | True | False | Mask and Ring retained; absent feature channel not fabricated |

## 历史候选（包括旧失败）

| tag | status |
| --- | --- |
| HISTORICAL_FULL_LightGlue | HISTORICAL_UNCHANGED |
| HISTORICAL_FULL_RoMa | HISTORICAL_UNCHANGED |
| GICP_FULL_LightGlue | STOPPED_RING_BOUNDS |
| GICP_FULL_RoMa | STOPPED_RING_BOUNDS |
| GICP_RingYaw | STOPPED_RING_BOUNDS |
| GICP_RingYaw_minus5 | STOPPED_RING_BOUNDS |
| GICP_RingYaw_plus5 | STOPPED_RING_BOUNDS |
| CACHED_LIGHTGLUE_PNP_SEED0 | PNP_RANSAC_THREE_FIXED_SUBSAMPLES |

## 全部帧证据

`metrics/ALL_FRAME_METRICS.csv`包含815个方法—帧评价记录；`evaluation/per_view`本地保存逐方法帧JSON，`figures/details`提供全部55个005帧的统一投影，不删差帧。
