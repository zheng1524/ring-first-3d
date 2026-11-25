# 小证据入口

逐视频输入/配置/相机NPZ、全部门控/指标/运行身份、代码协议哈希和日志合并在[运行证据归档](archive/RUNTIME_EVIDENCE.tar.gz)，每成员SHA见[清单](archive/RUNTIME_EVIDENCE_MANIFEST.csv)。已逐成员解压读回验证。归档不含RAW视频、模型或全量Mesh。

在本任务目录执行 `tar -xzf archive/RUNTIME_EVIDENCE.tar.gz` 即恢复 `evidence/runs`、`evidence/prepared`、`evidence/protocols`、`logs`。本地这些小文件原本也保留；Git中只存一次压缩包以减少重复包装。高层逐源CSV、逐视频CSV、全部中文可视化和关键验证回执直接提交。

数值深度/大Mesh的本地绝对路径及SHA在SOURCE_MANIFEST.csv；RAW路径、选帧/分割身份及实际相机在上述归档。报告中的所有不可评价项保留null/空值与状态，不填0伪装成功。
