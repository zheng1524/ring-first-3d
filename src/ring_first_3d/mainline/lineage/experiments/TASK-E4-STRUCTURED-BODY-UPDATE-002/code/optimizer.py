"""One graph/sweep PyTorch optimizer; fresh projection/collision gates on every trial."""
from ring_first_3d.mainline.paths import historical_path as _mainline_path
import copy
from pathlib import Path
import numpy as np
import torch
from deformation_graph import DeformationGraph,so3
from smooth_arap import SmoothARAP
from bspline_sweep import BSplineSweep
from projection_gate import ProjectionGate
from ring_collision_gate import RingCollisionGate
from common import legacy,dump,geometry
from growth_evidence import candidates as growth_candidates


def save_pairs(path,assignments,full=False):
    path.mkdir(exist_ok=True)
    for cid,a in assignments.items():
        content=dict(a['pairs']);content.update(R_plus=a['R_plus'],R_minus=a['R_minus'],unknown=a['unknown'],predicted=a['predicted'],target=a['target'])
        if full:content.update(visible_face=a['visible_face'],visible_bary=a['visible_bary'])
        np.savez_compressed(path/(cid+'.npz'),**content)

def train(initial,views,ring,base,chart,cfg,out,arm):
    iterations=cfg.get('iterations',36)
    if type(iterations) is not int or not 1<=iterations<=36:
        raise ValueError('iterations must be an integer in [1,36]; historical default 36')
    assert all(v['role']=='FIT'for v in views);assert all(set(v)<={'id','video','role','direction_block','K','C','labels','RGB'}for v in views)
    out=Path(out);out.mkdir(parents=True);device='cuda:0';weights=legacy.balanced_weights(views)
    graph=DeformationGraph(initial['V'],initial['F_solid'],32,4,device);arap=SmoothARAP(initial['V'],initial['F_solid'],.7,device)
    rotation=torch.nn.Parameter(torch.zeros((32,3),dtype=torch.float64,device=device));translation=torch.nn.Parameter(torch.zeros_like(rotation));sweep=None
    gate=ProjectionGate(views,ring,weights,cfg['projection']);rg=RingCollisionGate(initial,ring)
    ns=legacy.legacy_geometry(str(legacy.Path(str(_mainline_path('/home/liu/ring_first_3d_structural_update/experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001/legacy015/safe_geometry.py')))))
    cap_nodes=None;n=None
    if initial['inferred_base_faces'].any():
        ids=np.unique(graph.vertex_nodes_np[initial['boundary_vertex']]);cap_nodes=torch.zeros(32,dtype=torch.bool,device=device);cap_nodes[torch.as_tensor(ids,device=device)]=True;n=torch.as_tensor(base['selected_plane'][:3],device=device,dtype=torch.float64)
    def transforms():
        if cap_nodes is None:return rotation,translation
        w=torch.where(cap_nodes[:,None],(rotation@n)[:,None]*n,rotation)
        t=torch.where(cap_nodes[:,None],translation-(translation@n)[:,None]*n,translation)
        return w,t
    def generated(sw=None):
        w,t=transforms();V=graph.mesh(w,t);info=None
        if sw is None:return V,dict(initial,V=V.detach().cpu().numpy()),info,V
        full,info=sw.generate(V);return full,sw.body(full.detach().cpu().numpy(),initial),info,V
    def make_optimizer(sw):
        groups=[dict(params=[rotation],lr=cfg['rotation_lr_rad']),dict(params=[translation],lr=cfg['translation_lr_mm'])]
        if sw is not None:groups.append(dict(params=list(sw.parameters()),lr=cfg['sweep_lr_mm']))
        return torch.optim.Adam(groups)
    opt=make_optimizer(sweep);V,current,_,_=generated();initial_pairs=gate.rebuild(current,True);gate.initial=copy.deepcopy(initial_pairs);current_pairs=initial_pairs
    np.savez_compressed(out/'INITIAL.npz',**initial);save_pairs(out/'INITIAL_PAIRS',initial_pairs,True)
    dump(out/'INPUT_CONTRACT.json',dict(weights=weights,FIT=[v['id']for v in views],initialization='EXACT_013_INPUT_MESH_V_F_SOLID_CAP',camera_optimized=False,HERO_read=False,GT_read=False,ring_calibration=rg.calibration,graph_nodes=graph.node_ids,graph_edges=graph.edges_np,vertex_nodes=graph.vertex_nodes_np,vertex_weights=graph.weights_np,cap_nodes=None if cap_nodes is None else cap_nodes.detach().cpu().numpy()))
    rows=[];growth=[]
    def loss(sw,R,pairs):
        V,body,info,oldV=generated(sw);contour,_=gate.loss(V,body['F'],pairs);ea,es,ss=arap.energies(oldV,R);w,t=transforms();eg=graph.energy(w,t);prior=translation.square().mean()+rotation.square().mean();bend=rad=attach=V.sum()*0
        if sw is not None:bend,rad,attach=sw.penalties(V,info)
        total=contour+cfg['lambda_graph']*eg+cfg['lambda_sarap']*ss/arap.mass.sum()+cfg['lambda_prior']*prior+cfg['lambda_centerline']*bend+cfg['lambda_radius']*rad+cfg['lambda_attachment']*attach
        return total,dict(contour=contour,ARAP=ea,smooth=es,SARAP=ss,graph=eg,prior=prior,centerline=bend,radius=rad,attachment=attach),V,body,info
    for iteration in range(iterations):
        attempt_sweep=sweep;growth_record=None;previous_optimizer=opt
        if arm=='DEFORM_SWEEP'and sweep is None and iteration in cfg['growth_iterations']:
            pp={}
            for cid,a in current_pairs.items():
                p=a['pairs'];support=p['growth_candidate'].copy()
                # Low-IoU views remain in fitting but cannot create growth alone.
                if a['stats']['IoU']<cfg['growth_min_view_IoU']:support[:]=False
                pp[cid]=dict(p,accepted=support,missing_support=support,projected_uv=p['source_uv'])
            candidates,audit=growth_candidates(current,views,pp,cfg['growth']);growth_record=dict(iteration=iteration,**audit,status='UNDERCONSTRAINED_GROWTH'if not candidates else'CANDIDATE',candidates=candidates)
            if candidates:
                c=candidates[0]
                try:attempt_sweep=BSplineSweep(current,c['patch'],c['delta'],min(cfg['max_sweep_length_mm'],float(np.linalg.norm(c['delta']))),device=device);opt=make_optimizer(attempt_sweep)
                except ValueError as e:growth_record.update(status='ATTACHMENT_REJECTED',reason=str(e))
                else:
                    for p in [rotation,translation]:
                        if p in previous_optimizer.state:opt.state[p]=copy.deepcopy(previous_optimizer.state[p])
                # Attachment exceptions leave the existing optimizer untouched.
                if attempt_sweep is sweep:opt=previous_optimizer
        parameters=[rotation,translation]+([]if attempt_sweep is None else list(attempt_sweep.parameters()));before=[p.detach().clone()for p in parameters];state=copy.deepcopy(opt.state_dict())
        # First candidate pairs must refer to its actual new topology, never old IDs.
        V0,template,info,baseV=generated(attempt_sweep);pairs=current_pairs if attempt_sweep is sweep else gate.rebuild(template)
        R=arap.rotations(baseV);old_loss=float(loss(sweep,R,current_pairs)[0].detach());old_region=gate.regional_score(current_pairs)
        start_loss,_,_,_,_=loss(attempt_sweep,R,pairs);gradients=[]
        for _ in range(cfg['inner_steps']):
            opt.zero_grad();value,parts,_,_,_=loss(attempt_sweep,R,pairs);value.backward();gradients.append(float(torch.sqrt(sum((p.grad.square().sum()if p.grad is not None else p.sum()*0)for p in parameters)).detach()));opt.step()
        delta=[p.detach()-q for p,q in zip(parameters,before)]
        accepted=False;rejected=[];candidate=None;fresh=None;ring_summary=None;ge=None
        for ls in range(cfg['line_search_steps']):
            alpha=.5**ls
            with torch.no_grad():
                for p,q,d in zip(parameters,before,delta):p.copy_(q+alpha*d)
            try:
                _,candidate,info,_=generated(attempt_sweep)
                # FORCE a real full FIT render, residual and Face/bary rebuild.
                fresh=gate.rebuild(candidate);protected=gate.protect(fresh);reasons=[]
                if protected:reasons.append('PER_VIEW_NON_REGRESSION')
                if info is not None:
                    axes=info['axes'].detach().cpu().numpy();C=info['centerline'].detach().cpu().numpy();length=float(np.linalg.norm(np.diff(C,axis=0),axis=1).sum())
                    if axes.min()<.05 or axes.max()>cfg['max_sweep_radius_mm'] or length>cfg['max_sweep_length_mm']:reasons.append('SWEEP_DIMENSION_BOUND')
                if attempt_sweep is not sweep and ls==0:
                    folder=out/f'GROWTH_PROPOSAL_{iteration:03d}';folder.mkdir(exist_ok=True);np.savez_compressed(folder/'BODY.npz',**candidate);np.savez_compressed(folder/'SWEEP.npz',**{k:v.detach().cpu().numpy()for k,v in info.items()},root_loop=attempt_sweep.loop,removed_faces=attempt_sweep.patch)
                if np.linalg.norm(candidate['V'][:len(initial['V'])]-current['V'][:len(initial['V'])],axis=1).max()>chart['tau_mm']:reasons.append('STEP_TRUST')
                region=gate.regional_score(fresh)
                if region>old_region+1e-9:reasons.append('FRESH_REGION_REGRESSION')
                for cid in fresh:
                    if fresh[cid]['stats']['accepted_N']<.7*current_pairs[cid]['stats']['accepted_N']:reasons.append('CORRESPONDENCE_COVERAGE_COLLAPSE');break
                ok,ring_summary,ring_arrays=rg.check(candidate,current,attempt_sweep)
                if not ok:reasons.append('RING_COLLISION_WORSENING')
                other,ge=geometry(candidate,current,initial,base,chart,ns);reasons+=other
                new_loss=float(loss(attempt_sweep,R,fresh)[0].detach())
                if new_loss>old_loss+1e-9:reasons.append('FRESH_FIT_OBJECTIVE')
                if attempt_sweep is not sweep and region>=old_region-cfg['min_growth_region_gain']:reasons.append('NO_MULTIVIEW_GROWTH_GAIN')
                if not reasons:accepted=True;break
                rejected.append(dict(alpha=alpha,reasons=sorted(set(reasons)),protected_views=protected,region_score=region,objective=new_loss,ring=ring_summary,geometry=ge,view_stats=[a['stats']for a in fresh.values()]))
            except (ValueError,RuntimeError)as e:rejected.append(dict(alpha=alpha,reasons=['NUMERICAL_CANDIDATE_REJECTED'],detail=str(e)))
        if accepted:
            sweep=attempt_sweep;current=candidate;current_pairs=fresh
            if growth_record:growth_record['status']='ACCEPTED_SWEEP'
        else:
            with torch.no_grad():
                for p,q in zip(parameters,before):p.copy_(q)
            if attempt_sweep is not sweep:opt=previous_optimizer
            else:opt.load_state_dict(state)
            for group in opt.param_groups:group['lr']*=.5
            if growth_record and growth_record['status']=='CANDIDATE':growth_record['status']='SWEEP_GATES_REJECTED'
        if growth_record:growth.append(growth_record)
        current_pairs=gate.rebuild(current,iteration in [0,12,24,iterations-1]);V,body,info,bV=generated(sweep);_,parts,_,_,_=loss(sweep,arap.rotations(bV),current_pairs)
        w,t=transforms();rec=dict(iteration=iteration,accepted=accepted,growth=bool(sweep),gradient_norms=gradients,energies={k:float(v.detach())for k,v in parts.items()},views=[a['stats']for a in current_pairs.values()],rejections=rejected,graph_rotation_rad=w.detach().cpu().numpy(),graph_translation_mm=t.detach().cpu().numpy(),ring=ring_summary if accepted else rg.measure(current))
        # Full arrays stored once at meaningful stages; compact summaries every step.
        rec['ring']={k:v for k,v in rec['ring'].items()if not isinstance(v,np.ndarray)}
        rows.append(rec);dump(out/f'STEP_{iteration:03d}.json',rec)
        if iteration in [0,12,24,iterations-1]:
            p=out/f'STEP_{iteration:03d}';p.mkdir();np.savez_compressed(p/'BODY.npz',**current);save_pairs(p/'PAIRS',current_pairs,True);np.savez_compressed(p/'GRAPH.npz',nodes=graph.g.detach().cpu().numpy(),rotation=w.detach().cpu().numpy(),translation=t.detach().cpu().numpy(),edges=graph.edges_np)
            if info:np.savez_compressed(p/'SWEEP.npz',**{k:v.detach().cpu().numpy()for k,v in info.items()},root_loop=sweep.loop,removed_faces=sweep.patch)
        print('STRUCTURED',arm,iteration,'accepted',accepted,'nodes',32,'V',len(current['V']),flush=True)
    np.savez_compressed(out/'FINAL.npz',**current);save_pairs(out/'FINAL_PAIRS',current_pairs,True)
    dump(out/'UPDATES.json',dict(iterations=rows,growth=growth,GT_read=False,HERO_read=False,free_vertex_parameters=False,configuration=cfg))
    dump(out/'PREDICTION_FROZEN.json',dict(arm=arm,mesh='FINAL.npz',GT_read=False,checkpoint=f'FINAL_FIXED_{iterations}_NO_GT_SELECTION'))
    np.savez_compressed(out/'RING_INITIAL.npz',**rg.measure(initial));np.savez_compressed(out/'RING_FINAL.npz',**rg.measure(current));return current
