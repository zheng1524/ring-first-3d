"""Independent GT audit, only after prediction freeze; no optimization."""
from model import *
from renderer import Renderer
import datetime
def vertex_area(V,F):
    ar=trimesh.triangles.area(V[F])/3;out=np.zeros(len(V))
    for j in range(3):np.add.at(out,F[:,j],ar)
    return out
def main():
    assert load(R/'metrics/FIT_FINISHED.json')['finished'];paths=list((R/'local_results').rglob('*'));pred=[asset(p)for p in paths if p.is_file()]
    if (R/'metrics/PREDICTION_FREEZE.json').exists():
        previous=load(R/'metrics/PREDICTION_FREEZE.json');assert all(sha(p['path'])==p['sha256']for p in previous['files']);save('metrics/PREDICTION_REFREEZE_VERIFICATION.json',dict(unchanged=True,timestamp=datetime.datetime.now().isoformat(),evaluation_only=True))
    else:save('metrics/PREDICTION_FREEZE.json',dict(files=pred,recorded_before_GT_read=True,timestamp=datetime.datetime.now().isoformat(),selection='last bounded optimizer iterate, never GT-selected'))
    gt=dict(np.load(R/'audit_only/TARGET_GT.npz'));base=np.load(R/'inputs/BASE_SOURCE_MESH.npz');V=base['V'];F=base['F'];w=vertex_area(V,F);changed=gt['normal_displacement_mm']>.01;support=gt['changed'];source_rt=scene(V,F);gt_rt=scene(gt['V'],gt['F']);dc=-signed(gt_rt,V)+signed(source_rt,V);gtcenter=np.average(V,axis=0,weights=w*abs(dc));renderer=Renderer();body=Body();hist=load(R/'metrics/FIT_HISTORY.json');ar=np.load(R/'local_results/INITIAL/MODEL.npz');initial_rt=scene(ar['V'],ar['F']);s0=signed(initial_rt,V);stages=[];field_rows=[]
    for h in hist:
        ar=np.load(R/'local_results'/h['stage']/'MODEL.npz');rt=scene(ar['V'],ar['F']);motion=-signed(rt,V)+s0;active=abs(motion)>.01;weight=w*abs(motion);center=np.average(V,axis=0,weights=weight)if weight.sum()>1e-9 else None;inter=float(w[changed&active].sum());union=float(w[changed|active].sum());direction=float((w[changed]*(motion[changed]>0)).sum()/max(w[changed].sum(),1e-12));peak=float(motion.max());false=w[active&~support].sum()/max(w[active].sum(),1e-12);err=motion-dc
        row=dict(stage=h['stage'],iteration=h['iteration'],q=h['q'],parameter_center_error_mm=float(np.linalg.norm(np.asarray(h['q'])[:3]-gt['true_center_mm']))if abs(h['q'][3])>1e-9 else None,actual_update_center_mm=center,GT_update_center_mm=gtcenter,actual_update_centroid_error_mm=float(np.linalg.norm(center-gtcenter))if center is not None else None,GT_true_center_mm=gt['true_center_mm'],GT_peak_mm=float(dc.max()),predicted_positive_peak_mm=peak,predicted_negative_peak_mm=float(motion.min()),relative_peak_error=float(abs(peak-dc.max())/dc.max()),GT_modified_N=int(changed.sum()),GT_modified_area_mm2=float(w[changed].sum()),actual_modified_N=int(active.sum()),actual_modified_area_mm2=float(w[active].sum()),changed_region_IoU=inter/max(union,1e-12),direction_agreement_GT_area=direction,false_update_area_fraction=float(false),wrong_region_displacement_mm=stats(motion[~support]),all_displacement_error_mm=stats(err),GT_region_displacement_error_mm=stats(err[changed]),quality=h['quality'],fit_IoU=float(np.mean([v['full_IoU']for v in h['per_view']if v['role']=='FIT'])),holdout_IoU=float(np.mean([v['full_IoU']for v in h['per_view']if v['role']!='FIT'])))
        stages.append(row);np.savez_compressed(R/'audit_only'/(h['stage']+'_SURFACE_AUDIT.npz'),V=V,F=F,GT_displacement_mm=dc,actual_displacement_mm=motion,error_mm=err,GT_changed=changed,GT_support=support,actual_changed=active,vertex_area_mm2=w)
    rows=list(csv.DictReader((R/'metrics/INITIAL_CORRESPONDENCES.csv').open()));cor=[]
    for r in rows:
        P=np.array(json.loads(r['P']));inside=np.linalg.norm(P-gt['true_center_mm'])<float(gt['true_radius_mm']);cor.append(dict(**r,inside_GT_support=bool(inside),distance_to_GT_center_mm=float(np.linalg.norm(P-gt['true_center_mm']))))
    weighted_total=sum(float(r['seed_weight'])for r in cor);weighted_good=sum(float(r['seed_weight'])for r in cor if r['inside_GT_support']);table('metrics/CORRESPONDENCE_GT_AUDIT.csv',cor)
    # Numerical local identifiability of Mask-only contour evidence, not the GT score.
    final=np.array(hist[-1]['q']);residuals=[]
    def residual(q):
        vv,ff=body.mesh(q);out=[]
        for cid in protocol()['fit_views']:
            a=renderer.silhouette(vv,ff,cid);out.extend(cKDTree(a['uv']).query(renderer.data[cid]['contour'])[0])
        return np.array(out)
    J=[]
    for k,step in enumerate([.02,.02,.02,.01]):
        e=np.eye(4)[k]*step;J.append((residual(final+e)-residual(final-e))/(2*step))
    J=np.column_stack(J);sv=np.linalg.svd(J,compute_uv=False);ident=dict(observations=J.shape[0],parameters=4,finite_difference_steps_mm=[.02,.02,.02,.01],singular_values_px_per_mm=sv,condition_number=float(sv.max()/sv.min())if sv.min()>1e-12 else None,numerical_rank=int(np.linalg.matrix_rank(J)),scope='local target-to-visible-contour distance Jacobian at final; piecewise visibility/topology may change; no global uniqueness certificate')
    a=np.load(R/'inputs/RING_CAD.npz');cad=scene(a['V'],a['F']);f=np.load(R/'local_results/FINAL/MODEL.npz');rt=scene(f['V'],f['F']);ring=dict(body_vertex_min_signed_mm=float(signed(cad,f['V']).min()),CAD_vertex_min_signed_mm=float(signed(rt,a['V']).min()),body_min_unsigned_mm=float(abs(signed(cad,f['V'])).min()),scope='Open3D bidirectional endpoint signs; independent Blender/FCL checks follow')
    final=stages[-1];initial=stages[0];p=protocol()['evaluation_thresholds'];gates=dict(Mask_improved=final['fit_IoU']>initial['fit_IoU'],parameter_center_error=final['parameter_center_error_mm']<=p['center_error_mm'],actual_update_centroid=final['actual_update_centroid_error_mm']<=p['centroid_error_max_mm'],direction=final['direction_agreement_GT_area']>=.95,peak_amplitude=final['relative_peak_error']<=p['relative_peak_error_max'],wrong_region=final['wrong_region_displacement_mm']['p95']<=p['wrong_region_displacement_p95_mm'],roughness=final['quality']['normal_angle_deg']['p95']<=initial['quality']['normal_angle_deg']['p95']+p['normal_angle_p95_growth_limit_deg'],closed_connected=final['quality']['closed']and final['quality']['components']==1,Ring_no_vertex_sign_penetration=ring['body_vertex_min_signed_mm']>=-1e-5 and ring['CAD_vertex_min_signed_mm']>=-1e-5)
    # Separate material construction displacement, Eulerian nearest-surface
    # change, and same-normal intersections. Never compare mismatched operators.
    normal=trimesh.Trimesh(V,F,process=False).vertex_normals;origin=V+.8*normal;rays=o3d.core.Tensor(np.c_[origin,-normal].astype(np.float32))
    def rays_at(rt):
        z=rt.cast_rays(rays)['t_hit'].numpy().astype(float);valid=np.isfinite(z)&(z<=1.6)&(signed(rt,origin)>0);return z,valid
    zs,vs=rays_at(source_rt);zg,vg=rays_at(gt_rt);zi,vi=rays_at(initial_rt);normal_rows=[]
    gt_ray=zs-zg
    for h in hist:
        cp=np.load(R/'local_results'/h['stage']/'MODEL.npz');zp,vp=rays_at(scene(cp['V'],cp['F']));valid=vs&vg&vi&vp;dp=np.full(len(V),np.nan);np.subtract(zi,zp,out=dp,where=valid);ee=dp-gt_ray;normal_rows.append(dict(stage=h['stage'],fixed_N=len(V),valid_N=int(valid.sum()),miss_N=int((~valid).sum()),GT_modified_N=int(changed.sum()),GT_modified_valid_N=int((changed&valid).sum()),GT_constructed_peak_mm=float(gt['normal_displacement_mm'].max()),GT_same_normal_peak_mm=float(gt_ray[valid].max()),pred_same_normal_peak_mm=float(np.nanmax(dp)),error_mm=stats(ee[valid]),GT_region_error_mm=stats(ee[valid&changed])));np.savez_compressed(R/'audit_only'/(h['stage']+'_NORMAL_RAYS.npz'),valid=valid,GT=gt_ray,pred=dp,error=ee)
    save('metrics/NORMAL_RAY_AUDIT.json',dict(rows=normal_rows,GT_ray_vs_constructed_mm=stats(gt_ray[vs&vg]-gt['normal_displacement_mm'][vs&vg]),GT_constructed_vs_nearest_surface_mm=stats(gt['normal_displacement_mm']-dc),definition='same fixed BASE vertex normals; origins X+0.8n, direction -n; missing intersections NaN, no GT or nearest-point fallback'))
    save('metrics/GEOMETRY_EVALUATION.json',dict(stages=stages,displacement_definition='prediction and GT each use the same signed nearest-surface-distance change at common BASE vertices; GT support and material displacement remain separately indexed',GT_constructed_peak_mm=float(gt['normal_displacement_mm'].max()),GT_access='post prediction-freeze only',GT_used_in_loss=False,localization_gates=gates,all_passed=all(gates.values()),local_identifiability=ident,initial_correspondence_weight_in_GT_support=weighted_good/max(weighted_total,1e-12),Ring=ring));table('metrics/ROUND_GEOMETRY.csv',stages);save('metrics/LOCAL_IDENTIFIABILITY.json',ident)
    checks=[]
    for x in load(R/'metrics/IMPLEMENTATION_FREEZE.json')['files']:checks.append(dict(path=x['path'],unchanged=sha(x['path'])==x['sha256']))
    assert all(x['unchanged']for x in checks);save('metrics/SOURCE_IMMUTABILITY.json',dict(all_unchanged=True,checks=checks))
    print('GEOMETRY_EVALUATION',gates,final,flush=True)
if __name__=='__main__':main()
