"""Read-only evidence/quality reporting after prediction+evaluation; no GT tuning."""
from pathlib import Path
import sys,json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[3];TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from common import load_case
from figures import mesh,bounds,save
from smooth_arap import SmoothARAP
from ring_first_3d.synthetic.raster import ray_map
import torch,trimesh

def read(p):return json.loads(p.read_text())
def run():
 state=read(TD/'runs/PILOT_002/RUN_MANIFEST.json');assert state.get('accepted');figdir=TD/'visualization/figures';extra=[];csvrows=[];quality=[];growth=[]
 for case in ['G01','G03','G05']:
  initial,views,ring,base,chart,source=load_case(case,'FIT');fig,axes=plt.subplots(4,4,figsize=(14,9))
  for ax,v in zip(axes.flat,views):
   r=ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape);target=v['labels']==2;cad=r['valid'];ax.imshow(v['RGB']);ax.contour(target,levels=[.5],colors=['lime'],linewidths=.7);ax.contour(cad,levels=[.5],colors=['red'],linewidths=.7);iou=(target&cad).sum()/max(1,(target|cad).sum());ax.set_title(v['id']+'\nRing IoU '+f'{iou:.3f}',fontsize=7);ax.axis('off')
  fig.suptitle(case+' | real Ring Mask green / CAD projection red | all original FIT retained');name=case+'_RING_PROJECTION_AUDIT.png';save(fig,figdir/name);extra.append(name)
  if initial['inferred_base_faces'].any():
   bodies=[('INITIAL',initial)]+[(a,dict(np.load(TD/'runs'/case/a/'FINAL.npz')))for a in ['DEFORM_ONLY','DEFORM_SWEEP']if (TD/'runs'/case/a/'FINAL.npz').exists()];VV=np.concatenate([b['V']for _,b in bodies]+[ring['V']]);fig=plt.figure(figsize=(12,4))
   for j,(name,b)in enumerate(bodies):
    ax=fig.add_subplot(1,3,j+1,projection='3d');cap=b['inferred_base_faces'];mesh(ax,dict(b,F_solid=b['F_solid'][~cap]),'purple',.6);mesh(ax,dict(b,F_solid=b['F_solid'][cap]),'orange',1.);mesh(ax,ring,'black',.2);bounds(ax,VV.min(0)-.5,VV.max(0)+.5,elev=-20,azim=-65);ax.set_title(name+' | orange=inferred cap',fontsize=8)
   fig.suptitle(case+' | predicted Body purple; inherited inferred cap orange, not observed anatomy');name=case+'_INFERRED_CAP_PROVENANCE.png';save(fig,figdir/name);extra.append(name)
  for arm in ['DEFORM_ONLY','DEFORM_SWEEP']:
   folder=TD/'runs'/case/arm
   if not (folder/'FINAL.npz').exists():continue
   final=dict(np.load(folder/'FINAL.npz'));u=read(folder/'UPDATES.json');steps=u['iterations'];s0=np.load(folder/'INITIAL.npz');lo=np.r_[initial['V'],final['V'],ring['V']].min(0)-.5;hi=np.r_[initial['V'],final['V'],ring['V']].max(0)+.5;D=np.linalg.norm(final['V'][:len(initial['V'])]-initial['V'],axis=1);F=final['F_solid'];tri=final['V'][F];edges=np.stack([np.linalg.norm(tri[:,1]-tri[:,0],axis=1),np.linalg.norm(tri[:,2]-tri[:,0],axis=1),np.linalg.norm(tri[:,2]-tri[:,1],axis=1)],1);area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)*.5;aspect=4*np.sqrt(3)*area/(edges*edges).sum(1)
   fig=plt.figure(figsize=(14,4));ax=fig.add_subplot(131,projection='3d');faceD=np.zeros(len(final['F_solid']));mask=(final['F_solid']<len(D)).all(1);faceD[mask]=D[final['F_solid'][mask]].mean(1);maxD=max(float(faceD.max()),1e-10);mesh(ax,final,'purple',.9,values=faceD/maxD);mesh(ax,ring,'black',.2);bounds(ax,lo,hi);ax.set_title(f'Actual vertex displacement 0..{maxD:.4f}mm',fontsize=8);ax=fig.add_subplot(132)
   for name in ['ARAP','smooth','graph']:ax.plot([x['iteration']for x in steps],[x['energies'][name]for x in steps],label=name)
   ax.set_yscale('symlog',linthresh=1e-6);ax.set_xlabel('fixed outer iteration');ax.set_title('Measured regularizer energies');ax.legend(fontsize=7);ax=fig.add_subplot(133);ax.hist(aspect,bins=30);ax.set_xlabel('equilateral quality (1=best)');ax.set_title(f'Actual mesh triangle quality; min {aspect.min():.4f}',fontsize=8);fig.suptitle(case+' '+arm+' | geometry evidence');name=case+'_'+arm+'_QUALITY.png';save(fig,figdir/name);extra.append(name)
   quality.append(dict(case=case,arm=arm,vertex_displacement_MAE_mm=float(D.mean()),vertex_displacement_P95_mm=float(np.quantile(D,.95)),vertex_displacement_max_mm=float(D.max()),min_triangle_quality=float(aspect.min()),median_triangle_quality=float(np.median(aspect)),ARAP_final=steps[-1]['energies']['ARAP'],smooth_final=steps[-1]['energies']['smooth'],graph_final=steps[-1]['energies']['graph'],SARAP_final=steps[-1]['energies']['SARAP']))
   swp=folder/'STEP_035/SWEEP.npz'
   proposals=sorted(folder.glob('GROWTH_PROPOSAL_*/SWEEP.npz'));visual_sweep=swp if swp.exists()else(proposals[0]if proposals else None)
   if visual_sweep is not None:
    from matplotlib.collections import LineCollection
    sw=np.load(visual_sweep);candidate=dict(np.load(visual_sweep.with_name('BODY.npz')));m=trimesh.Trimesh(candidate['V'],candidate['F_solid'],process=False);fig,axes=plt.subplots(1,3,figsize=(12,4));limit=max(float(sw['axes'].max())*2,.2)
    for ax,station in zip(axes,[3,7,11]):
     seg,faces=trimesh.intersections.mesh_plane(m,sw['frame_t'][station],sw['centerline'][station],return_faces=True);xy=np.einsum('nki,ij->nkj',seg-sw['centerline'][station],np.stack([sw['frame_r'][station],sw['frame_s'][station]],-1));is_new=(candidate['F_solid'][faces]>=len(initial['V'])).any(1);ax.add_collection(LineCollection(xy[~is_new],colors='gray',linewidths=.7));ax.add_collection(LineCollection(xy[is_new],colors='purple',linewidths=1.2));ax.set_xlim(-limit,limit);ax.set_ylim(-limit,limit);ax.set_aspect('equal');ax.set_xlabel('RMF e1 mm');ax.set_ylabel('RMF e2 mm');ax.set_title(f'actual triangle cut s={station}/15',fontsize=8)
    fig.suptitle(case+' '+arm+' | '+('ACCEPTED'if swp.exists()else'REJECTED candidate')+' | gray original Body / purple generated sweep');name=case+'_'+arm+'_SWEEP_TRIANGLE_SECTIONS.png';save(fig,figdir/name);extra.append(name)
   if swp.exists():
    sw=np.load(swp);C=sw['centerline'];F0=initial['F_solid'];deformed=final['V'][:len(initial['V'])];vol0=trimesh.Trimesh(deformed,F0,process=False).volume;vol1=trimesh.Trimesh(final['V'],F,process=False).volume;frame=np.stack([sw['frame_r'],sw['frame_s'],sw['frame_t']],-1);orth=float(abs(np.transpose(frame,(0,2,1))@frame-np.eye(3)).max());cont=float((sw['frame_r'][1:]*sw['frame_r'][:-1]).sum(1).min());growth.append(dict(case=case,arm=arm,accepted=True,length_mm=float(np.linalg.norm(np.diff(C,axis=0),axis=1).sum()),net_sweep_added_volume_mm3=float(vol1-vol0),total_body_volume_change_mm3=float(vol1-trimesh.Trimesh(initial['V'],F0,process=False).volume),RMF_orthogonality_max_error=orth,RMF_min_neighbor_axis_dot=cont,axes_mm=sw['axes'].tolist(),root_ids=sw['root_loop'].tolist()))
   else:growth.append(dict(case=case,arm=arm,accepted=False,length_mm=0.,net_sweep_added_volume_mm3=0.,status='No accepted sweep; no stalk length inferred',attempts=[dict(iteration=e['iteration'],status=e['status'],support_rows=e['support_rows'],eligible_patches=e['eligible_patches'],candidate_support=[{k:c[k]for k in ['seed','support_views','support_videos','singular_ratio','inconsistency']}for c in e['candidates']],seed_rejections={x:sum(x in d['rejections']for d in e['seed_diagnostics'])for x in {x for d in e['seed_diagnostics']for x in d['rejections']}})for e in u['growth']]))
 for g in growth:
  folder=TD/'runs'/g['case']/g['arm'];update=read(folder/'UPDATES.json');g['candidate_trials']=[]
  for event in update['growth']:
   step=read(folder/f'STEP_{event["iteration"]:03d}.json');trials=step['rejections'];g['candidate_trials'].append(dict(iteration=event['iteration'],status=event['status'],reasons=sorted({x for t in trials for x in t['reasons']}),first_candidate_geometry=trials[0].get('geometry')if trials else None,evidence=str(folder/f'STEP_{event["iteration"]:03d}.json')))
 # Per-video split means retain all original view denominators.
 with (TD/'metrics/PER_VIEW_METRICS.csv').open()as f:per=list(csv.DictReader(f))
 video_rows=[]
 for key in sorted({(r['case'],r['arm'],r['role'],r['video'])for r in per}):
  group=[r for r in per if (r['case'],r['arm'],r['role'],r['video'])==key];video_rows.append(dict(zip(['case','arm','role','video'],key),views=len(group),IoU=float(np.mean([float(r['IoU'])for r in group])),Boundary_MAE_px=float(np.mean([float(r['Boundary_MAE_px'])for r in group])),Boundary_Fscore_at2px=float(np.mean([float(r['Boundary_Fscore_at2px'])for r in group]))))
 with (TD/'metrics/VIDEO_SPLIT_METRICS.csv').open('w')as f:w=csv.DictWriter(f,list(video_rows[0]));w.writeheader();w.writerows(video_rows)
 # Read-only derived diagnostics, original Runner metrics retained verbatim.
 for filename,data in [('STRUCTURED_QUALITY_METRICS.csv',quality)]:
  with (TD/'metrics'/filename).open('w')as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 (TD/'evidence/GROWTH_DIAGNOSTICS.json').write_text(json.dumps(growth,indent=2))
 ledger_path=TD/'FAILURE_REGISTRY.json';ledger=read(ledger_path)
 for q in quality:
  if q['vertex_displacement_max_mm']<1e-4:ledger['records'].append(dict(id='STAGNATION-'+q['case']+'-'+q['arm'],type='SCIENTIFIC_NEGATIVE',case=q['case'],arm=q['arm'],symptom='NUMERICAL_STAGNATION',confirmed_cause='Measured maximum original vertex displacement below 1e-4mm; accepted-step count is not success',evidence=str(TD/'metrics/STRUCTURED_QUALITY_METRICS.csv'),rule_status='candidate',permanent_rule=False))
 ledger_path.write_text(json.dumps(ledger,indent=2))
 # Correct distinguish total body volume change from new sweep volume, without touching original evaluator output.
 p=TD/'metrics/BODY_METRICS.csv'
 with p.open()as f:reader=csv.DictReader(f);keys=reader.fieldnames;rows=list(reader)
 for r in rows:
  g=next((x for x in growth if x['case']==r['case']and x['arm']==r['arm']),None)
  if g:r['growth_volume_mm3']=g['net_sweep_added_volume_mm3']
 with p.open('w')as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
 index=TD/'visualization/index.html';page=index.read_text();page+='\n<h2>Additional fixed-input geometry diagnostics</h2>'
 for n in extra:page+=f'<details><summary>{n}</summary><img loading="lazy" src="figures/{n}"></details>'
 index.write_text(page)
 print('Read-only diagnostics',len(extra),'actual figures')
if __name__=='__main__':run()
