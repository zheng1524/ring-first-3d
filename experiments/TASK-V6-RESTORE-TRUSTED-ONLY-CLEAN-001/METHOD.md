# 历史 018 TRUSTED-only 方法恢复

历史依据：`exp/TASK-E4-HERO-BODY-ADAPT-018`，固定提交 `62c286fcbf39cbba9ec5adb148bd50ba9dc94093`。当前复用基准 `3b7b767a5ba51277584605304f462993f0396d14`。历史文件和逐文件 SHA 见 [IDENTITIES.json](evidence/history/IDENTITIES.json)；7 个核函数的 AST、阈值及 inherited_density 参数相同。本轮没有复制一套平行分类器。

| 环节 | 实际输入与输出／规则 | 代码与来源 |
|---|---|---|
| 输入 | 本轮完整落盘的单源 Raw PLY、原生深度、RGB/Mask、相机、Ring CAD；源身份在分类前冻结 | [SOURCES_FROZEN.json](config/SOURCES_FROZEN.json)，全量 manifest / PLAN_FROZEN / HERO_COMPLETE / INFERENCE_STARTS |
| 映射 | 实际原生 352×640，工作格 360×640。沿原 OpenCV 线性深度上采样定义恢复工作像素对应；保存最近原生像素和上下行／权重。K_native 与半像素 resize 内参一致；原 F 顺序及 float32 V 必须与原建面定义逐值匹配。分类及输出仍使用原 PLY 的 V/F | [surface_clean.mapped_input_for_source / native_mapping](../../src/ring_first_3d/v6_raw/surface_clean.py)；从既有适配段提取，尺寸来自资产，不新增建面过滤 |
| TRUSTED = 0 | 在冻结证据中既无警告、无未知、也无拒绝条件的原面；不意味着形状真值正确 | [classify / analyze](../../src/ring_first_3d/mainline/native/_clean_kernels.py)，017 |
| UNCERTAIN = 1 | 拉伸、跳深度、形状、密度、CAD材料、竞争、边界、小分量或非流形等警告；后续未知／拒绝覆盖此状态 | 同上；原边界邻接面本身就触发警告，因此可信筛选必然收缩开放边界 |
| UNKNOWN = 3 | 原生Mask绑定不足、切面估计不可靠、入射余弦过低，或合法CAD遮挡；**证据不足，不等于已证实错误** | 同上；正常薄结构与遮挡面也可能落在此类 |
| REJECTED = 2 | 严重透视与切面拉伸、跳深度、异常三角形／法线且处于边缘情境并非未知；或CAD材料内采样矛盾结合跳深度／形状条件并非未知 | 同上；冻结阈值为透视8、切面4、深度0.5mm、质量0.15、法线一致0.7／邻角65°、边缘2原生像素、入射0.2；完整定义见 [协议](../../src/ring_first_3d/mainline/native/cleaning_protocol.json) |
| 冻结 gap 补充 | 原生格上的两端排除端点外向片：每侧至少6/8有效像素，逆深度平面拟合；残差≤0.125mm，双向外推差>0.5mm，切面比>4、入射≥0.2。确认原生边后，归档面还须满足冻结形状、情境、Mask、可见性、跳深度及透视条件才改为2；两侧共享HERO预测，不是独立观测 | [classify_native](../../src/ring_first_3d/mainline/native/cleaning.py) → patch_plane / gap_edges；017冻结规则、018 clean018.py 的原表达式 |
| 实际输出 | 只取完整 Raw 的 `F[state==0]`；保留全原V、原Face/Vertex ID，另存所有排除面及四态／原因位。无坐标变化、平滑、补洞或重网格 | [trusted_restore.trusted_subset / run](../../src/ring_first_3d/v6_raw/trusted_restore.py)；018 `trust=state==0` |
| 统计和图 | 逐面面积、共享整条边的面连通分量、Raw/四态/实际子集；同一Raw+CAD完整范围与两个固定视角，RGB不变、CAD黑色 | 同文件 stats / render；复用 existing actual_mesh_image，渲染源码SHA见 [RENDER_RECEIPT](evidence/RENDER_RECEIPT.json) |

本轮执行完整分类和 gap，没有先套 C1，没有调用 OBS_TRUSTED 的额外观测资格条件，没有运行 Body。GT 和深度 MAE 不参与任何门控。历史 classify_native 顺带导出的 Conservative/Unknown/Uncertain 文件仅作原分类的本地中间产物；本轮主交付是 `TRUSTED_ONLY.npz/.ply`。`state!=2` 不是本轮目标，`state in {0,1}` 只记录诊断数量。

实际4源 gap 确认边为0、REJECTED为0。这个零结果被完整保留；图中减少的面均由排除 UNKNOWN/UNCERTAIN 产生，不能写成已识别错误面的清除率。
