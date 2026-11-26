from common import *
rows=read(T/'evidence/RESULTS.json')
a=next(r for r in rows if r['condition']=='V0'and r['method']=='M2');b=next(r for r in rows if r['condition']=='V1'and r['method']=='M2')
checks=dict(V0_surface_non_degradation=a['added_joint_p95_vs_clean_mm']<=CFG['V0_added_p95_mm'],V0_coverage_non_degradation=a['coverage_delta_vs_clean']>=-CFG['V0_coverage_drop_fraction'],V1_pose=b['pose_pass'])
assert all(checks.values()),checks
save(T/'evidence/V01_GATE_RECHECK.json',dict(checks=checks,V2_allowed=True,original_gate_preserved='V01_GATE.json'))
