from geometry import *
CFG=load(R/'config/PROTOCOL.json')

def main():
 srcs=load(R/'config/SOURCES.json');pool=load(M/'config/FINAL_CAMERA_POOL.json');out=[];receipts=[]
 for s in srcs:
  meta=load(s['source']);cache=s.get('target_cache')
  if cache is None:
   candidates=[v for v in pool if v['id']==s['view_id']or s['view_id']in v.get('aliases',[])];exact=[v for v in candidates if v.get('RGB_SHA256')==meta.get('target_SHA')];candidates=exact or candidates;assert candidates,s['id'];cache=candidates[0]['cache']
  a=np.load(cache);o=np.load(s['obs']);rgb=a['RGB'];labels=a['labels'];h,w=labels.shape;K=o['K'].copy();nh,nw=map(int,o['native_shape']);A=np.diag([w/nw,h/nh,1.]);A[:2,2]=np.array([w/nw,h/nh])*.5-.5;K=A@K;C=o['T'];e=ellipse_descriptor(labels==1);uv,z=project(o['X'],C,K);q=ellipse_coords(uv,e);inside=(q*q).sum(1)<=CFG['region_core_radius']**2;ids=sample_spatial(np.flatnonzero(inside),q[inside],CFG['region_anchors']);quality=np.full(len(o['uv']),'UNKNOWN',dtype='<U25');quality[inside]='CORE_REGION_CANDIDATE';regionpath=R/'inputs'/(s['id']+'.npz');np.savez_compressed(regionpath,RGB=rgb,labels=labels,K=K,C=C,anchor_index=ids,uv=uv,q=q,ellipse_center=e['center'],ellipse_axes=e['axes'],ellipse_U=e['U'],region_class=quality);rec=dict(s,cache=cache,view_cache=str(regionpath),ellipse=e,source_native_N=len(o['uv']),core_candidate_N=int(inside.sum()),anchors_N=len(ids),outside_core_N=int((~inside).sum()),C=C,K=K,RGB_content_SHA=hashlib.sha256(rgb.tobytes()).hexdigest(),Mask_content_SHA=hashlib.sha256(labels.tobytes()).hexdigest());out.append(rec)
  for key,p in [('observations',s['obs']),('trusted_mesh',s['mesh']),('source',s['source']),('image_cache',cache)]:receipts.append(dict(source=s['id'],kind=key,**asset(p)))
 for g in CFG['case_order']:
  root=P/'inputs'/g;v=load(root/'CASE.json');candidates=[a for a in v['views']if a['role']=='FIT'and a['video']=='004'];selected=[]
  # Image-only Ring-world origin for angular diversity; no Body/HERO mean used.
  for _ in range(min(CFG['body_fit_views'],len(candidates))):
   left=[a for a in candidates if a['id']not in selected]
   def score(x):
    c=np.load(root/(x['id']+'.npz'))['T'][:3,3];c=c/np.linalg.norm(c)
    return min([np.degrees(np.arccos(np.clip(c@d,-1,1)))for d in dirs],default=180.)
   dirs=[]
   for sid in selected:
    d=np.load(root/(sid+'.npz'))['T'][:3,3];dirs.append(d/np.linalg.norm(d))
   win=max(left,key=lambda a:(score(a),a['id']));selected.append(win['id'])
  save('config/'+g+'_BODY_FIT_VIEWS.json',dict(ids=selected,reference_video='004',selection='greedy complement from frozen018FIT; angular directions relative Ring origin, no HERO/old Body geometry'))
  (R/'inputs'/g).mkdir(exist_ok=True)
  for name in ['RING.npz','ALL_VIEW_META.json']:
   target=root/name
   if not(R/'inputs'/g/name).exists():(R/'inputs'/g/name).symlink_to(target.resolve())
  for sid in selected:
   target=root/(sid+'.npz')
   if not(R/'inputs'/g/target.name).exists():(R/'inputs'/g/target.name).symlink_to(target.resolve())
  receipts.append(dict(group=g,kind='Body-U',**asset(P/'runs'/g/'B3/FINAL.npz')));receipts.append(dict(group=g,kind='Ring',**asset(root/'RING.npz')))
 save('config/REAL_SOURCES.json',out);save('provenance/INPUT_SHA.json',receipts);save('provenance/PREPARATION.json',dict(epoch=time.time(),sources=len(out),by_group={g:sum(s['group']==g for s in out)for g in CFG['case_order']},Body_U_commit='e2d1eb16da103c0fa198596b4434c4ddfaebef8a',GT_used=False));print('PREPARED',len(out),flush=True)
if __name__=='__main__':main()
