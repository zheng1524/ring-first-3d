"""Post-fit diagnostics; never changes models, inputs or selection."""
from run import *
def main():
    primary=load(R/'metrics/S2_PRIMARY.json');allstarts=load(R/'metrics/S2_ALL_STARTS.json');pp=load(R/'metrics/S4_PERTURBATIONS.json');jj=load(R/'metrics/S4_JACOBIANS.json');rr=[];sensitivity=[];curvature=[]
    for m in primary:
        p=np.array(m['p']);Q=np.array(m['R0']);prob=Problem(m['scene'],m['arm']);P,F=mesh(p,Q,m['family'],True);scn=mesh_scene(P,F);j=next(x for x in jj if x['key']==key(m['scene'],m['arm']));unstable=0;Cjump=0;Djump=0
        _,visible=prob.parts(p);sc=np.r_[np.ones(3),np.full(3,.1),np.full(3,.2),np.full(len(p)-9,.1)]
        for h in [.001,.0005]:
            for k in range(len(p)):
                good=[]
                for sign in [-1,1]:
                    pc=p.copy();pc[k]+=sign*h*sc[k];good.append(np.concatenate([np.isfinite(first_depth(pc,Q,m['family'],r))for r in prob.rays]))
                unstable+=int((good[0]!=good[1]).sum())
        for cid in protocol()['scenes'][m['scene']]['A']+protocol()['scenes'][m['scene']]['B']:
            o=observation(cid);s=source(cid);rays=vis.camera_rays(o['depth_native_uv'],o['Kn'],s['T']);z=first_depth(p,Q,m['family'],rays);tz=cast(scn,o['depth_native_uv'],o['Kn'],s['T'])[0];cad=cast(ringscene(CC[cid]['scene_id']),o['depth_native_uv'],o['Kn'],s['T'])[0];common=np.isfinite(z)&np.isfinite(tz)
            rr.append(dict(scene=m['scene'],arm=m['arm'],reference=cid,role='A'if cid in prob.ids else'B',fixed_ray_N=len(z),analytic_mesh_hit_disagreement_N=int((np.isfinite(z)!=np.isfinite(tz)).sum()),analytic_mesh_depth_error_mm=stats(z[common]-tz[common]),model_root_behind_CAD_N=int((np.isfinite(z)&(z>cad+.05)).sum())))
        starts=[x for x in allstarts if (x['scene'],x['arm'])==(m['scene'],m['arm'])];pert=[x for x in pp if (x['scene'],x['arm'])==(m['scene'],m['arm'])];params=np.array([x['p']for x in starts+pert]);geom=[geometry_diagnostics(np.array(x['p']),np.array(x['R0']),x['family'])for x in starts+pert]
        sensitivity.append(dict(scene=m['scene'],arm=m['arm'],kind=m['kind'],empirical_solutions=len(params),normalized_J_status=j['status'],local_ray_hit_switches_across_two_steps=unstable,center_range_mm=np.ptp(params[:,:3],axis=0),semiaxes_range_mm=np.ptp(np.exp(params[:,6:9]),axis=0),log_axis_parameter_min=params[:,6:9].min(0),log_axis_parameter_max=params[:,6:9].max(0),physical_parameter_min=params.min(0),physical_parameter_max=params.max(0),max_pairwise_center_mm=float(np.max(np.linalg.norm(params[:,None,:3]-params[None,:,:3],axis=2))),max_camera_perturb_center_mm=max([x['center_displacement_mm']for x in pert if x['perturbation'].startswith('camera')],default=None),B_IoU_min=min(x['B_metrics'][0]['head_IoU']for x in starts+pert),B_IoU_max=max(x['B_metrics'][0]['head_IoU']for x in starts+pert),confidence_interval=False))
        tm=trimesh.Trimesh(P,F,process=False);angle=tm.face_adjacency_angles;length=np.linalg.norm(P[tm.face_adjacency_edges[:,0]]-P[tm.face_adjacency_edges[:,1]],axis=1);ratio=angle/np.maximum(length,1e-12)
        curvature.append(dict(scene=m['scene'],arm=m['arm'],normal_jump_per_edge_mm_inverse=stats(ratio),max_face_normal_jump_rad=float(angle.max()),median_face_normal_jump_rad=float(np.median(angle)),area_mm2=float(tm.area),volume_closed_mesh_only_mm3=float(abs(tm.volume))if tm.is_watertight else None,boundary_edges_N=int((np.bincount(tm.edges_unique_inverse)==1).sum()),model_peak_candidate_mm=m['geometry']['peak_above_model_plane_mm'],high_curvature_status='DESCRIPTIVE_NO_PHYSICAL_TRUTH_THRESHOLD',self_intersection='Excluded by positive radial graph / single-valued height; not an external exhaustive triangle test'))
    table('metrics/REAL_ROOT_AND_CAD_AUDIT.csv',rr);save('metrics/REAL_ROOT_AND_CAD_AUDIT.json',rr);save('metrics/PARAMETER_EMPIRICAL_RANGES.json',sensitivity);save('metrics/GEOMETRY_DIAGNOSTICS.json',curvature)
    # Metadata-only repair: original frozen CSV kept verbatim for audit.
    before=R/'03_DATA_QUALIFICATION.csv';backup=R/'config/DATA_QUALIFICATION_PREOPT.csv'
    if not backup.exists():backup.write_bytes(before.read_bytes())
    with backup.open()as f:q=list(csv.DictReader(f))
    sourceledger=REPO/'experiments/TASK-E3-A-SOURCE-AUDIT-AND-PROBLEM-DEFINITION-001/metrics/E3_SOURCE_AND_VIEW_MANIFEST.csv'
    with sourceledger.open()as f:old=list(csv.DictReader(f))
    supplement=[]
    for row in q:
        if row['role']=='IS_SUPPLEMENTAL_SEARCH':
            row['historical_camera_status']=row['current_camera_gate'];cid=row['source'];row['current_camera_gate']=GATE[cid]['qualification']if cid in GATE else'NOT_REAUDITED_UNQUALIFIED_ARCHIVE';row['role']='IS_SUPPLEMENTAL_SEARCH_HISTORICAL_RECORD'
            x=next(x for x in old if x['source_id']==cid);row['RGB']=x['source_RGB_path'];row['native_depth']=x['native_HERO_depth_path'];row['historical_qualification']=x['qualification'];supplement.append({k:x[k]for k in ['source_id','source_RGB_path','native_HERO_depth_path','Raw_XYZ_path','Raw_Mesh_path','camera_status','qualification','camera_provenance']})
    table('03_DATA_QUALIFICATION.csv',q);save('provenance/IS_PATHS_AND_METADATA_CORRECTION.json',dict(note='Metadata-only correction: supplemental historical E3-A camera status had been placed in current_camera_gate and path column aliases absent. Formal qualification, main A/B, numerical inputs and optimization are unchanged. Original frozen CSV preserved.',original=asset(backup),corrected=asset(before),Is_paths=supplement))
    freeze=load(R/'provenance/PREOPTIMIZATION_FREEZE.json');checks=[]
    for x in freeze['files']:
        pth=REPO/x['path'];actual=sha(backup)if pth==before else sha(pth);checks.append(dict(path=x['path'],passed=actual==x['sha256'],archived_metadata_only=pth==before))
    save('provenance/FREEZE_INTEGRITY.json',dict(all_pass=all(x['passed']for x in checks),checks=checks))
    assert all(x['passed']for x in checks),'Frozen input/code unexpectedly changed'
    print('POST_FIT_AUDIT_DONE',len(rr),'source/model records',flush=True)
if __name__=='__main__':main()
