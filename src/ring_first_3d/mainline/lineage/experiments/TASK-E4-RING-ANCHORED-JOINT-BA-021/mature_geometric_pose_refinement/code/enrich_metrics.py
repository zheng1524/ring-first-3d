"""Additional denominators/summary only. No new pose fitting or selection."""
from refine import *

def main():
 rows=load(M/'metrics/ALL_VIDEO_METHOD_METRICS.json');views={v['id']:v for v in load(M/'config/VIEWS.json')};groups=load(P/'config/FOUR_GROUP_INPUTS.json');cads={g['group']:RenderedCAD(g['ring']['path'])for g in groups};body={g['group']:np.load(g['bodies']['B2']['path'])for g in groups};scenes={g:scene(b['V'],b['F'])for g,b in body.items()};den=[]
 for r in rows:
  if r.get('C')is None:den.append(dict(group=r['group'],method=r['method'],id=r['id'],status=r['status'],Ring_union_N=None,body_union_N=None));continue
  v=views[r['id']];a=np.load(v['cache']);lab=a['labels'];C=np.array(r['C']);K=np.array(v['K']);rd=cast(cads[r['group']].cad,K,C,360,640);rp=np.isfinite(rd)&(lab!=1);rt=lab==2;bd=cast(scenes[r['group']],K,C,360,640);bp=np.isfinite(bd)&(~np.isfinite(rd)|(bd<rd-.05));pt=lab==1;rn=int((rp&rt).sum());rdn=int((rp|rt).sum());bn=int((bp&pt).sum());bdn=int((bp|pt).sum());assert abs(rn/max(1,rdn)-r['Ring_IoU'])<1e-12 and abs(bn/max(1,bdn)-r['body_IoU'])<1e-12;den.append(dict(group=r['group'],method=r['method'],id=r['id'],status=r['status'],Ring_intersection_N=rn,Ring_union_N=rdn,Ring_known_pixels_N=int((lab!=1).sum()),body_intersection_N=bn,body_union_N=bdn,unit='working640x360 pixels',rule='RingCAD prediction censored on observedPolyp unknown; bodyCAD front-order0.05mm',absolute_GT_accuracy='NOT_EVALUABLE'))
 save('metrics/EXACT_IMAGE_METRIC_DENOMINATORS.json',den);table('metrics/EXACT_IMAGE_METRIC_DENOMINATORS.csv',den)
 summary=load(M/'metrics/FOUR_GROUP_POSE_COMPARISON.json')
 for s in summary:
  rr=[r for r in rows if r['group']==s['group']and r['method']==s['method']and r['role']==s['role']and r.get('Ring_IoU')is not None]
  for src,dst in [('inner_P95_px','inner_P95_macro_px'),('outer_P95_px','outer_P95_macro_px')]:s[dst]=float(np.mean([r[src]for r in rr]))if rr else None
  s['worst_Ring_IoU']=min([r['Ring_IoU']for r in rr],default=None);s['worst_body_IoU']=min([r['body_IoU']for r in rr],default=None);s['SIFT_FIT_observations_N']=sum(r['SIFT_FIT']['N']for r in rr);s['SIFT_HELD_observations_N']=sum(r['SIFT_HELD']['N']for r in rr)
  for tag in ['SIFT_FIT','SIFT_HELD']:
   ev=[r[tag+'_EPI_px']for r in rr if r.get(tag+'_EPI_px')and r[tag+'_EPI_px']['N']];s[tag+'_EPI_observations_N']=sum(a['N']for a in ev);s[tag+'_EPI_MAE_macro_px']=float(np.mean([a['MAE']for a in ev]))if ev else None
  s['data_rank6_N']=sum(r.get('data_J_rank')==6 for r in rr);s['rank_tested_N']=sum('data_J_rank'in r for r in rr)
 save('metrics/FOUR_GROUP_POSE_COMPARISON.json',summary);table('FOUR_GROUP_POSE_COMPARISON.csv',[{k:('NaN'if v is None else v)for k,v in r.items()}for r in summary]);print('EXACT_DENOMINATORS_AND_P95_COMPLETE',flush=True)
if __name__=='__main__':main()
