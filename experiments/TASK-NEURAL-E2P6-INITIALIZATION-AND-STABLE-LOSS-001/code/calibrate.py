"""ONE frozen shell-median rule; no search, no GT or prediction-selected pixels."""
from common import *
from stable_losses import packet,sdf_only

def fibonacci(n):
    i=np.arange(n);z=1-2*(i+.5)/n;phi=np.pi*(3-np.sqrt(5))*i;r=np.sqrt(1-z*z)
    return np.c_[r*np.cos(phi),r*np.sin(phi),z]

def main():
    freeze('P1_BEFORE_OFFICIAL_SHELL_QUERY.json',dict(rule_N=1,source_probe_ids=asset(R/'provenance/SOURCE_PROBES_FROZEN.json')))
    rows=[];calibrations={};directions=fibonacci(cfg()['shell_point_N']);old_init=list(csv.DictReader((E25/'metrics/NEURAL_INITIALIZATION_AND_HITS.csv').open()))
    for scene,refs in selected().items():
        domain=domains()[scene];scale=domain['mm_per_unit'];radius=.5*domain['ROI_radius_mm']
        probe,ports=build_model(domain,0.);probe_hash=e25.parameter_hash(probe)
        shell=directions*radius/scale
        with torch.no_grad():raw=probe.implicit_network.forward(torch.tensor(shell,dtype=torch.float64))[:,0].numpy()
        bias=float(np.median(raw));model,ports=build_model(domain,bias);before=e25.parameter_hash(model)
        with torch.no_grad():
            final_shell=model.implicit_network.forward(torch.tensor(shell,dtype=torch.float64))[:,0].numpy()*scale
            sets=[np.zeros((1,3)),directions*(.25*domain['ROI_radius_mm']/scale),directions*(domain['ROI_radius_mm']/scale),directions*(1.25*domain['ROI_radius_mm']/scale)]
            values=[model.implicit_network.forward(torch.tensor(x,dtype=torch.float64))[:,0].numpy()*scale for x in sets]
        signs=dict(center_SDF_mm=float(values[0][0]),inner_negative_fraction=float((values[1]<0).mean()),
            ROI_boundary_positive_fraction=float((values[2]>0).mean()),outside_ROI_positive_fraction=float((values[3]>0).mean()),
            shell_median_mm=float(np.median(final_shell)),shell_abs_p95_mm=float(np.quantile(abs(final_shell),.95)))
        sign_ok=signs['center_SDF_mm']<0 and signs['inner_negative_fraction']>=.95 and signs['outside_ROI_positive_fraction']>=.95 and abs(signs['shell_median_mm'])<=cfg()['shell_median_abs_tolerance_mm']
        print('SHELL_CALIBRATION',scene,'bias',bias,signs,flush=True)
        beta_mm=float(model.density.get_beta().detach())*scale
        calibration=dict(scene=scene,rule=cfg()['calibration_rule'],bias_network=bias,radius_mm=radius,signs=signs,
            zero_shell_sign_gate=sign_ok,beta_mm=beta_mm,model_parameter_SHA256=before,probe_bias0_SHA256=probe_hash,
            constructor_CPU_ports=ports,seed=cfg()['seed'],optimizer_step_N=0,search_N=1)
        for split in ['small','extra']:
            for ref in refs:
                b=packet(ref,split);pred=sdf_only(model,domain,b);obs=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0)
                N=int(obs.sum());hit=int((pred['render_hit']&obs).sum());high=int(((pred['opacity']>.98)&obs).sum())
                rmask=(b['sampling_class']==3);valid=b['valid'];cap=b['Ring_t_mm']
                limits=valid&np.isfinite(cap);before_ring=bool(np.all(b['end'][limits]<=cap[limits]-.05+1e-8))
                row=dict(scene=scene,source=ref,split=split,rule='SHELL_MEDIAN_UNIFIED',observed_HERO_N=N,front_hit_N=hit,miss_N=N-hit,
                    hit_fraction=hit/N,high_opacity_N=high,high_opacity_without_front_N=int((obs&(pred['opacity']>.98)&~pred['raw_front_cross']).sum()),
                    raw_front_cross_N=int((pred['raw_front_cross']&obs).sum()),positive_Mask_N=int(((b['mask_target']==1)&(b['mask_weight']>0)).sum()),
                    beta_mm=beta_mm,bias_network=bias,Ring_sample_N=int(rmask.sum()),all_visible_segments_before_Ring=before_ring,
                    zero_shell_sign_gate=sign_ok,HERO_hit_gate=hit/N>=.5,rule_changed_after_predictions=False,
                    **signs)
                rows.append(row)
                folder=R/'local_results/initialization';folder.mkdir(exist_ok=True)
                np.savez_compressed(folder/(ref+'_'+split+'.npz'),**pred,source_pixel=b['source_pixel'],observed=obs)
                print('CALIBRATED_FRONT_HITS',ref,split,hit,'/',N,'gate',row['HERO_hit_gate'],flush=True)
        # True raw-head xz slice (same seeded network): historical B differs only
        # by final-layer SDF bias. No synthetic Sphere replaces the official net.
        coords=np.linspace(-1.25*domain['ROI_radius_mm'],1.25*domain['ROI_radius_mm'],97);x,z=np.meshgrid(coords,coords)
        P=np.c_[x.ravel(),np.zeros(x.size),z.ravel()]/scale
        with torch.no_grad():g=probe.implicit_network.forward(torch.tensor(P,dtype=torch.float64))[:,0].numpy()
        before_B=(g-domain['proposed_bias_network'])*scale;after=(g-float(model.implicit_network.lin8.bias[0].detach())*-1)*scale
        # The stored comparison is exactly the raw linear-head relation; validate
        # calibrated output directly so no bias sign error can fake a contour.
        with torch.no_grad():actual=model.implicit_network.forward(torch.tensor(P,dtype=torch.float64))[:,0].numpy()*scale
        assert np.max(abs(actual-after))<1e-8
        np.savez_compressed(R/f'local_results/initialization/{scene}_zero_slice.npz',coordinate_mm=coords,before_B_SDF_mm=before_B.reshape(97,97),after_SDF_mm=actual.reshape(97,97),
            shell_SDF_mm=final_shell,shell_point_network=shell,origin_mm=np.asarray(domain['world_origin_mm']))
        assert before==e25.parameter_hash(model)
        calibration['immutable_after_diagnostics']=True;calibrations[scene]=calibration
        del model,probe;gc.collect()
    table('INITIALIZATION_VALIDATION.csv',rows);save('config/SHELL_CALIBRATION_FROZEN.json',calibrations)
    passed=all(r['HERO_hit_gate'] and r['zero_shell_sign_gate'] and r['all_visible_segments_before_Ring'] for r in rows)
    save('metrics/INITIALIZATION_GATE.json',dict(status='PASS_ONE_RULE_ALL_SOURCES' if passed else 'FAIL_STOP_INITIALIZATION_SEARCH',
        one_rule=True,scene_N=2,source_N=6,split_N=2,passed=passed,additional_rule_search_allowed=False,
        optimizer_step_N=0,GPU='NOT_AUTHORIZED'))
    print('ONE_RULE_INITIALIZATION_COMPLETE',passed,'no additional rule search authorized',flush=True)

if __name__=='__main__':main()
