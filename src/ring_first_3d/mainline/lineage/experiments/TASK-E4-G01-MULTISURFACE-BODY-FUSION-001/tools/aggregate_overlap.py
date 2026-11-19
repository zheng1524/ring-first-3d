from pathlib import Path
import json,csv
import numpy as np
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts
from ring_first_3d.synthetic.io import fetch
root=Path.cwd();td=root/'experiments/TASK-E4-G01-MULTISURFACE-BODY-FUSION-001';run=td/'runs/MULTISURFACE_001';state=read_state(run);assert state['accepted'];assert verify_task(load_task(td/'TASK.yaml'))['freeze_sha256']==state['freeze_sha256'];check_artifacts(run,state)
from ring_first_3d.multisurface.geometry import transform,summary
pred=json.loads(fetch(run,'G3_all_predict','PREDICTIONS_FROZEN.json').read_text());pairs=json.loads(fetch(run,'G0_views_noise','private/OVERLAP_TARGETS.json').read_text());target={p['key']:dict(np.load(fetch(run,'G0_views_noise','private/overlaps/'+p['key']+'.npz')))for p in pairs};index=[r for r in json.loads(fetch(run,'G0_views_noise','public/FRAME_INDEX.json').read_text())if r['role']=='FIT'];rows=[]
for r in pred['rows']:
 if r['status']!='NUMERIC':continue
 cams={c['id']:np.array(c['estimated_C'])for c in json.loads(fetch(run,'G0_views_noise','public/conditions/'+r['condition']+'/ESTIMATED_POSES.json').read_text())};V={v['id']:np.load(fetch(run,'G3_all_predict',r['key']+'/'+v['id']+'.npz'))['V']for v in index};err={'within_video':[],'cross_video':[]}
 for p in pairs:
  q=target[p['key']]
  if not len(q['source_vertex']):continue
  P=V[p['first']][q['source_vertex']];Q=transform(q['target_camera_points'],np.asarray(r['surface_corrections'][p['second']])@cams[p['second']]);err[p['family']].append(np.linalg.norm(P-Q,axis=1))
 for family,arrays in err.items():
  e=np.concatenate(arrays)if arrays else np.empty(0);m=summary(e);rows.append(dict(key=r['key'],condition=r['condition'],arm=r['arm'],method=r['method'],kind=r['kind'],tolerance_mm=r['tolerance_mm'],family=family,target_pairs=sum(p['family']==family for p in pairs),physically_overlapping_pairs=sum(p['family']==family and p['fixed_target_N']>0 for p in pairs),fixed_target_N=len(e),MAE_mm=m['MAE'],median_mm=m['median'],P95_mm=m['p95'],maximum_mm=m['maximum'],GT_alignment=False))
# A shared rigid update cannot change within-video Euclidean disagreements.
by={(r['condition'],r['arm'],r['method'],r['tolerance_mm'],r['family']):r for r in rows}
for c in ['C0','C1','C2','C3','C4','C5']:
 for a in ['E1','E2']:
  p=by[c,a,'M0',.5,'within_video'];q=by[c,a,'BODY_VIDEO',.5,'within_video'];assert p['fixed_target_N']==q['fixed_target_N'];assert abs(p['MAE_mm']-q['MAE_mm'])<1e-8,(c,a,p,q)
vis=td/'visualization';(vis/'OVERLAP_FAMILY_METRICS.json').write_text(json.dumps(dict(rows=rows,fixed_targets=True,video_only_within_video_invariance_verified=True,GT_alignment=False),indent=2)+'\n')
with(vis/'OVERLAP_FAMILY_METRICS.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
for c in ['C3','C4']:
 print(c,[(method,by[c,'E1',method,.5,'within_video']['MAE_mm'],by[c,'E1',method,.5,'cross_video']['MAE_mm'])for method in ['M0','ICP','BODY_VIDEO','BODY_HIER']])
p=td/'TECHNICAL_REPORT.md';s=p.read_text();s+='\n## 固定重叠材料目标的总体一致性\n\n[全部同/跨视频重叠MAE/中位数/P95/最大值](visualization/OVERLAP_FAMILY_METRICS.csv)。所有方法使用预生成相同共可见材料目标，没有按配准后的距离筛除失败。额外核验了共享视频刚体不改变同视频内部距离这一物理不变量；帧级残余才可能改变内部错层。\n\n| C4/E1 method | Within-video MAE mm | Cross-video MAE mm |\n| --- | ---: | ---: |\n'
for method in ['M0','ICP','BODY_VIDEO','BODY_HIER']:s+=f"| {method} | {by['C4','E1',method,.5,'within_video']['MAE_mm']:.6f} | {by['C4','E1',method,.5,'cross_video']['MAE_mm']:.6f} |\n"
p.write_text(s);p=vis/'index.html';s=p.read_text().replace('</html>','<p><a href="OVERLAP_FAMILY_METRICS.csv">固定同视频/跨视频总体一致性及P95</a></p></html>');p.write_text(s)
print('Overlap aggregation',len(rows),'rows; physical rigid invariance passed')
