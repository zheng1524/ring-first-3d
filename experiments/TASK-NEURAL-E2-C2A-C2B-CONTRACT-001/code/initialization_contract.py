"""Static/analytic initialization guard; never constructs an official network."""
from context import *
from opacity import *

def main():
    require_c2a();domains=load(E1/'config/SDF_DOMAIN_CANDIDATES.json')['candidates']
    old=load(E0/'config/sdf_minimal.json');bias=old['model']['implicit_network']['bias']
    proposal={}
    for scene,ds in domains.items():
        q=next(d for d in ds if d['id']=='VISIBLE_ROI_CENTER_ENVELOPE');s=q['mm_per_unit'];r=q['ROI_radius_mm']
        proposal[scene]=dict(world_origin_mm=q['ROI_center_mm'],mm_per_unit=s,ROI_radius_mm=r,
            old_bias_network=bias,idealized_old_geometric_init_radius_mm=bias*s,
            proposed_init_radius_mm=.5*r,proposed_bias_network=.5*r/s,
            official_beta_initial_mm=.1001*s,official_beta_for_next_run='UNSET_REQUIRES_PHYSICAL_UNIT_PREREGISTRATION',
            status='analytic geometric-init idealization only; actual neural head still NOT_EXECUTED')
    save('config/SDF_INITIALIZATION_CANDIDATE.json',dict(rule='radius=0.5*source-derived fixed ROI; no GT or parameter search',scenes=proposal,weights_created=False,GPU='NOT_GRANTED'))
    freeze('INITIALIZATION_BEFORE_TEST.json')
    rows=[]
    for scene,q in proposal.items():
        refs=selected()[scene]
        for ref in refs:
            b=np.load(R/f'local_results/{ref}_batch.npz');uv=b['source_uv'];C=next(c for c in registry()['references']if c['id']==ref);p=np.load(C['pack'])
            ray=vis.camera_rays(uv,p['K'],p['pose']);f=np.linalg.norm(ray[:,3:],axis=1);d=ray[:,3:]/f[:,None];frame=np.load(R/f'local_results/rays/{ref}.npz');pix=b['source_pixel']
            intervals=dict(start_mm=frame['ROI_start_t_mm'][pix],end_mm=frame['ROI_end_t_mm'][pix],valid=frame['ROI_valid'][pix])
            center=torch.tensor(q['world_origin_mm'],dtype=torch.float64)
            for label,radius in [('OLD_INIT_IDEALIZATION',q['idealized_old_geometric_init_radius_mm']),('SOURCE_ROI_INIT_CANDIDATE',q['proposed_init_radius_mm'])]:
                out=integrate_visible(ray[:,:3],d,intervals,lambda P:torch.linalg.vector_norm(P-center,dim=-1)-radius,.08)
                observed=(b['sampling_class']==0)&(b['depth_weight']>0)
                rows.append(dict(scene=scene,source=ref,initialization=label,radius_mm=radius,ROI_radius_mm=q['ROI_radius_mm'],requested_P_interior_depth_N=int(observed.sum()),
                    analytic_front_surface_hit_N=int((out['render_hit']&observed).sum()),
                    status='EXPECTED_NO_ROI_ZERO_CROSSING'if radius>=q['ROI_radius_mm']else'OLD_INIT_IDEALIZATION_HAS_CROSSING'if label=='OLD_INIT_IDEALIZATION'else'ANALYTIC_CANDIDATE_NOT_OFFICIAL_MODEL',
                    actual_model_forward_N=0,weights_updated=False))
                if radius>=q['ROI_radius_mm']:assert not out['render_hit'][observed].any(),'geometric-init idealization contradicts ROI inclusion'
    table('metrics/INITIALIZATION_DOMAIN_GUARD.csv',rows)
    print('INITIALIZATION_CONTRACT_COMPLETE: old init idealization crosses004 ROI but not005 ROI; no official network executed',flush=True)

if __name__=='__main__':main()
