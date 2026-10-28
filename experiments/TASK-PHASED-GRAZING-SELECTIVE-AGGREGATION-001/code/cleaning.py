"""One Raw normal estimate; finite angle experiment, no density retuning."""
from geometry import *
def normal_fields(s):
    P,F=s['P'],s['F'];raw=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]);acc=np.zeros_like(P);mass=np.zeros(len(P));degree=np.zeros(len(P),int)
    for j in range(3):np.add.at(acc,F[:,j],raw);np.add.at(mass,F[:,j],np.linalg.norm(raw,axis=1));np.add.at(degree,F[:,j],1)
    length=np.linalg.norm(acc,axis=1);N=np.divide(acc,length[:,None],out=np.zeros_like(P),where=length[:,None]>0);coh=np.divide(length,mass,out=np.zeros(len(P)),where=mass>0);q=cfg();a=s['a'];ray=P-s['p']['pose'][:3,3];ray/=np.linalg.norm(ray,axis=1)[:,None];beta=np.degrees(np.arcsin(np.clip(abs((N*ray).sum(1)),0,1)))
    reliable=(degree>=q['normal_min_incident_faces'])&(coh>=q['normal_min_coherence'])&np.isfinite(beta)&(length>0)&(a['nonplanarity']<=q['normal_max_nonplanarity'])&(a['tangent_eigen_ratio']>=q['normal_min_tangent_eigen_ratio'])&(a['adjacency_perspective_stretch_max']<=q['normal_max_source_stretch'])
    protected=a['boundary']|a['Ring_near'];delete_reliable=reliable&~protected
    pca=np.degrees(np.arcsin(np.clip(abs((a['normal_world']*ray).sum(1)),0,1)))
    return dict(normal=N,beta_deg=beta,reliable=reliable,angle_deletion_eligible=delete_reliable,protected_boundary_or_Ring=protected,incident_faces=degree,coherence=coh,PCA_beta_diagnostic_deg=pca)
def main():
    verify();rows=[];viewrows=[];q=cfg()
    for c in cases():
        cid=c['id'];s=source(cid);n=normal_fields(s);N=len(s['P']);co=cohorts(s);deleted={'Raw':np.zeros(N,bool),'Density-T2':np.zeros(N,bool)}
        if c['group']=='G01':
            deleted['Density-T2']=s['a']['rho_surface_radius']<q['density_T2'][c['video']]
            z=np.load(ABS/f'local_results/{cid}/T2_exact.npz');assert np.array_equal(np.flatnonzero(deleted['Density-T2']),z['deleted_original_indices'])
        for deg in q['angles_deg']:deleted['Angle-'+str(deg)]=n['angle_deletion_eligible']&(n['beta_deg']<deg)
        folder=R/'local_results/cleaning'/cid;folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/'normals_and_identity.npz',**n,XYZ_mm=s['P'],RGB=s['C'],source_uv=s['uv'],original_faces=s['F'],original_ids=np.arange(N),source_c2w=s['p']['pose'],source_K=s['p']['K'])
        t=selection(sceneid(c));raw=projection(s['P'],s['C'],t);rawm=metric(raw,t)
        for version,mask in deleted.items():
            keep=~mask;ids=np.flatnonzero(keep);fkeep=~mask[s['F']].any(1);np.savez_compressed(folder/(version+'.npz'),deleted=mask,kept_original_ids=ids,deleted_original_ids=np.flatnonzero(mask),kept_original_face_ids=np.flatnonzero(fkeep),reason='Raw baseline'if version=='Raw'else('historical frozen rho < T2'if version=='Density-T2'else'reliable Raw triangle normal beta < '+version.split('-')[1]),normal_beta_deg=n['beta_deg'])
            pred=projection(s['P'][keep],s['C'][keep],t,ids);m=metric(pred,t);row=dict(reference=cid,group=c['group'],video=c['video'],condition=c['condition'],version=version,T2_active=c['group']=='G01',raw_points=N,deleted_points=int(mask.sum()),retained_points=int(keep.sum()),deleted_fraction=float(mask.mean()),normal_reliable_N=int(n['reliable'].sum()),angle_delete_eligible_N=int(n['angle_deletion_eligible'].sum()),unreliable_retained=int((~n['angle_deletion_eligible']&keep).sum()),beta_distribution_deg=stats(n['beta_deg'][n['reliable']]),normal_PCA_absolute_difference_deg=stats(abs(n['beta_deg'][n['reliable']]-n['PCA_beta_diagnostic_deg'][n['reliable']])),**topology(s,mask),selection_target=t['id'],selection_coverage=m['coverage'],selection_coverage_change=m['coverage']-rawm['coverage'],selection_RGB=m['RGB'],common_support=common_metric(raw,pred,t),GT_used=False)
            for name,sel in co.items():row[name+'_N']=int(sel.sum());row[name+'_removed']=int((sel&mask).sum());row[name+'_retention']=float((sel&keep).sum()/sel.sum())if sel.any()else None
            rows.append(row)
        print('ANGLE',cid,'eligible',int(n['angle_deletion_eligible'].sum()),'removed',{k:int(v.sum())for k,v in deleted.items()},flush=True)
    both('cleaning_comparison',rows)
    core=[r for r in rows if r['group']=='G01'];comp=q['cleaning_selection'];dec=[]
    for version in ['Angle-10','Angle-15','Angle-20']:
        a=[r for r in core if r['version']==version];f=[r for r in a if r['video']=='005'];fractions=[1-(r['sparse_stretched_proxy_retention']or 1)for r in f];checks=dict(sparse_reduction=np.median(fractions)>=comp['minimum_median_005_sparse_proxy_reduction'],stalk=all((r['possible_stalk_proxy_retention']if r['possible_stalk_proxy_retention']is not None else 1)>=comp['minimum_stalk_proxy_retention_each_G01']for r in a),main=all(r['largest_raw_main_piece_retention']>=comp['minimum_raw_main_largest_piece_retention_each_G01']for r in a),holes=all(r['interior_deletion_patches']<=comp['maximum_new_interior_deletion_patches_each_G01']for r in a),coverage=all(r['selection_coverage_change']>=-comp['maximum_selection_view_coverage_loss_each_G01']for r in a));dec.append(dict(version=version,median_005_sparse_proxy_reduction=float(np.median(fractions)),checks=checks,eligible=all(checks.values())))
    win=next((r['version']for r in dec if r['eligible']),'Raw');save('metrics/cleaning_decision.json',dict(selected=win,status='SELECTED_DERIVED_CLEANING'if win!='Raw'else'ANGLE_REJECTED_USE_RAW_BASELINE',comparisons=dec,proxies_are_not_true_labels=True,continue_B_to_E=True));save('provenance/CLEANING_OUTPUT_FROZEN.json',stamp(list((R/'local_results/cleaning').rglob('*.npz'))+[R/'metrics/cleaning_decision.json']))
if __name__=='__main__':main()
