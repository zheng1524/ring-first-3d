# 最终交付

固定5组10视频已运行；另有3个GRAPH试点。HIST生成163张（原规则99、放宽新增64），覆盖8/10视频；当前V6正式基线66张、5/10视频。已生成Target自身通过Q1为56/163，不能把所有生成量当有效重建覆盖。

候选不升级；保留当前V6基线。覆盖损失：无整视频丢失。恢复输出：Ip_12.0mm / R10 / 视频004；Ip_20.0mm / R10 / 视频004；Ip_20.0mm / R10 / 视频005。完整质量与异常见[技术报告](TECHNICAL_REPORT.md)。

- [完整中文HERO图集](VISUALIZATION_INDEX.html)
- [RGB/Mask/Ring观测链](OBSERVATIONS_INDEX.html)
- [逐视频比较](VIDEO_COMPARISON.csv) · [全部源身份与指标](SOURCE_MANIFEST.csv) · [相机拒绝原因](CAMERA_GATES.csv)
- 本地地址：http://127.0.0.1:8956/VISUALIZATION_INDEX.html

实际启动205/273次，未按输出误差删面或换Support重试。RAW、模型和全量Mesh在`/home/liu/ring_first_3d_workspace/runs/v6_raw_to_hero_001`及清单所指原始路径，代码、配置、日志、小证据和中文图随分支提交。
