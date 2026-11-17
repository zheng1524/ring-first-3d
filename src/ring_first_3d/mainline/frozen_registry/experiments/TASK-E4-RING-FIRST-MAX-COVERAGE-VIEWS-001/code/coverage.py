"""Fixed source-tagged surfels + greedy visible-set maximum coverage, not fusion."""
from geometry_io import *
from rgb import features,mutual

def proxy(g):
 path=selpath(g,'_PROXY.npz');path.parent.mkdir(exist_ok=True);conf,ss=frozen_sources(g);src=[];XX=[];NN=[];AA=[];FF=[];scenes=[]
 for i,s in enumerate(ss):
  tri=s['V'][s['F']];nn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);ar=np.linalg.norm(nn,axis=1)/2;nn/=np.maximum(2*ar[:,None],1e-15);sign=np.sign(nn[np.arange(len(nn)),np.argmax(abs(nn),axis=1)]);nn*=sign[:,None];X=tri.mean(1);XX.append(X);NN.append(nn);AA.append(ar);src.append(np.full(len(X),i));FF.append(s['mesh'].get('original_face_id',np.arange(len(X))));scenes.append(scene(s['V'],s['F']))
 X=np.concatenate(XX);norm=np.concatenate(NN);area=np.concatenate(AA);sid=np.concatenate(src);fid=np.concatenate(FF);key=np.c_[np.floor(X/.2).astype(int),np.rint(norm/.5).astype(int)];uni,ix,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
 # Correlated sources don't add independent area. Mean per-source bin area;
 # one representative original triangle retained with full original face provenance.
 weight=np.zeros(len(uni));ct=np.zeros(len(uni));
 for k in range(len(ss)):
  vals=np.bincount(inv[sid==k],weights=area[sid==k],minlength=len(uni));weight+=vals;ct+=vals>0
 weight/=np.maximum(ct,1);corr=ct.astype(int);repX=X[ix];repn=norm[ix];reps=sid[ix];repf=fid[ix];np.savez_compressed(path,X=repX,normal=repn,weight_mm2=weight,source_index=reps,original_face_id=repf,source_correlation_N=corr,key=uni,source_ids=[s['id']for s in ss]);return conf,ss,scenes,dict(np.load(path))

def visible(X,C,K,lab,sc,ring,tol=.15):
 uv,z=projection(X,C,K);p=np.floor(np.nan_to_num(uv,nan=-1e9,posinf=-1e9,neginf=-1e9)+.5).astype(int);ok=(z>0)&(p[:,0]>=0)&(p[:,0]<640)&(p[:,1]>=0)&(p[:,1]<360);ix=np.flatnonzero(ok);out=np.zeros(len(X),bool);unknown=np.zeros(len(X),bool)
 if len(ix):
  pix=p[ix];own=cast_points(sc,uv[ix],C,K)['t_hit'].numpy();cad=cast_points(ring,uv[ix],C,K)['t_hit'].numpy();surface=np.isfinite(own)&(abs(own-z[ix])<=tol);unknown[ix]=~np.isfinite(own);out[ix]=(lab[pix[:,1],pix[:,0]]==1)&surface&(z[ix]<cad-.05)
 return out,unknown

def direction_stats(vs):
 if not vs:return dict(N=0,max_deg=None,median_deg=None,NN_median_deg=None,occupied_blocks=0,total_blocks=72)
 d=np.array([unit(np.array(v['C'])[:3,3])for v in vs]);ang=np.degrees(np.arccos(np.clip(d@d.T,-1,1)));pairs=ang[np.triu_indices(len(d),1)];np.fill_diagonal(ang,np.inf);az=np.mod(np.degrees(np.arctan2(d[:,1],d[:,0])),360);el=np.degrees(np.arcsin(d[:,2]));blocks=set(zip((az//30).astype(int),np.clip(((el+90)//30).astype(int),0,5)));return dict(N=len(vs),max_deg=float(pairs.max())if len(pairs)else 0,median_deg=float(np.median(pairs))if len(pairs)else 0,NN_median_deg=float(np.median(ang.min(1)))if len(vs)>1 else None,occupied_blocks=len(blocks),total_blocks=72)

def greedy(vs,vis,weight,source_filter=None):
 chosen=[];covered=np.zeros(len(weight),bool);r=[];left=[i for i,v in enumerate(vs)if source_filter is None or v['video']in source_filter];total=weight.sum();dirs=[]
 while left and len(chosen)<36:
  c=[]
  for i in left:
   v=vs[i];di=unit(np.array(v['C'])[:3,3]);sep=min((angle(di,x)for x in dirs),default=180.)
   if sep<1.5:continue
   gain=float(weight[vis[i]&~covered].sum());qual=(v['RGB_evaluation']['FIT']['N']/(1+v['RGB_evaluation']['FEATURE_HELD']['median']))*(1-v['glare_fraction']);c.append((gain,sep,qual,i))
  if not c:break
  # Area primary; within0.1%absolute proxy area tie, prefer genuinely new direction.
  best=max(x[0]for x in c);ties=[x for x in c if x[0]>=best-.001*total];gain,sep,qual,i=max(ties,key=lambda x:(x[1],x[2]))
  # Don't pad36. Once8 chosen, stop if both newarea and newdirection exhausted.
  if len(chosen)>=8 and gain<.002*total and sep<5:break
  covered|=vis[i];chosen.append(i);dirs.append(unit(np.array(vs[i]['C'])[:3,3]));left.remove(i);r.append(dict(rank=len(chosen),id=vs[i]['id'],video=vs[i]['video'],marginal_mm2=gain,cumulative_mm2=float(weight[covered].sum()),proxy_total_mm2=float(total),min_direction_to_selected_deg=sep))
 return chosen,r

def support_pairs(vs,target):
 cache=N/'local_results/SUPPORT_RGB_PAIR_CACHE'/(target['id']+'.json')
 if cache.exists():
  old=load(cache)
  if old['pool_ids']==[v['id']for v in vs]:return old['pairs']
 ft=features(target);C=np.array(target['C']);out=[]
 for s in vs:
  if s['id']==target['id']:continue
  a=angle(C[:3,3],np.array(s['C'])[:3,3]);
  if a<1 or a>60:continue
  fs=features(s);mm=mutual(ft['des'],fs['des']);n=len(mm)
  if n<12:continue
  i=np.array([p[0]for p in mm]);j=np.array([p[1]for p in mm]);u=ft['xy'][i];v=fs['xy'][j];D=np.linalg.inv(np.array(s['C']))@C;t=D[:3,3];sk=np.array([[0,-t[2],t[1]],[t[2],0,-t[0]],[-t[1],t[0],0]]);F=np.linalg.inv(K0).T@sk@D[:3,:3]@np.linalg.inv(K0);p=np.c_[u,np.ones(n)];q=np.c_[v,np.ones(n)];fp=p@F.T;fq=q@F;err=abs((q*fp).sum(1))/np.maximum(np.sqrt((fp[:,:2]**2+fq[:,:2]**2).sum(1)),1e-12);good=err<=3.;nn=int(good.sum());
  if nn<12:continue
  up=u[good];cells=len(set(zip((up[:,0]//80).astype(int),(up[:,1]//60).astype(int))));over=nn/max(1,min(len(ft['xy']),len(fs['xy'])));ray1=(np.c_[u[good],np.ones(nn)]@np.linalg.inv(K0).T)@C[:3,:3].T;ray2=(np.c_[v[good],np.ones(nn)]@np.linalg.inv(K0).T)@np.array(s['C'])[:3,:3].T;ray1/=np.linalg.norm(ray1,axis=1)[:,None];ray2/=np.linalg.norm(ray2,axis=1)[:,None];par=np.degrees(np.arccos(np.clip((ray1*ray2).sum(1),-1,1)));pa=float(np.median(par));score=nn*(cells/48)*np.exp(-((pa-10)/20)**2)*over;out.append(dict(id=s['id'],video=s['video'],score=float(score),matches=n,geometric_inliers=nn,epipolar_px=stats(err[good]),parallax_deg=stats(par),direction_deg=a,grid_cells=cells,RGB_overlap_proxy=over))
 out=sorted(out,key=lambda s:s['score'],reverse=True);save(str(cache.relative_to(N)),dict(pool_ids=[v['id']for v in vs],pairs=out));return out

def main(g):
 checkfreeze('provenance/'+g+'_CAMERAS_FROZEN_BEFORE_HELD_HERO.json');allv=load(camera_file(g));vs=[v for v in allv if v['formal']and v['role']=='FIT'];conf,ss,sc,pr=proxy(g);rv=np.load(conf['ring']['path']);ring=scene(rv['V'],rv['F']);weight=pr['weight_mm2'];vis=[];unknown=[];body=np.load(conf['bodies']['B0']['path']);bv=body['V']if'V'in body else body['vertices'];bf=body['F']if'F'in body else body['faces'];bt=bv[bf];bX=bt.mean(1);ba=trimesh.triangles.area(bt);bsc=scene(bv,bf);bodyvis=[]
 for v in vs:
  C=np.array(v['C']);lab=np.load(v['cache'])['labels'];out=np.zeros(len(weight),bool);unk=np.zeros(len(weight),bool)
  for i,s in enumerate(ss):
   ix=np.flatnonzero(pr['source_index']==i);vi,uu=visible(pr['X'][ix],C,K0,lab,sc[i],ring);out[ix]=vi;unk[ix]=uu
  vis.append(out);unknown.append(unk);bodyvis.append(visible(bX,C,K0,lab,bsc,ring)[0])
 vis=np.array(vis,bool).reshape(len(vs),len(weight));bodyvis=np.array(bodyvis,bool).reshape(len(vs),len(bX));rank,rows=greedy(vs,vis,weight);selected=[vs[i]for i in rank];proxyid=[v['id']for v in vs];np.savez_compressed(selpath(g,'_VISIBILITY.npz'),candidate_ids=proxyid,visible=vis,unknown=unknown,body_visible=bodyvis,body_X=bX,body_area_mm2=ba,rank_indices=rank)
 for row in rows:row['group']=g
 table(str(selroot(g).relative_to(N))+'/'+g+'_MAX_COVERAGE.csv',rows);counts=[];independent=[]
 for i in rank:
  if not independent or min(angle(np.array(vs[i]['C'])[:3,3],np.array(vs[j]['C'])[:3,3])for j in independent)>=5:independent.append(i)
 baseline=[];basevis=[];basebody=[];basev=[]
 for pp in conf['views']:
  if pp['role']!='FIT' or pp['video']!='004':continue
  d=np.load(pp['cache']);C=d['T'];lab=d['labels'];out=np.zeros(len(weight),bool)
  for i,s in enumerate(ss):
   ix=np.flatnonzero(pr['source_index']==i);out[ix]=visible(pr['X'][ix],C,K0,lab,sc[i],ring)[0]
  basevis.append(out);basebody.append(visible(bX,C,K0,lab,bsc,ring)[0]);basev.append(dict(id=pp['view_id'],C=C,video='004'))
 if basevis:
  cc=np.array(basevis).any(0);bc=np.array(basebody).any(0);counts.append(dict(group=g,requested='HISTORICAL_ACTUAL_BASELINE',actual_N=len(basev),IDs=[v['id']for v in basev],direction=direction_stats(basev),HERO_proxy_visible_mm2=float(weight[cc].sum()),HERO_proxy_total_mm2=float(weight.sum()),body_visible_mm2=float(ba[bc].sum()),body_total_mm2=float(ba.sum()),direction1_mm2=None,direction2_mm2=None,direction3_mm2=None,unknown_HERO_proxy_mm2=float(weight[~cc].sum()),status='UNCHANGED018FITCAMERAS_LITERALBASELINE'))
 sets=[('E1_MATCH_BASELINE_N',rank[:len(basev)])]+[(str(n),rank[:n])for n in [8,12,20,28,36]]
 for label,ids in sets:
  vv=[vs[i]for i in ids];covered=vis[ids].any(0)if ids else np.zeros(len(weight),bool);ii=[i for i in independent if i in ids];directions=vis[ii].sum(0)if ii else np.zeros(len(weight),int);bc=bodyvis[ids].any(0)if ids else np.zeros(len(bX),bool);counts.append(dict(group=g,requested=label,actual_N=len(ids),IDs=[v['id']for v in vv],direction=direction_stats(vv),HERO_proxy_visible_mm2=float(weight[covered].sum()),HERO_proxy_total_mm2=float(weight.sum()),body_visible_mm2=float(ba[bc].sum()),body_total_mm2=float(ba.sum()),direction1_mm2=float(weight[directions>=1].sum()),direction2_mm2=float(weight[directions>=2].sum()),direction3_mm2=float(weight[directions>=3].sum()),unknown_HERO_proxy_mm2=float(weight[~covered].sum()),status='AVAILABLE'if label=='E1_MATCH_BASELINE_N'or len(ids)==int(label)else'NOT_ENOUGH_NONREDUNDANT_VALIDATED_CAMERAS'))
 contribution=[]
 for name,flt in [('004',['004']),('004+005',['004','005']),('004+005+PHOTO',['004','005','PHOTO'])]:
  ii,rr=greedy(vs,vis,weight,flt);cov=vis[ii].any(0)if ii else np.zeros(len(weight),bool);contribution.append(dict(group=g,sources=name,actual_N=len(ii),ids=[vs[i]['id']for i in ii],coverage_mm2=float(weight[cov].sum()),direction=direction_stats([vs[i]for i in ii]),same_frozen_eligible_pool=True))
 # Supports scored separately from targetcoverage. Match only formal FIT cameras.
 supports=[];plans=[]
 for v in selected:
  cand=support_pairs(vs,v);chosen=[]
  for s in cand:
   # prevent three nearly identical source views from dominating by match count.
   sv=next(x for x in vs if x['id']==s['id'])
   if chosen and min(angle(np.array(sv['C'])[:3,3],np.array(next(x for x in vs if x['id']==q['id'])['C'])[:3,3])for q in chosen)<1:continue
   chosen.append(s)
   if len(chosen)==3:break
  supports.append(dict(group=g,target=v['id'],support_N=len(chosen),selected=chosen,all_legal_candidates=cand,status='READY'if len(chosen)==3 else'INSUFFICIENT_VALIDATED_RGB_SUPPORT'))
  if len(chosen)==3:plans.append(dict(group=g,id=v['id'],view_id=v['id'],variant='GEOMETRIC3',target=v,support_views=[next(x for x in vs if x['id']==c['id'])for c in chosen],rank=next(r['rank']for r in rows if r['id']==v['id']),reused=False))
  print('SUPPORT',g,v['id'],len(chosen),flush=True)
 # E4 one input-selected canonical target with literal018 support IDs, current camera fixed.
 oldplan=load(P18/'config/VIEW_PLAN.json')
 for pp in oldplan:
  if pp['group']!=g or pp['role']!='FIT':continue
  target=next((v for v in selected if v['id']==pp['view_id']or pp['view_id']in v.get('aliases',[])),None)
  if target is None:continue
  sources=[]
  for sid in pp['support_views']:
   match=next((v for v in vs if v['id']==sid or sid in v.get('aliases',[])),None)
   if match is not None:sources.append(match)
  if len(sources)==3:plans.append(dict(group=g,id=target['id']+'__E4_018',view_id=target['id'],variant='ORIGINAL018_LITERAL3_CURRENT_POSES',target=target,support_views=sources,rank=None,reused=False));break
 save(str(selroot(g).relative_to(N))+'/'+g+'_SUPPORTS.json',supports);save(str(selroot(g).relative_to(N))+'/'+g+'_HERO_PLAN.json',plans);save(str(selroot(g).relative_to(N))+'/'+g+'_COUNT_ABLATION.json',counts);save(str(selroot(g).relative_to(N))+'/'+g+'_SOURCE_CONTRIBUTIONS.json',contribution);save(str(selroot(g).relative_to(N))+'/'+g+'_SELECTION.json',dict(group=g,eligible_N=len(vs),ranked=rows,recommended_N=len(rank),baseline_ids=[v['id']for v in basev],independent_direction_ids=[vs[i]['id']for i in independent],proxy_identity='0.2mm spatial/30degree normal bins;area meanwithinoccupiedsourcebins; not true anatomical area',selection_HERO_parents=[s['id']for s in ss],held_HERO_parents=0));freeze(planfreeze(g),[selpath(g,suffix)for suffix in ['_SELECTION.json','_HERO_PLAN.json','_COUNT_ABLATION.json','_SOURCE_CONTRIBUTIONS.json']],before_newHERO=True,GT=False);print('COVERAGE_PLAN',g,'eligible',len(vs),'targets',len(rank),'ready',len(plans),flush=True)
if __name__=='__main__':main(sys.argv[1])
