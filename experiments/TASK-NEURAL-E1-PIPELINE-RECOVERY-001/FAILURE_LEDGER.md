# E1 失败与限制台账

本表区分新合同失败、旧失败复核、输入不合格、未执行及工程兼容错误。全部模型运行数为0；测量结果均为NaN。

| ID | 组/视频/步骤 | 类型与具体原因 | 证据与图 | 处置 |
| --- | --- | --- | --- | --- |
| E1-SDF-01 | G01 004/005 / C1.2 official sampler / mask | `ADAPTER_INVALID`：旧近端sphere clamp可在表面前吸收；全射线weights.sum又被终端吸收强制饱和，不能当Polyp轮廓 | [数值/原始证据](metrics/SDF_GATE_STATUS.json)；[可视化](figures/Fig2_SDF_domain_gate.png) | STOP_SDF_BRANCH；NaN |
| E1-SDF-02 | G01 004/005 / C1.2 official components | `BLOCKED_STATIC_ANALYSIS_ONLY`：ErrorBoundSampler/LaplaceDensity/MonoSDFNetwork真实组件含CUDA/网络调用；仅执行NumPy等价几何，未伪造官方运行 | [数值/原始证据](provenance/SDF_OFFICIAL_SOURCE_BEHAVIOR.json)；[可视化](figures/Fig2_SDF_domain_gate.png) | separate review required；NaN |
| E1-SDF-03 | G01 004/005 / C1.2 candidate uniform fraction | `LIMITATION_NOT_RELAXED`：48个候选×源×类别行中44行未达预冻0.95均匀样本球内比例；末端吸收样本仍计入分母，未改阈值换PASS | [数值/原始证据](metrics/SDF_RAY_DOMAIN_SUMMARY.csv)；[可视化](figures/Fig2_SDF_domain_gate.png) | retain raw denominator; do not train；NaN |
| E1-M3-OLD | G01 005 / C1.3 old M3 recheck | `OLD_METRIC_FAILURE_NOT_NEW_RUN`：固定CAD中位偏差22.35/21.94mm；第二视角pose平移残差9.94mm | [数值/原始证据](metrics/E0_M3_FAILURE_RECHECK.csv)；[可视化](figures/Fig4_Map_legal_geometry_adapter.png) | do not adopt output pose；NaN |
| E1-004 | G01 004 / C0 source identity | `C0_LIMITED`：参考身份以归档图SHA成立；raw顺序编号未认证，004/005跨视频变换未认证 | [数值/原始证据](metrics/E1_SOURCE_MANIFEST.csv)；[可视化](figures/local/G01_004_failure_evidence.png) | same-video only；NaN |
| E1-G06 | G06 004 / C0.2 holdout | `KNOWN_HERO_INPUT_LEAKAGE`：raw00351曾输入G06_004_ref04 HERO | [数值/原始证据](provenance/SOURCE_LEAKAGE_LEDGER.csv)；[可视化](figures/local/G06_004_failure_evidence.png) | DIAGNOSTIC_ONLY；NaN |
| E1-G07 | G07 004 / C0.2 camera and holdout | `UNQUALIFIED_STRESS`：相机不合格；raw00293曾输入G07_004_ref04 HERO | [数值/原始证据](provenance/SOURCE_LEAKAGE_LEDGER.csv)；[可视化](figures/local/G07_004_failure_evidence.png) | stress only; exclude normal success；NaN |
| E1-G08 | G08 005 / C0.2 holdout | `LIMITED_STRESS`：raw00943/raw01080无预冻结严格独立留出证据 | [数值/原始证据](provenance/SOURCE_LEAKAGE_LEDGER.csv)；[可视化](figures/local/G08_005_failure_evidence.png) | diagnostic only；NaN |
| E1-PHOTO | G01 photo001/002/003 / C0.2 photo | `DATA_INELIGIBLE_FOR_METRIC_RECON`：真实图像/匹配存在但K/pose未认证 | [数值/原始证据](provenance/PHOTO_QUALIFICATION.json)；[可视化](figures/Fig1_scene_source_DAG.png) | no metric camera fabricated；NaN |
| E1-STRICT | ALL4 ALL5 / C0.2 leakage | `HOLDOUT_STRICT_UNAVAILABLE`：0严格全流程留出；历史曝光不能事后重新分组消除 | [数值/原始证据](provenance/SOURCE_LEAKAGE_LEDGER.csv)；[可视化](figures/Fig1_scene_source_DAG.png) | no blind-test claim；NaN |
| E1-ENGINEERING-01 | N/A N/A / SDF CPU integration | `RUNTIME_API_COMPATIBILITY_FIXED`：NumPy1.x没有trapezoid；改用同义trapz，原日志与原源码冻结SHA保留，未更改科学容差 | [数值/原始证据](runtime/SDF_attempt001.log)；[可视化](figures/Fig2_SDF_domain_gate.png) | resolved CPU-only；NaN |

所有复放命令见 [REPRODUCE.md](REPRODUCE.md)。`figures/local/`、`runtime/` 为本地证据，不进入Git；远端四幅核心图包含对应组的分层、来源和旧故障概览。
