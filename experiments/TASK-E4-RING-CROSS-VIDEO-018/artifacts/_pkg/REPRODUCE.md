1. 环境：Python 3.12, numpy, scipy, opencv-python（不再需要其他依赖）。
2. `python code/synthetic_yaw.py` 输出 `metrics/SYNTHETIC_GROUND_TRUTH.csv`（本包含 results/ 副本）。
3. `python -m unittest discover -s tests` 应 4/4 通过。
4. 真实对照需工作站上的 W0 相机与轨迹文件（路径与 SHA 见主报告），本包不含原始视频。
