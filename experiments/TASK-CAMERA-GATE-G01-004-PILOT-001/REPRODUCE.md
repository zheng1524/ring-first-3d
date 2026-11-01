# CPU复现

独立分支 `exp/TASK-CAMERA-GATE-G01-004-PILOT-001`，父提交 `e8feece0718fee24a1b04b5e250629820e4f8299`。保留本机原始绝对路径；不复制大型视频、原HERO/模型或其他历史数据。所有输入SHA见 `config/INPUT_HASHES_BEFORE.json`，五相机身份见 `config/INPUT_IDENTITY.json`。原始相机不修改。

Python使用已安装环境 `/home/liu/polyp_research/ring_anchor_3d/.venv/bin/python`；numpy、OpenCV CPU SIFT、SciPy、trimesh、Pillow、matplotlib以及原项目vendor Open3D，无需下载。真实图像匹配缓存只读取p/q，未执行神经网络；Test1/2不使用HERO深度。

完整复现到本任务独立、忽略的runtime目录，并精确比较原始Ring/全部匹配指标、RGB-only方法选择、局部秩、资格与HERO辅助结果：

```bash
cd /home/liu/ring_first_3d_camera_gate/experiments/TASK-CAMERA-GATE-G01-004-PILOT-001
PYTHONDONTWRITEBYTECODE=1 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/reproduce.py
```

运行顺序：`prepare.py`仅资产核对/协议冻结；`tests12.py`先缓存/补充RGB匹配与RGB-only充分性选择，再Ring/固定相机评分；`correction.py`数据无先验可观测性、原资格与一次触发检查；`hero_auxiliary.py`最后20个原始XYZ投影。复现不覆盖交付数值、不重放ENG02初版判定错误、不重复之前E1/E3审计或融合实验。没有满足触发条件，因此本轮及复现优化器调用均0次。

开发阶段出现过一次身份条件实现遗漏（ENG02），已修复；最终代码从一开始就要求ref13，直接产生最终资格。初版及修复记录保留在 `config/ADJUDICATION_IMPLEMENTATION_FIX.json`，不隐去历史文件。

重新生成三图和报告使用已保存数值/本机原始输入，写入当前任务同名派生产物：

```bash
PYTHONDONTWRITEBYTECODE=1 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/figures.py
PYTHONDONTWRITEBYTECODE=1 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/report.py
PYTHONDONTWRITEBYTECODE=1 /home/liu/polyp_research/ring_anchor_3d/.venv/bin/python code/validate.py
```

`runtime/`含全分辨率CAD投影、原始点投影像素/点ID和执行日志，忽略上传；只交付轻量的匹配坐标缓存、小数据表、配置、代码和三张精选PNG。全部原始几何、Mask、K/c2w通过SHA和历史Git状态复核。代码哈希分阶段保留，最终哈希与测试见config。

资格未通过是本轮研究结果，不能修改标准或以换匹配器/增加新参考使复现“通过”。`CAMERA_GATE_PROTOCOL_v0.1.md`仍为待PM审核的候选规范。
