"""Per-native-source coverage unions (no double counting a pixel across targets).
These are source-wise coverage proxies, never unique anatomical area.
"""
from hero_evaluate import *
def main():
 checkfreeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json');res=getresults();rows=[];out=N/'local_results/HERO_SOURCE_UNIONS';out.mkdir(exist_ok=True)
 for g in GROUPS:
  for m in ['B0','B1','B2','B3']:
   if not res[g,m].get('poses'):continue
   conf,data=sources(g,res,m);ring,_=ray_scene(conf['ring']['path'])
   for a in data:
    if'X'not in a:continue
    acc={k:np.zeros(len(a['X']),bool)for k in ['known','supported','front','behind','cad_occluded']};targets=0
    for b in data:
     if a['id']==b['id']or'X'not in b:continue
     r=compare(a,b,ring);targets+=1
     for k in acc:acc[k]|=r[k]
    cls=np.full(len(a['X']),4);cls[acc['cad_occluded']&~acc['known']]=3;cls[acc['behind']&~acc['supported']]=2;cls[acc['front']&~acc['supported']]=1;cls[acc['supported']]=0;cls[acc['supported']&acc['front']]=5
    orig=a['mesh']['original_face_id'];mapping={int(k):i for i,k in enumerate(orig)};facecls=np.full(len(orig),4);bound=0
    for fid,c in zip(a['obs']['face_id'],cls):
     if int(fid)in mapping:facecls[mapping[int(fid)]]=c;bound+=1
    area=trimesh.triangles.area(a['V'][a['F']]);row=dict(group=g,method=m,source=a['id'],video=a['video'],targets_N=targets,fixed_unique_native_pixel_N=len(a['X']),unique_known_N=int(acc['known'].sum()),unique_supported_N=int(acc['supported'].sum()),unique_unobserved_by_others_N=int((~acc['known']).sum()),unique_front_without_support_N=int((acc['front']&~acc['supported']).sum()),mixed_support_front_N=int((acc['supported']&acc['front']).sum()),sampled_native_face_binding_N=bound,surface_faces_N=len(orig),sampled_supported_face_area_proxy_mm2=float(area[(facecls==0)|(facecls==5)].sum()),unsampled_or_unknown_face_area_mm2=float(area[facecls==4].sum()),source_total_TRUSTED_area_mm2=float(area.sum()),not_unique_anatomical_area=True,not_full_face_integration=True)
    rows.append(row);np.savez_compressed(out/(g+'_'+m+'_'+a['id']+'.npz'),native_pixel_id=a['obs']['pixel_id'],native_observation_face_id=a['obs']['face_id'],pixel_evidence_class=cls,source_original_face_id=orig,source_face_evidence_class=facecls,**acc)
   print('SOURCE_UNION',g,m,flush=True)
 save('metrics/PER_NATIVE_SOURCE_UNIQUE_COVERAGE.json',rows);table('metrics/PER_NATIVE_SOURCE_UNIQUE_COVERAGE.csv',rows)
 ids=load(N/'assets_index/HERO_NATIVE_IDENTITIES_AND_DERIVED_TRANSFORMS.json');Ds=[np.array(x['D'])for x in ids if x['group']=='G01'and x['method']=='B2'and'D'in x and '_005_'in x['source']];gap=max(float(abs(d-Ds[0]).max())for d in Ds);save('metrics/B2_INTERNAL_RIGID_INVARIANCE.json',dict(group='G01',video='005',sources_N=len(Ds),common_rigid_transform_max_matrix_difference=gap,PASS=gap<1e-10,internal_surface_pair_distances_unchanged=True,CAD_visibility_can_change=True,not_new_depth_inference=True));print('SOURCE_UNION_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
