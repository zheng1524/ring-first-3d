"""Fixed-denominator monitoring; gradients never update from small pixels."""
from common import *
from fixed_renderer import render,raw,terms,eikonal,data_loss,array_pred

@lru_cache(None)
def ring_scene():
    c,_,_=source(REFS[0]);sys.path.insert(0,str(VENDOR));import open3d as o3d
    mesh=trimesh.load(c['Ring_CAD']['path'],process=False)
    if not mesh.is_watertight:raise RuntimeError('CAD_SIGN_NOT_CERTIFIED_NONWATERTIGHT')
    scene=o3d.t.geometry.RaycastingScene(nthreads=2);scene.add_triangles(o3d.core.Tensor(np.asarray(mesh.vertices,np.float32)),o3d.core.Tensor(np.asarray(mesh.faces,np.uint32)))
    return scene,o3d

def penetration(points):
    if not len(points):return dict(CAD_supported_N=0,CAD_penetration_N=0,CAD_penetration_fraction=0.,CAD_min_signed_mm=None)
    scene,o3d=ring_scene();distance=scene.compute_signed_distance(o3d.core.Tensor(np.asarray(points,np.float32))).numpy()
    return dict(CAD_supported_N=len(points),CAD_penetration_N=int((distance<-.1).sum()),CAD_penetration_fraction=float((distance<-.1).mean()),CAD_min_signed_mm=float(distance.min()))

def observed(b):return (b['depth_weight']>0)&np.isfinite(b['target_Z'])&(b['target_Z']>0)
def support_points(b,p):
    valid=observed(b)&p['render_hit'];return b['origin'][valid]+b['direction'][valid]*p['front_t_mm'][valid,None]

def row_metrics(arm,step,split,b,p,t):
    obs=observed(b);hits=p['render_hit']&obs;N=int(obs.sum());H=int(hits.sum());idx=REFS.index(b['source']);base=cfg()['baseline_E26'][split][idx]/N
    pred=p['opacity'].detach().cpu().numpy();y=b['mask_target']>0;w=b['mask_weight'];active=b['valid']&(w>0);pm=pred>=.5
    union=(w*(active&(pm|y))).sum();iou=float((w*(active&pm&y)).sum()/union) if union else None
    frontZ=p['front_t_mm']*b['cosine'];front_error=frontZ[hits]-b['target_Z'][hits]
    return dict(arm=arm,step=step,source=b['source'],split=split,observed_N=N,front_hit_N=H,miss_N=N-H,coverage=H/N,
        baseline_coverage=base,status='POTENTIAL_FAILURE_COVERAGE_LOWER' if H/N<base-1e-12 else 'NO_COVERAGE_DROP',
        RGB_loss=None if t['rgb'] is None else float(t['rgb'].detach()),Depth_loss=None if t['depth'] is None else float(t['depth'].detach()),
        Mask_loss=float(t['mask'].detach()),Anchor_loss=float(t['anchor'].detach()),weighted_sample_Mask_IoU=iou,
        observed_opacity_mean=float(pred[obs].mean()),high_opacity_without_front_N=int((obs&(pred>.98)&~p['render_hit']).sum()),
        front_HERO_MAE_mm=None if not H else float(abs(front_error).mean()),front_HERO_signed_median_mm=None if not H else float(np.median(front_error)),
        Ring_sample_N=int((b['sampling_class']==3).sum()),fixed_denominator=True,pixel_holdout_only=(split=='small'))

def grid_snapshot(model,arm,step):
    rad=domain()['ROI_radius_mm'];q=np.linspace(-rad,rad,cfg()['geometry_probe']['grid_N']);x,y,z=np.meshgrid(q,q,q,indexing='ij');P=np.c_[x.ravel(),y.ravel(),z.ravel()]+domain()['world_origin_mm'];values=[]
    with torch.no_grad():
        for first in range(0,len(P),4096):values.append(raw(model,P[first:first+4096])[0].cpu().numpy())
    f=np.concatenate(values).reshape(x.shape);inside=x*x+y*y+z*z<=rad*rad;surface_layer=inside&((x*x+y*y+z*z)>=(.95*rad)**2)
    folder=R/'local_results/grids';folder.mkdir(exist_ok=True);np.savez_compressed(folder/f'{arm}_step{step:03d}.npz',SDF_mm=f,coordinate_mm=q,origin_mm=domain()['world_origin_mm'])
    return dict(ROI_negative_fraction=float((f[inside]<0).mean()),ROI_outer_band_negative_fraction=float((f[surface_layer]<0).mean()),
        center_SDF_mm=float(f[len(q)//2,len(q)//2,len(q)//2]),SDF_min_mm=float(f[inside].min()),SDF_max_mm=float(f[inside].max()))

def probe(model,arm,step,cells):
    before=parameter_hash(model);rows=[];termvectors={};lossterms={k:[] for k in ['rgb','depth','mask','anchor']};points=[]
    for split in ['extra','small']:
        for ref in REFS:
            b=packet(ref,split);p=render(model,b,cells,REFS.index(ref));t=terms(model,b,p);row=row_metrics(arm,step,split,b,p,t)
            if split=='extra':
                for key,value in t.items():
                    if value is None:raise RuntimeError('MISSING_REFERENCE_DATA_TERM')
                    meta,vec,_=gradient(value,model);row[key+'_full_gradient_norm']=meta['full_norm'];row[key+'_implicit_gradient_norm']=meta['implicit_norm'];row[key+'_gradient_finite']=meta['finite']
                    if not meta['finite']:raise FloatingPointError('NONFINITE_PROBE_GRADIENT')
                    termvectors[key]=termvectors.get(key,torch.zeros_like(vec))+vec/3;lossterms[key].append(float(value.detach()))
            rows.append(row);points.extend(support_points(b,p));folder=R/'local_results/probes';folder.mkdir(exist_ok=True)
            np.savez_compressed(folder/f'{arm}_step{step:03d}_{ref}_{split}.npz',**array_pred(p),source_pixel=b['source_pixel'],observed=observed(b),mask_target=b['mask_target'])
            del p,t;gc.collect()
    e=eikonal(model);em,ev,_=gradient(e,model);joint=termvectors['rgb']+.1*termvectors['depth']+.1*termvectors['mask']+cfg()['arms'][arm]['anchor']*termvectors['anchor']+.1*ev
    curve=dict(arm=arm,step=step,**{k+'_loss':float(np.mean(v)) for k,v in lossterms.items()},Eikonal_loss=float(e.detach()),
        total_loss=sum(np.mean(lossterms[k])*c for k,c in [('rgb',1),('depth',.1),('mask',.1),('anchor',cfg()['arms'][arm]['anchor'])])+.1*float(e.detach()),
        total_full_gradient_norm=float(joint.double().norm()),**{k+'_joint_full_gradient_norm':float(v.double().norm()) for k,v in termvectors.items()},
        Eikonal_full_gradient_norm=em['full_norm'],beta_mm=float(model.density.get_beta().detach())*domain()['mm_per_unit'],
        GPU_peak_allocated_bytes=memory_guard(),**penetration(points),**grid_snapshot(model,arm,step))
    assert parameter_hash(model)==before,'monitoring must never change parameters'
    del termvectors,e,ev,joint;gc.collect();return rows,curve

def safety(model,arm,step,cells):
    rows=[];points=[]
    with torch.no_grad():
        for split in ['extra','small']:
            for ref in REFS:
                b=packet(ref,split);p=render(model,b,cells,need_color=False);obs=observed(b);N=int(obs.sum());H=int((obs&p['render_hit']).sum())
                if not bool(torch.isfinite(p['raw_sdf']).all())or not bool(torch.isfinite(p['opacity']).all()):raise FloatingPointError('NONFINITE_SDF_OR_OPACITY')
                idx=REFS.index(ref);base=cfg()['baseline_E26'][split][idx]/N
                rows.append(dict(arm=arm,step=step,split=split,source=ref,observed_N=N,front_hit_N=H,miss_N=N-H,coverage=H/N,
                    status='POTENTIAL_FAILURE_COVERAGE_LOWER' if H/N<base-1e-12 else 'NO_COVERAGE_DROP'))
                points.extend(support_points(b,p))
    cad=penetration(points);reason=None
    if any(r['front_hit_N']==0 for r in rows):reason='ZERO_FRONT_HITS'
    elif any(r['coverage']<.5 for r in rows):reason='PER_REFERENCE_COVERAGE_BELOW50'
    elif cad['CAD_penetration_fraction']>.01:reason='SUPPORTED_CAD_PENETRATION'
    return rows,cad,reason
