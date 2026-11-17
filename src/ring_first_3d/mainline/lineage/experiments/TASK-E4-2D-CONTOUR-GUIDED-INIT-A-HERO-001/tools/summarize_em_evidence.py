"""Separate fixed observed-boundary coverage from changing visible Body sample counts."""
from pathlib import Path
import json,csv,numpy as np
from ring_first_3d.contour_guided.correspondence import target_boundary
TD=Path.cwd()/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';VIS=TD/'visualization';rows=[];denominators={};src=json.loads((TD/'inputs/SOURCES.json').read_text());views={(g['case'],v['meta']['id']):v for g in src['cases']for v in g['FIT']}
for p in sorted((VIS/'intermediate').glob('*/*/SUMMARY.json')):
 g,step=p.parts[-3:-1];summary=json.loads(p.read_text())
 for v in summary['views']:
  a=dict(np.load(p.parent/(v['id']+'.npz')));row=dict(case=g,step=step,attempt=summary['attempt'],view=v['id'],video=views[g,v['id']]['meta']['video'],gradient_norm=float(np.linalg.norm(a['contour_gradient'])),previous_gradient_actual_descent_work=float(a['descent_work'].sum()),actual_shared_step_MAE_mm=float(np.linalg.norm(a['actual_shared_vertex_delta'],axis=1).mean()),actual_shared_step_P95_mm=float(np.quantile(np.linalg.norm(a['actual_shared_vertex_delta'],axis=1),.95)),actual_shared_step_max_mm=float(np.linalg.norm(a['actual_shared_vertex_delta'],axis=1).max()))
  if 'direction'in a:
   for d,label in [(0,'Body_to_observed'),(1,'observed_to_Body')]:
    keep=a['direction']==d;N=int(keep.sum());A=int((keep&a['accepted']).sum());row[label+'_target_N']=N;row[label+'_accepted_N']=A;row[label+'_coverage']=A/N if N else None;row[label+'_distance_MAE_native_px']=float(a['distance'][keep].mean())if N else None
    if d==1:
     key=(g,v['id']);denominators.setdefault(key,N);assert denominators[key]==N,'Observed boundary sample population must stay fixed across E steps'
   ok=a['accepted'];row['accepted_normal_MAE_native_px']=float(abs(a['normal_residual_px'][ok]).mean())if ok.any()else None;row['tracked_accepted_N']=int((a['tracked']&ok).sum());row['reason_counts']={x:int((a['reasons']==x).sum())for x in np.unique(a['reasons'])}
  else:
   labels=np.load(views[g,v['id']]['cache']['path'])['labels'];ct,_,_=target_boundary(labels);N=len(ct);denominators.setdefault((g,v['id']),N);assert denominators[g,v['id']]==N;row.update(observed_to_Body_target_N=N,observed_to_Body_accepted_N=0,observed_to_Body_coverage=0. if N else None,reason_counts={'NO_VISIBLE_BODY_CONTOUR':N})
  rows.append(row)
(VIS/'E_M_FIXED_BOUNDARY_COVERAGE.json').write_text(json.dumps(dict(rows=rows,fixed_observed_population_checked=True,forward_visible_Body_population_may_change=True,coverage_is_not_accuracy=True),indent=2)+'\n')
keys=list(dict.fromkeys(k for r in rows for k in r))
with(VIS/'E_M_FIXED_BOUNDARY_COVERAGE.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,keys);w.writeheader();w.writerows(dict(r,reason_counts=json.dumps(r['reason_counts']))for r in rows)
p=VIS/'index.html';p.write_text(p.read_text()+'<p><a href="E_M_FIXED_BOUNDARY_COVERAGE.csv">E/M fixed observed-boundary coverage and signed per-view descent work</a></p>\n');print('E/M per-view phase rows',len(rows),'fixed observed contours',len(denominators))
