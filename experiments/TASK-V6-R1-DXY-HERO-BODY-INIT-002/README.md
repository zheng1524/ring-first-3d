# R1 主体初始化修正 002

本任务只读 R1/M4/DXY/001；输出全部留在本目录。基础提交 `3b8610075a4959a32097cca83247faaddbf61aa1`。科学执行代码与统一配置见 `evidence/FULL_RUN_FREEZE.json`，实际资格先于拟合。

```bash
cd /home/liu/.config/superpowers/worktrees/ring_first_3d_workspace/TASK-V6-R1-BODY-INIT-002/experiments/TASK-V6-R1-DXY-HERO-BODY-INIT-002
bash run_python.sh code/test_registration.py
bash run_python.sh code/test_dxy_full.py
bash run_python.sh code/test_fit_revision.py
bash run_python.sh code/test_coordinates.py
bash run_python.sh code/registration.py
bash run_python.sh code/run_dxy_batch.py
# 逐帧完整过程完成后核验：
bash run_python.sh code/verify_dxy_full.py
# 重跑全量需保留已审核的 FULL_RUN_FREEZE；选择帧尚未完成会等待。
python3 code/batch_revision.py --workers 2
bash run_python.sh code/visibility_revision.py
bash run_python.sh code/visualize_revision.py
bash run_python.sh code/verify_revision.py
bash run_python.sh code/report_revision.py
bash run_python.sh code/package_revision.py
```

单组：`bash run_python.sh code/pipeline_revision.py --group GP_IIa_14.0mm_closed_R5_single_refY`。该命令仍必须读取冻结资格；拒绝组不会运行诊断联合。二维算法覆盖1700帧，不改变001所用790帧的FIT/HOLDOUT角色。脚本只用现成Python环境，CPU低优先级；4个二维worker与最多2个拟合worker，资源紧张可减少，禁止借此重跑上游模型。

本地中文审阅入口 `runs/results/index.html`；全帧二维过程 `runs/review/index.html`。未选定三维视角的页面明确说明仅二维；按需实际相机投影：

```bash
bash run_python.sh code/visualize_revision.py --frame GP_IIa_14.0mm_closed_R5_single_refY_005/raw_000000
```

完整二维科学文件位于 `runs/dxy/<case>/<frame>/`：FRAME身份/状态、CURVES原像素和边界身份、PROCESS实际候选/选择，以及官方完整导出。展示页写在另一个 `runs/review` 目录，避免污染科学缓存。PIXEL_ONLY是本帧实际可见P求解，不是正式毫米测量；曲线存在也不表示质量可靠。每条监督只使用选中候选，不使用profile、当前仍被拒绝的候选或候选池中所有可用曲线。官方恢复候选的历史拒绝原因仍保留；OFFICIAL仅表示有官方数值候选，不代表质量通过。

消费者 `code/consume_revision.py::load_configuration` 只接受本任务输出并校验当前资格/科学键及输入SHA。`corrected_source` 返回可信原面 ID 与 `D-b` 射线工作副本，未被原可信面引用的顶点不因此可信。单视频使用LOCAL；合格组件每视频用 `T_local_to_joint` 同步作用相机、射线和全部曲面，保持毫米尺度。返回的模型/可见面不是实测GT。推断底盖单列且不作深度监督。

资格中HELD用于本轮路由，二维HOLDOUT只未进入显式二维目标；HERO/上游相机可能使用同帧，不宣称端到端独立留出。真实GT不可评价。单/联合共享来源具有相关性，39组是物理组分母。

依赖及证据包见 `evidence/PRESERVE_DEPENDENCIES.csv` 与 `ARCHIVE_MANIFEST.json`。原图、Raw/Clean、完整二维过程大包保留可核验本地路径；仓库上传代码、表格、紧凑初体和精选图，不上传视频/模型权重。回执含本机绝对路径，异机解包不自动完成上游路径迁移。不要清理原资产来复现本任务。
