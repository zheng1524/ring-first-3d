# E3-B FAILURE LEDGER

所有17源均计入分母；工程构建成功不能覆盖以下科学限制或失败假设。原失败日志保留本地，SHA与末行摘要公开。

| ID | 对象 | 失败/限制机制 | 处置 | 证据 |
| --- | --- | --- | --- | --- |
| S01 | B0/Raw不等价 | 原顶点入带率96.84–100%；部分独有Raw面不被B0活动窄带覆盖 | 未放宽0.25mm。B1原面保留；B0原生身份/差异并列 | [逐源资格](LOCAL_FIELD_QUALIFICATION.csv) · [独有面检查](metrics/UNIQUE_GEOMETRY_PRESERVATION.csv) |
| S02 | 有向距离资格 | 边界、掠视、法向不可靠/竞争时无完整物体符号；32重心候选筛查非全局唯一性证明 | 返回UDF/UNKNOWN_SIGN；有向值仅条件性局部意义 | [定义域](LOCAL_FIELD_DOMAIN_STATS.csv) · [真实场](figures/Fig2_local_fields.png) |
| S03 | G01_004 | 3参考仍含候选上游相机、跨来源物理对应未认证 | 只报告条件性结果，未调相机 | [输入资格](HERO_NATIVE_INPUT_MANIFEST.json) · [来源图](figures/Fig1_multiview_HERO.png) |
| S04 | G01_005 | 8参考非候选链仍非GT；原生/Raw重采样导致B0保护缺口 | 全8源保留，不删困难raw00745或RESERVED | [增量覆盖](SOURCE_COVERAGE_INCREMENT.csv) · [局部场图](figures/Fig2_local_fields.png) |
| S05 | G06 | 4参考有上游条件；growth_r01新增仅4格但不删除 | 全部保留原面，不把小边际当错误 | [完整来源](LOCAL_FIELD_MANIFEST.json) · [覆盖图](figures/Fig3_multiview_coverage.png) |
| S06 | G08 | 2参考LIMITED且上游候选 | 单列条件结果；不升级为绝对准确 | [输入表](HERO_NATIVE_INPUT_MANIFEST.json) · [结构图](figures/Fig4_real_geometry.png) |
| S07 | G07 | E3-A参考筛查0；本轮17正式源不含G07 | 继承UNQUALIFIED_STRESS身份，未构建不混正式成功率 | [父阶段资格](../TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001/metrics/E3_CAMERA_QUALIFICATION.csv) |
| S08 | 真实结构/精度 | 长边、小片、possible-stalk均无人工真值；独立全链路评价帧0 | NOT_EVALUABLE，数值身份保持不等于三维正确 | [结构证据](figures/Fig4_real_geometry.png) · [保护表](metrics/SINGLE_SOURCE_UNIQUE_REGIONS.csv) |
| S09 | 自由空间 | HERO/相机可能错误，正Mask与CAD也可能矛盾 | 条件证据，不作后方不存在/ROI入口外部硬约束 | [场域统计](LOCAL_FIELD_DOMAIN_STATS.csv) |
| ENG01 | 白名单初始化001 | 注册函数先哈希读取，守卫因尚未注册阻断首次原生NPZ | 修复为临时准入指定路径后哈希，失败撤回；未变来源/数值标准 | [执行日志索引](provenance/EXECUTION_LOG_INDEX.json) |
| ENG02 | 字段脚本001/002 | validate_local_fields.py两个append多余括号，解析失败；未运行场构建 | 修复语法；正式运行003记录保留 | [执行日志索引](provenance/EXECUTION_LOG_INDEX.json) |
| ENG03 | native别名 | 两个005旧native为未融合缩放包，非真正原生网格 | 追溯既存raw输出，禁止新推理；全部Raw深度链数值一致 | [原生白名单](HERO_NATIVE_INPUT_MANIFEST.json) |
| ENG04 | Fig3重叠标记 | 初版CORE阶段只按前一阶段判新格，未标同阶段多源重叠 | 改为同时统计活动源格重合；未改覆盖数值或构建标准 | [图来源](provenance/FIGURE_PROVENANCE.json) |

没有测量输出，沿用主审计四物理组的测量值均NaN，历史测量回退0。本轮不把“所有科学问题已解决”作为PASS定义。
