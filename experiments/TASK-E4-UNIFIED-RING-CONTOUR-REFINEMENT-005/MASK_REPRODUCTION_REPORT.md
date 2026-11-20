# MASK_REPRODUCTION_REPORT

## 结论

**用 DXY 官方冻结权重（SHA `981aa596…`）+ DXY 的推理数学，重分割与冻结 Mask 逐像素一致：`agree = 1.0000`，Ring IoU 0.9999–1.0000。**

上一轮报告的 0.45% 差异，追查后是**两个原因叠加**，与"模型随机性/帧号标注"无关：

| 原因 | 上一轮做法 | DXY 冻结做法 | 影响 |
|---|---|---|---|
| 权重 | `models/preserved_best_multiclass_overlapaware_20260405`（SHA `4adfe96e…`） | `experiments/dxy_remeasurement_20260917/02_segmentation/model`（SHA `981aa596…`） | 主要 |
| logits 上采样 | `cv2.resize(pred, NEAREST)`（先 argmax 后插值） | `F.interpolate(logits, bilinear, align_corners=False)` 后 argmax | 边界带 |

## 复现证据

| view | 旧做法（4adfe9 + nearest） | 新做法（981aa5 + bilinear logits） |
|---|---|---|
| G02_v005_raw00104 | agree 0.9953, Ring IoU 0.9346 | **agree 1.0000, Ring IoU 0.9999** |
| G03_v005_raw00589 | agree 0.9956, Ring IoU 0.9352 | **agree 1.0000, Ring IoU 1.0000** |

官方权重加载到同一架构为 strict 匹配（missing 0 / unexpected 0），说明架构一致、权重就是 DXY 冻结点。

## 遗留

- DXY 的 `INITSegmentation` 类本身在该模型目录下会因 `models/backbones.py` 的 `list[int]` 注解在 Python 3.12 报错，因此本轮用"同架构 + 官方权重 + 逐字复刻的推理数学"实现，并以上表证明等价。
- 已把权重 SHA、推理数学、视频 SHA 写入 `runs/prepared/*/PREPARED.json` 与 `metrics/INPUT_PROVENANCE.csv`。
