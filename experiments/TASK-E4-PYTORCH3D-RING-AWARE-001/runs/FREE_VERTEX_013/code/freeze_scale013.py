from common import *
import shutil
MASTER=Path(__file__).resolve().parents[1]
def main():
 done=load(R/'runtime/ALL_PREDICTIONS_COMPLETED.json');assert len(done['cases'])==11;files=[];rows=[];metric=[]
 for n in done['cases']:
  root=R/'arms/FINAL_UNIFORM';src=root/'local_results'/n;out=R/'local_results'/n;shutil.copytree(src,out,dirs_exist_ok=True)
  for p in (root/'metrics').glob(n+'*'):
   if 'CANDIDATES'in p.name and p.suffix=='.csv':continue
   shutil.copyfile(p,R/'metrics'/p.name)
  files += [asset(p)for p in out.iterdir()if p.is_file()]
  c=getcase(n);r=np.load(R/'inputs'/n/'RING.npz');V=r['V'];center=V.mean(0);_,Q=np.linalg.eigh((V-center).T@(V-center));normal=Q[:,0];radial=(V-center)-((V-center)@normal)[:,None]*normal;diam=float(2*np.linalg.norm(radial,axis=1).min());true={'R5':5.,'R10':10.}[c['ring']];ratio=true/diam;applied=1. if abs(ratio-1)<=1e-4 else ratio
  stages=[('FINAL011',R/'inputs'/n/'INITIAL.npz'),('FINAL012',R.parent/'FREE_VERTEX_012/local_results'/n/'FINAL.npz'if n not in ['G10','G11']else R/'arms/REPLAY_012_FULL/local_results'/n/'FINAL.npz'),('FINAL013',out/'FINAL.npz')];dest=R/'local_results/metric'/n;dest.mkdir(parents=True,exist_ok=True)
  for tag,p in stages:
   z=dict(np.load(p));z['V']=center+applied*(z['V']-center);np.savez_compressed(dest/(tag+'.npz'),**z);metric.append(asset(dest/(tag+'.npz')))
  rows.append(dict(case=n,Ring=c['ring'],diameter_true_mm=true,CAD_diameter_mm=diam,recovery_ratio=ratio,applied_scale=applied,already_metric=applied==1.,scale_locked=True,GT_used=False,new_group_baseline_recipe_equivalent=n in ['G10','G11']))
 save('assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json',dict(epoch=time.time(),files=files,cases=11,GT_read=False,selection=done['selected']));save('metrics/RING_SCALE_VALIDATION.json',rows);table('metrics/RING_SCALE_VALIDATION.csv',rows);save('assets_index/SCALE_LOCK_BEFORE_GT.json',dict(epoch=time.time(),files=metric,GT_read=False,scale_from_Ring_only=True));print('ELEVEN_PREDICTIONS_SCALE_FROZEN')
if __name__=='__main__':main()
