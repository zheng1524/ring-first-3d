# E3-A FAILURE LEDGER

审计完成不删除未解决项；失败不能靠重定义资格制造PASS。本轮没有测量，四主物理组测量值均NaN。

| ID | 层级 | 对象 | 具体原因 | 处理/状态 | 证据 |
| --- | --- | --- | --- | --- | --- |
| F01 | 科学资格 | G01_004 | 3参考筛查通过但全部上游含候选相机；其余8参考未合格 | CONDITIONAL / 未修相机 | Fig1; E3_CAMERA_QUALIFICATION.csv |
| F02 | 科学资格 | G01_005 | 8参考上游均非候选，但同表面对应和绝对公制真值未认证 | CONDITIONAL | E3_VIEW_COVERAGE.csv |
| F03 | 科学资格 | G06 | 4/5参考筛查；上游仍各含候选 | CONDITIONAL | Fig1; camera CSV |
| F04 | 科学资格 | G08 | 2/6参考筛查，LIMITED且上游有候选 | LIMITED CONDITIONAL | Fig1; camera CSV |
| F05 | 科学资格 | G07 | 0/5参考筛查合格，不能进入正常成功分母 | UNQUALIFIED_STRESS | Fig1/3 |
| F06 | 来源 | 照片/跨视频 | 3张照片无认证K/c2w；G01跨视频fusion_certified=false | 不公制融合 | CROSSVIDEO_GATE历史哈希; PHOTO manifest |
| F07 | 物理对应 | 全部组 | 同表面独立标签缺失；投影残差/循环/历史匹配不能单独认证 | A类认证0，保留C | E3_CASEBOOK_POINTS.csv |
| F08 | 结构真值 | 全部组 | 长边、小片、thin/stalk均为代理，无人工解剖确认 | NOT_EVALUABLE | Fig3; 原面定位CSV |
| F09 | 独立评价 | 9候选目标 | HERO/相机/历史匹配/选择暴露；严格全链路独立帧0 | FULL_PIPELINE_INDEPENDENCE_NOT_AVAILABLE | E3_EVALUATION_FRAMES_FROZEN.json |
| F10 | 公平比较 | 历史方法 | F1/F2/F3输入集不同，过滤F3输出不能恢复共同输入重放 | 共同输入重放NOT_RUN | E3_BASELINE_INPUT_SCOPES.csv |
| F11 | 输入缺口 | 额外Is/R5 | 有界目录额外合格Is/R5=0；4补充HERO链/原索引未达主目录资格 | 不强行扩正式组 | manifest supplemental rows |
| F12 | 可见性 | 全部组 | 正Mask射线可能落在CAD后方；几何/相机/分割矛盾未决 | 与无原面首交分列，非自动合法遮挡 | Fig3/4; E3_OBSERVED_WITHOUT_TRIANGLE.csv |
| F13 | 未知区域 | 全部组 | 没有全解剖与全部认证视线身份，不能确定真实隐藏面 | Unknown保留，不补全 | Fig4; 全局合同 |
| F14 | 本地依赖 | 复现 | 原生深度/大NPZ/视频/PLY仅只读引用，没有全量上传 | 路径/SHA缺失应fail closed | INPUT_HASHES.json; REPRODUCE.md |
| ENG01 | 执行失败 | inventory attempt001 | 重复status关键字导致TypeError；未生成来源结果 | 修复字段名access_status，不改标准 | runtime日志摘要保留于EXECUTION_LOG_INDEX.json |
| ENG02 | 执行失败 | inventory attempt002 | 补充RESULTS.csv按group查找失败；实际主键为id | 修复精确主键；未改资格 | EXECUTION_LOG_INDEX.json |
| ENG03 | 执行失败 | geometry attempt001 | AST返回namespace未绑定face_components导致NameError，源几何数字输出前停止 | 显式绑定既有函数；无科学阈值变化 | EXECUTION_LOG_INDEX.json |
| ENG04 | 元数据修正 | RA access | 早期库存代码把文件存在等同read_complete | 修正为按阅读收据SHA；现两全文实际读完 | RA_READING_RECEIPTS.json |
| ENG05 | 绘图修订 | Figure2/4 | 完整长尾范围使主体过小；切片行距不足 | 增加统一±13mm主窗+完整范围小窗、调行距；不改数据/阈值 | FIGURES_LAYOUT002 log; FIGURE_PROVENANCE.json |
| ENG06 | 案例字段修正 | THIN_BASE_PROXY | 初次位置选择用了stalk或Ring保护并集，可能只代表Ring邻域 | 改为仅possible_stalk；无此代理则UNKNOWN，分别输出两种保护flag；未改评价门槛 | 初版CSV留runtime/CASEBOOK_POINTS_ATTEMPT001.csv；REV002记录 |

逐组证据：

| 组 | 可审查证据 |
| --- | --- |
| G01_004/005（同一物理组） | [相机逐源资格](metrics/E3_CAMERA_QUALIFICATION.csv) · [原面定位](metrics/E3_CASEBOOK_POINTS.csv) · [真实失败图](figures/Fig3_geometry_failure_cases.png) · [来源/视角图](figures/Fig1_sources_and_views.png) |
| G06_004 | [相机逐源资格](metrics/E3_CAMERA_QUALIFICATION.csv) · [原面定位](metrics/E3_CASEBOOK_POINTS.csv) · [真实失败图](figures/Fig3_geometry_failure_cases.png) · [来源/视角图](figures/Fig1_sources_and_views.png) |
| G08_005 | [相机逐源资格](metrics/E3_CAMERA_QUALIFICATION.csv) · [原面定位](metrics/E3_CASEBOOK_POINTS.csv) · [真实失败图](figures/Fig3_geometry_failure_cases.png) · [来源/视角图](figures/Fig1_sources_and_views.png) |
| G07_004 | [相机逐源资格](metrics/E3_CAMERA_QUALIFICATION.csv) · [原面定位](metrics/E3_CASEBOOK_POINTS.csv) · [真实失败图](figures/Fig3_geometry_failure_cases.png) · [来源/视角图](figures/Fig1_sources_and_views.png) |

所有失败尝试日志保留在本地runtime，公开[小型执行索引](provenance/EXECUTION_LOG_INDEX.json)保存退出/原因和日志SHA。没有从模型、历史直径或其他路线回退。未运行项目外部“Residual+TSDF”新实验；RA所述旧负面经验未在本轮冒充独立复核。
