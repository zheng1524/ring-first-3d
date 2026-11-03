from residuals import *
def jacobian(model,h,balanced=True):
    zero=np.zeros(model.p);cols=[]
    for k in range(model.p):
        v=zero.copy();v[k]=h;cols.append((model.vector(v,balanced=balanced)-model.vector(-v,balanced=balanced))/(2*h))
    return np.column_stack(cols)
def spectrum(J,names,stable):
    U,s,V=np.linalg.svd(J,full_matrices=False);rank={str(t):int((s>s[0]*t).sum())if len(s)and s[0]>0 else 0 for t in [1e-2,1e-3,1e-4,1e-6,1e-8]}
    # An empirical proxy Jacobian cannot establish structural nonidentifiability of the physical scene.
    ratio=float(s[-1]/s[0])if len(s)and s[0]>0 else 0
    status='NOT_EVALUABLE_DIFFERENCE_UNSTABLE'if not stable else'EMPIRICAL_PROXY_NULL'if ratio<1e-8 else'WEAK_LOCAL_IDENTIFIABILITY'if ratio<1e-3 else'LOCAL_PROXY_IDENTIFIABILITY_GOOD'
    norms=np.linalg.norm(J,axis=0);corr=np.abs(J.T@J)/np.maximum(1e-30,norms[:,None]*norms[None,:]);pairs=[]
    for i in range(len(names)):
        if ':bias_'not in names[i]:
            for j in range(len(names)):
                if ':bias_'in names[j]:pairs.append(dict(pose=names[i],depth=names[j],absolute_column_cosine=float(corr[i,j])))
    weak=V[-1];return dict(rows=J.shape[0],parameters=J.shape[1],singular_values=s,rank_by_relative_threshold=rank,primary_rank=rank['0.001'],rank_fraction=rank['0.001']/len(names),condition_number=float(s[0]/s[-1])if s[-1]>1e-15 else None,minimum_relative_singular_value=ratio,status=status,weakest_direction={n:float(v)for n,v in zip(names,weak)},top_couplings=sorted(pairs,key=lambda p:-p['absolute_column_cosine'])[:8]),s,V
def main():
    freeze=R/'provenance/BEFORE_B.json'
    if not freeze.exists():save('provenance/BEFORE_B.json',dict(protocol=asset(R/'config/PROTOCOL.json'),code=[asset(p)for p in sorted((R/'code').glob('*.py'))],UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),A_results_not_used_to_change_rules=True))
    f=load(freeze)
    for c in f['code']:assert sha(c['path'])==c['sha256']
    allresults=[];sense=[];joint=[];obsrows=[];grads=[];checks=[]
    for scene,order in protocol()['B_orders'].items():
        for count in protocol()['B_counts'][scene]:
            ids=order[:count];tag=scene+'_'+str(count);m=ResidualModel(ids);obsrows.extend([dict(scene=scene,views=count,**x)for x in m.inventory]);dest=R/'local_results/B'/tag;dest.mkdir(parents=True,exist_ok=True);m.save_observations(dest/'FIXED_OBSERVATIONS.npz')
            J1=jacobian(m,.01);J2=jacobian(m,.005);J3=jacobian(m,.0025)
            rel=lambda A,B:float(np.linalg.norm(A-B)/max(1e-12,np.linalg.norm(B)))
            err=rel(J2,J3);cols=np.linalg.norm(J2-J3,axis=0)/np.maximum(1e-8,np.linalg.norm(J3,axis=0));stable=err<=.05 and np.quantile(cols,.95)<=.1
            # Ring exact yaw symmetry independent of finite-difference SVD rank choices.
            T0=source(ids[-1])['T'];Z=np.eye(4);Z[:3,:3]=Rotation.from_rotvec([0,0,.0001]).as_matrix();yawerr=float(abs(ring_curves(ids[-1],Z@T0)-ring_curves(ids[-1],T0)).max())
            assert yawerr<1e-8,'ANALYTIC_RING_SYMMETRY_FAILED'
            checks.append(dict(scene=scene,views=count,J_h01_h005_relative=rel(J1,J2),J_h005_h0025_relative=err,column_p95_relative=float(np.quantile(cols,.95)),max_column_relative=float(cols.max()),finite=bool(np.isfinite(J3).all()),stable=bool(stable),ring_global_yaw_invariance_px=yawerr))
            lens={k:len(v)for k,v in m.zero.items()};offsets={};start=0
            # parts() order differs from C3 only by listed C3 order; explicitly compute each slice.
            for k in protocol()['B']['C3']:offsets[k]=(start,start+lens[k]);start+=lens[k]
            Jr=np.concatenate([J3[a:b]*np.sqrt(max(1,b-a))for a,b in offsets.values()],axis=0)
            for constraint in ['C1','C2','C3']:
                idx=np.concatenate([np.arange(*offsets[k])for k in protocol()['B'][constraint]]);J=J3[idx];sp,s,V=spectrum(J,m.names,stable);spraw,_,_=spectrum(Jr[idx],m.names,stable)
                z=m.vector(np.zeros(m.p),constraint);grad=J.T@z;physical=grad/m.scales
                row=dict(scene=scene,views=count,ids=ids,constraint=constraint,residual_counts={k:lens[k]for k in protocol()['B'][constraint]},finite_difference_stable=bool(stable),unit_noise_only_spectrum=spraw,**sp)
                allresults.append(row);np.savez_compressed(dest/(constraint+'_JACOBIAN_SVD.npz'),J_scaled_balanced=J,J_unit_noise_only=Jr[idx],parameter_scales=m.scales,parameter_names=np.array(m.names),residual_at_zero=z,singular_values=s,Vt=V,gradient_normalized=grad,gradient_physical=physical)
                grads.extend(dict(scene=scene,views=count,constraint=constraint,parameter=n,physical_scale=float(sc),dE_dnormalized=float(g),dE_dphysical=float(gp))for n,sc,g,gp in zip(m.names,m.scales,grad,physical))
            print('B',tag,'J',J3.shape,'difference',err,'stable',stable,'C3 ratio',allresults[-1]['minimum_relative_singular_value'],flush=True)
            if count==2:
                z=np.zeros(m.p);r0=m.vector(z);J=J3
                # All parameters, both signs, three prespecified amplitudes. No fit or step selection.
                for k,name in enumerate(m.names):
                    amps=protocol()['B']['sensitivity_rotation_deg']if '_rad'in name else protocol()['B']['sensitivity_depth_mm']if ':bias_'in name else protocol()['B']['sensitivity_translation_mm']
                    for a in amps:
                        y=z.copy();physical_a=np.deg2rad(a)if '_rad'in name else a;y[k]=physical_a/m.scales[k];rr=m.vector(y);dr=rr-r0;linear=J@y
                        # Fixed residual response and independently re-evaluated visibility/RGB.
                        p=m.parts(y);rec=dict(scene=scene,parameter=name,amplitude=float(a),amplitude_unit='deg'if '_rad'in name else'mm',E=float(rr@rr/2),delta_E=float((rr@rr-r0@r0)/2),linear_relative_error=float(np.linalg.norm(dr-linear)/max(1e-12,np.linalg.norm(dr))),parts_RMS={k:float(np.sqrt(np.mean(v*v)))if len(v)else None for k,v in p.items()},dynamic=m.dynamic(y))
                        sense.append(rec)
                # Fixed 5x5 two-parameter coupling map, not an optimizer.
                iz=2;ib=6*(m.n-1)+1
                for az in [-.2,-.1,0,.1,.2]:
                    for ab in [-.2,-.1,0,.1,.2]:
                        y=z.copy();y[iz]=az/.1;y[ib]=ab/.1;rr=m.vector(y);joint.append(dict(scene=scene,target_tz_mm=az,target_bias_mm=ab,E=float(rr@rr/2),dynamic=m.dynamic(y)))
                # Verify weakest mixed direction with real nonlinear residual; no parameter update adopted.
                sp,s,V=spectrum(J,m.names,stable);v=V[-1]
                for a in [-1.,-.5,0,.5,1.]:
                    y=a*v;rr=m.vector(y);joint.append(dict(scene=scene,direction='C3_weakest_SVD',amplitude=a,normalized_vector=v,E=float(rr@rr/2),predicted_delta_norm=float(np.linalg.norm(J@y)),actual_delta_norm=float(np.linalg.norm(rr-r0)),dynamic=m.dynamic(y)))
            save('metrics/B_SVD_RESULTS.json',allresults);save('metrics/B_SENSITIVITY.json',sense);save('metrics/B_JOINT_PERTURBATIONS.json',joint);table('metrics/B_OBSERVATION_COUNTS.csv',obsrows);table('metrics/B_GRADIENTS.csv',grads);table('metrics/B_DIFFERENCE_CHECKS.csv',checks)
    table('metrics/PERTURBATION_ERRORS.csv',[{k:json.dumps(clean(v))if isinstance(v,dict)else v for k,v in x.items()}for x in sense])
    save('provenance/B_OUTPUT_FROZEN.json',dict(files=[asset(p)for p in (R/'local_results/B').glob('**/*.npz')],network_training=False,GT=False,updated_cameras_adopted=0,updated_HERO_adopted=0))
if __name__=='__main__':main()
