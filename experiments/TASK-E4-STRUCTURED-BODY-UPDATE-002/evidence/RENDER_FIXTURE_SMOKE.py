"""Engineering fixture ONLY, fabricated sphere is never a scientific result."""
from pathlib import Path
import sys,json,numpy as np,trimesh
from unittest.mock import patch
sys.path.insert(0,'/home/liu/ring_first_3d_structured_body_002/experiments/TASK-E4-STRUCTURED-BODY-UPDATE-002/code')
import figures
from projection_gate import ProjectionGate
from ring_collision_gate import RingCollisionGate
from common import dump
from ring_first_3d.synthetic.raster import ray_map
p=Path('/tmp/structured002-figure-fixture');p.mkdir(exist_ok=True);e=p/'evaluation';e.mkdir();out=p/'attempts/figure';out.mkdir(parents=True)
m=trimesh.creation.icosphere(subdivisions=1);b=dict(V=np.asarray(m.vertices)+[0,0,5],F=np.asarray(m.faces),F_solid=np.asarray(m.faces),boundary_vertex=np.zeros(len(m.vertices),bool),inferred_base_faces=np.zeros(len(m.faces),bool));ring=dict(V=np.asarray(m.vertices)+[4,0,8],F=np.asarray(m.faces));K=np.array([[60.,0,32],[0,60,32],[0,0,1]]);v=dict(id='UNIT_FIXTURE',video='004',role='FIT',K=K,C=np.eye(4),RGB=np.zeros((64,64,3)),labels=ray_map(b['V'],b['F'],K,np.eye(4),(64,64))['valid'].astype(int));case='UNIT';(e/case).mkdir();np.savez_compressed(e/case/'GT.npz',**b)
figures.PREVIOUS=p/'previous';(figures.PREVIOUS/case/'DEFORM_GROW').mkdir(parents=True);np.savez_compressed(figures.PREVIOUS/case/'DEFORM_GROW/FINAL.npz',**b)
records=[];rows=[];summary=[];mapping={}
for arm in ['INITIAL','PREVIOUS_DEFORM_GROW','DEFORM_ONLY','DEFORM_SWEEP']:
 np.savez_compressed(e/case/(arm+'_GT_ALIGNED.npz'),**b,T=np.eye(4));s=dict(case=case,arm=arm,status='NUMERIC',FIT_IoU=1.,HOLDOUT_IoU=1.,GT_MAE_mm=0.,GT_p95_mm=0.,GT_coverage_0p5mm=1.,growth_length_mm=0.,growth_status='NOT_ACCEPTED',accepted_updates=0);summary.append(s);rows.append(dict(case=case,arm=arm,projection=[dict(id=v['id'],video='004',role='FIT',IoU=1.,Boundary_MAE_px=0.)]))
 if arm.startswith('DEFORM_'):
  folder=p/case/arm;folder.mkdir(parents=True);np.savez_compressed(folder/'FINAL.npz',**b);g=ProjectionGate([v],ring,{v['id']:1});a=g.rebuild(b,True)[v['id']];content=dict(a['pairs']);content.update(**{k:a[k]for k in ['R_plus','R_minus','unknown','predicted','target','visible_face','visible_bary']})
  for name in ['INITIAL_PAIRS','FINAL_PAIRS']:(folder/name).mkdir();np.savez_compressed(folder/name/(v['id']+'.npz'),**content)
  (folder/'STEP_035').mkdir();np.savez_compressed(folder/'STEP_035/GRAPH.npz',nodes=b['V'][:32],rotation=np.zeros((32,3)),translation=np.zeros((32,3)),edges=np.c_[np.arange(31),np.arange(1,32)])
  rg=RingCollisionGate(b,ring)
  for name in ['RING_INITIAL','RING_FINAL']:np.savez_compressed(folder/(name+'.npz'),**rg.measure(b))
  dump(folder/'UPDATES.json',dict(growth=[],iterations=[]));records.append(dict(status='NUMERIC',arm=arm,mesh_relative=case+'/'+arm+'/FINAL.npz'));mapping[('G1_'+case,case+'/'+arm+'/FINAL.npz')]=folder/'FINAL.npz'
dump(e/'EVALUATION.json',dict(summary=summary,rows=rows));dump(e/'FAILURE_REGISTRY.json',dict(records=[]));dump(p/'FROZEN.json',dict(records=records));mapping.update({('G2_evaluate','EVALUATION.json'):e/'EVALUATION.json',('G2_evaluate','FAILURE_REGISTRY.json'):e/'FAILURE_REGISTRY.json',('G1_'+case,'BODY_PREDICTIONS_FROZEN.json'):p/'FROZEN.json'})
with patch.object(figures,'load_case',return_value=(b,[v],ring,{},{},{})),patch.object(figures,'fetch',side_effect=lambda root,stage,name:mapping[stage,name]):
 result=figures.visualize(dict(structured=dict(cases=[case],arms=['DEFORM_ONLY','DEFORM_SWEEP'])),out)
print('Engineering-only figure smoke',result['status'],result['figures'])
