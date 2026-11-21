# 019 结果索引

本地根目录：`/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-POLYP-REGISTRATION-019`。

| 产物 | 位置 | 含义 |
| --- | --- | --- |
| 简洁结论 | TECHNICAL_REPORT_SUMMARY.md | 十项研究回答及固定审计表 |
| 完整指标与方法 | TECHNICAL_REPORT.md、METHOD_AND_INPUT_AUDIT.md | 全部A0–A5、负对照与实现偏差 |
| 完整输入68行 | INPUT_MANIFEST_COMPLETE.json/csv | 文件SHA、相机、图像身份、HERO与SIFT可用性 |
| 真正注册矩阵 | derived/T004_from005.json | R,t和逆，mm，尺度1，候选未认证 |
| 全005派生相机 | derived/VIDEO005_CAMERAS_IN004.json | 55个c2w，原相机未修改 |
| 所有候选及竞争终点 | results/、metrics/*SEARCH* | 原始法向规范、144角度、3个SE3终点 |
| 优化状态 | refinement/CROSS或NEGATIVE/seed0..2/ITER_*.pt | q+Adam，不是网络训练权重 |
| 完整日志 | *.log、refinement/*/*/HISTORY.json | 断点、接受/拒绝、数值异常 |
| 全逐帧评价 | metrics/ALL_FRAME_METRICS.csv/json | 815个方法—帧，目标00555帧全部保留 |
| 原分辨率预测 | evaluation/CROSS/方法/帧.npz | 640×360 body/Ring轴向depth与Mask |
| 特征与匹配 | features/、matches/、landmarks/ | 全真实feature ID、UV、RANSAC/地标轨迹 |
| 核心6图 | figures/Fig1..Fig6*.png | 实际数据，黑色实体CAD，mm |
| 全005视角详细图 | figures/details/All005_Projection_01..08.png | 全55目标视角而非挑选成功图 |
| 共同坐标诊断GLB | derived/G01_SHARED_SCENE_DIAGNOSTIC_NOT_FUSION.glb | 一份Ring、018body、21HERO独立组件、68个camera；非融合 |
| 派生005曲面 | derived/HERO_in004/*.npz | 8个TRUSTED来源，原F/面ID保留，刚体坐标副本 |
| Ring深度诊断 | ring_depth/*.npz | 22份原生/HERO/CAD/选择区域/残差；无被采用全图校正 |
| H0/H1诊断 | metrics/HERO_* | 固定分母、遮挡/未知、前方代理分歧 |
| 哈希与预测冻结 | provenance/ | 搜索前/精修前/留出前/最终完整性 |

所有大二进制及原数据保留本地，不上传视频/模型权重。`assets_index/LOCAL_RESULTS.json`提供本轮大文件路径、字节与SHA。Git提交源码、最终配置、指标、变换、精选核心图和小型真实匹配证据；完整匹配缓存依照源码及输入SHA复现。

无物理配准GT，绝对姿态误差/MARE/测量MAE/p95/max为NOT_EVALUABLE。图像轮廓与SIFT残差并非物理精度真值。历史A0涉及旧跨视频点云候选，仅对照，019生成不读取历史尺寸值回退。
