"""Fixed-denominator geometry and coverage; no GT or repaired depth."""
from common import *

def topology(valid):
    n,lab,st,_=cv2.connectedComponentsWithStats(valid.astype(np.uint8),connectivity=8)
    holes=ndimage.binary_fill_holes(valid)&~valid
    hn,_,_,_=cv2.connectedComponentsWithStats(holes.astype(np.uint8),connectivity=8)
    return dict(component_N=n-1,largest_component_N=int(st[1:,4].max()) if n>1 else 0,small_components_lt10_N=int((st[1:,4]<10).sum()),hole_regions_N=hn-1,hole_pixels_N=int(holes.sum())),lab,holes

@lru_cache(None)
def regions(cid):
    s=v1(cid);original=s['native_labels']==1;n,lab,st,_=cv2.connectedComponentsWithStats(original.astype(np.uint8),connectivity=8)
    yy,xx=np.nonzero(original);uv=np.c_[xx,yy];rays=vis.camera_rays(uv,s['Kn'],s['T']);t=-rays[:,2]/rays[:,5];P=rays[:,:3]+t[:,None]*rays[:,3:];inner=float(np.linalg.norm(np.asarray(ringmesh().vertices)[:,:2],axis=1).min());inside=(t>0)&(np.linalg.norm(P[:,:2],axis=1)<inner)
    scores=[int(inside[lab[yy,xx]==k].sum()) for k in range(1,n)];headid=int(np.argmax(scores)+1) if max(scores,default=0)>0 else -1
    head=lab==headid;side=original&~head;dt,ridge=ridge_proxy(original);thin=ridge&(2*dt<=6)
    q=mask_query(cid,uv);interior=np.zeros(original.shape,bool);j=(q['label']==1)&(q['distance_native_px']>2);interior[yy[j],xx[j]]=True
    return dict(head=head,side=side,body=interior,thin=thin,component_labels=lab,head_component_ID=headid,head_ring_hole_overlap_N=max(scores,default=0),inner_CAD_radius_mm=inner)

def fixed_edges(b,s):
    basepair=[];pair=[];jump=[]
    for axis in [0,1]:
        a=[slice(None),slice(None)];c=a.copy();a[axis]=slice(None,-1);c[axis]=slice(1,None);a=tuple(a);c=tuple(c)
        legal=b['valid'][a]&b['valid'][c];available=s['valid'][a]&s['valid'][c]&legal;diff=abs(b['depth'][a]-b['depth'][c])
        basepair.append(int(legal.sum()));pair.append(int(available.sum()));jump.append([int((legal&(diff>=1)).sum()),int((available&(diff>=1)).sum())])
    return dict(V1_fixed_pair_N=sum(basepair),available_pair_N=sum(pair),unavailable_pair_N=sum(basepair)-sum(pair),V1_jump_ge1mm_N=sum(j[0] for j in jump),remaining_jump_ge1mm_N=sum(j[1] for j in jump),removed_jump_observation_pairs_N=sum(j[0]-j[1] for j in jump))

def main():
    assert not (R/'THREE_VERSION_COMPARISON.json').exists(),'DO_NOT_OVERWRITE_RESULTS'
    protocol=primary_protocol();dom=protocol['common_model_domain'];O=np.asarray(dom['O_mm']);L=dom['L_mm'];metrics=[];geo=[];regionrows=[];comp=[];pairrows=[];gaprows=[];fixed=[]
    fixedcases=[r for r in read_csv(A2/'RESAMPLING_FAILURE_DIAGNOSIS.csv') if r['stage']=='A2_INCREMENTAL']
    for cid in IDS:
        b=v1(cid);reg=regions(cid);raw=raw_distances(cid,b['native_id']);cad,_=cast(ringscene(),b['native_uv'],b['Kn'],b['T']);z=b['depth'].ravel()[b['native_id']];visible=(~np.isfinite(cad))|(z<=cad+.002);bt,bl,bholes=topology(b['valid']);v1crop=None
        for version in VERSIONS:
            s=cohort(cid,version);c=make_crop(s);out=R/'local_results/crops'/version;out.mkdir(parents=True,exist_ok=True);np.savez_compressed(out/(cid+'.npz'),**{k:v for k,v in c.items() if isinstance(v,np.ndarray)})
            if v1crop is None:
                v1crop=c;old=np.load(A2/'local_results/crops'/(cid+'.npz'));assert np.array_equal(c['A'],old['A']) and np.array_equal(c['K_crop'],old['K_crop'])
            assert np.array_equal(c['A'],v1crop['A']) and np.array_equal(c['K_crop'],v1crop['K_crop']) and np.array_equal(c['source_ids'],v1crop['source_ids'])
            uv=s['native_uv'];zz=s['depth'].ravel()[s['native_id']].astype(float);q=affine_uv(uv,c['A']);xa=unproject(zz,s['T'],q,c['K_crop']);e=np.linalg.norm(xa-s['X'],axis=1);model=(s['X']-O)/L;T=s['T'].copy();T[:3,3]=(T[:3,3]-O)/L;xm=unproject(zz/L,T,uv,s['Kn']);outside=((model<0)|(model>=1)).any(1)
            selected=c['source_ids'][c['valid']];chosen=s['depth'].ravel()[selected];actual=unproject(chosen.astype(float),s['T'],np.c_[selected%640,selected//640],s['Kn']);rayerr=np.linalg.norm(actual-c['output_X_mm'],axis=1)
            geo.append(dict(source=cid,version=version,retained_N=len(uv),analytic_XYZ_max_mm=float(e.max()),metric_roundtrip_max_mm=float(np.linalg.norm(model*L+O-s['X'],axis=1).max()),camera_scale_max_mm=float(np.linalg.norm((model-xm)*L,axis=1).max()),out_of_grid_N=int(outside.sum()),common_L_mm=L,crop_A_K_sourceID_unchanged=True,c2w_unchanged=True,exact_selected_depth=bool(np.array_equal(chosen,c['depth_mm'][c['valid']])),actual_NN_ray_shift_max_mm=float(rayerr.max()),nonPolyp_depth_nonzero_N=int(((c['semantics']!=1)&(c['depth_mm']!=0)).sum())))
            now=s['valid'].ravel()[b['native_id']];lost=~now;vt,vl,holes=topology(s['valid']);ct,cl,ch=topology(c['valid']);q,p,picked,err=comparison(b,c);outputavailable=np.isfinite(err)
            row=dict(source=cid,version=version,V1_denominator_N=len(b['native_id']),retained_N=len(s['native_id']),new_suppressed_N=int(lost.sum()),crop_valid_N=int(c['valid'].sum()),original_ID_sampled_N=len(np.unique(selected)),V1_raw_far_gt1mm_N=int((raw>1).sum()),retained_raw_far_gt1mm_N=int((now&(raw>1)).sum()),suppressed_raw_near_le1mm_N=int((lost&(raw<=1)).sum()),V1_CAD_visible_proxy_N=int(visible.sum()),suppressed_CAD_visible_proxy_N=int((lost&visible).sum()),common_voxel_occupied_N=len(np.unique(np.floor(model*128).astype(int),axis=0)),fixed_V1_forward_pair_N=len(err),forward_pair_available_N=int(outputavailable.sum()),forward_pair_unavailable_N=int((~outputavailable).sum()),forward_pair_error_p95_mm=stats(err)['p95'],forward_pair_error_max_mm=stats(err)['maximum'],**{'native_'+k:v for k,v in vt.items()},**{'crop_'+k:v for k,v in ct.items()})
            metrics.append(row);pairrows.append(dict(source=cid,version=version,**fixed_edges(b,s)))
            gap=b['valid']&~s['valid'];gn,_,_,_=cv2.connectedComponentsWithStats(gap.astype(np.uint8),connectivity=8);gaprows.append(dict(source=cid,version=version,new_gap_pixels_N=int(gap.sum()),new_gap_components_N=gn-1,new_internal_hole_pixels_from_V1_valid_N=int((holes&b['valid']).sum()),native_hole_pixels_net_change=vt['hole_pixels_N']-bt['hole_pixels_N'],native_components_net_change=vt['component_N']-bt['component_N'],V1_denominator_N=len(b['native_id'])))
            for name in ['head','side','body','thin']:
                mask=reg[name]&b['valid'];n=int(mask.sum());left=int((mask&s['valid']).sum());regionrows.append(dict(source=cid,version=version,region=name,V1_fixed_N=n,retained_N=left,lost_N=n-left,retained_fraction=left/n if n else np.nan,anatomical_truth_certified=False,status='PROXY_MEASURABLE' if n else 'NOT_EVALUABLE',head_component_ID=reg['head_component_ID']))
            for k in range(1,bt['component_N']+1):
                own=bl==k;values=vl[own&s['valid']];v,nn=np.unique(values,return_counts=True);n=int(own.sum());comp.append(dict(source=cid,version=version,V1_component_ID=k,V1_component_N=n,retained_N=len(values),retained_pieces_N=len(v),largest_retained_piece_N=int(nn.max()) if len(nn) else 0,largest_piece_fraction_of_original=float(nn.max()/n) if len(nn) else 0,head_component=bool(np.sum(own&reg['head'])>0)))
            for oldcase in fixedcases:
                if oldcase['source']!=cid:continue
                u,v=int(oldcase['original_u']),int(oldcase['original_v']);su,sv=int(oldcase['selected_u']),int(oldcase['selected_v']);ou,ov=int(oldcase['output_u']),int(oldcase['output_v']);available=bool(c['valid'][ov,ou]);ox=unproject(np.array([b['depth'][v,u]],float),b['T'],np.array([[u,v]]),b['Kn'])[0];nx=unproject(np.array([c['depth_mm'][ov,ou]],float),b['T'],np.array([[ou,ov]]),c['K_crop'])[0] if available else np.full(3,np.nan)
                fixed.append(dict(source=cid,version=version,original_native_id=int(oldcase['original_native_id']),selected_native_id=int(oldcase['selected_native_id']),original_u=u,original_v=v,selected_u=su,selected_v=sv,output_u=ou,output_v=ov,original_ID_still_valid=bool(s['valid'][v,u]),selected_ID_still_valid=bool(s['valid'][sv,su]),output_available=available,V1_original_depth_mm=float(b['depth'][v,u]),V1_selected_depth_mm=float(b['depth'][sv,su]),current_output_depth_mm=float(c['depth_mm'][ov,ou]),fixed_original_to_output_XYZ_error_mm=float(np.linalg.norm(nx-ox)) if available else np.nan,mechanism='SAME_REAL_SELECTED_LAYER' if available else 'OBSERVATION_SUPPRESSED_NOT_DEPTH_CORRECTED'))
    table('SOURCE_VERSION_METRICS.csv',metrics);table('GEOMETRY_VALIDATION.csv',geo);table('REGION_RETENTION.csv',regionrows);table('COMPONENT_RETENTION.csv',comp);table('NEW_GAP_STATISTICS.csv',gaprows);table('FIXED_DENOMINATOR_DEPTH_JUMPS.csv',pairrows);table('FIXED_DEPTH_CASES.csv',fixed)
    versions=[]
    for version in VERSIONS:
        rr=[r for r in metrics if r['version']==version];points=np.concatenate([cohort(cid,version)['X'] for cid in IDS]);small=make_domain(points)
        versions.append(dict(version=version,retained_N=sum(r['retained_N'] for r in rr),new_suppressed_N=sum(r['new_suppressed_N'] for r in rr),retained_raw_far_gt1mm_N=sum(r['retained_raw_far_gt1mm_N'] for r in rr),suppressed_raw_near_le1mm_N=sum(r['suppressed_raw_near_le1mm_N'] for r in rr),suppressed_CAD_visible_proxy_N=sum(r['suppressed_CAD_visible_proxy_N'] for r in rr),diagnostic_min_enclosing_L_mm=small['L_mm'],diagnostic_voxel_mm=small['voxel_mm'],physical_domain_used_for_comparison=dom,source_metrics=rr))
    save('THREE_VERSION_COMPARISON.json',dict(protocol=asset(R/'config/A3_PREREGISTERED.json'),original_N=106144,previous46_cleanup_N=106098,A2_V1_N=105875,versions=versions,common_world_scale='V1 27.959mm domain for all variants, no geometry/camera rescale',minimal_domains_diagnostic_only=True,old3px_gate_used=False,physical_surface_truth_NOT_EVALUABLE=True))
    save('config/REGION_DEFINITIONS.json',dict(per_source=[dict(source=cid,head_component_ID=regions(cid)['head_component_ID'],head_ring_hole_overlap_N=regions(cid)['head_ring_hole_overlap_N'],CAD_inner_radius_mm=regions(cid)['inner_CAD_radius_mm'],possible_thin_proxy_N=int(regions(cid)['thin'].sum())) for cid in IDS],anatomy='head and side are fixed Mask/Ring projection proxies; possible thin region not certified tissue',existing_r14_native_uv=[282,215],old_3px_blocker_revoked=True))
    save('config/EXECUTED_REUSE.json',dict(functions=REUSE,neural_modules=[n for n in sys.modules if n.startswith(('torch','tensorflow','training','graphics'))],GT_read=False,GPU=0,NNforward=0))
    print('A3_METRICS',[(v['version'],v['retained_N'],v['new_suppressed_N'],v['retained_raw_far_gt1mm_N'],v['diagnostic_min_enclosing_L_mm']) for v in versions],flush=True)

if __name__=='__main__':main()
