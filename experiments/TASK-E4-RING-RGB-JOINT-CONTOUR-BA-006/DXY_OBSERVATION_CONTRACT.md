# DXY_OBSERVATION_CONTRACT

## 只读调用

```
PYTHONPATH=/home/liu/new-polyp-dxy/src /usr/bin/python3
from dxy_mid._engine import ring_component as RC
base, payload = RC.recover(labels_360x640, bgr, 10.0)
```

- 输入 Mask **必须**来自本轮冻结 INIT 推理（权重 SHA `981aa596…`，bilinear logits）。
- 输出 `inner / outer / centerline` 椭圆 + `diagnostics`（coverage / residual / instability / branch）。
- **不得**为新 Mask 复用旧 JSON；本任务按新 Mask 重新导出并比对。

## 坐标

- DXY 输出为 360×640 原图坐标；Ring-First 与 `torus_contours` 同坐标系，**无缩放**。
- 若未来换分辨率，必须用 `C' = H^{-T} C H^{-1}`，禁止逐参数缩放。
