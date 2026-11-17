# G0–G1 复现入口

项目目录 `/home/liu/ring_first_3d_synthetic_correspondence`。基线 fc63df356a577c61de75912b136f92d7f7b15e9d，执行源码 7c31af7a185f63fd58182eaffc36316cf49d2e73。所有源字节、输入 SHA、版本、角色和相机划分在 TASK.yaml、TEST_RESULTS.json、G0_SOURCE_CAMERA_PROTOCOL_FREEZE.json。

在仓库根目录：

```bash
bash tools/research/run.sh -m unittest discover -s tests -v
bash tools/research/run.sh tools/research/policy.py check --task experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/TASK.yaml
bash tools/research/run.sh tools/research/policy.py status --task experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/TASK.yaml --run-dir /home/liu/ring_first_3d_synthetic_correspondence/experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/runs/delivery-001
bash tools/research/run.sh tools/research/policy.py accept --task experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/TASK.yaml --run-dir /home/liu/ring_first_3d_synthetic_correspondence/experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/runs/delivery-001
```

预期 50 项通过，其中原 35 未改、新增 15。最终 14 阶段 PASS，accepted=True，scientific_acceptance=AWAITING_HUMAN_REVIEW。不要为“继续”进入未授权 G2；本轮已停止，以上状态/验收仅检查已冻结产物。

人工批准重放同一 G0–G1 时，换全新 run 名再用 run --stage all；不覆盖 delivery-001，也不修改历史输入。科学源/版本变更时旧 freeze 拒绝恢复。数据缺失为 NOT_EVALUABLE，不允许用演示几何或旧预测替代 G01。另一机器需重新绑定相同真实资产与运行环境，不能把未备份的本地数据假称已经上传。

离线首页：

`/home/liu/ring_first_3d_synthetic_correspondence/experiments/TASK-E4-SYNTHETIC-BODY-PIXEL-CORRESPONDENCE-001/runs/delivery-001/visualization/index.html`

页面和结果卡/manifest 自动生成并核验；九张精选 PNG、72 行代表点 Face/重心/XYZ 审计及全部逐帧/汇总指标随报告提交。所有逐像素 NPZ、原 GT/相机/CAD/Blender 和完整历史 attempt 留 LOCAL_ONLY。合成 Body 是真实 G01 GT 已知模板，不能用于宣称真实部署的 GT-free 重建性能。
