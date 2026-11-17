"""Only recovered spline parameters optimize; STEP024 Body and cameras are constants."""
from pathlib import Path
import copy
import numpy as np
import torch
from io_utils import dump
from embedded_sweep import EmbeddedSweep
from lengths import measure
from union_mesh import union,provenance,lifted_vertices
from geometry_gate import namespace,check,exterior_clearance
from ring_gate import CurrentRingGate
from projection import RecoveryProjection

def optimize(original,initial,views,ring,base,chart,configuration,support,cfg,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);weights=__import__('common').legacy.balanced_weights(views)
    projection=RecoveryProjection(views,ring,weights,cfg['projection']);projection.setup(original,initial,configuration,support)
    collision=CurrentRingGate(original,ring);ns=namespace();sweep=EmbeddedSweep(configuration,'cuda:0')
    optimizer=torch.optim.Adam([dict(params=[sweep.control_tail],lr=cfg['control_lr_mm']),dict(params=[sweep.radii],lr=cfg['radius_lr'])])
    records=[];best=None;best_score=float('inf');last=None;counter=0;legal_geometry=False
    np.savez_compressed(out/'ITERATION_024_BODY.npz',**original)
    dump(out/'LOCAL_CONFIGURATION.json',dict(embedding=configuration,optimizer=cfg,warm_start='REJECTED_CANDIDATE_WARM_START',Adam_state_restored=False,Body_fixed=True,weights=weights,ring_calibration=collision.calibration))
    dump(out/'RING_INITIAL.json',{k:v for k,v in collision.reference.items()if np.isscalar(v)})
    def trial(stage,iteration,tag):
        nonlocal counter,last,best,best_score,legal_geometry
        counter+=1;folder=out/'trials'/f'{counter:04d}_{stage}_{iteration}_{tag}';folder.mkdir(parents=True)
        V,info=sweep.generate();tube=V.detach().cpu().numpy();control=info['control'].detach().cpu().numpy()
        np.savez_compressed(folder/'SWEEP.npz',**{k:v.detach().cpu().numpy()for k,v in info.items()},V=tube,F=sweep.F)
        merged=union(original,tube,sweep.F,folder/'boolean')
        np.savez_compressed(folder/'BODY.npz',**merged)
        rec=dict(stage=stage,iteration=iteration,tag=tag,folder=str(folder.relative_to(out)),reasons=[])
        try: length=measure(control,original)
        except ValueError as e:length=None;rec['reasons'].append(str(e))
        geomwhy,geometry=check(merged,tube,sweep.F,original,initial,configuration,base,chart,ns);rec['reasons']+=geomwhy
        if not geomwhy:legal_geometry=True
        ok,ring_result,ring_arrays=collision.check(merged);rec['ring']=ring_result
        if not ok:rec['reasons'].append('CURRENT_RING_COLLISION_WORSENING')
        fresh=projection.rebuild(merged);pwhy,view_result=projection.assess(merged,fresh);rec['reasons']+=pwhy
        clearance=V.sum()*0
        if length:
            clearance,cl=exterior_clearance(V,info,configuration,original,length);rec['clearance']=cl
            if cl['unexpected_exterior_inside_samples']:rec['reasons'].append('EXTERIOR_SWEEP_REENTERS_BODY')
            if length['exposed_stalk_length_mm']<cfg['min_exposed_mm']or length['exposed_stalk_length_mm']>cfg['max_exposed_mm']:rec['reasons'].append('EXPOSED_LENGTH_BOUND')
        axes=info['axes'].detach().cpu().numpy()
        if axes.min()<.05 or axes.max()>3.:rec['reasons'].append('CROSS_SECTION_BOUND')
        p=provenance(merged,tube,sweep.F);lifted=lifted_vertices(merged,V,sweep.F,p);contour,per=projection.loss(lifted,merged['F'],fresh)
        priors=sweep.priors(info,clearance)
        # Normal continuity on actual new faces near the Boolean intersection.
        ids=torch.as_tensor(sweep.F,device=V.device);tri=V[ids];normal=torch.nn.functional.normalize(torch.linalg.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0],dim=1),dim=1)
        centers=tri.mean(1);from ring_first_3d.multisurface.geometry import scene,closest
        Q,_,face=closest(scene(original['V'],original['F_solid']),centers.detach().cpu().numpy())
        ot=original['V'][original['F_solid'][face]];n=np.cross(ot[:,1]-ot[:,0],ot[:,2]-ot[:,0]);n/=np.maximum(1e-12,np.linalg.norm(n,axis=1))[:,None]
        near=np.linalg.norm(Q-centers.detach().cpu().numpy(),axis=1)<.15
        nn=torch.as_tensor(n,dtype=V.dtype,device=V.device);active=torch.as_tensor(near,device=V.device)
        attachment=(1-(normal[active]*nn[active]).sum(1)).square().mean()if active.any()else V.sum()*0
        loss=contour+cfg['lambda_clearance']*priors['clearance']+cfg['lambda_bend']*priors['bend']+cfg['lambda_radius']*priors['radius']+cfg['lambda_attachment']*attachment+cfg['lambda_embed']*priors['embed']
        rec.update(reasons=sorted(set(rec['reasons'])),length=length,geometry=geometry,projection=view_result,
            energies=dict(contour=float(contour.detach()),attachment=float(attachment.detach()),total=float(loss.detach()),**{k:float(v.detach())for k,v in priors.items()}),
            Boolean_derivative='Frozen face/bary local surrogate; full Boolean/render rebuilt for acceptance',max_Boolean_provenance_error_mm=p['max_active_mapping_error_mm'])
        rec['accepted_growth']=not rec['reasons'];dump(folder/'GATES.json',rec);records.append(rec);last=rec
        if rec['accepted_growth']and view_result['data_score_delta']<best_score:
            best=copy.deepcopy(rec);best_score=view_result['data_score_delta']
        return loss,rec
    previous_fraction=None
    for stage,fraction in enumerate(cfg['continuation_fractions'],1):
        if previous_fraction is None:sweep.continuation(fraction)
        else:
            delta=(fraction-previous_fraction)*(sweep.reference_control[1:]-sweep.reference_control.new_tensor(configuration['exit_reference']))
            with torch.no_grad():sweep.control_tail.add_(delta)
        previous_fraction=fraction
        anchor=sweep.control_tail.detach().clone()
        loss,current=trial(stage,-1,'start')
        for iteration in range(cfg['iterations_per_stage']):
            parameters=[sweep.control_tail,sweep.radii];before=[p.detach().clone()for p in parameters];state=copy.deepcopy(optimizer.state_dict())
            optimizer.zero_grad();loss.backward()
            gradient_norms=[float(p.grad.norm())if p.grad is not None else 0. for p in parameters]
            assert all(np.isfinite(gradient_norms)), 'NONFINITE_SPLINE_GRADIENT'
            torch.nn.utils.clip_grad_norm_(parameters,10.);optimizer.step()
            with torch.no_grad():
                sweep.control_tail.copy_(anchor+(sweep.control_tail-anchor).clamp(-cfg['control_trust_mm'],cfg['control_trust_mm']))
                sweep.radii.copy_(sweep.reference_radii+(sweep.radii-sweep.reference_radii).clamp(-cfg['radius_logit_trust'],cfg['radius_logit_trust']))
            delta=[p.detach()-b for p,b in zip(parameters,before)];accepted=False
            for backtrack in range(cfg['backtracks']):
                with torch.no_grad():
                    for p,b,d in zip(parameters,before,delta):p.copy_(b+.5**backtrack*d)
                next_loss,new=trial(stage,iteration,'b'+str(backtrack));new['gradient_norms']=gradient_norms
                # Provisional local optimizer may lack final multiview gain, but never waives geometry/ring/protection.
                hard=[r for r in new['reasons']if not r.startswith(('NO_NEW_MULTIVIEW','SUPPORT_VIDEO_DATA','FRESH_2D_DATA'))]
                improvement=new['projection']['data_score_delta']<=current['projection']['data_score_delta']+1e-9
                if not hard and improvement:accepted=True;loss=next_loss;current=new;break
            if not accepted:
                with torch.no_grad():
                    for p,b in zip(parameters,before):p.copy_(b)
                optimizer.load_state_dict(state)
                for group in optimizer.param_groups:group['lr']*=.5
                # Rebuild at the restored real parameters; the rejected graph is never reused.
                loss,current=trial(stage,iteration,'restored')
            dump(out/'PROGRESS.json',dict(stage=stage,iteration=iteration,best=best,last=current,Body_fixed=True,GT_read=False))
            print('RECOVERY',out.name,'stage',stage,'iteration',iteration,'accepted_local',accepted,'final_growth',current['accepted_growth'],'reasons',current['reasons'],flush=True)
    chosen=best if best is not None else last
    mesh=dict(np.load(out/chosen['folder']/'BODY.npz'));sw=dict(np.load(out/chosen['folder']/'SWEEP.npz'))
    filename='FINAL.npz'if best is not None else'LAST_ATTEMPT.npz';np.savez_compressed(out/filename,**mesh)
    np.savez_compressed(out/'FINAL_SWEEP_PARAMETERS.npz',**sw)
    dump(out/'UPDATES.json',dict(trials=records,chosen=chosen,success=best is not None,legal_geometry_seen=legal_geometry,GT_read=False,HERO_read=False,Body_fixed=True,parameters='4 control3-vectors +5x2 radii logits',candidate_search=False))
    # No new secondary shape may be invented from saved seed metadata alone.
    if best is None and not legal_geometry:dump(out/'SECONDARY_STATUS.json',dict(status='NOT_INSTANTIATED',reason='Only secondary patch/delta metadata was saved; no secondary actual rejected BODY/SWEEP asset exists to restore within1e-5mm. No new candidate generated.'))
    return dict(success=best is not None,mesh=filename,chosen=chosen,ring_calibration=collision.calibration)
