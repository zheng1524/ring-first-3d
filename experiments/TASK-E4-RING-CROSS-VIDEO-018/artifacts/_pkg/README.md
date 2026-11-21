# CODE AUDIT — TASK-E4-RING-CROSS-VIDEO-018

复现：
```
PYTHONPATH=<ws>/src:<pkg>/code python code/synthetic_yaw.py     # 受控实验
PYTHONPATH=<ws>/src:<pkg>/code python -m unittest discover -s tests -v
```
关键结论：017 的 loss≈22/25 由缺失 `F=K^-T E K^-1` 造成；修正后 S0 loss=0、真实同视频误差 0.055°、
真实跨视频中位 28.9 px（匹配本身错误）。
