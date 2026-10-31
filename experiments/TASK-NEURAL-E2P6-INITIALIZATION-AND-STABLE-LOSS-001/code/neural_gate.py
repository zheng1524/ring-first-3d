"""Fixed small AND disjoint moderate probes, real shared network gradients, no updates."""
from common import *
from stable_losses import FiniteCPU,proposal,packet,mask_bundle,weak_anchor

def geom_vector(model,vec):
    out=[];cursor=0
    for name,p in model.named_parameters():
        if name.startswith('implicit_network'):out.append(vec[cursor:cursor+p.numel()])
        cursor+=p.numel()
    return torch.cat(out)

def main():
    save('config/P5_FIXED_PROTOCOL.json',dict(splits=['small','extra'],threshold=.5,
        Eikonal='one shared regularizer, first6 fixed P_INTERIOR ray midpoints from each reference',
        joint_gradient='exact linear sum of actual per-reference autograd vectors + one shared Eikonal; no optimizer',
        numerical_extra='FP32/FP64 implicit-parameter Mask gradient comparison on both probe sets',
        historical_coverage_comparisons=['both legacy A and source-ROI B; no cherry-picked old baseline']))
    freeze('P5_NEURAL_GATE_BEFORE_RUN.json',dict(initialization_rule_unchanged=True,no_search=True))
    rows=[];details=[];directions=[];states=[];precision_rows=[];cache={}
    for scene,refs in selected().items():
        domain=domains()[scene];cal=load(R/'config/SHELL_CALIBRATION_FROZEN.json')[scene];model,ports=build_model(domain,cal['bias_network'])
        before=e25.parameter_hash(model);assert before==cal['model_parameter_SHA256']
        adapter=FiniteCPU(model,domain);model_identity=scene+'_ONE_CALIBRATED_OFFICIAL_SDF'
        for split in ['small','extra']:
            packets=[packet(ref,split) for ref in refs];per_vectors=[];eik_points=[];source_rows=[]
            for j,b in enumerate(packets):
                ref=b['source'];adapter.beta=model.density.get_beta();adapter.current_ref=None
                pred=adapter.render(b,proposal(b,domain['mm_per_unit']),j)
                original,counts=e25.per_view_terms(pred,b)
                bundle=mask_bundle(model,domain,b);anchor=weak_anchor(model,domain,b)
                terms=dict(rgb=original['rgb'],depth=original['depth'],mask=bundle['stable'],old_mask=original['mask'],weak_anchor=anchor['loss'])
                vectors={};metas={}
                for term,value in terms.items():
                    if value is None:meta=dict(finite=False,full_norm=None,implicit_norm=None,trunk_norm=None,head_norm=None);vec=None
                    else:meta,vec=full_gradient(value,model)
                    metas[term]=meta;vectors[term]=vec
                    details.append(dict(scene=scene,source=ref,split=split,term=term,value=None if value is None else float(value.detach()),
                        full_gradient_norm=meta['full_norm'],geometry_gradient_norm=meta['implicit_norm'],trunk_gradient_norm=meta['trunk_norm'],head_gradient_norm=meta['head_norm'],
                        gradient_finite=meta['finite'],shared_network_identity=model_identity))
                observed=(b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0);N=int(observed.sum());hit=int((pred['render_hit']&observed).sum())
                primary=all(metas[k]['finite'] and metas[k]['implicit_norm'] is not None and metas[k]['implicit_norm']>cfg()['useful_geometry_gradient_norm_min'] for k in ['rgb','mask','depth'])
                limit_ok=all(q['max_t_mm']<=b['end'][q['ray']]+1e-8 and q['min_t_mm']>=b['start'][q['ray']]-1e-8 for q in pred['query_limits'])
                ring=np.isfinite(b['Ring_t_mm'])&b['valid'];before_Ring=bool(np.all(b['end'][ring]<=b['Ring_t_mm'][ring]-.05+1e-8))
                row=dict(scene=scene,source=ref,split=split,ray_N=len(b['source_pixel']),positive_Mask_N=int(((b['mask_target']==1)&(b['mask_weight']>0)).sum()),
                    observed_HERO_N=N,front_hit_N=hit,miss_N=N-hit,hit_fraction=hit/N,hit_gate=hit/N>=.5,
                    stable_Mask_loss=float(terms['mask'].detach()),old_Mask_loss=float(terms['old_mask'].detach()),
                    RGB_loss=None if terms['rgb'] is None else float(terms['rgb'].detach()),Depth_loss=None if terms['depth'] is None else float(terms['depth'].detach()),
                    weak_anchor_loss=float(terms['weak_anchor'].detach()),
                    Mask_geometry_gradient=metas['mask']['implicit_norm'],RGB_geometry_gradient=metas['rgb']['implicit_norm'],Depth_geometry_gradient=metas['depth']['implicit_norm'],
                    all_three_actual_gradient_gate=primary,Ring_ray_N=int((b['sampling_class']==3).sum()),finite_prefix_only=limit_ok,before_first_Ring=before_Ring,
                    shared_network_identity=model_identity,geometry_unchanged=True)
                rows.append(row);source_rows.append(row)
                folder=R/'local_results/neural';folder.mkdir(exist_ok=True)
                np.savez_compressed(folder/(ref+'_'+split+'.npz'),source_pixel=b['source_pixel'],opacity=pred['opacity'].detach().numpy(),
                    depth_mm=pred['axial_depth_mm'].detach().numpy(),RGB=pred['rgb_values'].detach().numpy(),render_hit=pred['render_hit'],observed=observed,
                    mask_target=b['mask_target'],stable_per_ray=bundle['per_ray'].detach().numpy(),stable_active_ids=bundle['active_ids'])
                complete=all(vectors[k] is not None for k in ['rgb','mask','depth'])
                base=None if not complete else vectors['rgb']+.1*vectors['mask']+.1*vectors['depth']
                per_vectors.append((ref,base,vectors['mask']))
                cache[(scene,split,ref)]=dict(loss=float(terms['mask'].detach()),geometry=geom_vector(model,vectors['mask']))
                eik_points.append(b['origin'][:6]+b['direction'][:6]*((b['start'][:6]+b['end'][:6])/2)[:,None])
                print('FINAL_TRUE_NEURAL',scene,ref,split,'hits',hit,'/',N,'geometryGrad',primary,'rateGate',row['hit_gate'],flush=True)
                del pred,original,terms,bundle,anchor,vectors,metas;gc.collect()
            eik=adapter.eikonal(np.concatenate(eik_points));eg,ev=full_gradient(eik,model)
            complete=all(v is not None for _,v,_ in per_vectors)
            joint=.1*ev+torch.stack([v for _,v,_ in per_vectors]).mean(0) if complete else None
            for i,(A,va,ma) in enumerate(per_vectors):
                for B,vb,mb in per_vectors[i+1:]:
                    for term,aa,bb in [('data_total',va,vb),('stable_Mask',ma,mb)]:
                        normA=0. if aa is None else robust_norm(aa);normB=0. if bb is None else robust_norm(bb)
                        cosine=None if not normA or not normB else float(torch.dot(aa,bb)/(normA*normB))
                        directions.append(dict(scene=scene,split=split,A=A,B=B,term=term,full_parameter_gradient_cosine=cosine))
            details.append(dict(scene=scene,source='SHARED_FIELD',split=split,term='eikonal',value=float(eik.detach()),
                full_gradient_norm=eg['full_norm'],geometry_gradient_norm=eg['implicit_norm'],trunk_gradient_norm=eg['trunk_norm'],head_gradient_norm=eg['head_norm'],
                gradient_finite=eg['finite'],shared_network_identity=model_identity))
            details.append(dict(scene=scene,source='SHARED_FIELD',split=split,term='joint_sum',value=None,
                full_gradient_norm=None if joint is None else robust_norm(joint),geometry_gradient_norm=None,trunk_gradient_norm=None,head_gradient_norm=None,
                gradient_finite=joint is not None and bool(torch.isfinite(joint).all()),shared_network_identity=model_identity))
            del per_vectors,eik,ev,joint;gc.collect()
        assert before==e25.parameter_hash(model)
        states.append(dict(scene=scene,precision='FP64',parameter_SHA256=before,unchanged=True,CPU_ports=ports))
        del model,adapter;gc.collect()
        model32,ports=build_model(domain,cal['bias_network'],torch.float32);hash32=e25.parameter_hash(model32)
        for split in ['small','extra']:
            for ref in refs:
                b=packet(ref,split);bundle=mask_bundle(model32,domain,b,torch.float32);meta,vec=full_gradient(bundle['stable'],model32)
                g32=geom_vector(model32,vec);g64=cache[(scene,split,ref)]['geometry'];n32=robust_norm(g32);n64=robust_norm(g64)
                cosine=float(torch.dot(g32,g64)/(n32*n64)) if n32 and n64 else None
                error=abs(float(bundle['stable'].detach())-cache[(scene,split,ref)]['loss'])
                rel=abs(n32-n64)/max(n64,1e-300)
                passed=cosine is not None and cosine>=cfg()['gradient_cosine_min'] and rel<=cfg()['gradient_norm_relative_tolerance'] and meta['finite']
                precision_rows.append(dict(scene=scene,source=ref,split=split,geometry_gradient_cosine_FP32_FP64=cosine,
                    geometry_norm_relative_difference=rel,loss_abs_difference=error,geometry_precision_gate=passed,FP32_parameters_unchanged=True))
                del bundle,vec,g32;gc.collect()
        assert e25.parameter_hash(model32)==hash32
        states.append(dict(scene=scene,precision='FP32',parameter_SHA256=hash32,unchanged=True,CPU_ports=ports))
        del model32;gc.collect()
        table('metrics/PER_REFERENCE_NEURAL_SUPERVISION.csv',rows);table('metrics/PER_REFERENCE_LOSSES_AND_GRADIENTS.csv',details)
        table('metrics/SHARED_GRADIENT_DIRECTIONS.csv',directions);table('metrics/PROBE_GEOMETRY_PRECISION.csv',precision_rows)
    strict=all(x['hit_gate'] and x['all_three_actual_gradient_gate'] and x['finite_prefix_only'] and x['before_first_Ring'] for x in rows)
    save('THREE_REFERENCE_NEURAL_GATE.json',dict(status='PASS_BOTH_VIDEO_ALL_PROBES' if strict else 'FAIL_FIXED_SOURCE_GATE',
        Q1_strict_pass=strict,per_reference=rows,small_and_disjoint_extra_both_required=True,threshold=.5,
        actual_shared_parameter_gradient_verified=all(x['all_three_actual_gradient_gate'] for x in rows),
        FP32_FP64_geometry_gradient_gate=all(x['geometry_precision_gate'] for x in precision_rows),
        initialization_rule_N=1,additional_search_performed=False,optimizer_step_N=0,GPU='NOT_AUTHORIZED'))
    save('provenance/P5_MODEL_STATES.json',states)
    print('THREE_REFERENCE_FINAL_GATE',strict,'no difficult reference removed; no parameter update')

if __name__=='__main__':main()
