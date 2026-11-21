"""Pre/post-fit diagnostic controls; no fitting and no model selection."""
from ring020 import *
from objective020 import SymmetricFeatures,Objective

def midpoint_control():
 v={v['id']:v for v in load(R/'config/VIEWS.json')};cur=CADCurves();base=np.asarray(next(a['T']for a in load(R/'config/HISTORICAL_CANDIDATES.json')if a['tag']=='HISTORICAL_FULL_RoMa'));rows=[]
 for cid in ['G01_005_raw00057','G01_005_raw00459','G01_005_raw00745']:
  a=v[cid];C=canonical(tensor(base@a['T'],torch.float64)).cpu().numpy();K=np.asarray(a['K']);cs=contours(np.isfinite(cast(cur.cad,K,C,360,640)));es={}
  for key,p in cs.items():
   (cx,cy),(w,h),angle=cv2.fitEllipse(p.astype(np.float32));
   if w<h:w,h=h,w;angle+=90
   es[key]=dict(cx=cx,cy=cy,major_radius=w/2,minor_radius=h/2,angle_deg=angle%180)
  I,O=es['inner'],es['outer'];mid={k:(I[k]+O[k])/2 for k in ['cx','cy','major_radius','minor_radius']};mid['angle_deg']=float(np.degrees(np.angle(np.exp(2j*np.radians([I['angle_deg'],O['angle_deg']])).mean()))/2);fit=ellipse_points(mid,np.arange(720)*2*np.pi/720);P=(cur.mid-C[:3,3])@C[:3,:3];u=P@K.T;u=u[:,:2]/u[:,2:];d=np.r_[cKDTree(u).query(fit)[0],cKDTree(fit).query(u)[0]];rows.append(dict(view=cid,controlled_actual_CAD=True,author_Polyp_GT=False,approx_Mid_from_fitted_CAD_inner_outer_vs_actual_3D_centerline_px=stats(d),not_extra_independent_observation=True))
 save('metrics/MID_APPROXIMATION_CONTROL.json',rows)

def inputs():
 rows=[]
 for v in load(R/'config/VIEWS.json'):
  p=R/'ring_evidence_v2'/(v['id']+'.npz');e=evidence(v);rows.append(dict(view=v['id'],video=v['video'],role=v['role'],RGB=asset(v['RGB_source']),Mask=asset(v['Mask_source']),original_K=v['K'],original_c2w=v['T'],qualification=v.get('qualification'),cache=asset(v['cache']),Ring_DXY_source=asset(R/'ring'/(v['id']+'.npz')),Ring_geometry_evidence=asset(p),Inner_N=len(e['inner']),Outer_N=len(e['outer']),Mid_dual_N=int((e['mid_support_class']==2).sum()),Mid_single_N=int((e['mid_support_class']==1).sum()),Mid_unknown_N=int((e['mid_support_class']==0).sum()),original_inner_raw_N=len(e['inner_raw']),original_outer_raw_N=len(e['outer_raw']),no_Body_or_HERO_selection=True))
 save('INPUT_MANIFEST.json',rows);table('INPUT_MANIFEST.csv',rows);save('metrics/RING_VISIBLE_EVIDENCE_COUNTS.json',[{k:x[k]for k in ['view','video','role','Inner_N','Outer_N','Mid_dual_N','Mid_single_N','Mid_unknown_N','original_inner_raw_N','original_outer_raw_N']}for x in rows])

def gradients():
 results=[];views=load(R/'config/VIEWS.json');ids=[v['id']for v in views if v['video']=='005'and v['role']=='FIT']
 for arm in ['R0','R1','R2','R3','R3_MASK_ONLY','R3_INNER_OUTER','R4']:
  body=None
  if arm=='R4':
   import importlib.util
   spec=importlib.util.spec_from_file_location('body019_post_freeze_only',REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019/code/renderer019.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);body=mod.FrozenRenderer(ids)
  H=tensor(load(R/'results'/(arm+'.json'))['T'],torch.float64);obj=Objective(ids,'CROSS','R4'if arm=='R4'else'R3',body);q=torch.zeros(6,device=device,dtype=torch.float64,requires_grad=True);val,parts=obj.evaluate(q,H,component_gradient=True);T=obj.transform(q,H);sf=obj.feature;F,E,report=sf.evaluate(T);F0,_,_=sf.evaluate(T,mode='single');F1=2*F-F0;g0=torch.autograd.grad(F0,q,retain_graph=True)[0].detach().cpu().numpy();g1=torch.autograd.grad(F1,q)[0].detach().cpu().numpy();g=parts['component_gradient_normalized_pose'];g['F_forward']=g0;g['F_reverse']=g1;combined=sum(obj.rw[k]*g[k]for k in obj.rw)+.2*g['F']+.02*g['E'];parts.update(gradient_reference='fresh left tangent exp(q*[.6mm,5deg]) H_endpoint; same units for all methods; no optimization',forward_reverse_cosine=float(np.dot(g0,g1)/max(np.linalg.norm(g0)*np.linalg.norm(g1),1e-20)),combined_Ring_SIFT_gradient=combined,body_to_Ring_SIFT_cosine=float(np.dot(g['body'],combined)/max(np.linalg.norm(g['body'])*np.linalg.norm(combined),1e-20))if body is not None else None,forward_reverse_sum_relative_error=float(np.linalg.norm(.5*(g0+g1)-g['F'])/max(np.linalg.norm(g['F']),1e-20)));results.append(dict(arm=arm,**parts));print('SHADOW_GRADIENT020',arm,flush=True)
 save('metrics/ENDPOINT_GRADIENT_RELATIONSHIPS.json',results)

def sift_perview():
 from evaluate020 import methods
 vv={v['id']:v for v in load(R/'config/VIEWS.json')};out=[]
 for meth in methods():
  H=np.asarray(meth['T'])
  for name,reverse in [('CROSS',False),('REVERSE',True),('CROSS_HOLDOUT',False),('REVERSE_HOLDOUT',True)]:
   for x in load(R/'features'/(name+'_PNP.json')):
    v=vv[x['target']];r=dict(method=meth['method'],view=x['target'],role=v['role'],direction='005_to004'if reverse else'004_to005',success=x['success'],candidate_descriptor_matches=x['matches'])
    if x['success']:
     C=np.asarray(v['T']);X=np.asarray(x['landmark_X']);X=X@H[:3,:3].T+H[:3,3]if reverse else X;C=C if reverse else H@C;P=(X-C[:3,3])@C[:3,:3];Q=P@np.asarray(v['K']).T;uv=Q[:,:2]/Q[:,2:];err=np.linalg.norm(uv-x['uv'],axis=1);r.update(N=len(X),error_px=stats(err),positive_axial_N=int((P[:,2]>0).sum()),landmark_ids=x['landmark_indices'],spatial_cells=x['image_cells'])
    else:r.update(N=0,error_px=stats([]),reason='NO_GEOMETRICALLY_VALIDATED_PNP_CORRESPONDENCES; view retained, no fake observations')
    out.append(r)
 save('metrics/SIFT_PER_VIEW.json',out);table('metrics/SIFT_PER_VIEW.csv',out)

def integrity():
 checks=[]
 for a in load(R/'provenance/UPSTREAM_READONLY.json'):checks.append(dict(path=a['path'],unchanged=sha(a['path'])==a['sha256']))
 for name in ['NO_BODY_PREDICTIONS_FROZEN.json','ALL_POSES_FROZEN_BEFORE_EVALUATION.json']:
  for a in load(R/'provenance'/name)['files']:checks.append(dict(path=a['path'],unchanged=sha(a['path'])==a['sha256']))
 assert all(a['unchanged']for a in checks)
 old=load(REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019/provenance/INPUT_FROZEN.json')
 for a in old['assets']:assert sha(a['path'])==a['sha256']
 save('provenance/FINAL_INTEGRITY.json',dict(checked=checks,original019_assets_checked=len(old['assets']),all_unchanged=True,body_unchanged=True,original_cameras_unchanged=True,scale=1.,no_HERO_inference=True,GT=False))

def reference004():
 vv=[v for v in load(R/'config/VIEWS.json')if v['video']=='004'];rr=RingRenderer([v['id']for v in vv]);rows=[]
 for v in vv:
  with torch.no_grad():L,aux,_=rr.losses(tensor(np.eye(4),torch.float64),v['id'])
  rows.append(dict(view=v['id'],role=v['role'],fixed_in_all_methods=True,M=float(L['M']),Inner_px=aux['I'].get('distance_px'),Mid_px=aux['C']['distance_px'],Outer_px=aux['O'].get('distance_px')))
 save('metrics/REFERENCE004_FIXED_RING_ERRORS.json',rows);table('metrics/REFERENCE004_FIXED_RING_ERRORS.csv',rows)

def main():
 inputs();midpoint_control()
 while not(R/'runtime/EVALUATION_COMPLETE.json').exists():time.sleep(5)
 reference004();sift_perview();gradients();integrity();print('AUDIT020_COMPLETE',flush=True)
if __name__=='__main__':main()
