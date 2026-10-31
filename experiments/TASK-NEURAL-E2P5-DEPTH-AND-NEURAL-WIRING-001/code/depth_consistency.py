"""P1: directed source-world-target HERO diagnostics; never same-pixel Z subtraction."""
from common import *

def main():
    cfg=load(R/'config/PREREGISTERED.json');uv=grid();rows=[];flows=[];checks=[]
    fields={};data={}
    for refs in selected().values():
        for ref in refs:
            c,p,r=source(ref);data[ref]=(c,p,r);fields[ref]=region_fields(p,r)
    for scene,refs in selected().items():
        for A in refs:
            ca,pa,ra=data[A];fA=fields[A];za=pa['depth_mm'].ravel();ta=za*ra['ray_length_factor']
            positive=pa['labels'].ravel()==1
            eligible=positive&np.isfinite(za)&(za>0)&ra['ROI_valid']&(ta>=ra['ROI_start_t_mm'])&(ta<=ra['ROI_end_t_mm'])
            pixels=np.flatnonzero(eligible);P=unproject(za[pixels],pa['pose'],uv[pixels],pa['K'])
            # Direct independent closure of the reused projection/unprojection.
            axy,az=vis.project_camera(P,pa['K'],pa['pose']);closure=float(np.max(abs(axy-uv[pixels])))
            checks.append(dict(source=A,source_roundtrip_max_px=closure,axial_roundtrip_mm=float(abs(az-za[pixels]).max()),pass_=closure<1e-6))
            for B in refs:
                if A==B:continue
                cb,pb,rb=data[B];fB=fields[B];xy,Z=vis.project_camera(P,pb['K'],pb['pose'])
                finite=np.isfinite(xy).all(1)&np.isfinite(Z)&(Z>0);px=np.zeros_like(xy,int);px[finite]=np.floor(xy[finite]+.5).astype(int)
                inside=finite&(px[:,0]>=0)&(px[:,0]<640)&(px[:,1]>=0)&(px[:,1]<360)
                ii=np.flatnonzero(inside);jj=px[ii,1]*640+px[ii,0]
                kind=np.full(len(pixels),1,np.uint8)  # 1 outside/invalid projection
                kind[ii]=2  # 2 target identity/depth unsupported
                bz=pb['depth_mm'].ravel();bvalid=(pb['labels'].ravel()[jj]==1)&np.isfinite(bz[jj])&(bz[jj]>0)&rb['ROI_valid'][jj]
                bt=bz[jj]*rb['ray_length_factor'][jj]
                bvalid&=(bt>=rb['ROI_start_t_mm'][jj])&(bt<=rb['ROI_end_t_mm'][jj])
                ii=ii[bvalid];jj=jj[bvalid];kind[ii]=3  # ring blocks projected A point
                Zring=rb['ring_first_t_mm'][jj]/rb['ray_length_factor'][jj]
                ring_clear=~np.isfinite(Zring)|(Z[ii]*rb['ray_length_factor'][jj]<rb['ring_first_t_mm'][jj]-.05)
                ii=ii[ring_clear];jj=jj[ring_clear];kind[ii]=4  # projected-A self-occlusion
                zbuffer=np.full(230400,np.inf);all_inside=np.flatnonzero(inside);all_j=px[all_inside,1]*640+px[all_inside,0]
                np.minimum.at(zbuffer,all_j,Z[all_inside])
                front=Z[ii]<=zbuffer[jj]+cfg['self_z_tolerance_mm']
                ii=ii[front];jj=jj[front]
                loose=ii.copy();target_pixel=jj.copy();kind[ii]=5  # ambiguous correspondence: loose diagnostic only
                error=Z[ii]-bz[jj];tau=np.maximum(cfg['depth_conflict_mm'],cfg['conflict_pixel_footprints']*Z[ii]/min(pb['K'][0,0],pb['K'][1,1]))
                # Cycle is only an additional conditional test, not independent
                # physical correspondence truth. Keep ALL loose results too.
                XB=unproject(bz[jj],pb['pose'],np.c_[jj%640,jj//640],pb['K'])
                back,_=vis.project_camera(XB,pa['K'],pa['pose']);cycle=np.linalg.norm(back-uv[pixels[ii]],axis=1)
                ndot=(fA['normal'][pixels[ii]]*fB['normal'][jj]).sum(1)
                normal_ok=fA['normal_valid'][pixels[ii]]&fB['normal_valid'][jj]&(ndot>=cfg['normal_dot_min'])
                conditional=(cycle<=cfg['cycle_max_px'])&normal_ok
                kind[ii[conditional]]=0
                full_e=np.full(230400,np.nan,np.float32);full_e[pixels[ii]]=error
                # Several A samples can land in one B pixel. Display the same
                # first-surface z-buffer, rather than last-writer depth.
                full_projected=zbuffer.astype(np.float32);full_projected[~np.isfinite(full_projected)]=np.nan
                full_target=np.full(230400,-1,np.int32);full_target[pixels[ii]]=jj
                eligible_map=np.zeros(230400,bool);eligible_map[pixels]=True
                kindmap=np.full(230400,255,np.uint8);kindmap[pixels]=kind
                conditional_map=np.zeros(230400,bool);conditional_map[pixels[ii[conditional]]]=True
                folder=R/'local_results/depth_pairs';folder.mkdir(exist_ok=True)
                np.savez_compressed(folder/(A+'__'+B+'.npz'),residual_A_mm=full_e.reshape(360,640),
                    A_projected_Z_in_B_mm=full_projected.reshape(360,640),source_eligible=eligible_map.reshape(360,640),
                    target_pixel=full_target.reshape(360,640),condition=kindmap.reshape(360,640),conditional=conditional_map.reshape(360,640),
                    source_pixel=pixels[ii],target_index=jj,residual=error,cycle_px=cycle,normal_dot=ndot,threshold_mm=tau,
                    conditional_subset=conditional,region=fA['region'][pixels[ii]],
                    bias_J_A=(np.c_[uv[pixels[ii]],np.ones(len(ii))]@np.linalg.inv(pa['K']).T@pa['pose'][:3,:3].T@pb['pose'][:3,:3])[:,2])
                flow=dict(scene=scene,A=A,B=B,source_positive_N=int(positive.sum()),source_visible_depth_N=len(pixels),
                    outside_projection_N=int((kind==1).sum()),target_invalid_or_identity_N=int((kind==2).sum()),
                    known_Ring_occluded_N=int((kind==3).sum()),projected_A_self_occluded_N=int((kind==4).sum()),
                    loose_candidate_N=len(ii),conditional_candidate_N=int(conditional.sum()),uncertified_correspondence_N=int((~conditional).sum()),
                    depth_order_ambiguous_N=int((abs(error)>tau).sum()),direction='directed; inverse direction NOT independent')
                assert sum(flow[k] for k in ['outside_projection_N','target_invalid_or_identity_N','known_Ring_occluded_N','projected_A_self_occluded_N','loose_candidate_N'])==len(pixels)
                flows.append(flow)
                for tier,tmask in [('LOOSE_PROJECTIVE_CANDIDATE',np.ones(len(ii),bool)),('CONDITIONAL_CYCLE_NORMAL',conditional)]:
                    for region in [-1,0,1,2,3]:
                        region_name='ALL' if region<0 else cfg['regions'][region]
                        use=tmask if region<0 else tmask&(fA['region'][pixels[ii]]==region)
                        source_n=len(pixels) if region<0 else int((fA['region'][pixels]==region).sum())
                        values=error[use];result=residual_stats(values);conf=abs(values)>tau[use]
                        cmap=np.zeros(230400,np.uint8);cmap[pixels[ii[use]][conf]]=1
                        ncomp,cc,stat,_=cv2.connectedComponentsWithStats(cmap.reshape(360,640),8)
                        areas=stat[1:,cv2.CC_STAT_AREA];keep=areas>=cfg['min_component_pixels']
                        footprint=za[pixels[ii[use]][conf]]**2/(pa['K'][0,0]*pa['K'][1,1])
                        rows.append(dict(scene=scene,A=A,B=B,tier=tier,region=region_name,source_eligible_N=source_n,
                            coverage=result['N']/source_n if source_n else None,**result,conflict_N=int(conf.sum()),
                            conflict_fraction=float(conf.mean()) if len(conf) else None,
                            continuous_conflict_component_N=int(keep.sum()),largest_conflict_component_pixel_N=int(areas.max()) if len(areas) else 0,
                            conflict_projected_footprint_mm2=float(footprint.sum()),area_caveat='source HERO pixel footprint, not true surface area',
                            cycle_median_px=float(np.median(cycle[use])) if use.any() else None,
                            correspondence='CONDITIONAL_NOT_PHYSICAL_TRUTH',opposite_direction_independent=False))
                print('DEPTH_PAIR',A,'->',B,'visible',len(pixels),'loose',len(ii),'conditional',int(conditional.sum()),flush=True)
    table('metrics/HERO_PAIRWISE_DEPTH_CONFLICTS.csv',rows);table('metrics/PAIRWISE_QUALIFICATION_FLOW.csv',flows)
    table('metrics/DEPTH_PROJECTION_CLOSURE.csv',checks)
    assert all(x['pass_'] for x in checks)
    save('metrics/P1_DEPTH_GATE.json',dict(status='PASS_DIRECTED_CONDITIONAL_DIAGNOSTICS',directed_pair_N=12,scene_N=2,
        row_N=len(rows),absolute_depth_accuracy_verified=False,HERO_modified=False,GT_used=False,unresolved_correspondences_retained=True,GPU='NOT_AUTHORIZED'))

if __name__=='__main__':main()
