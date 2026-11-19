"""Post-freeze aggregation and explicit dispersion-versus-GT contradiction audit."""
import json,csv
import numpy as np
from ..synthetic.io import fetch,save_json,outputs
from ..multisurface.evaluate import run as inherited_evaluate,fixed_stats
from ..multisurface.geometry import transform

def run(task,attempt):
 inherited_evaluate(task,attempt);root=attempt.parents[1];cfg=task['fusion'];pred=json.loads(fetch(root,'G3_all_predict','PREDICTIONS_FROZEN.json').read_text());models=json.loads((attempt/'MODEL_METRICS.json').read_text());modelby={m['key']:m for m in models['models']};frames=[r for r in json.loads(fetch(root,'G0_views_noise','public/FRAME_INDEX.json').read_text())if r['role']=='FIT'];truth={f['id']:dict(np.load(fetch(root,'G0_views_noise','private/'+f['id']+'_truth.npz')))for f in frames};pairs=json.loads(fetch(root,'G0_views_noise','private/OVERLAP_TARGETS.json').read_text());targets={p['key']:dict(np.load(fetch(root,'G0_views_noise','private/overlaps/'+p['key']+'.npz')))for p in pairs};rows=[]
 for r in pred['rows']:
  row={k:r[k]for k in ['key','condition','arm','method','kind','status']};row.update(target_views=16,target_material_vertices=sum(len(t['Ptrue'])for t in truth.values()),history_measurement_fallback=0,GT_alignment=False)
  if r['status']=='NUMERIC':
   V={f['id']:np.load(fetch(root,'G3_all_predict',r['key']+'/'+f['id']+'.npz'))['V']for f in frames};err=np.concatenate([np.linalg.norm(V[f['id']]-truth[f['id']]['Ptrue'],axis=1)for f in frames]);rel=np.concatenate([np.linalg.norm(V[f['id']]-truth[f['id']]['Ptrue'],axis=1)/((truth[f['id']]['Ptrue']-truth[f['id']]['true_C'][:3,3])@truth[f['id']]['true_C'][:3,:3])[:,2]for f in frames]);row.update(material=fixed_stats(err),median_absolute_relative_to_true_axial_depth=float(np.median(rel)),material_correct_fraction=float((err<=cfg['coverage_threshold_mm']).mean()))
   cams={c['id']:np.asarray(c['estimated_C'])for c in json.loads(fetch(root,'G0_views_noise','public/conditions/'+r['condition']+'/ESTIMATED_POSES.json').read_text())};family={'within_video':[],'cross_video':[]}
   for p in pairs:
    q=targets[p['key']];P=V[p['first']][q['source_vertex']];Q=transform(q['target_camera_points'],np.asarray(r['surface_corrections'][p['second']])@cams[p['second']]);family[p['family']].append(np.linalg.norm(P-Q,axis=1))
   row.update({k:fixed_stats(np.concatenate(v))for k,v in family.items()});row['pooled_dispersion']=fixed_stats(np.concatenate(family['within_video']+family['cross_video']))
   row['correspondence_before']=r['correspondence_before'];row['correspondence_after']=r['correspondence_after']
  else:row.update(material=fixed_stats(np.full(row['target_material_vertices'],np.nan)),within_video=None,cross_video=None,pooled_dispersion=None)
  m=modelby[r['key']];row['GT_bidirectional_mm']=m.get('bidirectional_mm');row['observed_GT_coverage']=m.get('GT_observed_region',{}).get('coverage');row['unique_GT_coverage']=m.get('GT_unique_coverage');row['observed_area_fraction']=m.get('observed_faces',{}).get('sampled_area_fraction');rows.append(row)
 by={(r['condition'],r['arm'],r['method']):r for r in rows};contradictions=[]
 for r in rows:
  base=by[r['condition'],r['arm'],'M0'];r['dispersion_reduced_but_material_worse']=False
  if r['status']=='NUMERIC'and base['status']=='NUMERIC':
   r['paired_vs_M0']=dict(dispersion_delta_mm=r['pooled_dispersion']['MAE']-base['pooled_dispersion']['MAE'],material_delta_mm=r['material']['MAE']-base['material']['MAE'])
   flag=r['pooled_dispersion']['MAE']<.8*base['pooled_dispersion']['MAE']and r['material']['MAE']>base['material']['MAE']+1e-6;r['dispersion_reduced_but_material_worse']=bool(flag)
   if flag:contradictions.append(dict(key=r['key'],reason='Dispersion >20% reduction but independent GT material error increased',before_dispersion_mm=base['pooled_dispersion']['MAE'],after_dispersion_mm=r['pooled_dispersion']['MAE'],before_material_mm=base['material']['MAE'],after_material_mm=r['material']['MAE']))
 save_json(attempt/'STRESS_METRICS.json',dict(rows=rows,fixed_denominators=True,contradictions=contradictions,independent_GT_only_after_freeze=True))
 with(attempt/'STRESS_METRICS.csv').open('w',newline='')as f:
  w=csv.writer(f,lineterminator='\n');w.writerow(['key','status','material_N','material_MAE_mm','material_median_mm','material_P95_mm','material_max_mm','median_absolute_relative_to_true_axial_depth','within_MAE_mm','cross_MAE_mm','pooled_dispersion_MAE_mm','body_correspondence_before','body_correspondence_after','pair_correspondence_before','pair_correspondence_after','GT_bidir_MAE_mm','GT_bidir_P95_mm','GT_observed_coverage','unique_GT_coverage','observed_model_area_fraction','dispersion_down_GT_worse'])
  for r in rows:
   val=lambda name,key:(r.get(name)or{}).get(key)
   w.writerow([r['key'],r['status'],r['target_material_vertices'],val('material','MAE'),val('material','median'),val('material','p95'),val('material','maximum'),r.get('median_absolute_relative_to_true_axial_depth'),val('within_video','MAE'),val('cross_video','MAE'),val('pooled_dispersion','MAE'),val('correspondence_before','body_rate'),val('correspondence_after','body_rate'),val('correspondence_before','pair_rate'),val('correspondence_after','pair_rate'),val('GT_bidirectional_mm','MAE'),val('GT_bidirectional_mm','p95'),r.get('observed_GT_coverage'),r.get('unique_GT_coverage'),r.get('observed_area_fraction'),r['dispersion_reduced_but_material_worse']])
 ledger=json.loads((attempt/'FAILURE_LEDGER.json').read_text());ledger['dispersion_GT_contradictions']=contradictions;save_json(attempt/'FAILURE_LEDGER.json',ledger)
 return outputs(attempt,dict(status='PASS',models=len(rows),numeric=sum(r['status']=='NUMERIC'for r in rows),scientific_failures=len(ledger['failures']),dispersion_GT_contradictions=len(contradictions),GT_alignment=False))
