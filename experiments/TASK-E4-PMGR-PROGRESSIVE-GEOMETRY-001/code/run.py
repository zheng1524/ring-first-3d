"""Fixed-budget P0-P3, direct and frequency controls. B is evaluation only."""
from observability import *
from trust_region import Guard
from mesh_basis import shape,geom
from scipy.spatial import cKDTree
import argparse,time,copy
def brief(parts):
    return [{k:(float(v.detach())if torch.is_tensor(v)else v)for k,v in x.items()if k in ['loss','M','D','H','hit','pair_hit','H_N','H_MAE']}for x in parts]
@torch.no_grad()
def evaluate(p,a,cid,baseline=None):
    V=p.vertices(tensor(a));s=source(cid);o=obs(cid);r=p.renderer.render(V,p.F,s['K'],s['T'],(640,360));pred=r['hard'].cpu().numpy();full=s['labels']==1;known=s['labels']!=2;intersection=(pred&full).sum();union=(full|(pred&known)).sum();ob=contour(full);pb=contour(pred&known);adj=cv2.dilate((~known).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    ob=ob[~adj[ob[:,1].astype(int),ob[:,0].astype(int)]];pb=pb[~adj[pb[:,1].astype(int),pb[:,0].astype(int)]];bd=np.r_[cKDTree(pb).query(ob)[0],cKDTree(ob).query(pb)[0]]if len(pb)and len(ob)else np.array([])
    rt=mesh_scene(V.cpu().numpy(),p.F);z=cast(rt,o['uv'],o['Kn'],o['T'])[0];hit=np.isfinite(z)&(z<=o['cad']+.05);pair=o['pairs'];pg=hit[pair].all(1);delta=z[pair[pg,0]]-z[pair[pg,1]]-o['delta'][pg];dist=rt.compute_distance(o3d.core.Tensor(o['X'].astype(np.float32))).numpy()
    common=pg.copy()if baseline is None else pg&baseline['pair_hit'];cp=pair[common];cr=z[cp[:,0]]-z[cp[:,1]]-o['delta'][common]
    row=dict(source=cid,IoU=float(intersection/max(1,union)),fixed_mask_N=int(full.sum()),mask_hit_N=int(intersection),mask_miss_N=int((full&~pred).sum()),outside_per_fixed_mask=float((pred&~full&known).sum()/max(1,full.sum())),unknown_ring_prediction_N=int((pred&~known).sum()),contour_px=stats(bd),depth_fixed_N=len(z),depth_hit_N=int(hit.sum()),depth_miss_N=int((~hit).sum()),first_depth_error_mm=stats(z[hit]-o['z'][hit]),relative_depth_fixed_pair_N=len(pair),relative_depth_hit_N=int(pg.sum()),relative_depth_error_mm=stats(delta),HERO_distance_mm=stats(dist),common_P0_pair_N=int(common.sum()),common_P0_relative_depth_mm=stats(cr),real_GT='NOT_EVALUABLE')
    return row,dict(z=z,hit=hit,pair_hit=pg,pred=pred)
def check_input_freeze():
    fr=load(R/'metrics/INPUT_FREEZE.json')
    for x in fr['inputs']+[fr['protocol'],fr['initials']]:assert sha(x['path'])==x['sha256'],x['path']
def optimize(scene,initial,seed,arm,counts=None):
    key=f'{scene}__{initial}__s{seed}__{arm}';folder=R/'local_results'/key;folder.mkdir(exist_ok=True)
    resultfile=R/'metrics/runs'/f'{key}.json'
    if resultfile.exists():return load(resultfile)
    p=Problem(scene,initial);pr=p.pr;gate=load(R/'metrics/P0_RENDERER_GATE.json');assert all(x['pass_gate']for x in gate if x['scene']==scene and x['initial']==initial)
    assert load(R/'metrics/SYNTHETIC_CONTROLS.json')[0]['pass_gradient'];a=np.zeros(128);m=np.zeros(128);v=np.zeros(128);adam_t=0;active=[];steps=[];stages=[];mode_rows=[];spectra=[];eval0={};evalarrays0={};start=time.monotonic();attempt_grad=0;accepted=0;fails=[]
    with torch.no_grad():loss,parts,_=p.objective(tensor(a))
    guard=Guard(p,parts)
    for cid in pr['scenes'][scene]['A']+pr['scenes'][scene]['B']:
        ev,ar=evaluate(p,a,cid);eval0[cid]=ev;evalarrays0[cid]=ar
    def snapshot(stage,lastparts,active):
        V=shape(p.b,a);cp=folder/(stage+'.npz');np.savez_compressed(cp,a=a,adam_m=m,adam_v=v,adam_t=adam_t,active=np.array(active),V=V,F=p.F,gradient_evaluations=attempt_grad,accepted_updates=accepted,seed=seed,protocol_sha256=sha(R/'config/LOCKED_PROTOCOL.json'))
        frozen_violation=guard.ring(V)<np.minimum(guard.ring0,0)-.010001
        if frozen_violation.any():raise RuntimeError('SAVED_GEOMETRY_VIOLATES_IMMUTABLE_P0_RING_BOUND')
        mesh=trimesh.Trimesh(V,p.F,process=False);mesh.export(folder/(stage+'.ply'))
        evals=[]
        for cid in pr['scenes'][scene]['A']+pr['scenes'][scene]['B']:
            ev,ar=evaluate(p,a,cid,evalarrays0[cid]);ev['role']='A'if cid in p.ids else'B';ev['P0_common_relative_depth_mm']=stats(evalarrays0[cid]['z'][obs(cid)['pairs'][ar['pair_hit']&evalarrays0[cid]['pair_hit'],0]]-evalarrays0[cid]['z'][obs(cid)['pairs'][ar['pair_hit']&evalarrays0[cid]['pair_hit'],1]]-obs(cid)['delta'][ar['pair_hit']&evalarrays0[cid]['pair_hit']]);evals.append(ev)
            np.savez_compressed(folder/(stage+'__'+cid+'.npz'),**ar)
        st=dict(stage=stage,active_N=len(active),active=active.copy(),gradient_evaluations=attempt_grad,accepted_updates=accepted,geometry=geom(V,p.F),max_P0_displacement_mm=float(np.linalg.norm(V-p.b['V'],axis=1).max()),per_view=brief(lastparts),evaluations=evals)
        stages.append(st);return st
    snapshot('P0',parts,active)
    for stage_idx,budget in enumerate(pr['budgets']):
        stage=f'P{stage_idx+1}';jac=jacobian(p,a);new,mode,summary=analyze(p,jac,active,budget)
        if arm=='PMGR':active=new
        elif arm=='C1_DIRECT_HIGH_DOF':active=list(range(128))
        elif arm=='C2_FREQ_ONLY_PROGRESSIVE':active=list(range(budget))
        elif arm=='C1_count_matched':active=list(range(counts[-1]))
        elif arm=='C2_count_matched':active=list(range(counts[stage_idx]))
        else:raise ValueError(arm)
        for row in mode:mode_rows.append(dict(stage=stage,**row,actual_active=row['mode']in active))
        spectra.append(dict(stage=stage,seconds=jac['seconds'],render_calls=jac['render_calls'],**summary))
        mask=np.zeros(128);mask[active]=1
        with torch.no_grad():oldloss,oldparts,_=p.objective(tensor(a));oldloss=float(oldloss)
        for k in range(pr['steps_per_stage']):
            idx=stage_idx*pr['steps_per_stage']+k;ta=tensor(a).requires_grad_(True);loss,view,terms=p.objective(ta,p.schedule(seed,idx));attempt_grad+=1
            vg=[]
            for vi in view:vg.append(torch.autograd.grad(vi['loss'],ta,retain_graph=True)[0].detach().cpu().numpy())
            grad=torch.autograd.grad(loss,ta)[0].detach().cpu().numpy()*mask
            if not np.isfinite(grad).all():fails.append('NONFINITE_GRADIENT');break
            mm=.9*m+.1*grad;vv=.999*v+.001*grad**2;t=adam_t+1;proposal=-.02*(mm/(1-.9**t))/(np.sqrt(vv/(1-.999**t))+1e-8)*mask
            d=p.b['phi']@proposal;maxd=float(abs(d).max());scale=min(1,p.tau/max(maxd,1e-15));proposal*=scale;oldV=shape(p.b,a);rejected=[];accept=False;checks={}
            for ls in range(7):
                aa=a+proposal*(.5**ls);V=shape(p.b,aa)
                with torch.no_grad():nl,npv,_=p.objective(tensor(aa));nl=float(nl)
                why,checks,rd=guard.check(V,oldV,npv,oldparts,nl,oldloss)
                if not why:
                    a=aa;m=mm;v=vv;adam_t=t;accepted+=1;accept=True;guard.last_ring=rd;oldparts=npv;oldloss=nl;break
                rejected.append(dict(backtrack=ls,reasons=why))
            gn=np.linalg.norm(vg,axis=1);cos=np.array(vg)@np.array(vg).T/np.maximum(gn[:,None]*gn[None,:],1e-15)
            steps.append(dict(step=idx+1,stage=stage,accepted=accept,active_N=len(active),sampled_loss=float(loss.detach()),accepted_full_loss=oldloss,gradient_norm=float(np.linalg.norm(grad)),per_source_gradient_norm=gn,gradient_cosine=cos,proposal_scale=scale,backtracks=len(rejected),rejected=rejected,geometry_checks=checks,per_view=brief(oldparts)))
            if(k+1)%20==0:print('STEP',key,stage,k+1,'accepted',accepted,'L',round(oldloss,4),flush=True)
        snapshot(stage,oldparts,active)
        save('metrics/runs/'+key+'__progress.json',dict(key=key,stages=stages,steps=steps))
        print('STAGE',key,stage,len(active),jac['rank'],'seconds',round(time.monotonic()-start,1),flush=True)
        if fails:break
    result=dict(key=key,scene=scene,initial=initial,seed=seed,arm=arm,qualification=pr['scenes'][scene]['tier'],status='HARD_FAILURE'if fails else'FIXED_BUDGET_COMPLETED',failures=fails,stages=stages,steps=steps,mode_rows=mode_rows,spectra=spectra,seconds=time.monotonic()-start,render_calls=p.renderer.calls,gradient_evaluations=attempt_grad,accepted_updates=accepted,trust_tau_mm=p.tau,P0_ring_min_signed_mm=float(guard.ring0.min()),P0_ring_inside_N=int((guard.ring0<-.01).sum()),P0_self_intersection=guard.base_self,peak_GPU_bytes=torch.cuda.max_memory_allocated(),initial_source=asset(A1/'metrics/PRIMARY_A_ONLY.json'),protocol=asset(R/'config/LOCKED_PROTOCOL.json'),core_code=[asset(R/'code'/f)for f in ['run.py','trust_region.py','losses.py','observability.py']])
    save('metrics/runs/'+key+'.json',result);return result
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scene');ap.add_argument('--initial');ap.add_argument('--seed',type=int);ap.add_argument('--arm');args=ap.parse_args();check_input_freeze();pr=protocol()
    for scene in([args.scene]if args.scene else pr['scenes']):
        for initial in([args.initial]if args.initial else pr['initials']):
            for seed in([args.seed]if args.seed is not None else pr['seeds']):
                results={}
                arms=[args.arm]if args.arm else pr['arms']+pr['supplemental']
                for arm in arms:
                    try:
                        counts=None
                        if'count_matched'in arm:
                            pm=results.get('PMGR')or load(R/'metrics/runs'/f'{scene}__{initial}__s{seed}__PMGR.json');counts=[s['active_N']for s in pm['stages'][1:]]
                        results[arm]=optimize(scene,initial,seed,arm,counts)
                    except Exception as exc:
                        import traceback
                        key=f'{scene}__{initial}__s{seed}__{arm}';traceback.print_exc();save('metrics/runs/'+key+'.json',dict(key=key,scene=scene,initial=initial,seed=seed,arm=arm,status='HARD_FAILURE',failures=[repr(exc)],stages=[],gradient_evaluations=0,seconds=0))
if __name__=='__main__':main()
