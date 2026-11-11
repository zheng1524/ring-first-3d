# 实际算法、目标和实现对照

| 原设计 | 实际实现 | 差异/限制 |
| --- | --- | --- |
| 原021共同BA目标 | `solver_review.one`直接调用原`BA.evaluate` | 数据18/553、全部52FIT、权重不变；q仍相对原RoMa、X prior仍相对原X0，不能在终点重置先验 |
| 成熟求解器 | SciPy `minimize(method=L-BFGS-B,jac=True)` | 25iteration/90evaluation软预算、12line-search；使用原完整AD。原耦合SE3/点范数/白化/正深度域以Infinity不可行域保持，非新增可行loss；外包盒覆盖原域 |
| 参数化 | 原6维q + (X−X0)/0.6mm | 只是变量尺度变化，梯度按链式乘0.6；不新增相机/尺度/观测 |
| 目标复现和梯度 | `solver_review`、`gradient_isolation` | 3次固定值重复；中心FD h=.01/.001；分离平滑SIFT/prior与Ring，未修复后冒称同一目标。完整Ring梯度未通过 |
| 独立评价 | `evaluate_review`调用原020/021评价组件 | 先冻结，统一52FIT+3HOLDOUT、全部固定21HERO源；共同比较同原生ID，不按条件均值选结果 |
| 照片身份 | `photo_assets` | 显式raw20260805路径/源SHA/原生Mask，拒绝旧同名采集；VIDEO_FRAME/INDEPENDENT_PHOTO分开 |
| Ring初始化 | `photo_registration.ring_initial` | 复用成熟Ring-First decode/image_seeds/solve，四个保留种子；解析实体圆环轮廓+材料/背景区域，保留绕轴/法向对称候选，不是完整pose认证 |
| 照片SIFT/位姿 | `source_banks`、`one` | 只提取三照片SIFT，复用153/980地标原RGB描述子；真实ID追溯，固定PHOTO_HELD，PnP不复制视频外参；005源只施加固定B3 |
| 照片精修目标 | `photo_registration.loss` | 成熟V5 Mask-region/轮廓 + 可见typedI/O .05 + SIFT .2 + posePrior .01；Huber3px、按源视频和观测数归一，least_squares线性外层；这与原BA的P3D软Mask不是同一个目标，明确分开 |
| 仅2D补充 | `photo_2d_geometry` | Sampson替代不可用2D3D时明确标注，OpenCV Essential+Ring距离生成候选、最多2个45nfev；不生成共同XYZ。原PnP FINAL不覆盖，不用held/body选择 |
| 相机评价 | `photo_audit` | 真实CAD三角面独立光栅、DXY原Mask支持点；PHOTO_HELD误差和种子差，原Gate标签不自动否决。K490是沿用同设备假设，非新标定 |
| HERO | `hero_prepare` | 官方权重SHA通过，仅准备；新相机门禁失败所以未推理，017 TRUSTED子集不伪造；无模型训练或权重更新 |

照片强监督门禁在正式照片拟合前以旧成熟3px/6px协议固定；源身份纠错不更改阈值。PHOTO_HELD=featureID%5==0，不是021历史8个整图HOLDOUT。解析圆环用于照片求解，最终用原完整三角面CAD独立评价；原BA的PyTorch3D目标完全保留。未知/Polyp遮挡区域不作为已知Ring不存在证据，Mid拟合曲线是诊断、不是完整可见物理边界。I/O采用原Mask≤2.5原生像素回溯，预处理外推点另存，不混作真实观察。

Ring纯绕轴本身不提供唯一yaw，新增真实图像特征对照片yaw给出数值约束，不认证绝对角度。照片没有HERO，因此当前没有可归因于照片的可信深度梯度；未做主体optimizer.step()。未来单主体适配应显式记录每来源Mask/HERO分量梯度和实际作用面，而不是将未观测深度填0。

照片匹配独立性复核：各视频PnP内部的地标和照片feature ID均唯一；合并004/005后，001的50个FIT观测对应46个独立照片像素、002的44个对应42个、003的15个对应15个。同一照片像素在两套独立三角化地标中重复出现，并非完全独立证据；原视频归一化仍保留，未改变冻结优化。PHOTO_HELD对应数量同样是观测数而非独立物理点数。详见metrics/PHOTO_INLIER_IDENTITY_INDEPENDENCE.csv。多种子精修各自以PnP为先验中心，所以FIT目标排序包含种子先验差异，不能据此认证唯一最优姿态；最终均未获强监督资格。
原生图1920×1080；照片Ring/SIFT重投影统计均为640×360工作像素，原生边界吸附阈值2.5px单独在原图定义。FD仅测试登记的位姿0/2/4轴和共同点X等方向，不冒称对全部60参数逐元素穷举。
