# Official NeuralFusion pipeline audit — actual 26-run evidence

官方仓库：https://github.com/weders/NeuralFusion ，commit `4f0c14f67ad9d2368b68cbeb78c237a6328971e5`，匹配ShapeNet noise005 config/checkpoint；24份历史核验文件中的实际使用模块再次逐SHA核对，见provenance/OFFICIAL_CHECKED_FILES.json。上轮F0也确实运行了Translator；历史未运行F1/F2是旧质量停机规则，不能解释为Translator缺失。

本轮G01正/逆8+8、G06正/逆5+5，共26次。每个metrics/*_RUN.json的actual_official_call_events均严格为`_extractor, _fusion, _integrator, _translator`。通过只读转调原bound forward方法记录真实输入/输出shape（不依赖会被直接.forward绕过的hook）。Translator点数等于对应非零latent known体素数，未替换为占据阈值或点云。全部1,403,920参数strict加载，逐前缀与checkpoint state_dict逐tensor bitwise相等，无optimizer、无梯度、无训练。

get_translation只提取官方training/utils.py中的该函数AST，不导入训练/dataset/GT数据库。128³使用全known同批Translator，未改变count归一范围；17维latent最后通道是官方use_count计数，外部count数组保持0属于官方配置行为，不是漏写状态。正/逆初始latent及count都为0，Integrator reset，序列前缀共享更新状态。

原始sdf_raw/occupancy_raw/known与MC正哨兵副本分别保存。unknown容器0是未查询，不是网络零SDF，也不是可靠自由空间；仅MC副本unknown=+0.04遵循官方mask导出意图。该处可制造封闭壳，保留原样并逐面all8-corners-known标记。全量Mesh没有因未观测/推断/unknown而删面。

Marching Cubes iso0，浮点插值顶点，毫米`vertex_index/128*L+O`；CPU逐一重放26个field，顶点/面与保存MC身份完全一致。raw/flat/smooth-normal PLY全部相同P/F，GLB单位米回转<1e−5mm。平滑仅插值法线，未几何平滑/补洞/缩面。详见metrics/MESH_EXTRACTION_AND_SHADING_AUDIT.csv及FINAL_INVARIANTS.json。

本轮所有网格有0开放边、0非流形边且watertight，不等于完整真实组织；局部窄带及unknown正哨兵倾向形成壳。G01最终约40.34%面邻接unknown，G06约57.02%。G01 ref08绝大多数bad首交点却来自all8-known单元，因此unknown封闭不是唯一机制。保留三类可见监督代理、跨来源冲突、实际多交点及原始Mesh供审阅，没有修改网络输出制造PASS。
