"""Read-only attribution and locality evidence; cannot change final decisions."""
from common017 import *
from analyze017 import get_source
from gap017 import patch_plane
def patch_reason(z,lab,uv,d,t):
    perp=np.array([-d[1],d[0]]);off=np.array([-a*d+b*perp for a in [0,1,2]for b in [-1,0,1]if a!=0 or b!=0]);p=uv+off;ok=(p[:,0]>=0)&(p[:,0]<z.shape[1])&(p[:,1]>=0)&(p[:,1]<z.shape[0]);pp=np.clip(p,[0,0],[z.shape[1]-1,z.shape[0]-1]);zz=z[pp[:,1],pp[:,0]];ok&=(lab[pp[:,1],pp[:,0]]==1)&np.isfinite(zz)&(zz>0);n=int(ok.sum())
    if n<6:return dict(reason='VALID_SOURCE_SAMPLES_LT6',N=n)
    A=np.c_[off[ok],np.ones(n)]
    if np.linalg.matrix_rank(A)<3:return dict(reason='SOURCE_PATCH_RANK_LT3',N=n)
    c=np.linalg.lstsq(A,1/zz[ok],rcond=None)[0];v=A@c
    if (v<=0).any():return dict(reason='PREDICTED_DEPTH_NONPOSITIVE',N=n)
    rms=float(np.sqrt(np.mean((1/v-zz[ok])**2)))
    if rms>t['native_depth_jump_mm']/4:return dict(reason='PLANE_RMS_TOO_LARGE',N=n,RMS_mm=rms)
    err=float(abs((1/c[2]if c[2]>0 else np.inf)-z[uv[1],uv[0]]))
    if err>t['native_depth_jump_mm']/4:return dict(reason='EXCLUDED_ENDPOINT_NOT_SUPPORTED',N=n,RMS_mm=rms,endpoint_error_mm=err)
    return dict(reason='SUPPORTED',N=n,RMS_mm=rms,endpoint_error_mm=err)
def main():
    rows=[];proj=[];regions=[];block=[];patch=[];t=load(R/'config/PROTOCOL.json')['thresholds']
    for r in load(R/'config/SOURCE_LOCK.json'):
        z=np.load(r['native_depth'])['depth_mm'];s=get_source(r,'NATIVE_GRID');edgefile=R/'metrics/TWO_SIDED_GAP'/(r['source_id']+'.csv');edata=list(csv.DictReader(edgefile.open()))if edgefile.exists()else[]
        for e in edata:
            ui=np.array([int(e['u_i']),int(e['v_i'])]);uj=np.array([int(e['u_j']),int(e['v_j'])]);di=uj-ui
            for side,uv,d in [('i',ui,di),('j',uj,-di)]:patch.append(dict(source=r['source_id'],pixel_i=e['pixel_i'],pixel_j=e['pixel_j'],side=side,**patch_reason(z,s['native_labels'],uv,d,t)))
        for rep in ['ARCHIVE_RAW','NATIVE_GRID']:
            a=dict(np.load(R/'final_results'/r['source_id']/rep/'FACE_EVIDENCE.npz'));P,F=a['V'],a['F'];state=a['state'];area=a['area_mm2'];old=np.load(R/'local_results'/r['source_id']/rep/'FACE_EVIDENCE.npz')
            severe=a['perspective_stretch']>8;dj=a['native_depth_jump_mm']>.5;pair=severe&dj;shape=(a['triangle_quality']<.15)|(a['normal_coherence']<.7)|(a['normal_angle_deg']>65);edge=a['boundary_distance_native_px']<=2;material=a['CAD_inside_samples']>=2;cf=a['two_sided_gap_face'];goodtan=a['tangent_reliable']&(a['tangent_stretch']>4)
            block.append(dict(source=r['source_id'],group=r['group'],representation=rep,all_faces=len(F),perspective_gt8=int(severe.sum()),native_jump_gt0_5=int(dj.sum()),stretch_and_jump=int(pair.sum()),plus_shape_and_edge=int((pair&shape&edge).sum()),plus_qualified_PCA_tangent=int((pair&shape&edge&goodtan).sum()),unknown_in_stretch_jump=int((pair&(state==3)).sum()),joint_CAD_shape_depth=int((material&shape&dj).sum()),confirmed_two_sided_gap_faces=int(cf.sum()),confirmed_gap_blocked_by_context=int((cf&~edge&~material).sum()),final_rejected=int((state==2).sum()),initial_TRUSTED_removed=int(((old['state']==0)&(state==2)).sum())))
            for name,mask in [('ALL',np.ones(len(F),bool)),('MASK_EDGE_2PX',edge),('INTERIOR',~edge),('RING_NEAR',a['CAD_nearest_sample_mm']<.3),('CAD_MATERIAL_SAMPLED',material),('STRETCH_DEPTH_PROXY',pair),('NORMALIZATION_UNKNOWN',~a['tangent_reliable'])]:
                regions.append(dict(group=r['group'],source=r['source_id'],representation=rep,cohort=name,face_N=int(mask.sum()),area_mm2=float(area[mask].sum()),trusted_N=int((mask&(state==0)).sum()),uncertain_N=int((mask&(state==1)).sum()),unknown_N=int((mask&(state==3)).sum()),rejected_N=int((mask&(state==2)).sum()),rejected_area_mm2=float(area[mask&(state==2)].sum()),physical_truth='NOT_EVALUABLE'))
            T=a['T'];K=a['K'];cam=(P-T[:3,3])@T[:3,:3];q=cam@K.T;uv=q[:,:2]/q[:,2:];roundtrip=float(abs(uv-a['uv']).max());p=a['uv'][F];cross=(p[:,1,0]-p[:,0,0])*(p[:,2,1]-p[:,0,1])-(p[:,1,1]-p[:,0,1])*(p[:,2,0]-p[:,0,0]);sortedF=np.sort(F,axis=1);duplicates=len(F)-len(np.unique(sortedF,axis=0));proj.append(dict(source=r['source_id'],representation=rep,min_depth_mm=float(cam[:,2].min()),max_roundtrip_px=roundtrip,pixel_lattice_area2_min=float(cross.min()),pixel_lattice_area2_max=float(cross.max()),duplicate_faces=duplicates,zero_area_faces=int((area<1e-12).sum()),projective_depth_graph=True,native_nonadjacent_intersection='no crossing of projected triangle interiors in exact positive-depth lattice; not arbitrary FCL mesh certification',physical_smoothness='not implied by depth graph property'))
    table('metrics/PATCH_FAILURE_ATTRIBUTION.csv',patch);table('metrics/RULE_BLOCKING_ATTRIBUTION.csv',block);table('metrics/REGION_PRESERVATION.csv',regions);table('metrics/PROJECTIVE_TOPOLOGY_AUDIT.csv',proj);save('metrics/RULE_BLOCKING_ATTRIBUTION.json',block)
    groups=[]
    allrows=load(R/'metrics/FINAL_SOURCE_SUMMARIES.json')
    for g in ['G01','G03','G05','G06']:
        for rep in ['NATIVE_GRID','ARCHIVE_RAW']:
            ss=[x for x in allrows if x['group']==g and x['representation']==rep];row=dict(group=g,representation=rep,source_N=len(ss))
            keys=['original_faces','original_area_mm2','TRUSTED_faces','TRUSTED_area_mm2','UNCERTAIN_faces','UNCERTAIN_area_mm2','REJECTED_faces','REJECTED_area_mm2','UNKNOWN_faces','UNKNOWN_area_mm2','original_visible_mesh_hits','original_first_surface_retained','CAD_inside_raw_faces','CAD_inside_retained_faces','Ring_near_faces','new_boundary_edges','interior_removed_patches']
            for key in keys:row[key]=sum(x[key]for x in ss)
            row.update(deleted_area_fraction=row['REJECTED_area_mm2']/row['original_area_mm2'],first_surface_retained_fraction=row['original_first_surface_retained']/max(1,row['original_visible_mesh_hits']),minimum_source_largest_piece_retention=min(x['largest_remaining_piece_of_raw_main_fraction']for x in ss),uncertain_unknown_area_fraction=(row['UNCERTAIN_area_mm2']+row['UNKNOWN_area_mm2'])/row['original_area_mm2'],areas_are_sum_of_source_observations_not_unique_anatomy=True)
            groups.append(row)
    save('metrics/GROUP_SUMMARY.json',groups);table('metrics/GROUP_SUMMARY.csv',groups)
    table('metrics/PATCH_FAILURE_COUNTS.csv',[dict(reason=k,count=sum(p['reason']==k for p in patch))for k in sorted({p['reason']for p in patch})])
    cameras=[]
    for r in load(R/'config/SOURCE_LOCK.json'):
        a=np.load(r['camera_metadata']);T=np.asarray(r['T']);trans=a['c2w']if'c2w'in a else a['pose'];err=np.max(abs(np.asarray(trans).reshape(-1,4,4)-T),axis=(1,2));cameras.append(dict(source=r['source_id'],min_pose_difference=float(err.min()),matching_index=int(err.argmin()),matched=bool(err.min()<1e-8)))
    save('metrics/CAMERA_METADATA_BINDING_AUDIT.json',cameras)
    print('READ_ONLY_ATTRIBUTION_COMPLETE',len(patch),'patches',len(groups),'group/representation rows',flush=True)
if __name__=='__main__':main()
