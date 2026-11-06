"""Prepare both routes once from frozen data; no optimization and no type dispatch."""
from common import *
from planes import normalize,compare,orient_retained
from clip_mesh import clip
from p3d import device
from pytorch3d.utils import ico_sphere
from scipy.ndimage import distance_transform_edt
PREV=R.parent/'BODY_BASE_INIT_009'

def full_mesh(V,F):
 return dict(V=np.asarray(V),F=np.asarray(F),F_solid=np.asarray(F),inferred_base_faces=np.zeros(len(F),bool),boundary_vertex=np.zeros(len(V),bool),original_vertex_ID=np.arange(len(V)),intersection_original_edge_ID=np.full((len(V),2),-1),original_face_ID=np.arange(len(F)))

def main():
 rows=[];bases=[];weights=[];pairs_audit=[];lineage=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];root=R/'inputs'/n;old=load(PREV/'inputs'/n/'BASE.json');base=load(root/'BASE.json');save('inputs/'+n+'/BASE_SIGN_REPAIRED_45PX.json',base);e=np.load(root/'BASE_EVIDENCE.npz');center=np.median(e['Polyp_internal_XYZ'],axis=0);trials=base['trials'];primary=next(t for t in trials if t['upper_px']==45)
  valid=[t for t in trials if t['plane']is not None];chosen=primary
  if base['base_status']!='RELIABLE':
   acceptable=[t for t in valid if t['N']>=100 and t['inlier_fraction']>=.5];chosen=min(acceptable or valid,key=lambda t:t['upper_px'])if valid else dict(plane=None,upper_px=None)
  plane=None;orientation=None
  if chosen['plane']is not None:plane,orientation=orient_retained(chosen['plane'],e['Polyp_internal_XYZ'])
  apply=old['contact_status']=='BROAD'and plane is not None
  base.update(previous_base_status=old['base_status'],previous_normal_change_deg=old['max_normal_change_deg'],previous_contact_status=old['contact_status'],contact_status=old['contact_status'],selected_ROI_upper_px=chosen['upper_px'],selected_plane=plane,orientation=orientation,truncate_allowed=apply,truncate_reason='BROAD frozen data-only contact; not gated on plane quality'if apply else'NO_BROAD_CONTACT_OR_NO_PLANE',uncertain_base=base['base_status']!='RELIABLE')
  save('inputs/'+n+'/BASE_SELECTION.json',base);bases.append(dict(case=n,previous_status=old['base_status'],new_status=base['base_status'],old_max_angle=old['max_normal_change_deg'],sign_equivalent_max_angle=base['max_normal_change_deg'],max_anchor_offset_mm=base['max_anchor_offset_change_mm'],selected_ROI_upper_px=chosen['upper_px'],contact=old['contact_status'],clipped=apply,orientation=orientation,plane=plane,uncertain=base['uncertain_base']))
  src=PREV/'local_results'/n/'B_SELECTED.npz';b=dict(np.load(src));P=clip(b['V'],b['F'],plane)if apply else full_mesh(b['V'],b['F']);np.savez_compressed(root/'P_INITIAL.npz',**P);np.savez_compressed(root/'B_UNCUT.npz',**full_mesh(b['V'],b['F']));trimesh.Trimesh(P['V'],P['F_solid'],process=False).export(root/'P_INITIAL_mm.ply')
  sourceid=old['primary'];a=np.load(root/(sourceid+'.npz'));o=np.load(R/'depth_observations'/(sourceid+'.npz'));y,x=np.where(a['labels']==1);assert len(x)and len(o['z']);z=float(np.median(o['z']));K=a['K'];T=a['T'];uv=np.array([(x.min()+x.max())/2,(y.min()+y.max())/2]);r=max(.25,z*(x.max()-x.min())/(2*K[0,0]),z*(y.max()-y.min())/(2*K[1,1]));C=(np.r_[uv,1.]@np.linalg.inv(K).T*z+np.array([0.,0.,.5*r]))@T[:3,:3].T+T[:3,3]
  sphere=ico_sphere(3,device=device);S=full_mesh(sphere.verts_packed().cpu().numpy().astype(float)*r+C,sphere.faces_packed().cpu().numpy());np.savez_compressed(root/'S_INITIAL.npz',**S);trimesh.Trimesh(S['V'],S['F_solid'],process=False).export(root/'S_INITIAL_mm.ply');save('inputs/'+n+'/NORMALIZATION.json',dict(center=C,scale_mm=r,source='S primary original Mask bbox + reliable axial HERO; shared P/S',B_used=False));srec=dict(case=n,source=sourceid,center_mm=C,radius_mm=r,vertices=len(S['V']),faces=len(S['F']),official_generator='pytorch3d.utils.ico_sphere(level=3)',HERO_median_axial_mm=z,Mask_bbox_xyxy=[int(x.min()),int(y.min()),int(x.max()),int(y.max())],HERO_native_pixel_ids=o['pixel_id'],B_parameters_used=False,GT_used=False);save('inputs/'+n+'/SPHERE_INITIALIZATION.json',srec)
  m=trimesh.Trimesh(P['V'],P['F_solid'],process=False);above=(b['V']@plane[:3]+plane[3]>=-1e-10)if apply else np.ones(len(b['V']),bool);lineage.append(dict(case=n,frozen_B=asset(src),original_V_N=len(b['V']),original_F_N=len(b['F']),above_original_vertex_N=int(above.sum()),preserved_original_vertex_N=int((P['original_vertex_ID']>=0).sum()),new_intersection_vertex_N=int((P['original_vertex_ID']<0).sum()),render_F_N=len(P['F']),inferred_cap_F_N=int(P['inferred_base_faces'].sum()),all_preserved_original_vertices_bitwise_unchanged=bool(np.array_equal(P['V'][P['original_vertex_ID']>=0],b['V'][P['original_vertex_ID'][P['original_vertex_ID']>=0]])),watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),components=len(m.split(only_watertight=False)),base_plane=plane,cap_excluded_from_render=True))
  # Same candidate IDs for P/S, reuse existing D2 boundary and same-view pair protocol.
  for v in c['views']:
   p=R/'depth_observations'/(v['id']+'.npz')
   if not p.exists():continue
   obs=dict(np.load(p));aa=np.load(root/(v['id']+'.npz'));lab=aa['labels'];uvn=obs['uv'];mapped=np.c_[uvn,np.ones(len(uvn))]@np.linalg.inv(obs['K']).T@aa['K'].T;px=np.rint(mapped[:,:2]/mapped[:,2:]).astype(int);db=distance_transform_edt(lab!=0);dr=distance_transform_edt(lab!=2);d=np.minimum(db[px[:,1],px[:,0]],dr[px[:,1],px[:,0]]);w=.1+.9*(1-np.exp(-(d/8)**2));reliable=w>=.5;tree=cKDTree(uvn);rng=np.random.default_rng(20261106);pairs=[];scales=[];seen=set();dense=np.load(root/(v['id']+'_DEPTH.npz'))['depth_mm']
   for scale in[4,16,48]:
    count=0
    for i in rng.permutation(np.flatnonzero(reliable)):
     angle=rng.uniform(0,2*np.pi);_,j=tree.query(uvn[i]+scale*np.array([np.cos(angle),np.sin(angle)]));j=int(j);gap=np.linalg.norm(uvn[i]-uvn[j]);key=tuple(sorted([int(i),j]))
     if not reliable[j]or key in seen or not(max(2,.5*scale)<=gap<=2*scale):continue
     line=np.rint(np.linspace(uvn[i],uvn[j],int(np.ceil(gap))+1)).astype(int);q=np.c_[line,np.ones(len(line))]@np.linalg.inv(obs['K']).T@aa['K'].T;pix=np.rint(q[:,:2]/q[:,2:]).astype(int);zz=dense[line[:,1],line[:,0]]
     if not(lab[pix[:,1],pix[:,0]]==1).all()or not(np.isfinite(zz)&(zz>0)).all()or np.max(abs(np.diff(zz)))>.5:continue
     pairs.append(key);scales.append(scale);seen.add(key);count+=1
     if count>=128:break
   pairs=np.asarray(pairs,int).reshape(-1,2);pw=np.sqrt(w[pairs[:,0]]*w[pairs[:,1]])if len(pairs)else np.empty(0);np.savez_compressed(p,**{**obs,'boundary_weight':w,'distance_background_px':db[px[:,1],px[:,0]],'distance_ring_px':dr[px[:,1],px[:,0]],'pairs':pairs,'pair_scale_px':scales,'pair_weight':pw});weights.append(dict(case=n,source=v['id'],role=v['role'],N=len(w),weight_min=float(w.min()),weight_median=float(np.median(w)),weight_sum=float(w.sum()),pairs_N=len(pairs),original_candidate_ID_equal_009=bool(np.array_equal(obs['pixel_id'],np.load(PREV/'depth_observations'/(v['id']+'.npz'))['pixel_id']))));pairs_audit.extend(dict(case=n,source=v['id'],i=int(i),j=int(j),native_id_i=int(obs['pixel_id'][i]),native_id_j=int(obs['pixel_id'][j]),scale_px=scale,weight=float(weight))for(i,j),scale,weight in zip(pairs,scales,pw))
  print('PREPARED',n,'clip',apply,'base',base['base_status'],'ROI',chosen['upper_px'],'P V/F',len(P['V']),len(P['F']),'S r',r,flush=True);rows.append(dict(case=n,route='P',V_N=len(P['V']),F_observed=len(P['F']),F_cap=int(P['inferred_base_faces'].sum()),source='frozen009B exact halfspace intersection'if apply else'frozen009B unchanged'));rows.append(dict(case=n,route='S',V_N=len(S['V']),F_observed=len(S['F']),F_cap=0,source='official ico_sphere data-only translation/uniform scale'))
 save('metrics/BASE_SIGN_REGRESSION.json',bases);table('metrics/BASE_SIGN_REGRESSION.csv',bases);save('metrics/EXACT_CLIPPING_AUDIT.json',lineage);table('metrics/EXACT_CLIPPING_AUDIT.csv',lineage);table('metrics/INITIALIZATION_COMPARISON.csv',rows);table('metrics/BOUNDARY_WEIGHT_AUDIT.csv',weights);table('metrics/FIXED_RELATIVE_PAIRS.csv',pairs_audit)
if __name__=='__main__':main()
