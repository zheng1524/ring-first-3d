# 完整失败与不确定性

| 对象 | 步骤 | 状态 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 004 | C_surface_topology | EXPERIMENTAL | 586 nonmanifold edges, boundary length not improved | [metrics/topology.json](metrics/topology.json) |
| 005 | C_surface_topology | EXPERIMENTAL | 1993 nonmanifold edges; no clear held geometry improvement | [metrics/topology.json](metrics/topology.json) |
| 004/005 | TSDF | NOT_DEFAULT | thin boundary proxy ray fraction .289/.296, lower than raw multiview .563/.661 | [metrics/ray_evaluation.json](metrics/ray_evaluation.json) |
| 005_745 | new_coverage_validation | UNKNOWN | 3613 far-old model points; only46 self-consistent, no independent new-area GT | [metrics/surface_model_coverage.json](metrics/surface_model_coverage.json) |
| 004/005 | cross_source | UNVERIFIED | frozen H not newly certified; layers only | [metrics/cross_exploratory.json](metrics/cross_exploratory.json) |
| 004/005 | black_Ring_MVS | UNVERIFIED | MVS Ring depth has large tails; use fixedCAD as prior, not copy depth to Polyp | [metrics/Ring_depth_diagnostic.json](metrics/Ring_depth_diagnostic.json) |
| evaluation | initial_face_adjacency | CORRECTED_METRIC_PRESERVED | Trimesh adjacency ignored nonmanifold edge incidences; all-edge metric added; no prediction changed | [diagnostics/initial_face_adjacency_metric/](diagnostics/initial_face_adjacency_metric/) |
| export | first_import | FIXED_NO_GEOMETRY_CHANGE | same-named historical evaluate module shadowed unused import; removed unused import | [logs/export_initial_import_failure.log](logs/export_initial_import_failure.log) |

## 坐标、尺度和置信边界

工作RGB640×360，K=(490,490,319.5,179.5)，D未知，沿用冻结候选0，不重新标定。深度是相机轴向Z、毫米；c2w把相机点变到各自视频的Ring局部坐标。Ring R10中心线半径5.6mm、截面半径0.6mm，完整torus为固定物理先验，不是MVS成功恢复黑环的证据。环平面不作为息肉基底。004/005的平面内yaw规范保持独立。

GLB按规范导出米：`p_GLTF=p_mm/1000`，H中的平移仍以毫米记录。跨视频同一个H作用于005全部物体、Ring和相机，未独立调整息肉、缩放、ICP或非刚性修形。两套跨视频候选始终UNVERIFIED。

状态区分：`MODEL_PREDICTED`；`MULTIVIEW_MODEL_CONSISTENT_POSE_CONDITIONAL`；`SPARSE_FEATURE_SUPPORTED_POSE_CONDITIONAL`；`UNKNOWN/CONFLICT`。多视图预测共用模型和相机，模型自一致不等于独立几何真值；独立轨迹支持仅限实际采样点，不向整个三角面传播。[逐点来源](provenance/)、[全查询](metrics/feature_queries.csv)、[完整指标](metrics/)、[复现配置](config.json)。

## 固定审计表

| 审计项目 | 必须汇报 |
| --- | --- |
| 目标组数 | 1个真实静态测量组，两段视频004/005独立；6个参考视角、2种对象的单视频融合、2套探索跨视频H |
| 本算法独立成功 | 6/6深度输入可用（复用5，新HERO1/1）；4/4对象C融合和4/4对象TSDF产生数值表面；两视频独立新融合2/2。真实绝对几何准确性UNKNOWN |
| 本算法失败 | C有非流形边；TSDF损失薄区域；可信新增表面未证实；跨视频正式认证0/1、正式H全NaN，不执行新配准 |
| 历史测量值回退 | 0。旧HERO是本轮明确授权的冻结输入，非失败补齐；历史单/多参考Mesh单列对照 |
| 失败组及具体原因 | DEV004/005：系统深度错层、薄边界缺失、拓扑问题与相机不确定性；详见[FAILURES.md](FAILURES.md)及[失败表](failure_ledger.csv) |
| 最终统计样本 | 两视频原Polyp像素/点分母51382/47461；各方法同分母。独立观察全查询541条/方法，5方法共2705记录，NaN保留；两个跟踪家族不冒充相互独立物理点 |
| 是否使用GT选择算法 | 否。无真实3D GT；不读取Blender GT、历史直径、Mesh配准GT。参数/输入/融合预测先冻结；评价不反调参数 |

真实GT不可用：绝对深度MAE、Chamfer到真实形状、真实新增面积、真实高度/体积及物理指标相对误差均为UNKNOWN。可计算的模型相互差异、像素残差均保留n、median、MAE、p95、max，不能冒充GT精度。未修改DXY-MID、未训练、未删/移/压缩旧资产；保留用户原有未提交修改。未新增清理候选。
