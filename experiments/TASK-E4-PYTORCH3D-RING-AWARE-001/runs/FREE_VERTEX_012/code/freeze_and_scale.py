from common import *

def main():
 runs=load(R/'runtime/SERIAL_STATUS.json');assert len(runs)==9
 for a in load(R/'assets_index/PREOPT_FREEZE.json')['files']:assert sha(a['path'])==a['sha256'],a['path']
 for a in load(R/'assets_index/HISTORY_011_PROTECTION.json'):assert sha(a['path'])==a['sha256'],a['path']
 files=[asset(p)for p in sorted((R/'local_results').rglob('*'))if p.is_file()];save('assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json',dict(files=files,time_epoch=time.time(),GT_read=False,model_selection='last accepted at predetermined stop',cases=9))
 rows=[];metricfiles=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];rr=np.load(R/'inputs'/n/'RING.npz');V=rr['V'];center=V.mean(0);_,Q=np.linalg.eigh((V-center).T@(V-center));normal=Q[:,0];radial=(V-center)-((V-center)@normal)[:,None]*normal;diam=float(2*np.linalg.norm(radial,axis=1).min());true={'R5':5.,'R10':10.}[c['ring']];ratio=true/diam;applied=1. if abs(ratio-1)<=1e-4 else ratio;out=R/'local_results/metric'/n;out.mkdir(parents=True,exist_ok=True)
  for tag,path in [('C011',R/'inputs'/n/'C_011.npz'),('FINAL011',R/'inputs'/n/'INITIAL.npz'),('FINAL012',R/'local_results'/n/'FINAL.npz')]:
   if not path.exists():continue
   z=dict(np.load(path));z['V']=center+applied*(z['V']-center);np.savez_compressed(out/(tag+'.npz'),**z);metricfiles.append(asset(out/(tag+'.npz')))
  np.savez_compressed(out/'RING.npz',V=center+applied*(V-center),F=rr['F']);metricfiles.append(asset(out/'RING.npz'));u=Q[:,1];v=Q[:,2];angle=np.arctan2(radial@v,radial@u);bins=np.floor((angle+np.pi)/(2*np.pi)*32).astype(int)%32;radii=np.linalg.norm(radial,axis=1);section_inner=np.array([2*radii[bins==i].min()for i in range(32)if(bins==i).any()]);rows.append(dict(case=n,source_ring=c['ring'],true_inner_diameter_mm=true,CAD_measured_inner_diameter=diam,inner_azimuth_diameter_min=float(section_inner.min()),inner_azimuth_diameter_max=float(section_inner.max()),inner_azimuth_relative_spread=float(np.ptp(section_inner)/diam),recovery_ratio=ratio,applied_scale=applied,already_metric=applied==1.,center=center,source=asset(R/'inputs'/n/'RING.npz'),measurement='2*min radial vertex radius in CAD own PCA plane; 32-sector inner-rim consistency',GT_used=False,scale_locked=True,not_independent_Ring_size_prediction=True))
 save('metrics/RING_SCALE_VALIDATION.json',rows);table('metrics/RING_SCALE_VALIDATION.csv',rows);save('assets_index/SCALE_LOCK_BEFORE_GT.json',dict(files=metricfiles,scale_table_sha256=sha(R/'metrics/RING_SCALE_VALIDATION.json'),time_epoch=time.time(),GT_read=False,all_scale_from_fixed_CAD=True));print('NINE_PREDICTIONS_AND_RING_SCALE_FROZEN')

if __name__=='__main__':main()
