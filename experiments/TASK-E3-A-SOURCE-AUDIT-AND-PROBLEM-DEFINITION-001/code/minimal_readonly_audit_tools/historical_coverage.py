"""Ray-query already existing historical outputs; no new fusion or geometry changes."""
from common import *
combine=extract(E0/'code/evidence.py',['combine'],dict(globals()))['combine'];f3=extract(E0/'code/evidence.py',['f3'],dict(globals()))['f3']

def main():
    freeze('BEFORE_HISTORICAL_OUTPUT_QUERIES.json');sys.path.insert(0,str(VENDOR));import open3d as o3d
    rows=[]
    for sid in scenes():
        refs=[c['id']for c in D['references']if c['scene_id']==sid];h9=[c['id']for c in D['references'][:9]if c['scene_id']==sid];h14=[c['id']for c in D['references'][:14]if c['scene_id']==sid]
        methods={'F1_incremental_original':combine(sid,'Cleaned_F1',h9),'F2_viewpartition_original':combine(sid,'F2',h14),'F3_BoundaryGrowth_original':f3(sid)}
        for name,m in methods.items():
            sc=o3d.t.geometry.RaycastingScene(nthreads=2);sc.add_triangles(o3d.core.Tensor(m['P'].astype(np.float32)),o3d.core.Tensor(m['F'].astype(np.uint32)))
            for cid in refs:
                s=source(cid);uv=np.argwhere(s['labels']==1)[:,::-1];own=np.load(R/f'local_results/own/{cid}.npz');base=own['visible'][uv[:,1],uv[:,0]];basez=own['raw_Z'][uv[:,1],uv[:,0]];cad=own['CAD_Z'][uv[:,1],uv[:,0]]
                rays=vis.camera_rays(uv,s['K'],s['T']);hit=sc.cast_rays(o3d.core.Tensor(rays.astype(np.float32)))['t_hit'].numpy();valid=np.isfinite(hit)&(hit>0)&(hit<=cad+.002);both=base&valid;delta=hit[both]-basez[both];tau=np.maximum(.5,3*basez[both]/min(s['K'][0,0],s['K'][1,1]));loss=base&~valid
                rows.append(dict(scene=sid,source=cid,method=name,source_in_historical_selected_output=cid in m['input_refs'],reference_camera_screened=eligible(CC[cid]),
                    full_Polyp_Mask_N=len(uv),raw_visible_triangle_N=int(base.sum()),historical_visible_triangle_N=int(valid.sum()),baseline_raw_hit_now_miss_N=int(loss.sum()),
                    baseline_raw_hit_survival_fraction=float(both.sum()/max(1,base.sum())),common_hits_N=int(both.sum()),historical_minus_own_raw_signed_median_mm=None if not len(delta)else float(np.median(delta)),
                    historical_minus_own_raw_abs_p95_mm=None if not len(delta)else float(np.quantile(abs(delta),.95)),common_hits_separated_beyond_diagnostic_window_N=int((abs(delta)>tau).sum()),
                    coverage_is_not_accuracy=True,strict_same_input_replay=False,physical_destruction_confirmed=False,
                    interpretation='existing-output source-ray diagnostic; scopes differ; replaced first hit may be other surface; omissions and misses require physical qualification'))
                if name=='F3_BoundaryGrowth_original':
                    folder=R/'local_results/historical_F3';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(cid+'.npz'),UV=uv,first_Z=hit,valid=valid,baseline_raw_hit_now_miss=loss)
    table('metrics/E3_HISTORICAL_SOURCE_RAY_COVERAGE.csv',rows);print('E3_HISTORICAL_COVERAGE_COMPLETE',len(rows),flush=True)
if __name__=='__main__':main()
