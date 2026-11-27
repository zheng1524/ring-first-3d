# 同快照恢复与状态

当前权威快照：`/home/liu/ring_first_3d_workspace/runs/v6_r1_full_b_001/SNAPSHOT.json`。最终实际身份见FULL_RUN_HANDOFF；失败工程启动保存在engineering_failed_launch，不算正式成果。

```bash
python3 - <<'RECOVER'
import json,os,subprocess
from pathlib import Path
root=Path('/home/liu/ring_first_3d_workspace/runs/v6_r1_full_b_001')
s=json.loads((root/'SNAPSHOT.json').read_text())
env=dict(os.environ,**s['environment'])
subprocess.run([s['python'],'-m','ring_first_3d.v6_raw.full_run','run','--config',s['config']],env=env,cwd=s['snapshot'],check=True)
RECOVER
```

单runner文件锁防止同一队列重复启动。需主动暂停时在run_root创建PAUSE_REQUESTED，当前阶段结束后暂停；恢复前移除此自建暂停文件。不要为恢复改config、换输入或清除FAILED状态。工程失败保留日志与attempt，明确定位修复后用原入口retry并保留记录；科学零输出不重试。

本地可视化：<http://127.0.0.1:8961/>，仅本机绑定。自动实时`PROGRESS.json`、`VIDEO_RESULTS.csv`、`GROUP_RESULTS.csv`、`BASELINE_COMPARISON.json`；完整终态由runner自动写FINAL_COVERAGE_REPORT.md。run_root/clean逐源FACE_EVIDENCE含原V/F、original_face_id及四态，Trusted_visible_mesh为原F[state==0]导出；Raw原Mesh/native保持原生成定义。
