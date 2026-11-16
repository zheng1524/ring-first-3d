# 复现

基线：`fa649fa1cf20b111bfdb8489e8af20ba90339bba`；首批可执行代码提交：`c8c3b3b7`，完整 SHA 见 TEST_RESULTS.json。正式 DXY：`75d58ca5b643fb4d8e0eb887b45ad0f056b0bb95`。冻结期望不通过测试程序重算或覆盖。

从仓库根目录执行：

```bash
bash tools/research/run.sh tools/research/preflight.py --output /tmp/harness-preflight.json
bash tools/research/run.sh tools/research/validate_contracts.py --output /tmp/harness-contracts.json
bash tools/research/run.sh tools/research/audit_reuse.py --output /tmp/harness-reuse.json
bash tools/research/run.sh tools/research/smoke.py --output /tmp/harness-smoke.json
```

预期：Preflight PASS；11 项独立契约；三个真实模块 Smoke 和 Contour/Guard 兼容测试均 PASS。普通数学契约无需 GPU、DXY 或大型实验，仅依赖基础数值包。真实 Smoke 使用本机登记的 G01 小样本、015/016 选择清单、MAX proxy/真实四视角 SIFT 子集与 014 的 108 相机输入 pack；只渲染一个相机。不提供模拟/随机几何替代数据。

测试环境为 Python 3.12.13、numpy 1.26.4、scipy 1.15.3、OpenCV 4.11.0、scikit-image 0.25.2、Torch 2.7.1+cu128、PyTorch3D 0.7.9、Open3D 0.19.0、trimesh 5.1.1、python-fcl 0.7.0.11、RTX 3060 Laptop GPU。所有运行路径/版本见 PREFLIGHT_AFTER.json，源码和扩展身份见 REUSE_AFTER.json、maintenance/storage/DEPENDENCIES_PRESERVED.json。没有在受保护环境安装包。

路径可由 run.sh 的环境变量替换；真实输入清单位于 tools/research/frozen_fixture.json 与 support_fixture.json。迁移机器须先提供同 SHA 输入/依赖，并在另一个任务冻结对应真实资产清单；缺失会失败或 NOT_EVALUABLE。main-ready 源对象供应方法见 docs/RESEARCH_EXECUTION_HARNESS.md。

数值容差：DXY center/basis 绝对 1e-7 px；015/016/MAX/support ID 完全一致；016 weights 1e-12；proxy 面积和 support score 1e-8；质量 1e-10；renderer loss 1e-7、alpha 总和 0.005、投影误差小于 0.001 px。PyTorch float32 归一化运算次序导致像素 alpha SHA 与 raw reference 不同，数值在冻结容差内；两个 SHA 均保留，不伪装字节一致。

`render_evidence.py` 可从 SMOKE_AFTER.json 及同一冻结输入生成精选图；不会读 GT。

不应重放存储删除：审计/归档/清理工具是已执行的单次事务，有不可变 Phase-0/Phase-2 和已存在的回执。已删除的缓存不属于复测依赖，Smoke 在清理后可继续运行。旧响应完整归档可按 CACHE_BACKUP_MANIFEST.json 逐成员验证并恢复；这份约 102.65 MB 的归档为 LOCAL_ONLY，不在 GitHub。恢复仅限清单原路径，禁止整树解包到任意目录。
