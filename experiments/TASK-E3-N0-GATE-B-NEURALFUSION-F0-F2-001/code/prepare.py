"""Freeze approved V6/V2 inputs, identities and non-GT progression rules."""
from common import *
import shutil,datetime
def main():
    assert not (R/'config/PREREGISTERED.json').exists()
    # Frozen official code/weights are reused in place and byte-checked.
    official=load(GA/'config/OFFICIAL_ARTIFACTS.json');checked=[]
    for a in official['official_files']:
        if a['relative_path'].startswith(('pipeline/','utils/geometry.py','pretrained_models/shapenet_noise_005/')):
            p=NF/a['relative_path'];assert sha(p)==a['sha256'];checked.append(asset(p))
    extra=R/'runtime/official_readonly/training_utils.py';b=extra.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    assert blob=='997c7e67c5f3167fd6c084478ead72f2bdeaaf5e'
    checked.append(asset(extra));save('provenance/OFFICIAL_CHECKED_FILES.json',dict(files=checked))
    sources=[];geos=[]
    for v in ['V6','V2']:
        for cid in IDS:
            for folder in ['inputs','crops']:
                src=A3/'local_results'/folder/v/(cid+'.npz');dst=R/'frozen_inputs'/v/folder/(cid+'.npz')
                dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);assert sha(src)==sha(dst)
                sources.append(dict(version=v,source=cid,kind=folder,original=asset(src),frozen=asset(dst)))
    save('provenance/FROZEN_INPUTS.json',dict(sources=sources,V6_confirmation='researcher accepted V6 and explicitly authorized phase2 F0-F2 pretrained inference',original_HERO_manifest=asset(REPO/'experiments/TASK-E3-D0-OPEN3D-TSDF-BASELINE-001/HERO_TSDF_INPUT_MANIFEST.json')))
    for name in ['V6_RESULT.json','V6_FINAL_REVIEW.json','V6_SUPPRESSED_NATIVE_POINTS.csv','V6_GEOMETRY_CHECK.csv','V6_LOCAL_REPORT.md']:
        shutil.copy2(A3/name,R/'provenance'/name)
    domain=load(A3/'config/A3_PREREGISTERED.json')['common_model_domain']
    protocol=dict(task=R.name,frozen_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        source_order=CORE,versions=['V6','V2'],sequences={'F0':CORE[:1],'F1':CORE[:2],'F2':CORE},
        domain=domain,official_commit='4f0c14f67ad9d2368b68cbeb78c237a6328971e5',checkpoint=load(GA/'config/CHECKPOINT_FILES.json')[0],
        official_architecture_modified=False,pretrained_only=True,optimizer_steps=0,
        empty_latent_shape=[128,128,128,17],empty_count_shape=[128,128,128],
        integration='one forward per new view; retained latent/count prefixes; reset between V6 and V2',
        translation='exact official get_translation AST function, 128-grid observed indices; both SDF/occupancy saved',
        extraction='official sdf iso0, known=nonzero latent; unknown sentinel +0.04 ONLY for marching cubes, unknown not a measured free-space observation; boundary faces audited separately; no mesh repairs/deletions',
        Open3D=dict(engine='ScalableTSDFVolume',voxel_mm=domain['voxel_mm'],sdf_trunc_mm=4*domain['voxel_mm'],depth_trunc_mm=100,depth_scale=1,internal_units='m',color='RGB8',depth_sampling_stride=1),
        evaluation=dict(native_fixed_denominator='all V2-valid native Polyp pixels, all3CORE reported each prefix; V6 availability flagged separately',
            raw_face_denominator='all original HERO face centroids/areas; no fusion as prediction input',
            agreement_mm=.25,neighborhood_mm=.25,CAD_tolerance_mm=.002,miss_is_loss=True,
            primary_known_vs_unknown_separate=True,holdout='ref13 at F0; ref03 at F0/F1; shared upstream HERO RGB, NOT independent blind test'),
        F0_gate=dict(basis='inherit D0 engineering gate; no3px rule',depth_error_p95_denominator='all current-input CAD-visible native observations, MISS=+inf; hit-only metrics also reported separately',native_CAD_visible_V6_hit_fraction_min=.90,native_CAD_visible_depth_error_p95_mm_max=.20,native_CAD_visible_point_retention_at_0p25mm_min=.90,finite_model=True,scale_inverse_mm_max=1e-5,
            failure='No F1/F2 if V6 F0 fails; V2 F0 and same-input Open3D remain bounded diagnosis; no threshold tuning'),
        later_prefix_stop='stop further views if prior-view agreement falls >0.10 absolute or new primary-view depth p95 >1mm or nonfinite/empty output',
        not_authorized=['training','weight updates','F3-F5','reverse order','new HERO','camera adjustment','GT/Oracle'],
        old_3px_gate=False)
    save('config/PREREGISTERED.json',protocol)
    for v in ['V6','V2']:
        for cid in IDS:
            n=native(cid,v);c=crop(cid,v);K,T=camera(cid);O=np.asarray(domain['O_mm']);L=domain['L_mm'];X=n['X'];xm=(X-O)/L
            assert ((xm>=0)&(xm<1)).all()
            ids=c['source_ids'][c['valid']];assert np.array_equal(n['depth'].flat[ids],c['depth_mm'][c['valid']])
            assert not ((~c['valid'])&(c['depth_mm']!=0)).any()
            TM=T.copy();TM[:3,3]=(TM[:3,3]-O)/L
            uv=c['output_uv'];xx=unproject(c['depth_mm'][c['valid']].astype(float)/L,TM,uv,c['K_crop'])*L+O
            error=float(np.linalg.norm(xx-c['output_X_mm'],axis=1).max());assert error<1e-5
            geos.append(dict(version=v,source=cid,native_N=len(X),crop_N=int(c['valid'].sum()),out_of_model_N=0,world_model_error_max_mm=error,K_crop=c['K_crop'].tolist(),c2w_mm=T.tolist(),pose_reestimated=False))
    for cid in IDS:
        a,b=crop(cid,'V6'),crop(cid,'V2')
        for k in ['A','K_crop','source_ids']:assert np.array_equal(a[k],b[k])
    table('INPUT_GEOMETRY_VALIDATION.csv',geos)
    save('config/CAMERAS.json',{cid:dict(K_archive=camera(cid)[0],c2w_mm=camera(cid)[1])for cid in IDS})
    save('provenance/ORIGINAL_SHA_START.json',dict(files=[asset(a['path'])for r in MANIFEST['sources']for a in r['assets'].values()]+[asset(CAD)]))
    print('FROZEN_V6_V2',len(sources),'GEOMETRY_PASS',len(geos),flush=True)
if __name__=='__main__':main()
