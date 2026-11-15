"""Separate native Mesh objects in metric GLB + interactive source/qualification/RGB UI."""
from plot_common import *
from evaluate_geometry import new_sources

def frustum(C,K):
 uv=np.array([[0,0],[639,0],[639,359],[0,359]],float);corners=(np.c_[uv,np.ones(4)]@np.linalg.inv(K).T*.75)@C[:3,:3].T+C[:3,3];V=np.r_[C[:3,3][None],corners];F=np.array([[0,1,2],[0,2,3],[0,3,4],[0,4,1]]);return V,F

def main():
 manifest=[];out=N/'local_results/interactive';out.mkdir(exist_ok=True);rgbdir=out/'RGB';rgbdir.mkdir(exist_ok=True)
 for g in GROUPS:
  conf,old=frozen_sources(g,False);new=new_sources(g);scene3=trimesh.Scene(base_frame='RingWorld');ring=np.load(conf['ring']['path']);vv=load(camera_file(g));sel=load(selpath(g,'_SELECTION.json'));rank={r['id']:r['rank']for r in sel['ranked']};layers=[];cameras=[];counter=0
  def add(name,V,F,c,kind,**meta):
   nonlocal counter
   node='layer_'+str(counter);counter+=1;m=trimesh.Trimesh(V,F,process=False);m.visual.vertex_colors=np.tile(np.asarray(c,np.uint8),(len(V),1));scene3.add_geometry(m,node_name=node,geom_name=node);layers.append(dict(node=node,label=name,kind=kind,**meta));return node
  add('Ring CAD frozen',ring['V'],ring['F'],[5,5,5,255],'Ring',default=True)
  for label,b in conf['bodies'].items():
   m=np.load(b['path']);F=m['F_solid']if'F_solid'in m else m['F'];add('Frozen018 '+label,m['V'],F,[140,140,145,100],'Body',default=False,source=b,unknown_inferred=True)
  for i,s in enumerate(old):
   co=np.r_[color(i)*255,255].astype(np.uint8);add('OLD '+s['id'],s['V'],s['F'],co,'HERO_OLD',default=False,video=s['video'],role=s['role'],source_id=s['id'],qualification='historical native; evaluation-only/holdout layer never selection',rank=None,source=s['source'])
  for i,s in enumerate(new):
   co=np.r_[color(len(old)+i)*255,255].astype(np.uint8);add('NEW '+s['id']+' TRUSTED',s['V'],s['F'],co,'HERO_NEW',default=s['variant']=='GEOMETRIC3',video=s['video'],role='FIT',source_id=s['id'],qualification='internal017TRUSTED, not global consistency certified',rank=s['rank'],state='TRUSTED',variant=s['variant'])
   root=N/'hero_fit'/s['id']
   for state,file in [('RAW','RAW_NATIVE_MESH.npz'),('UNKNOWN','UNKNOWN_HERO.npz'),('REJECTED','REJECTED_HERO.npz'),('UNCERTAIN','UNCERTAIN_HERO.npz')]:
    m=np.load(root/file)
    if not len(m['F']):continue
    cc=co if state=='RAW'else [145,145,145,255]if state=='UNKNOWN'else[220,40,40,255]if state=='REJECTED'else[235,190,35,255];add('NEW '+s['id']+' '+state,m['V'],m['F'],cc,'HERO_STATE',default=False,video=s['video'],role='FIT',source_id=s['id'],qualification='original native face subset',rank=s['rank'],state=state)
   # original public PLY remains per source, no merged geometry output.
  for v in vv:
   a=np.load(v['cache']);photo=rgbdir/(v['id']+'.jpg');Image.fromarray(a['RGB']).resize((320,180),Image.Resampling.LANCZOS).save(photo,quality=82);record=dict(id=v['id'],video=v['video'],role=v['role'],formal=v['formal'],qualification=v['status'],RGB='local_results/interactive/RGB/'+photo.name,RGB_original_path=v['RGB_source'],RGB_original_SHA256=v['RGB_SHA256'],raw_frame=v.get('raw_frame'),rank=rank.get(v['id']),located=v.get('C')is not None and(v.get('RGB_inliers_N',0)>=6 or v['role']=='HOLDOUT'),failure=v.get('qualification_reasons',[]))
   if record['located']:
    C=np.array(v['C']);V,F=frustum(C,K0);co=np.r_[np.array(matplotlib.colors.to_rgb(COLS[v['video']]))*255,100].astype(np.uint8);record['node']=add(v['id'],V,F,co,'Camera',default=False,video=v['video'],role=v['role'],formal=v['formal'],qualification=v['status'],rank=rank.get(v['id']),source_id=v['id']);record['C_mm']=C
   else:record['node']=None;record['note']='not inserted in common3Dworld; Ring-onlyyaw unresolved / no numericpose'
   cameras.append(record)
  for video in ['004','005']:
   seq=sorted([v for v in vv if v['video']==video and v.get('C')is not None and v.get('RGB_inliers_N',0)>=6],key=lambda v:v.get('raw_frame')or 0);pieces=[]
   for a,b in zip(seq[:-1],seq[1:]):
    p=np.array(a['C'])[:3,3];q=np.array(b['C'])[:3,3]
    if np.linalg.norm(p-q)<1e-8:continue
    pieces.append(trimesh.creation.cylinder(radius=.025,segment=np.array([p,q]),sections=6))
   if pieces:
    m=trimesh.util.concatenate(pieces);add(video+' sampled camera path (gaps not recovered frames)',m.vertices,m.faces,np.r_[np.array(matplotlib.colors.to_rgb(COLS[video]))*255,255].astype(np.uint8),'Trajectory',default=False,video=video,role='DIAGNOSTIC',qualification='sampledpath, not denseSLAM',rank=None)
  bounds=scene3.bounds.copy();scene3.apply_transform(np.diag([.001,.001,.001,1.]));scene3.metadata.update(research_unit='mm',GLTF_unit='meter',mm_equals_GLTF_times1000=True,no_ICP=True,no_fusion=True);path=out/(g+'_SOURCE_LAYERS.glb');path.write_bytes(scene3.export(file_type='glb',include_normals=True));back=trimesh.load(path,force='scene');err=float(np.max(abs(back.bounds-scene3.bounds)));assert err<1e-6
  for key,geom in scene3.geometry.items():
   assert key in back.geometry and np.array_equal(geom.faces,back.geometry[key].faces),(g,key,'faceorderchanged')
  # Focus geometry bounds separate from distant cameras/landmarks; all remain toggleable.
  small=bound_parts([s for s in old if s['role']=='FIT']+new,ring);center=(small.min(0)+small.max(0))/2*.001;radius=float(np.linalg.norm(small*.001-center,axis=1).max());data=dict(group=g,glb='local_results/interactive/'+path.name,layers=layers,cameras=cameras,focus_m=center,radius_m=radius,actual_recommended_N=sel['recommended_N'],all_source_native_vertices_unchanged=True,GLTF_unit='m, multiply1000 for researchmm',GLB=asset(path),roundtrip_bounds_error_m=err,unknown_regions='grayBody proxy is inference; gray native labels UNKNOWN; unlocated cameras listedbutnotmerged');save('assets_index/'+g+'_ATLAS_LAYERS.json',data);manifest.append(dict(group=g,GLB=asset(path),HTML=str(N/(g+'_MAX_COVERAGE_VIEW_ATLAS.html')),layer_N=len(layers),camera_N=len(cameras),unlocated_N=sum(not c['located']for c in cameras),roundtrip_bounds_error_m=err))
  template=(N/'code/atlas_template.html').read_text().replace('__GROUP__',g);(N/(g+'_MAX_COVERAGE_VIEW_ATLAS.html')).write_text(template)
  print('ATLAS_EXPORTED',g,len(layers),path.stat().st_size,'bytes',flush=True)
 save('assets_index/INTERACTIVE_ATLASES.json',manifest)
if __name__=='__main__':main()
