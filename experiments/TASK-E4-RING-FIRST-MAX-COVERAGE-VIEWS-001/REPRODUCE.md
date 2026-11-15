# 复现与资产取得

工作树：`/home/liu/ring_first_3d_e4_sdf_localization`；基础及提交分支：`exp/TASK-E4-RING-ANCHORED-JOINT-BA-021`。本轮没有覆盖旧任务。

## 先查看冻结结果

```bash
cd /home/liu/ring_first_3d_e4_sdf_localization
TASK_RUN="$PWD/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001"
TASK_PY=/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python
"$TASK_PY" -B "$TASK_RUN/code/replay.py"
"$TASK_PY" -B -m http.server 8897 --bind 127.0.0.1 --directory "$TASK_RUN"
```

浏览器打开 `http://127.0.0.1:8897/G03_MAX_COVERAGE_VIEW_ATLAS.html`；其他三组同名替换组号。不要用 `file://` 打开，因为GLB/JSON读取需HTTP。界面支持来源、资格、数量、原始/新增HERO、Raw/Trusted/Unknown、Body/推断区和真实RGB。Three.js固定0.169.0通过jsDelivr加载；无网环境需缓存同版本模块并替换importmap，几何资产本身均在本地。

## 大文件没有上传GitHub，如何取得

原生深度、Mesh、Face/Pixel证据和GLB仅在本地数据存储。确切包路径、字节数、SHA见 `assets_index/SCIENTIFIC_OUTPUT_BUNDLE.json`。本地包为：

`local_results/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001_SCIENTIFIC_OUTPUTS.tar.gz`

同工作站可直接复制该文件至持久存储；远程研究者使用其已获授权的工作站SSH账号执行下面命令（`RESEARCH_USER/RESEARCH_HOST`是待替换占位符，不是已经开通的公共下载端点）：

```bash
scp RESEARCH_USER@RESEARCH_HOST:/home/liu/ring_first_3d_e4_sdf_localization/experiments/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001/local_results/TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001_SCIENTIFIC_OUTPUTS.tar.gz ./
sha256sum TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001_SCIENTIFIC_OUTPUTS.tar.gz
# 必须与仓库assets_index/SCIENTIFIC_OUTPUT_BUNDLE.json一致，再解压：
tar -xzf TASK-E4-RING-FIRST-MAX-COVERAGE-VIEWS-001_SCIENTIFIC_OUTPUTS.tar.gz -C /path/to/ring-first-3d/experiments
```

包内有原生新HERO、原始/四状态Mesh、全部相机匹配与描述子、选帧代理、独立评价、GLB、缩略RGB、用于47次推理的完整RGB/Mask缓存，以及只读基线Mesh/观测/RGB地图的可搬运副本。`assets_index/LARGE_ASSET_MANIFEST.csv`给出逐文件校验和与包内相对路径。**没有声称这些大文件已经Git上传，也没有虚构公开下载链接。** 不需要取得原始视频即可查看Atlas；完整从头恢复相机仍需原始私有视频及既有坐标/地图资产。

原始视频/照片身份及SHA见 `config/SOURCE_DISCOVERY.json`、`config/RAW_CAMERA_CANDIDATES.json`，来源为 `/home/liu/polyp_research/smart_endoscope_20260805/raw/`。G01/G03/G05/G06分别为 `GP_Ip_12.0mm_closed_R10_single_refY`、`GP_Ip_20.0mm_closed_R10_single_refY`、`GP_Is_18.0mm_closed_R10_single_refY`、`GP_IIa_14.0mm_closed_R10_single_refY` 的004/005.mp4及001/002/003.jpg。它们不随Git分发，需从研究者原始数据存储按清单取得；旧同名20260415照片不能替换。

## 环境与官方HERO

复用当前已安装环境，不安装大型新框架。版本见 `provenance/ENVIRONMENT.json`：OpenCV/SIFT、PyTorch、Open3D、SciPy、PyCeres2.6/Ceres2.2。`runtime/packages`指向同工作树上一轮U的已有PyCeres依赖。官方源码/loader路径、SHA、commit和checkpoint信息见 `provenance/HERO_MODEL.json`、`provenance/READ_AND_REUSE_RECEIPT.json`。

官方checkpoint下载地址（如需在新设备恢复，由研究者自行下载并核验）：
`https://storage.googleapis.com/niantic-lon-static/research/mvsanywhere/mvsanywhere_hero.ckpt`

SHA256：`00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d`。不在包中重传权重。原始官方代码固定commit见HERO_MODEL；只复用既有完整loader，实际每目标3支持图，不能把opts里的num_views当成实际输入数。

## 实际执行顺序

本轮已执行完，不要在冻结目录重跑相机优化、覆盖写入或替换预测。实际命令日志在 `runtime/logs/`，阶段入口如下：

1. `discover.py`：完整帧发现；`segment.py`：501新增Mask。
2. `cameras.py G01/G03/G05/G06`：原Ring五维/RGB；`register.py GROUP`：共享/联合Ceres。
3. `native005_extension.py`：补G01真实005地图；`final_pool.py`：恢复全部HOLDOUT身份；`held_map_audit.py`：冻结后地图坐标核查。
4. `coverage.py GROUP`：正式结果在 `selection_verified/`；`selection/`是保留的失败初轮，禁止冒用。
5. `verify.py`：50项测试；`infer.py`：47真实官方推理；`clean_native.py`：冻结017分类。
6. `evaluate_geometry.py`、`evaluate_cameras.py`、`historical_camera_audit.py`（相同地图与各自H的命名历史对照）、`post_freeze_audit.py`、`solver_audit.py`、`lineage.py`。
7. `figures.py`、`atlas.py`、`deliver.py`、`archive.py`。

若要重新求解，应创建同仓库下新的独立实验副本，复制code和冻结配置，建立空输出目录后再运行。所有父输入只读。当前脚本中`N`由自身位置确定；`context.py`保留明确的历史源路径。原始输入或软件版本改变时不可宣称逐字节复现。精确原预测以包内SHA为准。

若仅复核官方推理，使用 `code/reproduce_frozen_inference.py` 在**独立副本**中读取本轮冻结计划和 `local_results/selected_inputs`，不需要重新跑884相机或选帧。说明见该脚本`--help`。不允许把重新投影旧深度当新推理。

## 指标与失败

深度是camera axial Z/mm；像素误差在640×360工作坐标，HERO原生352×640 Kn带半像素映射。表面积是累计来源或明确命名的voxel/normal-bin代理，非唯一解剖面积。`known`、前方分歧、后方可遮挡、CAD遮挡、UNKNOWN分别报告。E4另提供固定共同native像素与共同可见分母。

`HERO_eligible`表示相机组合条件；实际每目标3支持图已验证、已推理的46个目标以HERO_PLAN及NEW_HERO_SOURCE_MANIFEST为准，不能把550个相机候选都说成已验证MVS支持图组合。

所有GT绝对精度NOT_EVALUABLE。没有Body更新、ICP、HERO融合或DXY改动。最终报告必须连同失败和NaN一起阅读。
