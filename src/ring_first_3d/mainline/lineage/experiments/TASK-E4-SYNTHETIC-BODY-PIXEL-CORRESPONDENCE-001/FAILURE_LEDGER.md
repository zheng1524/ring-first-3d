# G1 失败与限制台账

目标为一个 G01 / 004 视频，ref08、ref13、ref03 是 FIT，growth_r04 是 HOLDOUT。3 条件、每条件 24,531 个实际观察点，不将遮挡 GT 当作观测补齐。

| 阶段/条件 | 失败事实 | 已核验原因/边界 | 原始证据 |
| --- | --- | --- | --- |
| C0 | 无数值失败；max≈0.0001304 mm | 剩余 float32 射线/栅格差在预冻 0.001 mm 内 | PER_VIEW_METRICS.csv，03_errors_C0.png |
| C1 最近三角面 | 24,531 点均出数值，但只有 127 点在 0.1 mm 内；MAE0.760325 | axial Z+1 mm 的受扰点寻找最近面会滑向不同材料位置，不是最近顶点实现错误 | 02_injected_layers.png，05_correspondence_vectors.png，PIXEL_FACE_AUDIT.csv |
| C3 最近三角面 | 全部出数值，0 点在 0.1 mm 内；MAE1.290998 | 受扰位姿生成错误世界点，最近面不恢复其真材料身份 | 03_errors_C3.png，全点 evaluation NPZ |
| C3 Pixel-to-Face | 4,906 NaN；其余 MAE1.869378、max8.460369 mm | 右局部2°/0.5mm 导致估计相机射线偏移；Face=-1 为栅格无交点/边界无效。有限命中也可能是错误材料区域，不用 GT 自动重配 | 洋红失败区域、04_pixel_face_barycentric.png、全点 predictions NPZ |
| C3 Pixel+Ring | 5,729 NaN，额外823 CAD拒绝；最大误差未降低 | 估计相机下 Body 首次深度不在 CAD 前方。过滤不移动点，不能称为修正；共同成功点误差差为0 | 03_errors_C3.png，PAIRED_COMPARISON.csv |
| Oracle | 误差按潜在真材料点构造为0 | evaluator 专属、有 GT/真相机权限；不是可部署的独立重建结果 | TEST_RESULTS.json，独立真相机射线复核 |

C3 各来源无数值对应（Pixel / Pixel+Ring）：ref08 1007/1169，ref13 929/1098，ref03 1589/1852，growth_r04 1381/1610。每个无命中点均保留 NaN，Face ID=-1，barycentric=NaN。全部有限误差和超过2mm色标的8.46mm尾部仍在原数值表，不缩图/删点掩盖。

单位测试另发现硬栅格对共享三角边界可能丢像素，采用独立全图射线定义观测分母，保留缺口；真实 C0 四视角没有此类丢点。这个观察不是永久删除边界像素的规则。

源 GT 与真实部署位姿未独立关联：本实验采用作者原生 canonical pose=I，不做 GT 对齐/旧主体回退。GT 派生已知初始 Body 是受控校准假设，不是待验收的真实重建。GT/Ring 的具体相对放置也只代表此已声明合成场景，不认证真实临床接触或组织基底。

开发失败完整保留，均不参与正式统计：

- pilot-001：新增角色拒绝测试的临时 private 目录清理与 verification 门禁冲突；修正测试夹具清理，不开放 predictor GT 权限。
- pilot-002：C0/C1/C3 计算完成，但 G1 绘图的只读 fc-list 被命令门禁拒绝；仅对 G1_visualize 开放固定字体元数据查询。
- final-001：visualizer 计算与图像已提交，发布器错误读取旧 current 而非新 attempt；旧结果保留，改用已验证的新 attempt 元数据，新增原子发布回归。
- final-002：新增发布测试使用外指临时 symlink，外层 worker 门禁拒绝清理；改为本地副本夹具。没有修改科学参数或重配失败点。

所有源码变更均另建运行目录，未绕过旧 freeze；最终 delivery-001 50 项回归和14阶段通过。详细 traceback/回执在 [DEVELOPMENT_FAILURES.json](DEVELOPMENT_FAILURES.json) 与 development_failures/，原 run 下完整 attempt 仍存在。
