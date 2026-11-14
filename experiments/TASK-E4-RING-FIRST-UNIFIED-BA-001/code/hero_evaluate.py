"""Frozen-only native HERO counterfactuals. No fitting, merging, ICP or new depth."""
from evaluate import *
import trimesh
# Read only the already-audited first-visible-depth query; no historical optimizer imports.
_VIS=extract(P/'code/evaluate020.py',['visibility_query'],dict(np=np,o3d=o3d));visibility_query=_VIS['visibility_query']

def sources(g,results=None,method='B0'):
 conf=next(c for c in load(N/'config/FOUR_GROUP_INPUTS.json')if c['group']==g);vs=[v for v in load(N/'config/VIEWS.json')if v['group']==g];out=[]
 for s in conf['sources']:
  assert sha(s['mesh']['path'])==s['mesh']['sha256']and sha(s['observation']['path'])==s['observation']['sha256'];a=dict(np.load(s['observation']['path']));m=dict(np.load(s['mesh']['path']));matches=[v for v in vs if s['id']==v['id']or s['id']in v.get('aliases',[])];v=matches[0]if len(matches)==1 else None;H0=np.array(load(N/'config/H0.json')['G01_005_to004'])if g=='G01'and s['video']=='005'else np.eye(4);C0=H0@a['T'];C=getpose(results,g,method,v['id'])if results is not None and v is not None else(C0 if method=='B0'else None)
  if C is None:out.append(dict(id=s['id'],status='MISSING_CAMERA_IDENTITY_NO_FALLBACK',source=s));continue
  # aX and native mV remain byte-unchanged on disk. D below is the sole view re-expression.
  D=C@np.linalg.inv(a['T']);grid=np.full(tuple(a['native_shape']),np.nan);grid[a['uv'][:,1],a['uv'][:,0]]=a['z'];normalgrid=np.full((*a['native_shape'],3),np.nan);normalgrid[a['uv'][:,1],a['uv'][:,0]]=a['normal']@D[:3,:3].T
  out.append(dict(id=s['id'],source=s,obs=a,mesh=m,C=C,D=D,X=a['X']@D[:3,:3].T+D[:3,3],V=m['V']@D[:3,:3].T+D[:3,3],F=m['F'],grid=grid,normal=a['normal']@D[:3,:3].T,normalgrid=normalgrid,video=s['video'],role=s['role'],canonical=v['id'],status='FROZEN_NATIVE_BASELINE'if method=='B0'else'RIGID_VIDEO_ONLY_NO_INTERNAL_CHANGE'if method=='B2'else'POSE_CHANGED_DEPTH_NOT_REINFERRED'))
 return conf,out

def compare(a,b,ring):
 r=visibility_query(a['X'],b['C'],b['obs']['K'],b['grid'],ring);uv,z=projection(a['X'],b['C'],b['obs']['K']);ij=np.floor(np.where(np.isfinite(uv),uv,-1e9)+.5).astype(int);h,w=b['grid'].shape;inside=(ij[:,0]>=0)&(ij[:,0]<w)&(ij[:,1]>=0)&(ij[:,1]<h);bn=np.full_like(a['normal'],np.nan);bn[inside]=b['normalgrid'][ij[inside,1],ij[inside,0]];an=a['normal'];nn=np.linalg.norm(an,axis=1)*np.linalg.norm(bn,axis=1);angle=np.degrees(np.arccos(np.clip(abs((an*bn).sum(1))/np.maximum(nn,1e-15),0,1)));angle[~r['supported']]=np.nan;r['normal_angle_deg']=angle;return r

def main():
 checkfreeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json');res=getresults();per=[];agg=[];source_rows=[];pairchoice=[];matchindex=[];local=N/'local_results/HERO_DIAGNOSTICS';local.mkdir(exist_ok=True)
 for g in GROUPS:
  conf,base=sources(g,res,'B0');ring,_=ray_scene(conf['ring']['path']);baseby={s['id']:s for s in base};choice=None;best=-1
  for method in ['B0','B1','B2','B3']:
   rr=res[g,method]
   if not rr.get('poses'):
    agg.append(dict(group=g,method=method,status=rr['status'],fixed_N=None,known_N=None));continue
   _,data=sources(g,res,method);sby={s['id']:s for s in data};bucket={k:dict(N=0,known=0,supported=0,front=0,behind=0,cad=0,unknown=0,dz=[],normal=[],common0=[],common1=[],gained=0,lost=0,threshold={t:0 for t in [.2,.5,1.]},pairs=0)for k in ['SAME_VIDEO','CROSS_VIDEO']}
   for a in data:
    if a['status'].startswith('MISSING'):matchindex.append(dict(group=g,method=method,source=a['id'],status=a['status']));continue
    area=trimesh.triangles.area(a['V'][a['F']]);fa0=trimesh.triangles.area(a['mesh']['V'][a['F']]);assert np.allclose(area,fa0,rtol=1e-9,atol=1e-10);source_rows.append(dict(group=g,method=method,id=a['id'],video=a['video'],canonical=a['canonical'],TRUSTED_faces_N=len(a['F']),TRUSTED_area_mm2=float(area.sum()),native_pixels_N=len(a['X']),face_ID_source=a['source']['mesh']['path'],geometry_status=a['status'],source_area_not_unique_anatomical_area=True))
    for b in data:
     if a['id']==b['id']or b['status'].startswith('MISSING'):continue
     scope='SAME_VIDEO'if a['video']==b['video']else'CROSS_VIDEO';B=bucket[scope];r=compare(a,b,ring);r0=compare(baseby[a['id']],baseby[b['id']],ring)if method!='B0'else r;co=r['known']&r0['known'];N0=len(a['X']);B['pairs']+=1;B['N']+=N0;B['known']+=int(r['known'].sum());B['supported']+=int(r['supported'].sum());B['front']+=int(r['front'].sum());B['behind']+=int(r['behind'].sum());B['cad']+=int(r['cad_occluded'].sum());B['unknown']+=int((~r['known']&~r['cad_occluded']).sum());B['dz'].append(r['dz'][r['known']]);B['normal'].append(r['normal_angle_deg'][r['supported']]);B['common0'].append(r0['dz'][co]);B['common1'].append(r['dz'][co]);B['gained']+=int((~r0['known']&r['known']).sum());B['lost']+=int((r0['known']&~r['known']).sum())
     for t in B['threshold']:B['threshold'][t]+=int((r['known']&(abs(r['dz'])<=t)).sum())
     pr=dict(group=g,method=method,source=a['id'],target=b['id'],scope=scope,fixed_N=N0,known_N=int(r['known'].sum()),supported_N=int(r['supported'].sum()),front_N=int(r['front'].sum()),behind_possible_occlusion_N=int(r['behind'].sum()),CAD_occluded_N=int(r['cad_occluded'].sum()),unknown_N=int((~r['known']&~r['cad_occluded']).sum()),depth_mm=stats(r['dz'][r['known']]),same_facing_supported_normal_deg=stats(r['normal_angle_deg']),common_N=int(co.sum()),gained_N=int((~r0['known']&r['known']).sum()),lost_N=int((r0['known']&~r['known']).sum()),status=a['status'],not_GT=True);per.append(pr)
     if method=='B0'and(scope=='CROSS_VIDEO'if g=='G01'else scope=='SAME_VIDEO')and pr['known_N']>best:best=pr['known_N'];choice=(a['id'],b['id'])
    matchindex.append(dict(group=g,method=method,source=a['id'],canonical=a['canonical'],native_obs=asset(a['source']['observation']['path']),native_mesh=asset(a['source']['mesh']['path']),D=a['D'],C=a['C'],status=a['status']))
   for scope,B in bucket.items():
    if not B['N']:continue
    cat=lambda k:np.concatenate(B[k])if B[k]else np.array([]);rec=dict(group=g,method=method,scope=scope,sources_N=len(data),ordered_pairs_N=B['pairs'],fixed_N=B['N'],known_N=B['known'],support_fraction_fixed=B['supported']/B['N'],front_fraction_fixed=B['front']/B['N'],behind_possible_occlusion_fraction_fixed=B['behind']/B['N'],CAD_occluded_fraction_fixed=B['cad']/B['N'],unknown_fraction_fixed=B['unknown']/B['N'],depth_mm=stats(cat('dz')),normal_deg_supported_only=stats(cat('normal')),exact_common_N=len(cat('common0')),common_B0_mm=stats(cat('common0')),common_candidate_mm=stats(cat('common1')),gained_N=B['gained'],lost_N=B['lost'],single_source_accuracy='NOT_EVALUABLE_NO_GT',support_sensitivity_fixed={str(t):n/B['N']for t,n in B['threshold'].items()},all_differences_includes_legitimate_deeper_layers=True,no_new_HERO_inference=True);agg.append(rec)
   print('FROZEN_HERO_EVAL',g,method,flush=True)
  if choice:
   pairchoice.append(dict(group=g,source=choice[0],target=choice[1],selection='largestB0fixedknownN;G01crossotherwise_samevideo;noGTorBAmetricranking'))
   for method in ['B0','B1','B2','B3']:
    if not res[g,method].get('poses'):continue
    _,dd=sources(g,res,method);by={s['id']:s for s in dd};a,b=by[choice[0]],by[choice[1]];r=compare(a,b,ring);cls=np.full(len(a['X']),4);cls[r['supported']]=0;cls[r['front']]=1;cls[r['behind']]=2;cls[r['cad_occluded']]=3;uv,z=projection(a['X'],b['C'],b['obs']['K']);rays=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(b['obs']['K']).T;ij=np.floor(np.where(np.isfinite(uv),uv,-1e9)+.5).astype(int);inside=(ij[:,0]>=0)&(ij[:,0]<b['grid'].shape[1])&(ij[:,1]>=0)&(ij[:,1]<b['grid'].shape[0]);dep=np.full(len(uv),np.nan);dep[inside]=b['grid'][ij[inside,1],ij[inside,0]];targetX=(rays*dep[:,None])@b['C'][:3,:3].T+b['C'][:3,3]
    np.savez_compressed(local/(g+'_'+method+'_REAL_PAIR.npz'),source_X=a['X'],target_first_layer_X=targetX,known=r['known'],pixel_id=a['obs']['pixel_id'],original_face_id=a['obs']['face_id'],class_id=cls,dz_mm=r['dz'],normal_angle_deg=r['normal_angle_deg'],source_id=a['id'],target_id=b['id'])
 save('metrics/HERO_SURFACE_ALIGNMENT_SCORECARD.json',agg);table('HERO_SURFACE_ALIGNMENT_SCORECARD.csv',agg);save('metrics/HERO_PER_PAIR.json',per);table('metrics/HERO_PER_PAIR.csv',per);save('metrics/HERO_NATIVE_SOURCE_AREAS.json',source_rows);table('metrics/HERO_NATIVE_SOURCE_AREAS.csv',source_rows);save('metrics/REAL_OVERLAP_PAIRS_FOR_FIGURES.json',pairchoice);save('assets_index/HERO_NATIVE_IDENTITIES_AND_DERIVED_TRANSFORMS.json',matchindex);print('HERO_ALL4_COMPLETE',flush=True)
if __name__=='__main__':main()
