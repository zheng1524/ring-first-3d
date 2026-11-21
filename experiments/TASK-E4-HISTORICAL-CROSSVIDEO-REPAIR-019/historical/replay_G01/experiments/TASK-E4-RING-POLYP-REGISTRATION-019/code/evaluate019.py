from common import *
from scipy.spatial.transform import Rotation
from scipy.ndimage import binary_erosion
import features019

def methods(scope):
 s=load(R/'results'/(scope+'_SEARCH_SELECTION.json'));f=load(R/'results'/(scope+'_A5_FINAL.json'));out=[dict(tag='IDENTITY_CANONICAL_RING_ONLY',T=np.eye(4),kind='DIAGNOSTIC')]
 if scope=='CROSS':out +=[dict(tag='A0_'+x['tag'],T=x['T'],kind='HISTORICAL',status=x['status'])for x in load(R/'config/HISTORICAL_CANDIDATES.json')]
 for key in ['A1','A2','A3','A4']:
  if s[key]is not None:out.append(dict(tag=key,T=s[key]['T'],kind='NEW',yaw_deg=s[key]['yaw_deg'],parity=s[key]['parity']))
 out.append(dict(tag='A5',T=f['T'],kind='NEW'));return out

def contour_stats(pred,target):
 p,q=contour(pred),contour(target)
 if not len(p)or not len(q):return dict(MAE=None,median=None,p95=None,maximum=None,N=0)
 return stats(np.r_[cKDTree(p).query(q)[0],cKDTree(q).query(p)[0]])
def ring_edges(mask):
 c,h=cv2.findContours(mask.astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_NONE)
 if h is None:return np.empty((0,2)),np.empty((0,2))
 outer=[x[:,0]for x,y in zip(c,h[0])if y[3]<0];inner=[x[:,0]for x,y in zip(c,h[0])if y[3]>=0];return np.concatenate(inner)if inner else np.empty((0,2)),np.concatenate(outer)if outer else np.empty((0,2))

def main():
 freeze=load(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json')
 for a in freeze['results']:assert sha(a['path'])==a['sha256']
 views=load(R/'config/VIEWS.json');features019.VIEWS={v['id']:v for v in views};fit4=[v['id']for v in views if v['video']=='004'and v['role']=='FIT'];hold5=[v['id']for v in views if v['video']=='005'and v['role']=='HOLDOUT'];neg=load(R/'config/NEGATIVE_SPLIT.json');features019.cross(fit4,hold5,dict(np.load(R/'landmarks/CROSS_004.npz')),'CROSS_HOLDOUT');features019.cross(neg['reference_fit'],neg['target_holdout'],dict(np.load(R/'landmarks/NEGATIVE_004.npz')),'NEGATIVE_HOLDOUT')
 a=np.load(R/'inputs/G01/BODY018.npz');rv=np.load(R/'inputs/G01/RING.npz');body=scene(a['V'],a['F']);ring=scene(rv['V'],rv['F']);per=[];summary=[]
 for scope in ['CROSS','NEGATIVE']:
  vv=[v for v in views if v['video']=='005']if scope=='CROSS'else[v for v in views if v['id']in neg['target_fit']+neg['target_holdout']]
  for meth in methods(scope):
   H=np.asarray(meth['T']);F=H[:3,:3];t=H[:3,3];rnorm=float(np.degrees(np.arccos(np.clip(abs(F[2,2]),-1,1))));rangle=float(np.degrees(Rotation.from_matrix(F).magnitude()));yaw=float(np.degrees(np.arctan2(F[1,0],F[0,0]))%360);outdir=R/'evaluation'/scope/meth['tag'];outdir.mkdir(parents=True,exist_ok=True)
   for v in vv:
    d=np.load(v['cache']);T=H@d['T'];z=cast(body,d['K'],T,360,640);rz=cast(ring,d['K'],T,360,640);pred=np.isfinite(z)&(z<rz);target=d['labels']==1;intersection=(pred&target).sum();union=(pred|target).sum();IoU=float(intersection/max(1,union));coverage=float(intersection/max(1,target.sum()));extra=float((pred&~target).sum()/max(1,pred.sum()));cb=contour_stats(pred,target);ri,ro=ring_edges(np.isfinite(rz));obs=np.load(R/'ring'/(v['id']+'.npz'));ir=cKDTree(ri).query(obs['inner'])[0]if len(ri)and len(obs['inner'])else np.array([]);orr=cKDTree(ro).query(obs['outer'])[0]if len(ro)and len(obs['outer'])else np.array([]);known=d['labels']!=1;RP=np.isfinite(rz)&known;RT=(d['labels']==2)&known;R_iou=float((RP&RT).sum()/max(1,(RP|RT).sum()));row=dict(scope=scope,method=meth['tag'],view=v['id'],role=v['role'],Polyp_pixels=int(target.sum()),IoU=IoU,foreground_coverage=coverage,extra_prediction_fraction=extra,contour_px=cb,Ring_inner_px=stats(ir),Ring_outer_px=stats(orr),Ring_known_IoU=R_iou);per.append(row);np.savez_compressed(outdir/(v['id']+'.npz'),pred=pred,target=target,body_z_mm=z,Ring_z_mm=rz);save('evaluation/per_view/'+scope+'_'+meth['tag']+'_'+v['id']+'.json',row)
   rows=[x for x in per if x['scope']==scope and x['method']==meth['tag']];rec=dict(scope=scope,method=meth['tag'],kind=meth['kind'],T=H,R=F,t_mm=t,center_displacement_mm=float(np.linalg.norm(t)),unsigned_Ring_normal_tilt_deg=rnorm,rotation_magnitude_deg=rangle,yaw_deg=yaw,scale_singular_values=np.linalg.svd(F,compute_uv=False),GT='NO_DEPLOYMENT_GT_USED')
   for role in ['FIT','HOLDOUT']:
    x=[x for x in rows if x['role']==role];rec[role+'_N']=len(x);rec[role+'_IoU']=float(np.mean([x['IoU']for x in x]))if x else None;rec[role+'_worst_IoU']=min([x['IoU']for x in x])if x else None;rec[role+'_contour_px']=float(np.mean([x['contour_px']['MAE']for x in x if x['contour_px']['MAE']is not None]))if x else None;rec[role+'_Ring_boundary_px']=float(np.mean([np.mean([x['Ring_inner_px']['MAE'],x['Ring_outer_px']['MAE']])for x in x if x['Ring_inner_px']['MAE']is not None and x['Ring_outer_px']['MAE']is not None]))if x else None
   summary.append(rec);print('EVAL019',scope,meth['tag'],'FIT/HOLD',rec['FIT_IoU'],rec['HOLDOUT_IoU'],flush=True)
 save('metrics/REGISTRATION_COMPARISON.json',summary);table('metrics/REGISTRATION_COMPARISON.csv',summary);save('metrics/ALL_FRAME_METRICS.json',per);table('metrics/ALL_FRAME_METRICS.csv',per);print('ALL_METHODS_FROZEN_EVALUATION_COMPLETE',flush=True)
if __name__=='__main__':main()
