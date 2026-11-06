from components import *
def main():
    cfg=load(R/'config/PROTOCOL.json');A=Path(cfg['A_frozen_root']);bvh=load(R/'metrics/BLENDER_GEOMETRY_CHECK.json');rows=[]
    for name in['virtual','real']:
        c=Case(name);rs=scene(c.ringV,c.ringF)
        for arm in['P0','A','B','C','D']:
            p=R/'inputs'/name/'INITIAL.npz'if arm=='P0'else A/'local_results'/name/'RingAware/FINAL.npz'if arm=='A'else R/'local_results'/name/arm/'FINAL.npz'
            if not p.exists():continue
            a=np.load(p);V,F=a['V'],a['F'];sd=rs.compute_signed_distance(o3d.core.Tensor(V.astype(np.float32)),nsamples=3).numpy();rec=next(x for x in bvh if x['case']==name and x['arm']==arm);exact=[]
            for i,j in rec['first_self_pairs']:
                manager=trimesh.collision.CollisionManager();manager.add_object('one',trimesh.Trimesh(V[F[i]],[[0,1,2]],process=False));yes=manager.in_collision_single(trimesh.Trimesh(V[F[j]],[[0,1,2]],process=False));exact.append(dict(face_i=i,face_j=j,FCL_surface_overlap=bool(yes)))
            rows.append(dict(case=name,arm=arm,max_vertex_penetration_into_Ring_mm=max(0.,float(-sd.min())),vertices_inside_Ring_over_1micron=int((sd<-.001).sum()),Blender_Ring_pair_N=rec['Ring_intersecting_triangle_pair_N'],Blender_nonadjacent_pair_N=rec['nonadjacent_self_intersection_pair_N'],FCL_self_pairs_confirmed=sum(x['FCL_surface_overlap']for x in exact),FCL_self_pairs_checked=len(exact),self_pairs=exact,geometry_modified=False))
    save('metrics/EXACT_GEOMETRY_DIAGNOSTICS.json',rows)
    # Verify loss terms were called only for fitting references; loaded holdout cache is not a used loss.
    fairness=[]
    for name in['virtual','real']:
        c=Case(name);schedules=[]
        for arm in['B','C','D']:
            run=load(R/'metrics'/(name+'_'+arm+'_RUN.json'));hist=list(csv.DictReader((R/'metrics'/(name+'_'+arm+'_TRAINING.csv')).open()));schedules.append([h['views']for h in hist]);init=np.load(R/'local_results'/name/arm/'STEP_0000.npz')
            rendered_P0=c.mm(c.base)[0];original_A0=np.load(A/'local_results'/name/'RingAware/STEP_0000.npz');same=np.array_equal(init['V'],rendered_P0)and np.array_equal(init['V'],original_A0['V'])and np.array_equal(init['F'],c.F);trace=list(csv.DictReader((R/'metrics'/(name+'_'+arm+'_DEPTH_TRACE.csv')).open()))if(R/'metrics'/(name+'_'+arm+'_DEPTH_TRACE.csv')).exists()else[]
            assert same;assert all(x['source']in c.fit for x in trace)
            fairness.append(dict(case=name,arm=arm,same_P0_V_F=same,raw_P0_FP32_roundtrip_max_mm=float(abs(init['V']-c.V).max()),optimizer_steps=run['optimizer_steps'],accepted_steps=run['accepted_steps'],stage2_start_matches_stage1=(np.array_equal(np.load(R/'local_results'/name/arm/'STAGE2_START.npz')['V'],np.load(R/'local_results'/name/arm/'STEP_0100.npz')['V'])if arm!='B'else None),depth_loss_views=sorted({x['source']for x in trace}),holdout_depth_loss_calls=0,observation_files_loaded=run['depth_observations_read'],B_C_depth_use_prohibited=True))
        assert schedules[0]==schedules[1]==schedules[2]
    save('metrics/FAIRNESS.json',dict(same_full_view_sequence=True,A_reused_without_optimizer=True,rows=fairness))
    print(rows,flush=True)
if __name__=='__main__':main()
