# G01 双视频：STOPPED_AT_G0

Preflight、Contracts、65项回归通过。G0场景门禁失败，任务NOT_ACCEPTED。

- Ring投影：004通过0/22，005通过4/11；HOLDOUT通过0/8。
- 原始Blender形状与缓存一致，但只有“球体”，缺少Ring/相机及固定Body-to-Ring部署凭据。
- G1–G4和S0–S4全部NOT_RUN；无注入、初始化或配准；配准指标NaN，历史回退0。

[完整报告](TECHNICAL_REPORT.md) · [离线可视化](visualization/index.html) · [运行清单](RUN_MANIFEST.json) · [逐帧指标](FRAME_AUDIT.csv) · [失败记忆](FAILURE_REGISTRY.json)

实现提交：`8bd150ab7870db42c11942d385242910e2daff00`。目标组G01=1，配准独立成功0/1；门禁未通过不能宣称科学任务完成。
