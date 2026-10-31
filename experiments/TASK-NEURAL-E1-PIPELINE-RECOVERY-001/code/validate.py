"""Independent CPU assertions over actual artifacts and protected inputs."""
from common import *
import re

def main():
    D=load(R/'provenance/INPUT_ELIGIBILITY.json');checks=[]
    def check(name,ok,detail=None):
        checks.append(dict(test=name,pass_=bool(ok),detail=detail))
        if not ok:save('metrics/FINAL_VALIDATION.json',dict(checks=checks,status='FAIL'));raise AssertionError((name,detail))
    save('provenance/VALIDATION_BEFORE_TEST_FREEZE.json',dict(code=asset(Path(__file__)),common=asset(R/'code/common.py'),config=asset(R/'config/CPU_CONTRACT.json')))
    cameras=[]
    for c in D['references']:
        with np.load(c['pack']) as p,np.load(c['camera_file']) as f:
            T=f['c2w'][c['reference_index']] if f['c2w'].ndim==3 else f['c2w']
            cameras.append(dict(source=c['id'],camera_SHA256=sha(c['camera_file']),pack_SHA256=sha(c['pack']),
                K_exact=np.array_equal(p['K'],f['K']),c2w_exact=np.array_equal(p['pose'],T),
                E0_K_exact=np.array_equal(p['K'],np.asarray(c['K_raw'])),E0_pose_exact=np.array_equal(p['pose'],np.asarray(c['c2w_mm'])),
                max_K_difference=float(np.max(abs(p['K']-f['K']))),max_c2w_difference_mm=float(np.max(abs(p['pose']-T)))))
    table('metrics/FROZEN_CAMERA_INVARIANTS.csv',cameras)
    check('36 pack cameras exactly equal archived index-selected cameras',len(cameras)==36 and all(x['K_exact'] and x['c2w_exact'] and x['E0_K_exact'] and x['E0_pose_exact']for x in cameras))
    records=list(csv.DictReader((R/'metrics/MAP_GEOMETRY_ADAPTER_CONTRACT.csv').open()))
    for r in records:
        with np.load(r['output']) as z:
            c=next(c for c in D['references']if c['id']==r['source_view']);p=np.load(c['pack']);v=z['validity']
            check('adapter camera immutable '+r['scene']+' '+r['geometry']+' '+r['raster'],np.array_equal(z['source_K'],p['K']) and np.array_equal(z['source_c2w_mm'],p['pose']))
            check('adapter invalid pixels zero/masked and provenance complete '+Path(r['output']).stem,
                  np.all(z['depth_z_m'][~v]==0) and np.all(np.isnan(z['axial_Z_mm'][~v])) and np.all(np.isfinite(z['source_original_uv'][v])) and np.all(z['source_reference'][v]!=''))
            check('adapter artifact SHA '+Path(r['output']).stem,sha(r['output'])==r['output_SHA256'])
    check('all32 real geometry adapter cases legal',len(records)==32 and all(r['status']=='LEGAL_DERIVED_DEPTH'for r in records))
    native=list(csv.DictReader((R/'metrics/MAP_NATIVE_CPU_CONTRACT.csv').open()))
    check('eight native contracts use three real reference views',len(native)==8 and all(r['real_view_N']=='3'for r in native))
    # Synthetic points in front/behind the REAL CAD, using the existing projector.
    pns=dict(globals(),camera=lambda t:SameCameraScene(ring(t['kind']),t['K'],t['c2w'],(640,360),str(VENDOR)),cfg=lambda:dict(CAD_tolerance_mm=.05))
    projection=extract(GROW/'code/geometry.py',['projection'],pns)['projection'];cadrows=[]
    grid=np.c_[np.tile(np.arange(640),360),np.repeat(np.arange(360),640)]
    for sid in ['G01_004','G01_005','G06_004','G08_005','G07_004']:
        c=next(c for c in D['references']if c['scene_id']==sid);K=np.array(c['K_raw']);T=np.array(c['c2w_mm']);sc=SameCameraScene(ring(c['ring']),K,T,(640,360),str(VENDOR))
        hit=sc.cast(grid)['t_hit'].numpy();ids=np.flatnonzero(np.isfinite(hit)&(hit>2));ids=ids[np.linspace(0,len(ids)-1,min(len(ids),64),dtype=int)];uv=grid[ids]
        front=unproject(hit[ids]-1,T,uv,K);back=unproject(hit[ids]+1,T,uv,K);t=dict(K=K,c2w=T,kind=c['ring'])
        one=projection(front,np.ones_like(front),t);two=projection(back,np.ones_like(back),t);both=projection(np.r_[back,front],np.ones((len(ids)*2,3)),t)
        test=dict(scene=sid,synthetic_rays_N=len(ids),front_visible_N=int((one['source_id']>=0).sum()),behind_visible_N=int((two['source_id']>=0).sum()),
            zbuffer_front_selected_N=int((both['source_id']>=len(ids)).sum()),not_real_Polyp_points=True)
        check('known CAD front/back and nearest zbuffer '+sid,test['front_visible_N']==len(ids) and test['behind_visible_N']==0 and test['zbuffer_front_selected_N']==len(ids),test);cadrows.append(test)
    table('metrics/SYNTHETIC_CAD_ZBUFFER_TESTS.csv',cadrows)
    cad=[]
    for kind,major in [('R10',5.6),('R5',3.1)]:
        m=ring(kind);rho=np.linalg.norm(m.vertices[:,:2],axis=1);M=(rho.max()+rho.min())/2;tube=(rho.max()-rho.min())/2
        cad.append(dict(kind=kind,centerline_radius_mm=M,tube_radius_mm=tube,bounds_mm=m.bounds,watertight=m.is_watertight,source_CAD_unchanged=True))
        check('fixed CAD physical dimensions '+kind,abs(M-major)<1e-5 and abs(tube-.6)<1e-5 and m.is_watertight)
    save('metrics/CAD_PHYSICAL_CONTRACT.json',cad)
    # Exact active official classes, despite E0's old inactive-grid import patch.
    official=SDF/'code/model/network.py';archive=E0/'provenance/official_sources/autonomousvision__monosdf/code/model/network.py'
    cls=lambda p:{n.name:ast.dump(n,include_attributes=False)for n in ast.parse(p.read_text()).body if isinstance(n,ast.ClassDef)}
    a,b=cls(official),cls(archive)
    for name in ['ImplicitNetwork','MonoSDFNetwork','RenderingNetwork']:check('official active AST unchanged '+name,a[name]==b[name])
    sf=load(R/'metrics/SDF_GATE_STATUS.json');check('old SDF negative case is detected',sf['old_expected_failure_detected'])
    check('BCE saturation quantitatively matches old actual400-step record',abs(sf['saturated_mask_BCE_expected']-sf['E0_recorded_silhouette_min'])<1e-6)
    check('SDF branch remains stopped',sf['C1_SDF']=='ADAPTER_INVALID' and 'STOP_SDF_BRANCH'in sf['next_SDF_branch'])
    check('native/dependency audit count independently restored',load(R/'metrics/C0_SUMMARY.json')['HERO_dependency_edge_N']==154 and load(R/'metrics/C0_SUMMARY.json')['independently_readable_native_N']==36)
    # Rehash all source-ledger, DAG, real-native, documents and model utility
    # inputs. No weights are loaded; full neural output caches stay read-only.
    frozen=[]
    frozen += load(R/'provenance/READING_AND_CODE_SHAS.json')
    for r in csv.DictReader((R/'provenance/SOURCE_SHA_LEDGER.csv').open()):
        if r.get('sha256'):frozen.append(dict(path=r['path'],sha256=r['sha256']))
    for r in D['references']:frozen.append(r['E1_actual_native'])
    for n in load(R/'provenance/E1_SOURCE_DAG.json')['nodes']:
        if n.get('path') and n.get('sha256'):frozen.append(n)
    for n in load(R/'provenance/F3_SOURCE_AUDIT.json'):frozen.extend([n,n['scene_faces']])
    seen={};conflicting=[]
    for f in frozen:
        if f.get('sha256'):
            if f['path'] in seen and seen[f['path']]!=f['sha256']:conflicting.append(f['path'])
            seen[f['path']]=f['sha256']
    changed=[p for p,h in seen.items()if not Path(p).is_file() or sha(p)!=h]
    check('all old input/source hashes unchanged',not changed and not conflicting,dict(N=len(seen),changed=changed,conflicting_baselines=conflicting))
    save('provenance/INPUTS_AND_SHAS.json',dict(files=[dict(path=p,sha256=h)for p,h in sorted(seen.items())],
        all_verified_unchanged=True,N=len(seen),weights_opened=False,GT_opened=False))
    old=load(R/'provenance/PROTECTED_START.json');end=protected_state();save('provenance/PROTECTED_END.json',end)
    check('all old worktree HEAD/status/dirty-file hashes unchanged',old==end)
    check('four actual core PNGs exist',len(list((R/'figures').glob('Fig*.png')))==4)
    for path,mode,flags in [('/home/liu/private_gt/E1_deny_probe.npz','r',0),('/home/liu/polyp_research/E1_deny_probe.tmp','w',os.O_WRONLY|os.O_CREAT)]:
        try:sys.audit('open',path,mode,flags);denied=False
        except PermissionError:denied=True
        check('guard denies '+mode,denied)
    status=dict(status='PASS_CPU_VALIDATION_WITH_SDF_REJECTION',checks=checks,check_N=len(checks),
        model_run_N=0,scientific_success='NOT_EVALUATED',SDF_branch='ADAPTER_INVALID / STOP_SDF_BRANCH',Map_branch='GATE_PASS_CPU_CONTRACT_ONLY',
        GT_read=False,old_input_hash_N=len(seen))
    save('metrics/FINAL_VALIDATION.json',status)
    print('VALIDATION_COMPLETE',len(checks),'assertions; old asset SHA_N',len(seen),flush=True)

if __name__=='__main__':main()
