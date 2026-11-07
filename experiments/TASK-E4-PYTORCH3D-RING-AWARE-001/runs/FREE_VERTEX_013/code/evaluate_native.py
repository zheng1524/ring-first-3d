from evaluation_kernels import *

def main():
 for a in load(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json')['files']:assert sha(a['path'])==a['sha256']
 summary=[];allper=[];records=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];rr=np.load(R/'inputs'/n/'RING.npz');rs=scene(rr['V'],rr['F']);ring=trimesh.Trimesh(rr['V'],rr['F'],process=False);initial=np.load(R/'inputs'/n/'INITIAL.npz');variants=[(tag,R/'local_results/metric'/n/(tag+'.npz'))for tag in ['FINAL011','FINAL012','FINAL013']]
  for label,path in variants:
   if not path.exists():continue
   z=dict(np.load(path));g=geometry(c,z,rs,ring);rt=scene(z['V'],z['F']);per=view_metrics(c,z,rt,rs);rec=dict(case=n,type=c['morphology'],label=label,path=str(path),accepted=int(z.get('accepted',0)),**g,displacement_from_011FINAL_mm=stats(np.linalg.norm(z['V']-initial['V'],axis=1)),evaluation_frame='original frozen cameras before rigid alignment')
   for role,key in [('FIT','FIT'),('HOLDOUT','HOLDOUT')]:
    subset=[x for x in per if (x['role']=='FIT')==(role=='FIT')];depth=[x for x in subset if x['fixed_depth_N']>0];N=sum(x['fixed_depth_N']for x in depth);rec[key+'_IoU']=float(np.mean([x['IoU']for x in subset]));rec[key+'_Mask_coverage']=float(np.mean([x['Mask_coverage']for x in subset]));rec[key+'_contour_MAE_px']=float(np.mean([x['contour_px']['MAE']for x in subset if x['contour_px']['MAE']is not None]));rec[key+'_fixed_depth_N']=N;rec[key+'_depth_hits']=sum(x['depth_hit_N']for x in depth);rec[key+'_depth_coverage']=sum(x['depth_hit_N']for x in depth)/N if N else None;rec[key+'_fixed_depth_cost']=sum(x['raw_fixed_depth_cost']*x['fixed_depth_N']for x in depth)/N if N else None
   # Visible evidence is a projection qualification, never an anatomical truth label.
   P=z['V'][z['F']].mean(1);supported=np.zeros(len(P),bool)
   for v in c['views']:
    if v['role']!='FIT':continue
    a=np.load(R/'inputs'/n/(v['id']+'.npz'));uv,zz,rz=pointcast(rs,P,a['K'],a['T']);_,_,bz=pointcast(rt,P,a['K'],a['T']);inside=(zz>0)&(uv[:,0]>=0)&(uv[:,0]<640)&(uv[:,1]>=0)&(uv[:,1]<360);pix=np.clip(np.rint(uv).astype(int),[0,0],[639,359]);supported|=inside&(a['labels'][pix[:,1],pix[:,0]]==1)&(zz<rz)&(abs(zz-bz)<.05)
   dest=R/'local_results/native_eval'/n;dest.mkdir(parents=True,exist_ok=True);np.savez_compressed(dest/(label+'_FACE_EVIDENCE.npz'),face_supported=supported,face_ID=np.arange(len(P)),not_physical_GT=True);summary.append(rec);records.append(dict(**rec,per_view=per));allper.extend(dict(case=n,label=label,**x)for x in per)
  print('NATIVE_EVAL',n,flush=True)
 save('metrics/NATIVE_SUMMARY.json',summary);table('metrics/NATIVE_SUMMARY.csv',summary);save('metrics/NATIVE_RESULTS.json',records);save('metrics/PER_VIEW_METRICS.json',allper);table('metrics/PER_VIEW_METRICS.csv',allper)

if __name__=='__main__':main()
