# RAW_VIDEO_PROVENANCE

**结论：在本环境中，"原始视频 → INIT 分割 → Mask" 这一前端不可执行。**

## 1. 检索结果

| 检查项 | 结果 |
|---|---|
| `/home/liu/**/*.zip` | 有 6 个 ZIP，均为研究包/标注包，**不是**十段原始视频 |
| `assets/protected_raw_data`（3.5 GB） | 内容为 `tf-imports/` 等无关包，**不是**本项目的视频数据 |
| `find /home/liu -maxdepth 3 -type d -name "*video*"` | 只有其它项目的视频目录（sam2、SAC-MPC 等） |
| INIT 权重 | `/home/liu/new-polyp-dxy/mainline/MAINLINE_MANIFEST.json` 明示 `"full39 raw inputs, full videos and model weights remain restricted"`；仓库内未找到 `*.pth/*.pt` 权重 |
| DXY 冻结 `C_joint` | 存在于 DXY 仓库，但只用于其自身主线，不能替代 INIT 分割 |

## 2. 影响

- **Step 1–2（原始视频解码、候选帧、INIT Mask、质量评价）无法执行。**
- 因此本轮所有相机/诊断结果都基于 **005 冻结的 Mask 与相机**，不是从原始视频重新生成。
- 这是**已声明的偏差**，不是静默替换：`metrics/PREPARE_STAGE_STATUS.csv` 中每条实例都标记
  `status=BLOCKED_RESTRICTED_WEIGHTS`，并记录当时的候选视频数与权重数（均为 0）。

## 3. 若要解除阻塞，需要

1. 十段原始视频（或 DXY 已解码帧）的可用路径与 SHA256；
2. INIT 分割权重（同一 SHA）与预处理配置；
3. 一份帧率/总帧数/分辨率清单，用于把 `raw_frame` 与历史缓存做像素级核对。

## 4. 已核实的输入身份

- 80 个 FIT 视角缓存：`metrics/INPUT_MANIFEST.csv`（005 产物，路径 + SHA256）。
- Ring CAD：R=5.6 mm, r=0.6 mm（`configs/unified_config.json` 中为全局常量，不按视频变化）。
- 内参：K=[[490,0,319.5],[0,490,179.5],[0,0,1]]，全部实例一致（005 已断言）。

## 5. 未做的事

- 未声称与历史缓存逐位一致（因为无法从原始视频重生成来比对）。
- 未用 DXY 主线结果替代 INIT 分割。
