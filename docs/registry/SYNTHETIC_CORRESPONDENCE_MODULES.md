# G0–G1 受控合成对应模块注册

任务 TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001，基线 fc63df356a577c61de75912b136f92d7f7b15e9d。只注册本任务的 schema 2、来源和角色，不改变 schema 1 的无 GT 契约，不授权 G2/优化/训练/BA。源码完整 SHA 冻结于 TASK 的运行指纹，阶段内生成文件另有 SHA 清单。

| ID | 入口 | 角色与复用 |
| --- | --- | --- |
| S01 | src/ring_first_3d/synthetic/scene.py；export_g01_blender.py | generator：真实 G01 `.blend`；复用原 export_blender_gt.py 的 evaluated-world 变换/三角化 AST，现场导出与登记缓存一致；身份与米→毫米固定 |
| S02 | synthetic/raster.py | generator/predictor：复用 T24 tensor/mesh/PyTorch3D 与 OpenCV 相机契约；硬 Pixel-to-Face + barycentric；独立 Open3D 全像素射线定义观测分母 |
| S03 | synthetic/correspondence.py；synthetic/handlers.py | predictor：三维最近三角面、像素 Face/重心对应、CAD 首次遮挡；不更新 Body。误差只在生成端注入，预测只收受扰深度/相机与公开 Body |
| S04 | synthetic/evaluate.py | evaluator：在预测 SHA 冻结后读取私有真值和真相机；误差注入独立复核、逐点材料对应误差、覆盖、配对和独立 Oracle |
| S05 | synthetic/visualize.py；synthetic/artifacts.py | evaluator/controller：实际几何、位移、Face ID、barycentric、对应点、失败图、固定毫米轴/色标和离线本地首页 |

阶段：preflight→contracts→research_regression（原 35 加新增测试）→G0_prepare→C0_smoke_predict→C0_smoke_evaluate→C0_predict→C0_evaluate→C1_predict→C1_evaluate→C3_predict→C3_evaluate→G1_visualize→artifacts。每一阶段须有完整前置 PASS，失败停止；G1 后只允许验收与报告，不自动进入扩大矩阵或主体优化。

G0 的公开 Body 是真实 G01 GT 网格的精确受控副本，仅服务此合成校准实验，不能冒充独立重建/GT-free 初始化。真实部署位姿未知，本实验固定作者原生 canonical pose，不使用 GT 配准或历史主体预测。原始 GT、真相机、真深度、面 ID 与重心点位保存在 private；预测进程拒绝读取 private、原始相机缓存、GT 源和先前评价目录。

初步科学结论需要人工审阅：Pixel-to-Face 能隔离已校准相机下的轴向深度偏差；位姿扰动会破坏像素对应，Ring 过滤也不能恢复真位姿。工程接口通过不改变既有科学状态。完整数值与失败证据见本任务报告；本模块状态为 G1_REPORTED_AWAITING_HUMAN_REVIEW。
