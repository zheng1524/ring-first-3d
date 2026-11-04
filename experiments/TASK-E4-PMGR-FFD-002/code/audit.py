"""Final reproducibility and physical invariants, without optimization."""
from inputs import *
from shape import Body
from physical import volume,blender_check
from collision import Collision
import shutil,datetime,platform,importlib.metadata as md,subprocess
from zoneinfo import ZoneInfo

def main():
    checks=[]
    def walk(x):
        if isinstance(x,dict):
            if 'path'in x and'sha256'in x:checks.append(dict(path=x['path'],frozen_sha256=x['sha256'],actual_sha256=sha(x['path'])))
            else:
                for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(load(R/'assets_index/INHERITED_SOURCES.json'));walk(load(R/'metrics/INPUT_FREEZE.json'));assert all(x['frozen_sha256']==x['actual_sha256']for x in checks)
    if(R/'metrics/G06_CONTINUATION_START.json').exists():
        assert load(R/'metrics/G06_CONTINUATION_FINISHED.json')['finished'];walk(load(R/'metrics/G06_CONTINUATION_START.json')['candidate']);assert checks[-1]['frozen_sha256']==checks[-1]['actual_sha256']
    model_checks=[];updates=[];transfers=[]
    for scene in protocol()['scene_order']:
        for arm in ['C1','C2','C3']:
            row=p0(scene,protocol()['scenes'][scene]['initial']);p=np.load(R/'local_results'/scene/arm/'P0.npz')['q'][:9];basis=np.load(R/'inputs'/(scene+'_'+('spectral'if arm=='C1'else'ffd')+'_BASIS.npz'))['fields'];m=Body(row,p,basis);log=load(R/'metrics'/(scene+'_'+arm+'_UPDATE_LOG.json'));updates+=log
            assert all(not x['physical']['collision']and x['path']is not None for x in log if x['accepted'])
            b=load(R/'metrics'/(scene+'_'+('spectral'if arm=='C1'else'ffd')+'_BASIS.json'));gate=np.array(b['support']['P3_gate']);assert abs(basis[~gate,:,48:]).max()<1e-10
            for stage in ['P0','P1','P2','P3','BEST','LAST_SAFE']:
                file=R/'local_results'/scene/arm/(stage+'.npz');cp=dict(np.load(file));assert abs(cp['V']-m.vertices(cp['q'])).max()<1e-10;mesh=trimesh.Trimesh(cp['V'],cp['F'],process=False);assert mesh.is_watertight and mesh.is_winding_consistent and volume(cp['V'],cp['F'])>0
                rt=mesh_scene(cp['V'],cp['F']);center=mesh.center_mass;sg=rt.compute_signed_distance(o3d.core.Tensor(np.array([center,center+[100,0,0]],np.float32))).numpy();assert sg[0]<0 and sg[1]>0
                d=load(R/'metrics'/(scene+'_'+arm+'_'+stage+'.json'));assert d['Blender']['EXACT_intersection_volume_mm3']<=1e-8 and not d['collision']['collision']
                model_checks.append(dict(case=scene,arm=arm,stage=stage,mesh=asset(file),closed=True,winding=True,inside_outside_signed_mm=sg,positive_volume_mm3=volume(cp['V'],cp['F']),FCL_gap_mm=d['collision']['distance_mm'],Blender_intersection_mm3=d['Blender']['EXACT_intersection_volume_mm3'],status=d['status']))
                if stage in ['P1','P2','P3']:
                    extra=d['extra'];jump=extra.get('zero_mode_transfer_mm')if extra else None;transfers.append(dict(case=scene,arm=arm,stage=stage,transfer_mm=jump));assert jump is None or jump<1e-10
    results=load(R/'metrics/RESULTS.json');assert len(updates)==sum(a['accepted_N']+a['rejected_N']for c in results for a in c['arms'])
    assert all(not any(k.startswith('VIEW_CONTOUR_REGRESSION')for k in x['reasons'])for x in updates)
    # The failed second case is diagnosed without additional fit or trial.
    g=load(R/'metrics/G06_004_SAFE_P0.json');row=p0('G06_004','E1');body=Body(row,np.array(g['old_p']));V=body.vertices(body.p);old_col=Collision('G06_004').check(V,body.F,True);old_bl=blender_check('G06_004_HISTORICAL_P0_DIAGNOSTIC','G06_004',V,body.F);save('metrics/G06_004_FAILURE_PHYSICAL_DIAGNOSTIC.json',dict(original_collision=old_col,original_Blender=old_bl,no_new_optimization=True,failed_candidate_status='DIAGNOSTIC_ONLY_NOT_PREDICTION'))
    frozen=load(R/'metrics/IMPLEMENTATION_FREEZE.json');diff=[]
    for item in frozen['files']:
        actual=sha(item['path'])
        if actual!=item['sha256']:diff.append(dict(path=item['path'],frozen=item['sha256'],current=actual))
    assert len(diff)==3 and {Path(x['path']).name for x in diff}=={'optimize.py','p0.py','run.py'}
    current=datetime.datetime.now(ZoneInfo('Asia/Shanghai'));start=datetime.datetime.fromisoformat(load(R/'metrics/RUN_START.json')['started']);end=datetime.datetime.fromtimestamp((R/'metrics/RUN_FINISHED.json').stat().st_mtime,ZoneInfo('Asia/Shanghai'));free=shutil.disk_usage('/home/liu').free;before=load(R/'metrics/DISK_CLEANUP.json')['free_after_cleanup']
    gpu=subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,driver_version','--format=csv,noheader'],text=True).strip();env=dict(Python=platform.python_version(),CPU=Path('/proc/cpuinfo').read_text().split('model name')[1].splitlines()[0],GPU=gpu,packages={n:md.version(n)for n in ['torch','numpy','scipy','trimesh','python-fcl','nvdiffrast']},Open3D=o3d.__version__,Blender='5.0.1 a3db93c5b259',runtime_nvdiffrast_direct_url=md.distribution('nvdiffrast').read_text('direct_url.json'),official_read_reference_heads={'PhysicsNeMo':'30ecd227ffed3467cc9c17492c343fae55653145','PyTorch3D':'e4ad6e5687a360ccdc6ebd91348e8dbbac97bf31'},new_frameworks_installed=[],formal_start=start.isoformat(),formal_end=end.isoformat(),formal_wall_seconds=(end-start).total_seconds())
    env['runtime_nvdiffrast_source_commit']='253ac4fcea7de5f396371124af597e6cc957bfae'
    if(R/'metrics/G06_CONTINUATION_FINISHED.json').exists():env['G06_continuation']=dict(start=load(R/'metrics/G06_CONTINUATION_START.json')['timestamp'],end=load(R/'metrics/G06_CONTINUATION_FINISHED.json')['timestamp'])
    accepted=sum(x['accepted']for x in updates);save('metrics/ENVIRONMENT.json',env);save('metrics/FINAL_AUDIT.json',dict(checked_at=current.isoformat(),asset_checks=checks,all_frozen_inputs_unchanged=True,model_checks=model_checks,transfers=transfers,accepted_N=accepted,rejected_N=len(updates)-accepted,actual_candidates_N=len(updates),majority_stop_not_applied=True,all_accepted_paths_certified_by_existing_Lipschitz_FCL=True,path_scope='linear interpolation of world vertices, not exact nonlinear parameter interpolation',post_stop_code_changes=diff,scope='optimize.py reporting corrections; p0.py removes unauthorized observation veto; run.py/continue_g06.py now enforce per-case numerical gate. No old geometry/update replay.',numerical_Mask_gate='FAIL_G06_POST_HOC; original pre-run gate covered G01 only',overall_engineering_acceptance=False,free_bytes=free,post_cleanup_to_now_delta_bytes=free-before,safety_reserve_4GiB_intact=free>=4*2**30,GT='NOT_EVALUABLE',history_measurement_fallback=0,no_next_task_scheduled=True));assert free>=4*2**30
    files=[asset(p)for folder in ['inputs','local_results']for p in sorted((R/folder).rglob('*'))if p.is_file()];save('assets_index/LOCAL_RESULTS.json',dict(root=str(R),files=files,final_main_meshes=[str(R/'local_results'/s/'C2/P3.ply')for s in protocol()['scene_order']],main_arm='C2 predeclared, not replaced by C3 based on result',G06='Conditional physical start with original Mask regression warning preserved',coordinates='all scientific data mm; GLB m',large_data_uploaded=False))
    print('AUDIT_PASS',len(checks),'source/input SHA;',len(model_checks),'accepted saved endpoint checks; no new optimization',flush=True)

if __name__=='__main__':main()
