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

---

## 6. 阻塞已解除（2026-11-20 复检）

用户将原始数据复制到工作空间后，重新核查结果如下。

### 6.1 原始视频：可用

| 项 | 结果 |
|---|---|
| 位置 | `/home/liu/ring_first_3d_workspace/smart_endoscope_20260805 (1)/raw/` |
| mp4 总数 | 109（30 段临床 `分割_0xx` + 79 段体模 `GP_*`） |
| **十段实验视频** | 全部为**体模序列**（`GP_*_R10_single_refY_00{4,5}.mp4`） |
| 帧号语义 | `raw_frame` **就是视频帧号**（逐帧验证） |

**逐实例映射（`metrics/VIDEO_FRAME_MAP.csv`，用冻结 PNG 与解码帧逐像素比对）：**

| 实例 | 视频 | 匹配差 |
|---|---|---:|
| G01/004 | `GP_Ip_12.0mm_closed_R10_single_refY_004.mp4` | 0.0088 |
| G01/005 | `GP_Ip_12.0mm_closed_R10_single_refY_005.mp4` | 0.000 |
| G02/004 | `GP_Ip_4.0mm_closed_R10_single_refY_004.mp4` | 0.000 |
| G02/005 | `GP_Ip_4.0mm_closed_R10_single_refY_005.mp4` | 0.000 |
| G03/004 | `GP_Ip_20.0mm_closed_R10_single_refY_004.mp4` | 0.000 |
| G03/005 | `GP_Ip_20.0mm_closed_R10_single_refY_005.mp4` | 0.000 |
| G05/004 | `GP_Is_18.0mm_closed_R10_single_refY_004.mp4` | 0.0004 |
| G05/005 | `GP_Is_18.0mm_closed_R10_single_refY_005.mp4` | 0.000 |
| G06/004 | `GP_IIa_14.0mm_closed_R10_single_refY_004.mp4` | 0.000 |
| G06/005 | `GP_IIa_14.0mm_closed_R10_single_refY_005.mp4` | 0.000 |

**解码 RGB 与冻结缓存逐像素一致（`rgb_mean_abs_diff = 0.00`）。**

### 6.2 INIT 权重：找到官方本体，可复现 Mask

| 项 | 结果 |
|---|---|
| 权重 | `/home/liu/polyp_research/models/preserved_best_multiclass_overlapaware_20260405`（`model.safetensors`, `out_channels=3`） |
| 架构 | UNet3Plus / EfficientNet-B0，3 类 `{0:bg, 1:polyp, 2:ring}` |
| 预处理 | RGB → 256×256 双线性 → /255，无 mean/std |
| 推理环境 | `polyp_research` venv，`torch 2.7.1+cu128`（本机 CPU 推理即可） |

**复现检验（`metrics/MASK_REGENERATION_CHECK.csv`）：**

| view | label 一致率 | ring IoU | polyp IoU |
|---|---:|---:|---:|
| G02_v005_raw00104 | **0.9953** | 0.9346 | — |
| G02_v005_raw00211 | **0.9956** | 0.9352 | — |

即：**同一帧解码 → INIT 推理，可复现冻结 Mask 到 99.55%**；剩余 0.45% 集中在边界带（约 1 px），Ring IoU 0.93。

### 6.3 结论修正

- 004 报告原文"原始视频不可得、源图已下线"**作废**：视频与权重均可用，且已跑通 `视频 → 帧 → INIT Mask → cache`。
- 之前"密度实验只能在 2 段视频上执行"的结论**作废**：十段视频均有视频源，密度 8/16/22 可在**同源**条件下对全部十段重做。
- 唯一保留的偏差：重分割 Mask 与冻结 Mask 有 0.45% 边界差异，因此**新流程产物不复用旧相机**，需各自重解；两者应并列报告，不得混用。
