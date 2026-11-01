"""Retain same-real-ray depth alternatives. No average, winner, or new surface."""
from run_consensus import *
def choose_rays():
    selected=[]
    for sid in scene_ids():
        regular=[];separated=[]
        for a in sorted(scene_sources(sid)):
            c=candidates(a);peer={b:{k:z[k]for k in z.files}for b in sorted(x for x in scene_sources(sid)if x!=a)for z in[np.load(observer_file(a,b))]}
            for j in np.argsort(c['face_id']):
                for b in sorted(x for x in scene_sources(sid)if x!=a):
                    q=peer[b];good=bool(c['own_visible'][j]and q['minimum'][j])
                    if not good:continue
                    row=dict(scene=sid,origin=a,face_id=int(c['face_id'][j]),candidate_index=int(j),observer=b,delta_native_mm=float(q['delta'][j]))
                    if len(regular)<2:regular.append(dict(row,selection='REGULAR_FIRST_LEXICOGRAPHIC'))
                    if .5<=abs(q['delta'][j])<=1 and len(separated)<2:separated.append(dict(row,selection='PREREGISTERED_05_TO_1MM'))
                    if len(regular)>=2 and len(separated)>=2:break
                if len(regular)>=2 and len(separated)>=2:break
            if len(regular)>=2 and len(separated)>=2:break
        # Identical candidate/ray can satisfy both purposes; retain selection labels.
        selected+=regular+separated
    for i,r in enumerate(selected):r['ray_id']='ray'+str(i).zfill(3)+'_'+r['origin']+'_f'+str(r['face_id'])+'_in_'+r['observer']
    return selected
def roi_ray_interval(sid,ray):
    lo=np.array(ROI[sid]['minimum_mm']);hi=np.array(ROI[sid]['maximum_mm']);o,d=ray[:3],ray[3:];near=-np.inf;far=np.inf
    for j in range(3):
        if abs(d[j])<1e-14:
            if not lo[j]<=o[j]<=hi[j]:return np.nan,np.nan
        else:
            x,y=(lo[j]-o[j])/d[j],(hi[j]-o[j])/d[j];near=max(near,min(x,y));far=min(far,max(x,y))
    return max(0.,near),far
def mode_interval(source_id,observer,point,normal,kind):
    a=source(source_id);b=source(observer);_,za=vis.project_camera(point[None],a['K'],a['T']);_,zb=vis.project_camera(point[None],b['K'],b['T']);ra=(point-a['T'][:3,3])/za[0];rb=(point-b['T'][:3,3])/zb[0];tau=float(width(source_id,za)[0])
    if kind=='OBSERVER_NATIVE_PIXEL':return float(zb[0]-tau),float(zb[0]+tau),'OBSERVER_NATIVE_AXIAL_INTERVAL'
    denom=float(normal@rb);inc=abs(denom)/np.linalg.norm(rb)
    if inc<.2:return None,None,'GRAZING_LOCAL_PLANE_INTERVAL_UNBOUNDED_UNRESOLVED'
    radius=tau*abs(float(normal@ra)/denom);return float(zb[0]-radius),float(zb[0]+radius),'LOCAL_PLANE_AXIAL_ERROR_PROPAGATION_UNCALIBRATED'
def main():
    allow_manifest();freeze('BEFORE_RAY_WINDOWS_REV002.json'if(R/'provenance/BEFORE_RAY_WINDOWS.json').exists()else'BEFORE_RAY_WINDOWS.json');selected=choose_rays();save('provenance/RAY_SELECTION_FROZEN.json',selected);modes=[];windows=[];curve_rows=[]
    sys.path.insert(0,str(VENDOR));import open3d as o3d
    for spec in selected:
        a,b=spec['origin'],spec['observer'];c=candidates(a);j=spec['candidate_index'];X=c['XYZ'][j];N=c['normal'][j];Bcam=source(b);uv,z=vis.project_camera(X[None],Bcam['K'],Bcam['T']);ray=vis.camera_rays(uv,Bcam['K'],Bcam['T'])[0];qa=pf(b).query(X[None]);D=float(qa['native_Z_mm'][0]);local=[]
        def add(src,kind,point,fid,normal,visible,extra=''):
            _,depth=vis.project_camera(point[None],Bcam['K'],Bcam['T']);lower,upper,status=mode_interval(src,b,point,normal,kind);local.append(dict(ray_id=spec['ray_id'],scene=spec['scene'],origin=a,origin_original_face_id=spec['face_id'],observer=b,mode_source_id=src,mode_kind=kind,
                original_face_id=fid,axial_depth_in_observer_mm=float(depth[0]),lower_mm=lower,upper_mm=upper,interval_status=status,source_own_legal_visibility=bool(visible),
                source_family=source(src)['row']['source_family'],position_provenance=extra,mode_retained=True,independent_new_evidence=False,physical_same_surface_truth='UNRESOLVED',
                observer_CAD_occluded=bool(np.isfinite(qa['CAD_Z_mm'][0])and depth[0]>qa['CAD_Z_mm'][0]+protocol()['ordering_epsilon_mm']),
                behind_observer_native_first_proxy=bool(np.isfinite(D)and depth[0]>D+width(b,np.array([D]))[0])))
        add(a,'ORIGIN_ORIGINAL_FACE',X,int(c['face_id'][j]),N,c['own_visible'][j],'exact original triangle centroid, immutable')
        if np.isfinite(D)and D>0:
            point=ray[:3]+D*ray[3:];fid=int(qa['original_face_id'][0]);normal=model(b).N[fid]if fid>=0 else np.zeros(3);qn=pf(b).query(point[None]);add(b,'OBSERVER_NATIVE_PIXEL',point,-1,normal,qn['valid_surface'][0],'native pixel '+str(qa['native_pixel'][0].tolist())+'; depth-only mode, no invented original face')
        for src in sorted(scene_sources(spec['scene'])):
            h=scene(src).cast_rays(o3d.core.Tensor(ray[None].astype(np.float32)));depth=float(h['t_hit'].numpy()[0]);fid=int(h['primitive_ids'].numpy()[0])
            if not np.isfinite(depth)or depth<=0:continue
            point=ray[:3]+depth*ray[3:];q=model(src).query(point[None]);add(src,'ORIGINAL_MESH_FIRST_ON_OBSERVER_RAY',point,fid,model(src).N[fid],q['valid_surface'][0],'exact ray/original triangle intersection; retain even if not visible from its own source')
        lo_roi,hi_roi=roi_ray_interval(spec['scene'],ray);low=min([r['lower_mm']for r in local if r['lower_mm']is not None]+[r['axial_depth_in_observer_mm']for r in local])-.5;high=max([r['upper_mm']for r in local if r['upper_mm']is not None]+[r['axial_depth_in_observer_mm']for r in local])+.5
        lo=max(lo_roi,low);hi=min(hi_roi,high);assert np.isfinite(lo)and np.isfinite(hi)and hi>lo
        t=np.linspace(lo,hi,protocol()['ray_windows']['samples']);points=ray[:3]+t[:,None]*ray[3:];scores={};mode_depths=[r['axial_depth_in_observer_mm']for r in local]
        for src in sorted(scene_sources(spec['scene'])):
            q=peer_evidence(a,src,points,np.broadcast_to(N,points.shape),np.full(len(t),c['own_visible'][j]),origin_anchor=X,origin_align=np.full(len(t),c['origin_native_Raw_alignment'][j]));scores[src]=q
            for k,tt in enumerate(t):curve_rows.append(dict(ray_id=spec['ray_id'],source_id=src,observer_depth_mm=tt,S=q['S'][k],O=q['O'][k],F_numeric=q['F'][k],F_minimum_admissible=q['F'][k]*q['minimum'][k],free_V2_proxy=q['native_free'][k],free_V3_proxy=q['free3'][k],CAD_occluded=q['cad'][k],self_source_excluded_from_consensus=src==a))
        folder=R/'local_results/rays';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(spec['ray_id']+'.npz'),t=t,points=points,source_ids=np.array(sorted(scores)),S=np.array([scores[s]['S']for s in sorted(scores)]),O=np.array([scores[s]['O']for s in sorted(scores)]),
            F=np.array([scores[s]['F']for s in sorted(scores)]),F_V2=np.array([scores[s]['F']*scores[s]['minimum']for s in sorted(scores)]),F_V3=np.array([scores[s]['F']*scores[s]['free3']for s in sorted(scores)]),cad=np.array([scores[s]['cad']for s in sorted(scores)]),origin_X=X,ray=ray)
        origin_mode=next(r for r in local if r['mode_kind']=='ORIGIN_ORIGINAL_FACE');native_mode=next((r for r in local if r['mode_kind']=='OBSERVER_NATIVE_PIXEL'),None);separation=None if native_mode is None else abs(origin_mode['axial_depth_in_observer_mm']-native_mode['axial_depth_in_observer_mm'])
        windows.append(dict(**spec,query_t_min_mm=lo,query_t_max_mm=hi,ROI_t_min_mm=lo_roi,ROI_t_max_mm=hi_roi,mode_N=len(local),mode_source_N=len({r['mode_source_id']for r in local}),mode_depth_min_mm=min(mode_depths),mode_depth_max_mm=max(mode_depths),
            origin_native_separation_mm=separation,origin_mode_retained=True,native_observer_mode_retained=native_mode is not None,mode_average_created=False,mode_winner_selected=False,
            interval_identity='source-labelled continuous intervals may overlap or remain disjoint; never replace by one averaged depth',unbounded_interval_mode_N=sum(r['lower_mm']is None for r in local)))
        modes+=local;print('RAY_WINDOW',spec['ray_id'],'modes',len(local),'gap',separation,flush=True)
    table('MULTIMODAL_DEPTH_CANDIDATES.csv',modes);table('metrics/RAY_WINDOWS.csv',windows)
    path=R/'metrics/RAY_CHANNEL_CURVES.csv.gz';keys=list(curve_rows[0])if curve_rows else[]
    with gzip.open(path,'wt',newline='')as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(keys)
        for r in curve_rows:w.writerow([compact(r[k])for k in keys])
    save('provenance/WINDOW_STATUS.json',dict(ray_N=len(windows),mode_N=len(modes),curve_query_N=len(curve_rows),averaged_mode_N=0,mode_selection_N=0,raw_faces_modified=0,
        qualification='finite engineering search intervals, not calibrated depth confidence intervals; source visibility and physical correspondence remain conditional'))
def annotate_observer_visibility():
    """Add ray-observer visibility columns from fixed ray/depth identities only."""
    allow_manifest();rs=rows(R/'MULTIMODAL_DEPTH_CANDIDATES.csv');specs={r['ray_id']:r for r in load(R/'provenance/RAY_SELECTION_FROZEN.json')};state={}
    for rid,spec in specs.items():
        c=candidates(spec['origin']);X=c['XYZ'][spec['candidate_index']];q=pf(spec['observer']).query(X[None]);state[rid]=(float(q['CAD_Z_mm'][0]),float(q['native_Z_mm'][0]),spec['observer'])
    for r in rs:
        cad,D,b=state[r['ray_id']];depth=float(r['axial_depth_in_observer_mm']);r['observer_CAD_occluded']=bool(np.isfinite(cad)and depth>cad+protocol()['ordering_epsilon_mm']);r['behind_observer_native_first_proxy']=bool(np.isfinite(D)and depth>D+width(b,np.array([D]))[0])
    table('MULTIMODAL_DEPTH_CANDIDATES.csv',rs);save('provenance/MODE_OBSERVER_VISIBILITY_ANNOTATION.json',dict(ray_queries=len(specs),mode_N=len(rs),mode_positions_changed=False,geometry_changed=False))
if __name__=='__main__':annotate_observer_visibility()if'--annotate-observer-only'in sys.argv else main()
