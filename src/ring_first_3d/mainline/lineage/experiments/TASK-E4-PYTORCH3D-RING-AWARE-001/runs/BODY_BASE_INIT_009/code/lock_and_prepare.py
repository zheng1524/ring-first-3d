from common import *
from scipy.spatial.transform import Rotation
from scipy.cluster.hierarchy import linkage,fcluster
from scipy.spatial.distance import squareform
from ring_sides import sample
import shutil
LEG=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');BATCH=LEG/'multigroup_ring_hero_visual_audit_v1';NEXT=LEG/'multigroup_surface_gt_vnext';E1=Path('/home/liu/ring_first_3d_neural_e1/experiments/TASK-NEURAL-E1-PIPELINE-RECOVERY-001');D2=R.parent/'BOUNDARY_RELATIVE_DEPTH_D2_001';PM=Path('/home/liu/ring_first_3d_e4_pmgr/experiments/TASK-E4-PMGR-PROGRESSIVE-GEOMETRY-001')
def main():
 assert not(R/'config/CASE_LOCK.json').exists();manifest=[];cases=[];partitions=[];source={x['id']:x for x in load(E1/'provenance/INPUT_ELIGIBILITY.json')['references']};groups={g['id']:g for g in load(NEXT/'inputs/groups.json')};metadata=Path('/home/liu/polyp_research/result/01_keyframes_and_inputs/full_multimodal_manifest.csv');identity={}
 for x in csv.DictReader(metadata.open()):
  if x['setup_id']not in identity:identity[x['setup_id']]={k:x[k]for k in['setup_id','specimen_id','paris_type','ring_code']}
 ninth=load(R/'config/NEW_CASE_LOCK.json')['pipeline_case'];groups['G09']=ninth;existing={'G01':('real_Ip','G01_004'),'G06':('real_IIa','G06_004'),'G07':('real_Is','G07_004')};source_manifest=[]
 def record(p):manifest.append(asset(p))
 for gid in['G01','G02','G03','G07','G04','G05','G06','G08','G09']:
  g=groups[gid];ident=identity.get(g['group']);
  if ident is None:
   # Frozen catalog aliases resolve specimen identity, never geometry or nominal dimensions.
   family=Path(g['trusted_GT_path']).parent.name if g.get('trusted_GT_path')else'FROZEN_PHYSICAL_GROUP:'+gid;matches=[v for v in identity.values()if v['specimen_id'].replace('spec_','').rstrip('-')==family.rstrip('-')];ident=matches[0]if matches else dict(setup_id=g['group'],specimen_id='catalog_family:'+family,paris_type=g['morphology_label'],ring_code=g['ring'])
  assert ident and ident['paris_type']==g['morphology_label'];name=gid;out=R/'inputs'/name;out.mkdir(exist_ok=True);vv=[];depthpaths={}
  if gid in existing:
   old,sceneid=existing[gid];meta=load(D2/'inputs'/old/'CASE.json');shutil.copyfile(D2/'inputs'/old/'INITIAL.npz',out/'INITIAL.npz');shutil.copyfile(D2/'inputs'/old/'RING.npz',out/'RING.npz');record(D2/'inputs'/old/'INITIAL.npz');record(D2/'inputs'/old/'RING.npz')
   for v in meta['views']:
    cid=v['id'];a=np.load(D2/'inputs'/old/(cid+'.npz'));np.savez_compressed(out/(cid+'.npz'),**dict(a));vv.append(dict(v,raw_frame=source[cid]['raw_frame'],RGB_source=source[cid]['RGB'],Mask_source=source[cid]['Mask']));depthpaths[cid]=source[cid]['E1_actual_native']['path'];record(D2/'inputs'/old/(cid+'.npz'))
   a_source='exact frozen D2/PMGR prior P0'
  elif gid=='G08':
   sceneid='G08_005';fit=['G08_005_growth_r01','G08_005_growth_r02'];hold=['G08_005_ref04'];a=np.load(PM/'inputs/G08_005_E2_basis.npz');np.savez_compressed(out/'INITIAL.npz',V=a['V'],F=a['F']);record(PM/'inputs/G08_005_E2_basis.npz');mesh=trimesh.load(source[fit[0]]['Ring_CAD']['path'],process=False);np.savez_compressed(out/'RING.npz',V=mesh.vertices,F=mesh.faces);record(source[fit[0]]['Ring_CAD']['path'])
   for cid in fit+hold:
    s=source[cid];p=np.load(s['pack']);im=np.array(Image.open(s['RGB']).convert('RGB'));lab=np.array(Image.open(s['Mask']));assert np.array_equal(lab,p['labels']);np.savez_compressed(out/(cid+'.npz'),RGB=im,labels=lab,K=p['K'],T=p['pose']);vv.append(dict(id=cid,role='FIT'if cid in fit else'UPDATE_HOLDOUT',qualification=s.get('pose_status','HISTORICAL_ONLY_DIAGNOSTIC'),raw_frame=s['raw_frame'],RGB_source=s['RGB'],Mask_source=s['Mask']));depthpaths[cid]=s['E1_actual_native']['path']
   a_source='exact frozen PMGR E2 P0'
  else:
   root=R/'new_input_pipeline/groups/G09'if gid=='G09'else BATCH/'groups'/gid;L=load(root/'inputs/ledger005.json');mvs=load(root/'inputs/MVS_cases.json')[0];nativepath=root/'predictions/HERO_native.npz';raw=np.load(nativepath);camera=root/f'predictions/local005_camera_{mvs["primary_version"]}.npz';cam=np.load(camera);K=cam['K'];poses=cam['c2w'];ref=int(raw['reference']);fit=[ref]+[i for i in mvs['sources']if i!=ref][:2];held=int(mvs['independent_image_heldout']);assert held not in fit
   for i in fit+[held]:
    cid=gid+'_'+L[i]['id'];im=np.array(Image.open(L[i]['RGB_path']).convert('RGB'));lab=np.array(Image.open(L[i]['Mask_path']));assert im.shape[:2]==lab.shape==(360,640);np.savez_compressed(out/(cid+'.npz'),RGB=im,labels=lab,K=K,T=poses[i]);vv.append(dict(id=cid,role='FIT'if i in fit else'UPDATE_HOLDOUT',qualification='MODEL_PREDICTED_OR_LEGACY_SCREEN_ONLY_DIAGNOSTIC',raw_frame=L[i]['raw_frame'],RGB_source=L[i]['RGB_path'],Mask_source=L[i]['Mask_path'],camera_index=i));record(L[i]['RGB_path']);record(L[i]['Mask_path'])
    if i==ref:depthpaths[cid]=str(nativepath)
   ringpath=LEG/'surface_fusion_v2/inputs/R10_ring.obj';ring=trimesh.load(ringpath,process=False);np.savez_compressed(out/'RING.npz',V=ring.vertices,F=ring.faces);record(ringpath);record(camera);record(root/'inputs/ledger005.json');a_source='old generic A1 ellipse initializer rule, newly instantiated; no historical P0 exists'
  for v in vv:
   cid=v['id'];a=dict(np.load(out/(cid+'.npz')));p=out/(cid+'_SIDES.npz');sides,cl,band=sample(a['labels']);np.savez_compressed(p,classes=cl,band=band);save('metrics/sides/'+cid+'.json',sides)
   if cid in depthpaths:
    rawpath=depthpaths[cid];raw=np.load(rawpath);z=raw['depth_mm'];h,w=z.shape;K=a['K'];T=a['T'];Kn=K.copy();S=np.diag([w/640,h/360,1]);S[:2,2]=np.array([w/640,h/360])*.5-.5;Kn=S@K
    rk=next((k for k in['K_index_native','K_index']if k in raw),None)
    if rk:assert np.allclose(raw[rk],Kn,atol=1e-8)
    pose=raw['pose']if'pose'in raw else raw['reference_pose_mm'];assert np.allclose(pose,T,atol=1e-8)
    np.savez_compressed(out/(cid+'_DEPTH.npz'),depth_mm=z,Kn=Kn,K=K,T=T,native_shape=z.shape,source_path=rawpath);v['HERO_status']='NATIVE_ORIGINAL_AVAILABLE';v['HERO_source']=rawpath;record(rawpath)
   else:v['HERO_status']='NO_PREDICTED_DEPTH_FOR_THIS_REFERENCE';v['HERO_source']=None
  # Generic old A1 9D initialization only when no frozen historical P0 exists.
  if not(out/'INITIAL.npz').exists():
   first=next(v for v in vv if v['HERO_source']);a=np.load(out/(first['id']+'.npz'));dep=np.load(out/(first['id']+'_DEPTH.npz'));z=dep['depth_mm'];h,w=z.shape;uv=np.stack(np.meshgrid(np.arange(w),np.arange(h)),axis=-1).reshape(-1,2);RGBuv=np.c_[uv,np.ones(len(uv))]@np.linalg.inv(dep['Kn']).T@a['K'].T;RGBuv=RGBuv[:,:2]/RGBuv[:,2:];xy=np.clip(np.rint(RGBuv).astype(int),[0,0],[639,359]);good=(a['labels'][xy[:,1],xy[:,0]]==1)&np.isfinite(z.ravel())&(z.ravel()>0);rays=np.c_[uv[good],np.ones(good.sum())]@np.linalg.inv(dep['Kn']).T;X=(rays*z.ravel()[good,None])@a['T'][:3,:3].T+a['T'][:3,3];c=np.median(X,axis=0);normal=a['T'][:3,3]-c;normal/=np.linalg.norm(normal);xx=a['T'][:3,0]-np.dot(a['T'][:3,0],normal)*normal;xx/=np.linalg.norm(xx);Q=np.c_[xx,np.cross(normal,xx),normal];q=(X-c)@Q;axes=np.clip(np.quantile(abs(q),.9,axis=0)*1.5,.3,15);axes[2]=max(axes[2],.8*np.sqrt(axes[0]*axes[1]));sphere=trimesh.creation.icosphere(subdivisions=3);V=np.array(sphere.vertices)*axes@Q.T+c;np.savez_compressed(out/'INITIAL.npz',V=V,F=sphere.faces);save('inputs/'+name+'/INITIAL_PROVENANCE.json',dict(rule=a_source,center=c,axes=axes,Q=Q,GT_read=False))
  # Same existing complete-link angular partition mechanism, frozen before body fit; no Gate rejection.
  primary=next(v for v in vv if v['role']=='FIT'and v['HERO_source']);ad=np.load(out/(primary['id']+'.npz'));dd=np.load(out/(primary['id']+'_DEPTH.npz'));zz=dd['depth_mm'];yy,xx=np.mgrid[:zz.shape[0],:zz.shape[1]];uvv=np.c_[xx.ravel(),yy.ravel(),np.ones(zz.size)];ray=uvv@np.linalg.inv(dd['Kn']).T;pix=ray@ad['K'].T;pix=np.clip(np.rint(pix[:,:2]/pix[:,2:]).astype(int),[0,0],[639,359]);ok=np.isfinite(zz.ravel())&(zz.ravel()>0)&(ad['labels'][pix[:,1],pix[:,0]]==1);cent=np.median((ray[ok]*zz.ravel()[ok,None])@ad['T'][:3,:3].T+ad['T'][:3,3],axis=0);dirs=np.array([np.load(out/(v['id']+'.npz'))['T'][:3,3]-cent for v in vv]);dirs/=np.linalg.norm(dirs,axis=1)[:,None];angles=np.degrees(np.arccos(np.clip(dirs@dirs.T,-1,1)));np.fill_diagonal(angles,0);angles=(angles+angles.T)/2;blocks=fcluster(linkage(squareform(angles),method='complete'),t=10.,criterion='distance')if len(vv)>1 else[1]
  for v,b in zip(vv,blocks):v['partition_block']=int(b);partitions.append(dict(case=name,source=v['id'],role=v['role'],partition=int(b),raw_frame=v['raw_frame'],view_direction=dirs[vv.index(v)],HERO_status=v['HERO_status']))
  meta=dict(name=name,identity=g['group'],physical_group=gid,physical_specimen=ident['specimen_id'],morphology=ident['paris_type'],ring=g['ring'],R_mid_mm=g['R_mm'],wire_mm=.6,unit='mm',views=vv,initialization=a_source,historical_Gate_used_for_admission=False,case_status='INPUT_COMPLETE',qualification_semantics='input integrity only; observation errors are outcomes, not exclusion',GT='NOT_EVALUABLE');save('inputs/'+name+'/CASE.json',meta);cases.append(meta)
 assert len({c['physical_specimen']for c in cases})==9;assert all(sum(c['morphology']==t for c in cases)==3 for t in['Ip','Is','IIa']);save('config/CASE_LOCK.json',cases);table('metrics/VIEW_PARTITION.csv',partitions);record(metadata);save('assets_index/SOURCE_MANIFEST.json',manifest)
 print('NINE_CASES_LOCKED',[(c['name'],c['morphology'],c['physical_specimen'])for c in cases])
if __name__=='__main__':main()
