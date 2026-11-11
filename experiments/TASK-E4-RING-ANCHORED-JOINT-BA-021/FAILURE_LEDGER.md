# 021 失败与不确定性台账

| 项目 | 真实证据与处理 |
| --- | --- |
| 特征缓存字段适配错误 | 准备期KeyError desc，实际缓存键为des；正式freeze之前修正，553条描述子及547链接逐项核对，无原数据修改 |
| 执行中断 | B1进程随会话中断退出，无数值错误trace；ITER030恢复q/X/Adam，旧INITIAL和首次预注册保留，累计耗时给下界而非伪造精确墙钟 |
| 严格旋转矩阵检查失败 | SENS_B2_020R2继承历史R2正交误差5.17e−8和det偏离3.07e−8，1e−9检查失败；冻结矩阵不变，阈值不放宽。全部检查继续收集，不把失败改为PASS。FROZEN_ROTATION_NUMERICAL_AUDIT保留所有历史/新矩阵及正确SE3增量的独立数值 |
| 优化后期停滞 | 各路线真实接受数/拒绝原因见运行表；保留整个100次轨迹。终点影子分解q/X提案，只诊断不提交结果，不把停滞说成科学否定BA |
| 非零点漂移不等于正确 | 地标只是RGB支持，背景重复纹理/高光/固定相机误差仍可能；协方差未校准；原独立3D差不能等同错匹配 |
| 仅背景共同地标 | 18条全背景，没有Polyp同名三维纹理锚；类别权重无法创造缺失观测；全部实际帧保留但部分SIFT方向/帧N0 |
| 独立轨迹检查缺方向风险 | 未参与源track和目标同像素均排除；若某方向N0，双向F明确NOT_EVALUABLE，不以0报改善；完整每帧N0/来源保留 |
| 原生HERO不是物理GT | 四组TRUSTED有噪声/错层/未知；后方可为正常自遮挡，前方也只是代理，不能自动删除或宣称错误双层 |
| G03长柄仍失败 | 真RGB有长柄Mask，HERO有长条片，主体仍短棱/翼；首层错误/未命中与来源不一致共同记录，新增命中可能数毫米错误，不声称已恢复 |
| G05/G06继承CAD相交 | B0/B2 FCL相交和微小负距离均如实记录；不以数值容差调高制造无碰撞PASS |
| G06局部质量 | B2边长伸长/面积压缩虽无非邻接自交，仍属局部形变质量问题，不通过平滑显示掩盖 |
| 补充覆盖图RGB背景归一化 | 初版将uint8 RGB乘0.4后作为float显示而被imshow截断；已仅修复为RGB/255再变暗，旧图保存在provenance/coverage_RGB_display_before_normalization_fix，深度/Mask/指标未改变 |
| 基底不确定 | G05等WEAK基底保持；估计平面/推断底盖非真实观察，主体模型Hmax不是实际测量精度 |
| 面积/覆盖代理限制 | 累计来源面积重复计数；0.25mm面心格依赖离散和格相位，不是去重解剖面积；灰色未知不是零误差 |
| 历史祖先独立性 | 本轮保护视角不进BA；018/014祖先可能曾使用部分评价图，不宣称端到端从未接触；HERO来源共享RGB不当独立统计票 |
| 缺绝对位姿GT | 绝对姿态/测量MedARE、MAE、P95、Max均NOT_EVALUABLE，不用旧Dxy或历史模型回退填值 |
| 其他视频缺资产 | 真实清单见OTHER_VIDEO_ASSET_INVENTORY，MISSING按具体RGB/Mask/相机/HERO/SIFT记录；本轮不新恢复其相机或推理HERO |

| arm | accepted | rejected | rejections | max_X_displacement_mm |
| --- | --- | --- | --- | --- |
| B1 | 16 | 84 | {'FULL_FIT_OBJECTIVE': 84} | 0.000000 |
| B2 | 30 | 70 | {'FULL_FIT_OBJECTIVE': 70} | 0.290942 |
| B3 | 21 | 79 | {'FULL_FIT_OBJECTIVE': 79} | 0.281908 |
| NEG_B1 | 5 | 95 | {'FULL_FIT_OBJECTIVE': 95} | 0.000000 |
| NEG_B2 | 8 | 92 | {'FULL_FIT_OBJECTIVE': 92} | 0.114765 |
| NEG_B3 | 5 | 95 | {'FULL_FIT_OBJECTIVE': 95} | 0.070337 |
| SENS_B2_LightGlue | 24 | 76 | {'FULL_FIT_OBJECTIVE': 76} | 0.186977 |
| SENS_B2_020R2 | 22 | 78 | {'FULL_FIT_OBJECTIVE': 78} | 0.205265 |

全部原始负结果、错误区域原面ID、数值未命中和Unknown均保留。个别代理下降不等于绝对真误差增加或路线被否定。
