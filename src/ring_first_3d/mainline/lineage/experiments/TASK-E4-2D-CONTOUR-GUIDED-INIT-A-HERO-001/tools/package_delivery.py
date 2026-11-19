"""Read-only accepted-run export; never mutate original snapshots or predictions."""
from pathlib import Path
import json,hashlib,shutil,csv,subprocess,html
import numpy as np
import trimesh
from ring_first_3d.policy.contracts import load_task,verify_task
from ring_first_3d.policy.artifacts import read_state,check_artifacts,heads
from ring_first_3d.synthetic.io import fetch
ROOT=Path.cwd();TD=ROOT/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';TASK=load_task(TD/'TASK.yaml');RUN=TD/'runs/CONTOUR_004';STATE=read_state(RUN);assert STATE['accepted'];assert verify_task(TASK)['freeze_sha256']==STATE['freeze_sha256'];check_artifacts(RUN,STATE)
VIS=TD/'visualization';assert not VIS.exists(),'Do not overwrite curated delivery';shutil.copytree(RUN/'visualization',VIS,symlinks=False)
for n in ['TECHNICAL_REPORT.md','RESULT_CARD.md','metrics.json','failures.json','evidence.png']:shutil.copyfile(RUN/n,TD/n)
EV=TD/'evidence';EV.mkdir(exist_ok=True);shutil.copyfile(RUN/'FREEZE.json',EV/'ORIGINAL_FREEZE.json');shutil.copyfile(RUN/'RUN_MANIFEST.json',EV/'ORIGINAL_RUN_MANIFEST.json')
for p in (RUN/'attempts').glob('*/*'):
 if p.is_file() and p.suffix in ['.json','.txt']:d=EV/'attempts'/p.parent.name/p.name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,d)
for r in sorted((TD/'runs').glob('CONTOUR_*')):
 if r==RUN:continue
 for p in (r/'attempts').rglob('*'):
  if p.is_file() and(p.name in ['TRAIN_STDOUT.txt','result.json','request.json','stderr.txt','stdout.txt']):q=EV/'FAILED_RUNS'/r.name/p.relative_to(r);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q)
old=Path('/home/liu/ring_first_3d_multivideo_init_a/experiments/TASK-E4-MULTIVIDEO-INIT-A-HERO-ALIGN-001');shutil.copyfile(old/'visualization/BODY_SHAPE_METRICS.json',EV/'ORIGINAL_A2_EVALUATION.json')
# All precise native HERO meshes, not just visualization float32 exports.
hpred=json.loads(fetch(RUN,'G2_all_hero','ALL_HERO_PREDICTIONS_FROZEN.json').read_text());source=json.loads(Path(TASK['inita']['assets']['sources']['path']).read_text());groups={r['group']:r for r in source['real_groups']};transforms=[]
for g in hpred['groups']:
 if g['status']!='NUMERIC':continue
 views=[v for v in groups[g['case']]['views']if v['role']=='FIT']
 for r in g['records']:
  if r['status']!='NUMERIC':continue
  for v in views:
   src=fetch(RUN,'G2_all_hero',g['case']+'/'+r['method']+'/'+v['id']+'.npz');dest=VIS/'meshes'/g['case']/r['method']/(v['id']+'.npz');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
   name=g['case']+'/'+r['method']+'/'+v['id']+'_CANDIDATES.npz';src=fetch(RUN,'G2_all_hero',name);dest=VIS/'HERO_CORRESPONDENCES'/g['case']/r['method']/(v['id']+'.npz');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
  transforms.append(dict(case=g['case'],**r))
(VIS/'HERO_TRANSFORMS_AND_MOTION.json').write_text(json.dumps(transforms,indent=2)+'\n')
# Full frozen optimization traces and summary; selected actual E/M pair NPZ already exported by original visualization stage.
for g in TASK['inita']['cases']:
 for arm in ['A2D','A3']:
  try:run=fetch(RUN,'G1_all_train',g+'/'+arm+'/metrics/'+g+'_RUN.json')
  except (KeyError,ValueError,OSError):continue
  folder=run.parents[1];out=EV/'optimization'/g/arm;out.mkdir(parents=True)
  for p in (folder/'metrics').glob('*.json'):shutil.copyfile(p,out/p.name)
  shutil.copyfile(folder/'TRAIN_STDOUT.txt',out/'TRAIN_STDOUT.txt')
  provenance=folder/'provenance'/(g+'_OPT_START.json')
  if provenance.is_file():shutil.copyfile(provenance,out/'ORIGINAL_OPT_START.json')
# Exact initial geometry diagnostics were independently measured on these same013 V/F in parent.
initial_geometry=json.loads((old/'visualization/OPTIMIZATION_DIAGNOSTICS.json').read_text())
shutil.copyfile(old/'visualization/OPTIMIZATION_DIAGNOSTICS.json',EV/'ORIGINAL_INITIAL_GEOMETRY_DIAGNOSTICS.json')
# Same scientific metrics, explicitly recalculate aggregate comparisons from actual rows.
body=json.loads((VIS/'BODY_SHAPE_METRICS.json').read_text())['rows'];hero=json.loads((VIS/'HERO_METRICS.json').read_text())['groups'];pairs=json.loads((VIS/'PAIRED_COMPARISONS.json').read_text())['body'];by={(r['case'],r['arm']):r for r in body};aggregate={}
for reference in ['A2','A2D']:
 rr=[r for r in pairs if r['reference']==reference];ss=[r for r in rr if r['strict_IoU_delta']is not None];a=dict(common_numeric_groups=len(rr),strict_common_groups=len(ss),strict_IoU_better=sum(r['strict_IoU_delta']>0 for r in ss),conditional_IoU_better=sum(r['conditional_IoU_delta']>0 for r in rr),Chamfer_better=sum(r['Chamfer_delta_mm']<0 for r in rr),mean_Chamfer_delta_mm=float(np.mean([r['Chamfer_delta_mm']for r in rr]))if rr else None,mean_conditional_IoU_delta=float(np.mean([r['conditional_IoU_delta']for r in rr]))if rr else None)
 if ss:a.update(strict_reference_mean=float(np.mean([by[r['case'],reference]['IoU_3D']for r in ss])),strict_A3_mean=float(np.mean([by[r['case'],'A3']['IoU_3D']for r in ss])))
 for role in ['FIT','HOLDOUT']:
  for video in ['004','005']:
   key=role+'_'+video+'_IoU_delta';z=[r[key]for r in rr if r.get(key)is not None];a[key]=dict(N=len(z),mean=float(np.mean(z))if z else None,better=sum(v>0 for v in z))
 aggregate[reference]=a
hcomp={}
for reference in ['H1','H2','H3']:
 hcomp[reference]={}
 for family in ['within_video','cross_video']:
  rr=[]
  for g in hero:
   methods={r['method']:r for r in g.get('methods',[])if r['status']=='NUMERIC'}
   if not all(z in methods and methods[z][family]['MAE']is not None for z in [reference,'H4']):continue
   rr.append(dict(case=g['case'],reference_MAE_mm=methods[reference][family]['MAE'],H4_MAE_mm=methods['H4'][family]['MAE'],delta_H4_minus_reference_mm=methods['H4'][family]['MAE']-methods[reference][family]['MAE']))
  hcomp[reference][family]=dict(common_groups=len(rr),H4_better=sum(r['delta_H4_minus_reference_mm']<0 for r in rr),rows=rr)
summary=dict(task_id=TASK['task_id'],target_groups=11,A3_numeric=sum(r['arm']=='A3'and r['status']=='NUMERIC'for r in body),body=aggregate,HERO_numeric=sum(g['status']=='NUMERIC'for g in hero),HERO=hcomp,real_absolute_3D_accuracy='NOT_EVALUABLE',GT_used_for_selection=False,scientific_acceptance='AWAITING_HUMAN_REVIEW')
(TD/'SCIENTIFIC_RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
# Before/after Ring, topology, self-intersection, displacement and face diagnostics.
initial_by={r['case']:r['initial_geometry_dense64']for r in initial_geometry if 'initial_geometry_dense64'in r};geometry_rows=[]
for r in body:
 if r['status']!='NUMERIC':continue
 before=initial_by.get(r['case']);after=r['world_geometry'];geometry_rows.append(dict(case=r['case'],arm=r['arm'],initial=before,final=after,initial_identity=next(c for c in source['cases']if c['case']==r['case'])['resolved013_initial'],initial_dense64_source_commit=TASK['contour']['parent_commit'],ring_negative_min_change_mm=float(min(0,after['ring_min_dense64_mm'])-min(0,before['ring_min_dense64_mm']))if before else None))
(VIS/'GEOMETRY_BEFORE_AFTER.json').write_text(json.dumps(geometry_rows,indent=2)+'\n')
# Version sources pin every reused file and all world baselines.
versions=[]
for r in json.loads(Path(TASK['inita']['assets']['code_lock']['path']).read_text())['files']:versions.append(dict(role='exact015_source',path=r['path'],sha256=r['sha256'],commit=r['commit']))
for r in TASK['contour']['baseline_assets']:versions.append(dict(role='frozen_parent_identity',**r,commit=TASK['contour']['parent_commit']))
for r in source['frozen_assets']:versions.append(dict(role='frozen_data_identity',**r,commit=TASK['contour']['parent_commit']))
for base in ['src/ring_first_3d/contour_guided','src/ring_first_3d/inita','src/ring_first_3d/multisurface']:
 for p in (ROOT/base).glob('*.py'):versions.append(dict(role='execution_source',path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),commit=json.loads((TD/'EXECUTION_VERSION.json').read_text())['implementation_commit']))
(TD/'VERSION_SOURCES.json').write_text(json.dumps(versions,indent=2)+'\n')
with(TD/'VERSION_SOURCES.csv').open('w',newline='')as f:w=csv.DictWriter(f,['role','path','sha256','commit'],extrasaction='ignore');w.writeheader();w.writerows(versions)
# Redraw final GT reference itself gray while keeping actual aligned copies and metric bounds.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
srcby={r['case']:r for r in source['cases']};fig=plt.figure(figsize=(18,44),layout='constrained')
for row,g in enumerate(TASK['inita']['cases']):
 gt=dict(np.load(srcby[g]['GT']['path']));arms={}
 for arm in ['A0','A2','A3']:
  p=VIS/'meshes'/(g+'_'+arm+'_ALIGNED.npz')
  if p.exists():arms[arm]=dict(np.load(p))
 allv=np.concatenate([gt['V']]+[m['V']for m in arms.values()]);center=(allv.min(0)+allv.max(0))/2;rad=np.ptp(allv,axis=0).max()*.55
 for col,arm in enumerate(['A0','A2','A3','GT']):
  ax=fig.add_subplot(11,4,row*4+col+1,projection='3d');ax.add_collection3d(Poly3DCollection(gt['V'][gt['F']],facecolors=(.5,.5,.5,.35 if arm!='GT'else .8),edgecolors='none'));title=g+' '+arm
  if arm!='GT'and arm in arms:
   m=arms[arm];ax.add_collection3d(Poly3DCollection(m['V'][m['F']],facecolors=(.5,.15,.7,.8),edgecolors='none'));rr=by[g,arm];title+='\nstrict '+str(rr['IoU_3D'])+'; conditional %.4f\nCD %.3f / p95 %.3fmm'%(rr['conditional_occupancy_IoU'],rr['Chamfer_MAE_mm'],rr['Chamfer_P95_mm'])
  elif arm!='GT':title+=' NOT_EVALUABLE'
  ax.set(xlim=(center[0]-rad,center[0]+rad),ylim=(center[1]-rad,center[1]+rad),zlim=(center[2]-rad,center[2]+rad),xlabel='X [mm]',ylabel='Y [mm]',zlabel='Z [mm]');ax.set_box_aspect((1,1,1));ax.view_init(15,-65);ax.tick_params(labelsize=5);ax.set_title(title,fontsize=8)
fig.suptitle('Figure2 | Actual scale1 rigid-aligned copies: gray independent GT / purple prediction\nSource-world models remain untouched for HERO. GT reference is gray in all columns.',fontsize=11);fig.savefig(VIS/'figures/Fig2_ALL_BODY_GT.png',dpi=100);plt.close(fig)
# Re-render actual sections with one common extent including ALL source surfaces, retaining outliers.
from matplotlib.collections import LineCollection
from ring_first_3d.multisurface.geometry import mesh_sections,plane_coordinates
section_audit=[]
for group in hpred['groups']:
 if group['status']!='NUMERIC':continue
 g=group['case'];dat=[v for v in groups[g]['views']if v['role']=='FIT'];meshes={}
 for rr in group['records']:
  if rr['status']=='NUMERIC':meshes[rr['method']]=[dict(np.load(VIS/'meshes'/g/rr['method']/(v['id']+'.npz')))for v in dat]
 bodies={a:dict(np.load(VIS/'meshes'/(g+'_'+a+'_WORLD.npz')))for a in ['A2','A3']};ring=dict(np.load(groups[g]['assets']['ring']['path']));base=np.concatenate([bodies['A2']['V'],bodies['A3']['V'],ring['V']]);center=(base.max(0)+base.min(0))/2;rad=max(.5,np.ptp(base,axis=0).max()*.55);planes=[(0,center[0]-.12*rad),(1,center[1]+.12*rad),(2,center[2]-.12*rad),(2,center[2]+.12*rad)];allv=np.concatenate([base]+[m['V']for mm in meshes.values()for m in mm]);cc=(allv.max(0)+allv.min(0))/2;rrad=max(.5,np.ptp(allv,axis=0).max()*.55);fig,axes=plt.subplots(4,4,figsize=(19,16),layout='constrained');counts=[]
 for row,(axis,offset)in enumerate(planes):
  dims=[i for i in range(3)if i!=axis]
  for col,method in enumerate(['M0','H1','H3','H4']):
   ax=axes[row,col];arm='A3'if method=='H4'else'A2'
   for mm,color,style in [(bodies[arm],'gray','--'),(ring,'black','-')]:ax.add_collection(LineCollection(plane_coordinates(mesh_sections(mm['V'],mm['F'],axis,offset),axis),colors=color,linewidths=1.1,linestyles=style))
   for v,mm in zip(dat,meshes.get(method,[])):
    segments=mesh_sections(mm['V'],mm['F'],axis,offset);ax.add_collection(LineCollection(plane_coordinates(segments,axis),colors='red'if v['video']=='004'else'blue',linewidths=.6,alpha=.7));counts.append(dict(method=method,view=v['id'],axis=axis,offset_mm=float(offset),triangle_intersection_segments=len(segments)))
   ax.set(xlim=(cc[dims[0]]-rrad,cc[dims[0]]+rrad),ylim=(cc[dims[1]]-rrad,cc[dims[1]]+rrad),xlabel='XYZ'[dims[0]]+' [mm]',ylabel='XYZ'[dims[1]]+' [mm]',title=method+' / '+'XYZ'[axis]+'=%.3fmm'%offset);ax.set_aspect('equal');ax.grid(alpha=.2)
 fig.suptitle(g+' Figure3 | Exact native triangle-plane intersections; red004 / blue005 / gray Body / black Ring\nSame physical planes for every method; fixed limits include all complete original/corrected surfaces. No fused skin / average contour.',fontsize=11);fig.savefig(VIS/'figures'/(g+'_Fig3_HERO_SECTIONS.png'),dpi=115);plt.close(fig);section_audit.append(dict(case=g,plane_specifications=[dict(axis=a,offset_mm=float(o))for a,o in planes],common_center_mm=cc.tolist(),common_half_width_mm=float(rrad),all_surface_vertices_in_extent=True,segments=counts))
(VIS/'EXACT_MESH_SECTION_AUDIT.json').write_text(json.dumps(section_audit,indent=2)+'\n')
# Portable glTF uses metres; NPZ and all scientific axes remain in mm. No prediction is changed.
GLB_units=[]
for path in(VIS/'meshes').glob('*.glb'):
 scene=trimesh.load(path,force='scene',process=False)
 if scene.metadata.get('export_scale_from_source')!=.001:scene.apply_scale(.001)
 scene.metadata.update(unit='m',one_coordinate_unit_mm=1000,source_coordinate_unit='mm',export_scale_from_source=.001);path.write_bytes(scene.export(file_type='glb'));GLB_units.append(dict(path=str(path.relative_to(VIS)),coordinate_unit='m',source_coordinate_unit='mm',source_to_export_scale=.001,full_mesh_topology=True))
(VIS/'GLB_EXPORT_UNITS.json').write_text(json.dumps(GLB_units,indent=2)+'\n')
# Put numerical conclusions before the long evidence tables, retain the first mechanism figure.
p=TD/'TECHNICAL_REPORT.md';text=p.read_text();needle='## All-case comparisons';addition='## Frozen aggregate results\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n\nA2 Mesh bytes are unchanged. All arms are re-evaluated in this task using one common Sobol domain per case, so its newly reported occupancy estimate can differ slightly from the prior report; the original report metrics remain in evidence/ORIGINAL_A2_EVALUATION.json. Strict and conditional occupancy are never interchanged. Per-view gradient/actual shared displacement evidence reports descent-work attribution, not a uniquely identifiable causal decomposition of the shared vertex update. No per-view meshes or image transforms are optimized.\n\n';p.write_text(text.replace(needle,addition+needle,1))
(TD/'RESULT_CARD.md').write_text('# '+TASK['task_id']+'\n\n[Technical report](TECHNICAL_REPORT.md) · [body all11](visualization/BODY_SHAPE_METRICS.csv) · [HERO all11](visualization/HERO_ALL11_METRICS.csv) · [failure ledger](visualization/FAILURE_LEDGER.json)\n\n```json\n'+json.dumps(summary,indent=2)+'\n```\n\nNo GT/HOLDOUT model selection; source-world coordinates never GT aligned. Full missing-case denominator retained.\n')
# A plain offline file index, as requested; images are the review product.
paths=sorted(p for p in VIS.rglob('*')if p.is_file()and p.name!='index.html');page='<!doctype html><meta charset="utf-8"><title>PNG and GLB artifact index</title><h1>Scientific PNG / GLB files</h1><p>Images are the primary review deliverable. GLB coordinates: metres (source NPZ / scientific axes: mm, export factor 0.001). Full named triangle meshes, no fused skin.</p><a href="../TECHNICAL_REPORT.md">Technical report</a><ul>'
for p in paths:rel=str(p.relative_to(VIS));page+='<li><a href="'+html.escape(rel)+'">'+html.escape(rel)+'</a></li>'
(VIS/'index.html').write_text(page+'</ul>\n')
# Curated manifest and local assertions are finalized by verify_delivery.py.
all_runs={r.name:json.loads((r/'RUN_MANIFEST.json').read_text())['spent_seconds']for r in(TD/'runs').glob('CONTOUR_*')if(r/'RUN_MANIFEST.json').is_file()};(TD/'RUN_MANIFEST.json').write_text(json.dumps(dict(schema='contour-delivery-1',task_id=TASK['task_id'],runner_accepted=True,freeze_sha256=STATE['freeze_sha256'],original_run=str(RUN),spent_seconds=STATE['spent_seconds'],all_preserved_run_seconds=all_runs,total_preserved_run_seconds=sum(all_runs.values()),budget=TASK['budget'],summary=summary),indent=2)+'\n')
print(json.dumps(summary,indent=2))
