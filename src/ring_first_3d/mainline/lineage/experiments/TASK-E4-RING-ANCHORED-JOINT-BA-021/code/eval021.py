"""Independent post-freeze 020-compatible evaluation, plus unused SIFT track tests."""
from geometry021 import *
import evaluate020 as ev
from objective020 import SymmetricFeatures
from ring020 import RingRenderer,tensor,torch
from scipy.spatial.transform import Rotation

METHODS=['B0_RoMa','B0_020_R2','B0_020_R3','B0_020_MASK','B1','B2','B3','SENS_B2_LightGlue','SENS_B2_020R2']
def methods():return [dict(method=n,T=load(R/'results'/(n+'.json'))['T'])for n in METHODS]

def independent_tracks():
 excluded=[set(),set()];ban={}
 for t in load(R/'observations/CROSS_COMMON_TRACKS.json'):
  excluded[0].add(t['source_landmark004']);excluded[1].add(t['source_landmark005'])
  for o in t['observations']:ban.setdefault(o['view'],[]).append(o['uv'])
 rows=[]
 for role in ['FIT','HOLDOUT']:
  f=SymmetricFeatures('CROSS',held=role=='HOLDOUT')
  for direction,obs in enumerate(f.directions):
   for a in obs:
    keep=np.array([k not in excluded[direction]for k in a['landmark']]);uv=a['uv'].detach().cpu().numpy()
    if a['view']in ban:keep&=(np.linalg.norm(uv[:,None]-np.asarray(ban[a['view']])[None],axis=-1).min(1)>1e-4)
    ix=np.flatnonzero(keep);a['X']=a['X'][ix];a['uv']=a['uv'][ix];a['landmark']=a['landmark'][ix]
  for m in methods():
   with torch.no_grad():F,E,p=f.evaluate(tensor(m['T'],torch.float64),details=True)
   valid=all(p[k]['N']>0 for k in ['forward','reverse']);rows.append(dict(method=m['method'],role=role,source_tracks_and_exact_target_feature_pixels_disjoint_from_BA=True,excluded_source_track_counts=[len(s)for s in excluded],F=float(F)if valid else None,symmetric_status='COMPUTED'if valid else'NOT_EVALUABLE_EMPTY_DIRECTION',E_full_2D_only_pool_diagnostic=float(E),E_not_claimed_track_disjoint=True,**p))
 save('metrics/UNUSED_SIFT_TRACK_EVALUATION.json',rows);table('metrics/UNUSED_SIFT_TRACK_EVALUATION.csv',rows)

def negative():
 n=load(R/'config/NEGATIVE_SPLIT.json');vv={v['id']:v for v in load(R/'config/VIEWS.json')};ids=n['target_fit']+n['target_holdout'];rr=RingRenderer(ids);d=np.load(R/'inputs/G01/BODY018.npz');body=scene(d['V'],d['F']);rv=np.load(R/'inputs/G01/RING.npz');cad=scene(rv['V'],rv['F']);per=[];out=[];plan=[('IDENTITY',np.eye(4))]+[(a,np.asarray(load(R/'results'/(a+'.json'))['T']))for a in ['NEG_B1','NEG_B2','NEG_B3']]+[('020_NEGATIVE_R3',np.asarray(load(P20/'results/NEGATIVE_R3.json')['T']))]
 for name,H in plan:
  for cid in ids:
   v=vv[cid];a=np.load(v['cache']);C=H@a['T'];z=cast(body,a['K'],C,360,640);rz=cast(cad,a['K'],C,360,640);pred=np.isfinite(z)&(z<rz);target=a['labels']==1
   with torch.no_grad():ls,aux,_=rr.losses(tensor(H,torch.float64),cid)
   per.append(dict(method=name,view=cid,role=v['role'],IoU=float((pred&target).sum()/max(1,(pred|target).sum())),Ring_M=float(ls['M']),Inner_px=aux['I']['distance_px'],Outer_px=aux['O']['distance_px']))
  row=dict(method=name,translation_mm=float(np.linalg.norm(H[:3,3])),rotation_deg=float(np.degrees(Rotation.from_matrix(H[:3,:3]).magnitude())),T=H)
  for role in ['FIT','HOLDOUT']:
   sub=[x for x in per if x['method']==name and x['role']==role];row[role+'_IoU']=float(np.mean([x['IoU']for x in sub]));row[role+'_N']=len(sub)
   with torch.no_grad():F,E,p=SymmetricFeatures('NEGATIVE',held=role=='HOLDOUT').evaluate(tensor(H,torch.float64),details=True)
   row[role+'_SIFT']=dict(F=float(F),E=float(E),**p)
  out.append(row)
 save('metrics/NEGATIVE_CONTROL.json',out);table('metrics/NEGATIVE_CONTROL.csv',out);save('metrics/NEGATIVE_PER_VIEW.json',per);table('metrics/NEGATIVE_PER_VIEW.csv',per)

def main():
 wait_freeze();ev.methods=methods;ev.body_ring_eval();independent_tracks();negative();ev.hero_eval();save('runtime/BA_INDEPENDENT_EVALUATION_COMPLETE.json',dict(epoch=time.time(),methods=METHODS,no_feedback_to_optimization=True));print('021_BA_EVALUATION_COMPLETE',flush=True)
 import layer_diagnostic020 as ld
 ld.methods=methods;ld.main()
if __name__=='__main__':main()
