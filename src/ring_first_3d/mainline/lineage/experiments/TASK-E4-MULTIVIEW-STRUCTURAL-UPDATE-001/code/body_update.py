"""One FIT-only metric updater for both domains. Discrete assignments are detached.
No camera variables, GT loader, depth observations, DXY or per-image Body.
"""
from pathlib import Path
import ast, copy, json
from types import SimpleNamespace
import numpy as np
import torch
import cv2
import trimesh
import open3d as o3d
from scipy.spatial import cKDTree
from scipy.ndimage import binary_erosion, binary_dilation, distance_transform_edt
from ring_first_3d.synthetic.raster import ray_map
from ring_first_3d.multisurface.geometry import scene, sample_mesh
from ring_first_3d.contour_guided.correspondence import project, project_torch
from ring_first_3d.synthetic.io import save_json
from ring_first_3d.policy.contracts import require


def initialize(asset, ring, reference_ring):
    """Exact 013, identity Ring frame only. Never fits a shape or reads GT."""
    require(all(np.array_equal(ring[k],reference_ring[k]) for k in ('V','F')),
            'CAD_FRAME', 'Identity frame requires byte-identical canonical CAD')
    a=dict(np.load(asset))
    require(all(k in a for k in ('V','F','F_solid','inferred_base_faces','boundary_vertex')),
            'INITIALIZATION_LINEAGE','EXACT_013_INPUT_MESH_V_F_SOLID_CAP required')
    return {k:a[k].copy() for k in ('V','F','F_solid','inferred_base_faces','boundary_vertex')}


def balanced_weights(views):
    # Exactly historical multiview.weights formula; no new view selection.
    videos=sorted({v['video'] for v in views});w={}
    for video in videos:
        vv=[v for v in views if v['video']==video];blocks={v['direction_block'] for v in vv}
        for b in blocks:
            block=[v for v in vv if v['direction_block']==b]
            for v in block:w[v['id']]=1/len(videos)/len(blocks)/len(block)
    return w


def boundary(mask):
    y,x=np.nonzero(mask & ~binary_erosion(mask));return np.c_[x,y]


def take(a,n):
    return a[np.linspace(0,len(a)-1,min(n,len(a)),dtype=int)] if len(a) else a


def ring_maps(views,ring):
    return {v['id']:ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape)['z'] for v in views}


def assignments(body,views,ringz,cfg,folder=None):
    """Dense R+/R- saved; sampled fixed-denominator constraints carry actual Face/bary."""
    V,F=body['V'],body['F'];pairs={};stats=[]
    for v in views:
        cid=v['id'];lab=v['labels'];r=ray_map(V,F,v['K'],v['C'],lab.shape)
        pred=r['valid'] & (r['z']>0)&(r['z']<ringz[cid]-.05)
        unknown=binary_dilation(lab==2,iterations=cfg['ring_unknown_px'])
        target=lab==1;known=~unknown
        plus=target&~pred&known;minus=pred&~target&known
        b=boundary(pred)
        if len(b):b=b[known[b[:,1],b[:,0]]]
        t=boundary(target)
        if len(t):t=t[known[t[:,1],t[:,0]]]
        src=[];dst=[];kind=[]
        if len(b) and len(t):
            bs=take(b,cfg['samples_per_direction']);ts=take(t,cfg['samples_per_direction'])
            tb=cKDTree(t).query(bs)[1];bt=cKDTree(b).query(ts)[1]
            src=[bs,b[bt]];dst=[t[tb],ts];kind=[np.zeros(len(bs),int),np.ones(len(ts),int)]
            # Dense negative residuals map to their *own* visible triangles.
            ms=take(np.c_[np.nonzero(minus)[1],np.nonzero(minus)[0]],cfg['negative_samples'])
            if len(ms):src.append(ms);dst.append(t[cKDTree(t).query(ms)[1]]);kind.append(np.full(len(ms),2))
        uv=np.concatenate(src).astype(int) if src else np.empty((0,2),int)
        q=np.concatenate(dst).astype(float) if dst else np.empty((0,2))
        di=np.concatenate(kind) if kind else np.empty(0,int)
        fi=r['face'][uv[:,1],uv[:,0]];bar=r['bary'][uv[:,1],uv[:,0]]
        xyz=np.einsum('ni,nij->nj',bar,V[F[fi]]) if len(fi) else np.empty((0,3))
        projected=project(xyz,v['K'],v['C'])[0]
        distance=np.linalg.norm(projected-q,axis=1)
        keep=(fi>=0)&np.isfinite(bar).all(1)&(distance<=cfg['capture_px'])
        # R+ support is a missing *region*, not any nearest contour pair.
        pix=q.astype(int);isplus=plus[pix[:,1],pix[:,0]] if len(pix) else np.empty(0,bool)
        pp=dict(face=fi,bary=bar,source_uv=uv,target_uv=q,direction=di,
                projected_uv=projected,distance_px=distance,accepted=keep,
                missing_support=isplus&(di==1)&(distance>=cfg['growth_min_gap_px']))
        pairs[cid]=pp
        stats.append(dict(id=cid,video=v['video'],R_plus_N=int(plus.sum()),R_minus_N=int(minus.sum()),
                          target_N=int(target.sum()),candidate_N=len(fi),accepted_N=int(keep.sum()),
                          rejected_outside_capture_N=int((~keep).sum()),mean_distance_px=float(distance.mean()) if len(fi) else None))
        if folder is not None:
            np.savez_compressed(folder/(cid+'.npz'),**pp,R_plus=plus,R_minus=minus,
                                predicted=pred,target=target,unknown=unknown,
                                visible_face=r['face'],visible_bary=r['bary'])
    return pairs,stats


def projection_metrics(body,views,ringz):
    out=[]
    for v in views:
        r=ray_map(body['V'],body['F'],v['K'],v['C'],v['labels'].shape)
        pred=r['valid']&(r['z']>0)&(r['z']<ringz[v['id']]-.05);target=v['labels']==1;known=v['labels']!=2
        tp=(pred&target).sum();union=(target|(pred&known)).sum()
        a=boundary(pred&(v['labels']!=2));b=boundary(target)
        if len(a) and len(b):
            precision=(cKDTree(b).query(a)[0]<=2).mean();recall=(cKDTree(a).query(b)[0]<=2).mean();bf=2*precision*recall/max(1e-12,precision+recall)
        else:bf=0.
        out.append(dict(id=v['id'],video=v['video'],role=v['role'],IoU=float(tp/max(1,union)),
                        Boundary_Fscore_at2px=float(bf),target_N=int(target.sum()),
                        FN=int((target&~pred).sum()),FP=int((pred&~target&known).sum())))
    return out


def legacy_geometry(path):
    # Exact historical functions, without importing common.py (which creates dirs).
    p=Path(path);tree=ast.parse(p.read_text());names=['self_intersections','dense_face_distance','points','GeometryGuard']
    nodes=[x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name in names]
    scope=dict(np=np,o3d=o3d,trimesh=trimesh,scene=scene)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),scope)
    return scope


def make_guard(body,ring,base,chart,ns):
    c=SimpleNamespace(V=body['V'],F=body['F'],F_solid=body['F_solid'],inferred=body['inferred_base_faces'],
                      ringV=ring['V'],ringF=ring['F'])
    ch=SimpleNamespace(plane=np.asarray(base['selected_plane']),cap=bool(c.inferred.any()),
                       tau=chart['tau_mm'],D=chart['D_mm'],total_trust_D=1.)
    return ns['GeometryGuard'](c,ch)


def objective(V,body,rest,views,pairs,weights,cfg,gradient=False):
    F=torch.as_tensor(body['F'],device=V.device,dtype=torch.long);total=V.sum()*0;per={}
    for v in views:
        pp=pairs[v['id']];ok=pp['accepted'];ix=F[torch.as_tensor(pp['face'][ok],device=V.device)]
        b=torch.as_tensor(pp['bary'][ok],device=V.device,dtype=V.dtype)
        points=(V[ix]*b[:,:,None]).sum(1);uv=project_torch(points,v['K'],v['C'])
        q=torch.as_tensor(pp['target_uv'][ok],device=V.device,dtype=V.dtype)
        direction=pp['direction'][ok];value=V.sum()*0
        for d in (0,1,2):
            mask=torch.as_tensor(direction==d,device=V.device)
            # Original target count, including rejected samples, stays denominator.
            N=max(1,int((pp['direction']==d).sum()))
            rr=(uv[mask]-q[mask])/cfg['pixel_loss_scale']
            value+=torch.nn.functional.smooth_l1_loss(rr,torch.zeros_like(rr),reduction='sum')/N/3
        value*=weights[v['id']];total=total+value
        if gradient:per[v['id']]=torch.autograd.grad(value,V,retain_graph=True)[0].detach().cpu().numpy()
    from pytorch3d.structures import Meshes
    mesh=Meshes(verts=[rest],faces=[F]);edges=mesh.edges_packed();L=mesh.laplacian_packed().detach().to(dtype=V.dtype)
    delta=V-rest;lap=torch.sparse.mm(L,delta);edge0=(rest[edges[:,0]]-rest[edges[:,1]]).norm(dim=1)
    edge=(V[edges[:,0]]-V[edges[:,1]]).norm(dim=1)
    reg=cfg['lambda_lap']*(lap*lap).mean()+cfg['lambda_edge']*((edge-edge0)**2).mean()+cfg['lambda_prior']*(delta*delta).mean()
    return total+reg,per,dict(contour=float(total.detach()),prior=float(reg.detach()))


def projection_jacobian(P,K,C):
    cam=(P-C[:3,3])@C[:3,:3];x,y,z=cam
    J=np.array([[K[0,0]/z,K[0,1]/z,-(K[0,0]*x+K[0,1]*y)/z**2],
                [0,K[1,1]/z,-K[1,1]*y/z**2]])
    return J@C[:3,:3].T


def growth_candidates(body,views,pairs,cfg):
    """Local multiview least-squares displacement; no pixel-to-arbitrary-depth lift."""
    V,F=body['V'],body['F'];centers=V[F].mean(1);evidence=[]
    # Assign nearest boundary support to local mesh vertices, merge within geodesic patch.
    for v in views:
        p=pairs[v['id']];ok=p['accepted']&p['missing_support']
        for face,b,uv,q in zip(p['face'][ok],p['bary'][ok],p['projected_uv'][ok],p['target_uv'][ok]):
            P=b@V[F[face]];vertex=int(F[face][np.argmax(b)])
            evidence.append(dict(vertex=vertex,face=int(face),view=v['id'],video=v['video'],
                                 J=projection_jacobian(P,v['K'],v['C']),residual=q-uv,C=v['C'][:3,3]))
    if not evidence:return [],dict(reason='NO_MULTIVIEW_MISSING_REGION_EVIDENCE',support_rows=0)
    adj=[set() for _ in V]
    for f in F:
        for a in f:adj[a].update(int(b) for b in f if a!=b)
    candidates=[];seen=set()
    for seed in sorted({e['vertex'] for e in evidence}):
        vertices={seed};front={seed}
        for _ in range(cfg['growth_patch_rings']):
            front=set().union(*(adj[x] for x in front))-vertices;vertices|=front
        patch=np.flatnonzero(np.isin(F,list(vertices)).all(1))
        if not len(patch) or len(patch)>cfg['growth_max_patch_faces']:continue
        identity=tuple(patch)
        if identity in seen:continue
        seen.add(identity)
        ev=[e for e in evidence if e['vertex'] in vertices]
        perview={}
        for e in ev:perview.setdefault(e['view'],[]).append(e)
        if len(perview)<cfg['growth_min_views'] or len({e['video'] for e in ev})<cfg['growth_min_videos']:continue
        J=[];r=[];centers_view=[]
        for es in perview.values():
            J.append(np.mean([e['J'] for e in es],0));r.append(np.mean([e['residual'] for e in es],0));centers_view.append(es[0]['C'])
        J=np.concatenate(J);r=np.concatenate(r);s=np.linalg.svd(J,compute_uv=False)
        if s[-1]/max(1e-12,s[0])<cfg['growth_min_singular_ratio']:continue
        d=np.linalg.lstsq(J,r,rcond=None)[0];fit=np.linalg.norm(J@d-r)/max(1e-12,np.linalg.norm(r))
        if fit>cfg['growth_max_inconsistency'] or np.linalg.norm(d)<cfg['growth_min_mm']:continue
        d*=min(1.,cfg['growth_max_mm']/np.linalg.norm(d))
        # Face patch extrusion must expand along outward local normals, not tunnel through the body.
        tri=V[F[patch]];normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]).sum(0)
        if np.dot(normal,d)<=0:continue
        if body['inferred_base_faces'][patch].any() or body['boundary_vertex'][np.unique(F[patch])].any():continue
        candidates.append(dict(seed=seed,patch=patch,delta=d,support_views=sorted(perview),
                               support_videos=sorted({e['video'] for e in ev}),singular_ratio=float(s[-1]/s[0]),
                               inconsistency=float(fit),predicted_pixel_improvement=float(np.linalg.norm(r)-np.linalg.norm(J@d-r))))
    candidates.sort(key=lambda e:(-e['predicted_pixel_improvement'],e['seed']))
    return candidates[:cfg['growth_candidates']],dict(support_rows=len(evidence),eligible_patches=len(candidates),reason='MULTIVIEW_JACOBIAN_EVIDENCE')


def extrude_patch(body,patch,delta):
    """Replace connected disk patch by translated cap + oriented side walls."""
    V,F=body['V'],body['F'];patch=np.asarray(patch,int);selected=F[patch];ids=np.unique(selected);mapping={int(v):len(V)+i for i,v in enumerate(ids)}
    directed=np.concatenate([selected[:,[0,1]],selected[:,[1,2]],selected[:,[2,0]]]);sort=np.sort(directed,1)
    _,inverse,count=np.unique(sort,axis=0,return_inverse=True,return_counts=True);rim=directed[count[inverse]==1]
    require(len(rim)>=3,'GROWTH_TOPOLOGY','Patch has no disk boundary')
    graph={}
    for a,b in rim:graph.setdefault(int(a),set()).add(int(b));graph.setdefault(int(b),set()).add(int(a))
    require(all(len(v)==2 for v in graph.values()),'GROWTH_TOPOLOGY','Nonmanifold patch rim')
    start=next(iter(graph));visited={start};stack=[start]
    while stack:
        for x in graph[stack.pop()]-visited:visited.add(x);stack.append(x)
    require(len(visited)==len(graph),'GROWTH_TOPOLOGY','More than one rim loop')
    newV=np.r_[V,V[ids]+delta];top=np.array([[mapping[int(x)] for x in f] for f in selected])
    walls=np.array([[int(a),int(b),mapping[int(b)]] for a,b in rim]+[[int(a),mapping[int(b)],mapping[int(a)]] for a,b in rim])
    keep=np.ones(len(F),bool);keep[patch]=False;newF=np.r_[F[keep],top,walls]
    # Original solid is either identical F or F plus explicitly inferred closing faces.
    extra=body['F_solid'][len(F):]
    solid=np.r_[newF,extra] if len(extra) else newF.copy()
    inferred=np.r_[body['inferred_base_faces'][:len(F)][keep],np.zeros(len(top)+len(walls),bool),body['inferred_base_faces'][len(F):]]
    out=dict(V=newV,F=newF,F_solid=solid,inferred_base_faces=inferred,
             boundary_vertex=np.r_[body['boundary_vertex'],np.zeros(len(ids),bool)])
    return out,dict(removed_face_ids=patch,new_vertex_ids=np.arange(len(V),len(newV)),
                    parent_vertex_ids=ids,new_top_face_ids=np.arange(keep.sum(),keep.sum()+len(top)),
                    new_wall_face_ids=np.arange(keep.sum()+len(top),len(newF)),
                    delta_mm=delta,source='MULTIVIEW_2D_JACOBIAN_PATCH_EXTRUSION')


def growth_quality(candidate,old,ring,ns,base,chart):
    V,F=candidate['V'],candidate['F_solid'];m=trimesh.Trimesh(V,F,process=False);oldm=trimesh.Trimesh(old['V'],old['F_solid'],process=False)
    si=ns['self_intersections'](V,F)['intersections'];tri=V[F];areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
    rs=scene(ring['V'],ring['F']);sd=ns['dense_face_distance'](rs,V,F,ring['V'],32,ring['F']);prev=ns['dense_face_distance'](rs,old['V'],old['F_solid'],ring['V'],32,ring['F'])
    manager=trimesh.collision.CollisionManager();manager.add_object('Ring',trimesh.Trimesh(ring['V'],ring['F'],process=False));col=bool(manager.in_collision_single(m));oldcol=bool(manager.in_collision_single(oldm));why=[]
    if si:why.append('NONADJACENT_SELF_INTERSECTION')
    if areas.min()<1e-8:why.append('AREA_DEGENERACY')
    if oldm.is_watertight and not m.is_watertight:why.append('TOPOLOGY_OPENED')
    if not m.is_winding_consistent:why.append('WINDING')
    if len(m.split(only_watertight=False))!=len(oldm.split(only_watertight=False)):why.append('DISCONNECTED_GROWTH')
    lookup={tuple(int(x) for x in f):i for i,f in enumerate(old['F_solid'])}
    limits=np.array([min(0.,prev[lookup[tuple(int(x) for x in f)]]) if tuple(int(x) for x in f) in lookup else 0. for f in F])
    if (sd<limits-1e-5).any():why.append('RING_WORSENING')
    probes=np.r_[ring['V'],ring['V'][ring['F']].mean(1)].astype(np.float32)
    old_reverse=scene(old['V'],old['F_solid']).compute_signed_distance(o3d.core.Tensor(probes),nsamples=3,nthreads=2).numpy()
    new_reverse=scene(V,F).compute_signed_distance(o3d.core.Tensor(probes),nsamples=3,nthreads=2).numpy()
    if (new_reverse<np.minimum(old_reverse,0.)-1e-5).any():why.append('RING_CONTAINMENT_WORSENING')
    if col and not oldcol:why.append('NEW_CAD_COLLISION')
    # Existing inferred base remains exactly unchanged. No new structure below its plane.
    if old['inferred_base_faces'].any():
        plane=np.asarray(base['selected_plane']);h=V@plane[:3]+plane[3]
        if h.min()<-1e-7:why.append('BASE_HALFSPACE')
    return why,dict(self_intersections=si,watertight=bool(m.is_watertight),winding_consistent=bool(m.is_winding_consistent),minimum_double_area_mm2=float(areas.min()),Ring_min_signed_mm=float(sd.min()),Ring_surface_collision=col)


def cap_feasible_proposal(delta,body,plane,centers):
    """Exact inherited FreeVertices cap-rim tangent and closing-center mechanism.
    On non-cap inputs return the original tensor without any arithmetic.
    """
    if not body['inferred_base_faces'].any():return delta
    n=torch.as_tensor(np.asarray(plane)[:3],device=delta.device,dtype=delta.dtype)
    rim=torch.as_tensor(body['boundary_vertex'],device=delta.device,dtype=torch.bool)
    tangent=delta-torch.where(rim[:,None],(delta@n)[:,None]*n,torch.zeros_like(delta))
    if len(centers):
        tangent=tangent.clone();tangent[torch.as_tensor(centers,device=delta.device)]=tangent[rim].mean(0)
    return tangent


def update(initial,views,ring,base,chart,cfg,out,geometry_source,growth=True):
    require(all(v['role']=='FIT' for v in views),'HOLDOUT_LEAK','Updater accepts FIT only')
    require(all(set(v)<=set(('id','video','role','direction_block','K','C','labels','RGB')) for v in views),'DEPTH_LEAK','Only RGB/Mask/frozen cameras')
    cap_centers=np.setdiff1d(np.arange(len(initial['V'])),np.unique(initial['F']))
    out.mkdir(parents=True);body=copy.deepcopy(initial);weights=balanced_weights(views);rz=ring_maps(views,ring);ns=legacy_geometry(geometry_source)
    save_json(out/'INPUT_CONTRACT.json',dict(weights=weights,FIT_ids=[v['id'] for v in views],camera_optimization=False,HERO_depth_used=False,GT_read=False,same_shared_body=True,configuration=cfg))
    np.savez_compressed(out/'INITIAL.npz',**body);before=projection_metrics(body,views,rz);records=[];growth_log=[];accepted=0
    def reset():
        q=torch.tensor(body['V'],dtype=torch.float64,device='cuda:0',requires_grad=True);rest=q.detach().clone();opt=torch.optim.Adam([q],lr=cfg['learning_rate_mm']);guard=make_guard(body,ring,base,chart,ns);return q,rest,opt,guard
    q,rest,opt,guard=reset()
    for it in range(cfg['iterations']):
        step=out/('STEP_%03d'%it);step.mkdir();body['V']=q.detach().cpu().numpy().copy();pairs,stats=assignments(body,views,rz,cfg,step)
        value,per,parts=objective(q,body,rest,views,pairs,weights,cfg,True);opt.zero_grad();value.backward();grad=q.grad.detach().cpu().numpy().copy();old=q.detach().clone();oldnp=body['V'].copy();oldstate=copy.deepcopy(opt.state_dict());opt.step();proposal=q.detach()-old;
        if body['inferred_base_faces'].any():
            proposal=cap_feasible_proposal(proposal,body,base['selected_plane'],cap_centers)
        move=float(proposal.norm(dim=1).max());proposal*=min(1.,chart['tau_mm']/max(move,1e-12));done=False;rejections=[]
        with torch.no_grad():q.copy_(old)
        for ls in range(cfg['line_search_steps']):
            candidate=old+proposal*(.5**ls);V=candidate.detach().cpu().numpy();why,geo,extra=guard.inspect(V,oldnp)
            if np.linalg.norm(V-oldnp,axis=1).max()<1e-9:why.append('ZERO_GEOMETRIC_STEP')
            loss=None
            if not why:
                with torch.no_grad():loss=float(objective(candidate,body,rest,views,pairs,weights,cfg)[0])
                if loss>float(value)+1e-9:why.append('FULL_FIT_OBJECTIVE')
            rejections.append(dict(alpha=.5**ls,reasons=why,objective=loss,geometry=geo))
            if not why:
                with torch.no_grad():q.copy_(candidate)
                guard.lastsd,guard.lastreverse=extra;done=True;accepted+=1;break
        if not done:opt.load_state_dict(oldstate);opt.param_groups[0]['lr']*=.5
        body['V']=q.detach().cpu().numpy().copy();delta=body['V']-oldnp
        for v in views:np.savez_compressed(step/(v['id']+'_GRADIENT.npz'),gradient=per[v['id']],actual_shared_vertex_delta=delta,descent_work=-np.einsum('ij,ij->i',per[v['id']],delta))
        np.savez_compressed(step/'BODY_BEFORE.npz',V=oldnp,F=body['F']);np.savez_compressed(step/'BODY_AFTER.npz',**body,actual_delta=delta,full_gradient=grad)
        record=dict(iteration=it,accepted=done,objective=float(value.detach()),parts=parts,views=stats,gradient_norm=float(np.linalg.norm(grad)),actual_displacement_MAE_mm=float(np.linalg.norm(delta,axis=1).mean()),actual_displacement_max_mm=float(np.linalg.norm(delta,axis=1).max()),rejections=rejections)
        records.append(record);save_json(step/'UPDATE.json',record)
        if growth and it in cfg['growth_iterations']:
            current_pairs,_=assignments(body,views,rz,cfg);candidates,audit=growth_candidates(body,views,current_pairs,cfg);entry=dict(iteration=it,**audit,proposals=[],accepted=False)
            baseline=sum(weights[r['id']]*r['IoU'] for r in projection_metrics(body,views,rz))
            for j,cand in enumerate(candidates):
                proposal,provenance=extrude_patch(body,cand['patch'],cand['delta']);np.savez_compressed(step/('GROWTH_%02d.npz'%j),**proposal,**provenance)
                why,geo=growth_quality(proposal,body,ring,ns,base,chart)
                score=None
                if not why:
                    score=sum(weights[r['id']]*r['IoU'] for r in projection_metrics(proposal,views,rz))
                    if score<=baseline+cfg['growth_min_FIT_IoU_gain']:why.append('NO_BALANCED_FIT_GAIN')
                entry['proposals'].append(dict(**cand,geometry=geo,rejections=why,FIT_before=baseline,FIT_candidate=score))
                if not why:
                    body=proposal;q,rest,opt,guard=reset();entry['accepted']=True;entry['provenance']=provenance;break
            growth_log.append(entry);save_json(step/'GROWTH.json',entry)
        print('STRUCTURAL_UPDATE',it,'accepted',accepted,'vertices',len(body['V']),'loss',float(value.detach()),flush=True)
    body['V']=q.detach().cpu().numpy().copy();np.savez_compressed(out/'FINAL.npz',**body)
    final=out/'FINAL_CORRESPONDENCES';final.mkdir();assignments(body,views,rz,cfg,final)
    save_json(out/'UPDATES.json',dict(records=records,growth=growth_log,accepted_deformations=accepted,accepted_growth=sum(e['accepted'] for e in growth_log),initial_vertices=len(initial['V']),final_vertices=len(body['V']),camera_optimization=False))
    save_json(out/'FIT_PROJECTIONS.json',dict(before=before,after=projection_metrics(body,views,rz)))
    return body
