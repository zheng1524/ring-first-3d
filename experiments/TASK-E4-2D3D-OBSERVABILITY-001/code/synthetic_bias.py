"""A2 diagnostic only. Old same-kernel controls never become native N0 inputs."""
from continuous import *
from model import Body
def main():
    rows=[]
    old=REPO/'experiments/E4-SDF-LOCALIZATION-BLENDER-001/runs/SAME_KERNEL_BIDIRECTIONAL_001/cases'
    for name in ['A_expansion','B_contraction']:
        root=old/name;gt=dict(np.load(root/'audit_only/TARGET_GT.npz'));body=Body(root/'inputs/BASE_FIELD.npz');renderer=Renderer(root);q=gt['q'];V0,F0=body.mesh(q);rt0=scene(V0,F0);reference=signed(rt0,V0)
        offsets=[]
        for cid in protocol()['fit_views']:
            d=renderer.data[cid];p=renderer.silhouette(V0,F0,cid)['uv'];dist,ii=d['tree'].query(p);c=d['contour'][ii]
            # distance magnitude only; sign evidence was separately frozen in the old audit.
            offsets.append(dict(view=cid,GT_to_foreground_center_px=stats(dist)))
        entries=[]
        for label,qq in [('GT',q),('GT_a_minus_0p02',q+[0,0,0,-.02]),('GT_a_plus_0p02',q+[0,0,0,.02]),('previous_FINAL',load(root/'metrics/FIT_FINISHED.json')['q'])]:
            qq=np.array(qq);V,F=body.mesh(qq);move=-signed(scene(V,F),V0)+reference;lo,po=objective(body,renderer,qq);lc,pc=objective(body,renderer,qq,True)
            entries.append(dict(label=label,q=qq,old_loss=lo,half_pixel_target_loss=lc,physical_change_from_GT_mm=stats(move),old_parts=po,corrected_parts=pc))
        base=entries[0];prior=load(root/'metrics/GT_OBJECTIVE_DIAGNOSTIC.json');assert abs(base['old_loss']-prior['GT_loss'])<1e-12;assert abs(entries[-1]['old_loss']-prior['final_loss'])<1e-12
        directional=any(x['old_loss']<base['old_loss']-1e-6 and x['physical_change_from_GT_mm']['maximum']>1e-4 for x in entries[1:3])
        rows.append(dict(case=name,identity='same-kernel synthetic control ONLY',entries=entries,directional_bias_detected=directional,GT_mask_projection=load(root/'metrics/PROJECTION_GATE.json')['passed'],offsets=offsets))
    trigger=any(x['directional_bias_detected']for x in rows)
    save('metrics/SYNTHETIC_OBJECTIVE_AUDIT.json',dict(controls=rows,trigger_single_target_boundary_correction=trigger,no_optimization=True,native_GT_not_read=True,no_GT_parameters_for_native_N0=True))
    print('SYNTHETIC_BIAS_TRIGGER',trigger,[(x['case'],x['directional_bias_detected'],[(z['label'],round(z['old_loss'],7),round(z['half_pixel_target_loss'],7))for z in x['entries']])for x in rows],flush=True)
if __name__=='__main__':main()
