"""Secondary fixed-material/common-rigid evaluation ONLY, after Policy acceptance.
Never replaces historical independently best-rigid primary endpoints or selects models.
"""
from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[3];TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from common import load_case
from ring_first_3d.multisurface.geometry import sample_mesh,scene,closest
from ring_first_3d.multisurface.evaluate import fixed_stats

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 run=TD/'runs/PILOT_002';state=json.loads((run/'RUN_MANIFEST.json').read_text());assert state.get('accepted');evaluation=next((run/'attempts').glob('0008-G2_evaluate-*'));rows=[];identities={}
 for case in ['G01','G03','G05']:
  initial,_,_,_,_,_=load_case(case,'FIT');base=np.load(evaluation/case/'INITIAL_GT_ALIGNED.npz');T0=base['T'];gt=dict(np.load(evaluation/case/'GT.npz'));G,_,_=sample_mesh(gt['V'],gt['F'],12000,20261118);_,faces,bary=sample_mesh(initial['V'],initial['F'],12000,20261117);gt_scene=scene(gt['V'],gt['F']);baseline=None
  for arm in ['INITIAL','DEFORM_ONLY','DEFORM_SWEEP']:
   p=None if arm=='INITIAL'else(TD/'runs'/case/arm/'FINAL.npz').resolve();body=initial if p is None else dict(np.load(p));digest=None if p is None else sha(p)
   if not np.array_equal(body['F'],initial['F']):continue # Material-ID diagnostic only when topology identical, no remapping.
   V=body['V']@T0[:3,:3].T+T0[:3,3];P=np.einsum('ni,nij->nj',bary,V[body['F'][faces]]);Q,_,_=closest(gt_scene,P);d=np.linalg.norm(P-Q,axis=1);Q,_,_=closest(scene(V,body['F']),G);e=np.linalg.norm(G-Q,axis=1);metric=fixed_stats(np.r_[d,e]);own=np.load(evaluation/case/(arm+'_GT_ALIGNED.npz'))['T'];D=own@np.linalg.inv(T0)
   row=dict(case=case,arm=arm,N_per_direction=12000,common_INITIAL_SE3_fixed=True,shared_material_faces_bary=True,common_frame_Chamfer_MAE_mm=metric['MAE'],common_frame_Chamfer_p95_mm=metric['p95'],own_alignment_vs_initial_rotation_deg=float(np.rad2deg(Rotation.from_matrix(D[:3,:3]).magnitude())),own_alignment_vs_initial_translation_mm=float(np.linalg.norm(D[:3,3])),actual_vertex_displacement_max_mm=float(np.linalg.norm(body['V']-initial['V'],axis=1).max()),aligned_copy_displacement_max_mm=float(np.linalg.norm(np.load(evaluation/case/(arm+'_GT_ALIGNED.npz'))['V']-base['V'],axis=1).max()))
   rows.append(row)
   if p is not None:assert sha(p)==digest;identities[case+'/'+arm]=dict(path=str(p),sha256=digest)
 with (TD/'metrics/ALIGNMENT_SENSITIVITY_DIAGNOSTIC.csv').open('w')as f:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
 (TD/'evidence/ALIGNMENT_SENSITIVITY.json').write_text(json.dumps(dict(purpose='Independent post-freeze numerical sensitivity diagnostic only; no training/model selection; primary historical best-rigid evaluation unchanged',task_sha256=sha(TD/'TASK.yaml'),canonical_evaluation_sha256=sha(evaluation/'EVALUATION.json'),prediction_identity=identities,rows=rows),indent=2))
 # Show BOTH primary independently fitted and common-reference views; no winner selection.
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from figures import mesh,bounds,save
 for case in ['G01','G03','G05']:
  initial,_,_,_,_,_=load_case(case,'FIT');T0=np.load(evaluation/case/'INITIAL_GT_ALIGNED.npz')['T'];gt=dict(np.load(evaluation/case/'GT.npz'));models=[]
  for arm in ['INITIAL','DEFORM_ONLY','DEFORM_SWEEP']:
   b=initial if arm=='INITIAL'else dict(np.load(TD/'runs'/case/arm/'FINAL.npz'));aligned=dict(b,V=b['V']@T0[:3,:3].T+T0[:3,3]);models.append((arm,aligned));np.savez_compressed(TD/'review_assets'/case/(arm+'_COMMON_INITIAL_GT_FRAME.npz'),**aligned,T=T0)
  allV=np.concatenate([gt['V']]+[b['V']for _,b in models]);lo=allV.min(0)-.3;hi=allV.max(0)+.3;fig=plt.figure(figsize=(12,7))
  for row,(el,az)in enumerate([(20,-65),(5,25)]):
   for j,(arm,b)in enumerate(models):
    ax=fig.add_subplot(2,3,row*3+j+1,projection='3d');mesh(ax,gt,'gray',.2);mesh(ax,b,'purple',.65);bounds(ax,lo,hi,el,az);r=next(x for x in rows if x['case']==case and x['arm']==arm);ax.set_title(arm+f' | MAE {r["common_frame_Chamfer_MAE_mm"]:.5f} mm',fontsize=8)
  fig.suptitle(case+' | FIXED INITIAL->GT SE(3), shared material samples | secondary diagnostic ONLY');name=case+'_COMMON_GT_REFERENCE.png';save(fig,TD/'visualization/figures'/name)
  index=TD/'visualization/index.html';index.write_text(index.read_text()+f'<details><summary>{name}</summary><img src="figures/{name}"></details>')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':run()
