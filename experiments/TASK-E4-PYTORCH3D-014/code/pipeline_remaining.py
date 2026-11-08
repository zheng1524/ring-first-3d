"""Serial continuation C-recovery -> video control -> D -> E -> final freeze.
No Blender data are opened by this script. It stops after all predictions freeze.
"""
from driver014 import *
import shutil

def subprocess_gpu(script,args,envroot,log):
 with log.open('a')as f:subprocess.run([PY,'-B',str(MASTER/'code'/script)]+list(map(str,args)),env=dict(os.environ,E4_RUN_DIR=str(envroot)),stdout=f,stderr=subprocess.STDOUT,check=True)

def video_controls():
 for tag in ['B_A_ONLY','B0_UNCORRECTED']:
  root=setup(tag,'C1_8','D0_013');casep=root/'inputs/G01/CASE.json';meta=load(casep)
  if tag=='B_A_ONLY':
   for v in meta['views']:
    if v['video']!='004':v['role']='UPDATE_HOLDOUT'
  else:
   for v in meta['views']:
    if v['video']=='004':continue
    p=root/'inputs/G01'/(v['id']+'.npz');z=dict(np.load(p));z['T']=np.array(v['T_original'])
    if p.is_symlink():p.unlink()
    np.savez_compressed(p,**z)
  casep.write_text(json.dumps(meta,ensure_ascii=False,indent=2));save('provenance/'+tag+'_VIEW_FREEZE.json',dict(epoch=time.time(),case=asset(casep),camera_mode=tag,GT_used=False));run(tag,'C1_8','D0_013',cases=['G01'])

def refine_stage():
 coarse=load(MASTER/'config/D_SELECTION.json')['method'];ccfg=load(MASTER/'arms'/coarse/'config/ARM.json');view,loss=ccfg['view_arm'],ccfg['loss'];tags=['E0_none','E1_global','E2_adaptive']
 save('provenance/E_METHOD_FROZEN.json',dict(epoch=time.time(),coarse=coarse,view=view,loss=loss,local_signal='FIT apparent contour gradient >=75th nonzero quantile in at least2views, highest20%vertices; OR edge stretch>1.5 with nonzero FIT signal',single_subdivision=True,normalization='common coarse restriction, area-averaged fine residual .01; optimizer reset',GT_read=False,code=[asset(MASTER/'code'/p)for p in ['refine_mesh.py','bmesh_subdivide.py','refinement_prior.py','density_preflight.py']]))
 for tag in tags:
  root=setup(tag,view,loss,start=coarse)
  for n in CASES:
   initial=root/'inputs'/n/'SHAPE_REFERENCE.npz';log=MASTER/'runtime'/(tag+'_'+n+'_PREPARE.log')
   if not initial.exists():subprocess_gpu('refine_mesh.py',[n,tag,MASTER/'arms'/coarse/'local_results'/n/'FINAL.npz',root],MASTER/'arms'/coarse,log)
   p=root/'metrics'/(n+'_DENSITY_CONTROL.json')
   if not p.exists():subprocess_gpu('density_preflight.py',[n],root,log)
   run(tag,view,loss,start=coarse,cases=[n])
 chosen=select(tags,'E');save('provenance/FINAL_METHOD_FROZEN_BEFORE_HOLDOUT_GT.json',dict(epoch=time.time(),C=view,D=loss,E=chosen,coarse=coarse,GT_used=False,HOLDOUT_used_for_method_selection=False))
 # Check actual prior normalization before final adoption; retain every value.
 controls=[]
 for n in CASES:
  vals=[load(MASTER/'arms'/tag/'metrics'/(n+'_DENSITY_CONTROL.json'))for tag in tags];ref=vals[0]['values'];err=max(abs(v['values'][k]['prior']-ref[k]['prior'])for v in vals for k in range(2));controls.append(dict(case=n,max_E_prior_control_difference=err,passed=err<1e-5))
 table('metrics/DENSITY_NORMALIZATION_CONTROLS.csv',controls)
 if not all(c['passed']for c in controls):raise RuntimeError('Density-invariance control failed; no silent final adoption')
 root=setup('FINAL_014',view,loss,formal=True,start=chosen)
 for n in CASES:
  source=MASTER/'arms'/chosen/'inputs'/n/'SHAPE_REFERENCE.npz';dest=root/'inputs'/n/'SHAPE_REFERENCE.npz'
  if not dest.exists():dest.symlink_to(source)
 run('FINAL_014',view,loss,formal=True,start=chosen)
 files=[];scales=[]
 for c in load(MASTER/'config/CASE_LOCK.json'):
  n=c['name'];source=root/'local_results'/n/'FINAL.npz'
  if not source.exists():raise RuntimeError('Final prediction actually missing: '+n)
  rg=np.load(MASTER/'inputs'/n/'RING.npz');diam=2*np.linalg.norm(rg['V'][:,:2],axis=1).min();true=5. if c['ring']=='R5'else 10.;factor=true/diam;assert abs(factor-1)<1e-6,'Metric CAD mismatch; do not secretly rescale';out=MASTER/'meshes'/n;out.mkdir(exist_ok=True);dest=out/'FINAL014_mm.npz';shutil.copyfile(source,dest);files.append(asset(dest));scales.append(dict(case=n,diameter_true_mm=true,CAD_inner_diameter_mm=float(diam),derived_scale_factor=float(factor),applied_scale_factor=1.,scale_locked=True,source='fixed CAD in existing Ring-First metric frame',GT_used=False))
 save('metrics/RING_SCALE_VALIDATION.json',scales);table('metrics/RING_SCALE_VALIDATION.csv',scales);save('provenance/ALL_014_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json',dict(epoch=time.time(),files=files,scale=asset(MASTER/'metrics/RING_SCALE_VALIDATION.json'),code=[asset(p)for p in (MASTER/'code').glob('*.py')],GT_used=False));print('ALL_FINAL_PREDICTIONS_FROZEN_NO_GT',flush=True)

def main():
 while not(MASTER/'config/C_SELECTION.json').exists():time.sleep(5)
 # Resume any objective engineering interruption from exact optimizer checkpoints.
 for tag in ['C0','C1_8','C2_16','C3_32','C4_ALL']:run(tag,tag,'D0_013')
 select(['C0','C1_8','C2_16','C3_32','C4_ALL'],'C');video_controls()
 view=load(MASTER/'config/C_SELECTION.json')['method'];tags=[view]
 for loss in ['D1_split','D2_bidir','D3_combo']:tag='D_'+loss;run(tag,view,loss);tags.append(tag)
 select(tags,'D');refine_stage()
if __name__=='__main__':main()
