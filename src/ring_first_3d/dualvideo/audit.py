"""DV01: actual native Ring projection and original Blender scene evidence.

No error injection, Body fitting or registration is permitted by this handler.
"""
import io,json,os,subprocess,unittest
from pathlib import Path
import numpy as np
from scipy.ndimage import distance_transform_edt,binary_erosion
from ..policy.contracts import ROOT,require,PolicyError
from ..contracts.coordinates import validate_c2w,validate_ring
from ..contracts.identities import sha256
from ..synthetic.io import save_json,outputs
from ..synthetic.raster import rasterize


def projection_metrics(observed,projected):
    """Occlusion-safe observed support, plus full-boundary diagnostic.

    Unobserved CAD pixels are not asserted to be wrong: a real Polyp may occlude
    them. Observed contours include occlusion cuts; report their p95 explicitly.
    """
    n=int(observed.sum());edge=observed&~binary_erosion(observed)
    boundary=projected&~binary_erosion(projected)
    dist=distance_transform_edt(~projected) if projected.any()else np.full(projected.shape,np.inf)
    ed=distance_transform_edt(~boundary) if boundary.any()else np.full(projected.shape,np.inf)
    return dict(observed_ring_pixels=n,projected_ring_pixels=int(projected.sum()),
        support_within2px=float((dist[observed]<=2).mean())if n else None,
        observed_to_CAD_boundary_p95_px=float(np.percentile(ed[edge],95))if edge.any()and boundary.any()else None,
        IoU_diagnostic=float((observed&projected).sum()/max(1,(observed|projected).sum())),
        unmatched_observed_pixels=int((observed&(dist>2)).sum()))


def passes(m,g):
    return (m['observed_ring_pixels']>=g['min_observed_ring_pixels']and
        m['support_within2px']is not None and m['support_within2px']>=g['observed_ring_CAD_support_within2px_min']and
        m['observed_to_CAD_boundary_p95_px']is not None and m['observed_to_CAD_boundary_p95_px']<=g['observed_to_full_CAD_boundary_p95_px_max'])


def check_sources(row):
    for k in ['cache','RGB_source','Mask_source','pose_origin','ring']:
        r=row[k];require(Path(r['path']).is_file(),'NOT_EVALUABLE',row['source_id']+':'+k)
        require(sha256(r['path'])==r['sha256'],'SOURCE_SHA',row['source_id']+':'+k)
    validate_c2w(np.asarray(row['Camera_to_Ring']))
    p=Path(row['pose_origin']['path'])
    if p.suffix=='.npz':
        # The frozen MAST3R pack names its camera matrix "pose", whereas
        # original observation packs use "T". This is a format adapter only.
        with np.load(p)as a:native=np.array(a['T']if 'T'in a else a['pose'])
    else:
        a=json.loads(p.read_text())
        if isinstance(a,list):a=a[int(row['pose_origin']['fragment'])]
        if 'view'in a:a=a['view'][0]
        native=np.asarray(a['c2w']if 'c2w'in a else a['T'])
    require(np.allclose(native,row['Camera_to_Ring'],atol=1e-9,rtol=0),'CAMERA_BINDING',row['source_id']+': frozen native pose differs from original provenance')


def fixed_pose_certificate(inventory,manifest):
    # A shape-only .blend plus independent Ring reconstructions do not provide
    # a measured Body->Ring transform. Never mint a certificate by shape fitting.
    return dict(status='NOT_EVALUABLE',transform=None,
        reason='No source-bound Body-to-Ring deployment transform or real dual-video common-world certificate is supplied in the frozen source manifest.',
        mesh_objects=[o['name']for o in inventory['objects']if o['type']=='MESH'],
        camera_objects=[o['name']for o in inventory['objects']if o['type']=='CAMERA'],
        common_world_certified=manifest['shared_world_certified'])


def regression(attempt):
    loader=unittest.defaultTestLoader
    base=unittest.TestSuite([loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_harness_contracts.py','test_policy_bootstrap.py']])
    n=base.countTestCases()
    suite=unittest.TestSuite([base]+[loader.discover(str(ROOT/'tests'),pattern=p)for p in ['test_synthetic_correspondence.py','test_dualvideo_gate.py']])
    stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    (attempt/'regression_log.txt').write_text(stream.getvalue())
    return dict(status='PASS'if r.wasSuccessful()and n==35 else'FAIL',baseline_tests=n,tests=r.testsRun,failures=len(r.failures),errors=len(r.errors))


def audit(task,attempt):
    assets=task['dualvideo']['assets'];manifest=json.loads(Path(assets['source_manifest']['path']).read_text())
    # Validate every bound input before Blender/projection. No substitute inputs.
    for row in manifest['rows']:check_sources(row)
    request=dict(blend=assets['blend'],output=str(attempt))
    save_json(attempt/'SCENE_REQUEST.json',request)
    command=[assets['blender_binary']['path'],'-b','--factory-startup','--disable-autoexec','-t','2','--python',str(ROOT/'tools/research/inspect_g01_scene.py'),'--',str(attempt/'SCENE_REQUEST.json')]
    with (attempt/'blender_stdout.txt').open('w')as out:
        subprocess.run(command,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=90,
            env=dict(os.environ,XDG_CONFIG_HOME=str(attempt/'runtime/blender_config')))
    inventory=json.loads((attempt/'BLENDER_SCENE_INVENTORY.json').read_text())
    fresh=np.load(attempt/'fresh_body_mm.npz');cached=np.load(assets['gt_cache']['path'])
    require(np.array_equal(fresh['F'],cached['F'])and np.allclose(fresh['V'],cached['V'],atol=1e-10,rtol=0),'GT_EXPORT','Fresh original Blender differs from frozen cache')
    pose=fixed_pose_certificate(inventory,manifest);save_json(attempt/'BODY_RING_POSE_CERTIFICATE_AUDIT.json',pose)
    (attempt/'figures').mkdir();rows=[]
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image
    import hashlib
    for row in manifest['rows']:
        data=np.load(row['cache']['path']);rgb=data['RGB'];labels=data['labels'];K=np.asarray(row['K']);T=np.asarray(row['Camera_to_Ring'])
        require(np.allclose(data['K'],K,atol=1e-10),'CAMERA_BINDING',row['source_id']+': K')
        require(np.array_equal(rgb,np.asarray(Image.open(row['RGB_source']['path']).convert('RGB'))),'SOURCE_CONTENT',row['source_id']+': RGB')
        source_labels=np.asarray(Image.open(row['Mask_source']['path']))
        require(np.array_equal(labels,source_labels),'SOURCE_CONTENT',row['source_id']+': labels')
        if row.get('RGB_content_SHA'):require(hashlib.sha256(rgb.tobytes()).hexdigest()==row['RGB_content_SHA'],'SOURCE_CONTENT',row['source_id'])
        ring=np.load(row['ring']['path']);validate_ring(ring['V'],10.)
        projected=rasterize(ring['V'],ring['F'],K,T,labels.shape)['valid'];observed=labels==2
        m=projection_metrics(observed,projected);good=passes(m,task['dualvideo']['gates'])
        record=dict(source_id=row['source_id'],view_id=row['view_id'],video=row['video'],role=row['role'],**m,
            projection_gate='PASS'if good else'FAIL',native_camera_to_ring=T.tolist(),K=K.tolist(),
            cache_T_differs_from_native=bool('T'in data and not np.allclose(data['T'],T,atol=1e-9)),
            source_pose_sha256=row['pose_origin']['sha256'],ring_sha256=row['ring']['sha256'],
            source_rgb_sha256=row['RGB_source']['sha256'],source_mask_sha256=row['Mask_source']['sha256'],
            figure='figures/'+row['view_id']+'.png',error_setting='NONE; G0 before injection')
        rows.append(record)
        fig,ax=plt.subplots(1,3,figsize=(15,3.8),layout='constrained')
        ax[0].imshow(rgb);ax[0].set_title('Real source RGB')
        ax[1].imshow(rgb)
        for mask,color,label in [(observed,'lime','Observed Ring label=2'),(projected,'magenta','Full R10 CAD native pose')]:
            if mask.any():ax[1].contour(mask,levels=[.5],colors=[color],linewidths=.6)
            ax[1].plot([],[],color=color,label=label)
        ax[1].legend(fontsize=7);ax[1].set_title(f'Support@2px={m["support_within2px"]:.4f}; {record["projection_gate"]}')
        mismatch=np.zeros((*labels.shape,3));mismatch[projected]=[.5,.2,.6];mismatch[observed&projected]=[.1,.7,.2];mismatch[observed&~projected]=[1,.2,.05]
        ax[2].imshow(mismatch);ax[2].set_title(f'Orange: unmatched observed; purple: CAD only\np95 boundary={m["observed_to_CAD_boundary_p95_px"]:.2f}px')
        for a in ax:a.set(xlim=(0,labels.shape[1]-1),ylim=(labels.shape[0]-1,0),xlabel='native x [px]',ylabel='native y [px]')
        fig.suptitle(f'{row["source_id"]} | {row["role"]} | R10 in mm | no injected error\nRGB {row["RGB_source"]["sha256"][:12]} / pose {row["pose_origin"]["sha256"][:12]}',fontsize=9)
        fig.savefig(attempt/record['figure'],dpi=100);plt.close(fig)
    signatures={v:[np.asarray(r['Camera_to_Ring']).round(10).tolist()for r in manifest['rows']if r['video']==v]for v in ['004','005']}
    distinct=signatures['004']!=signatures['005']
    failures=[]
    if pose['status']!='PASS':failures.append(dict(code='BODY_RING_POSE_UNCERTIFIED',category='incomplete_evaluation',reason=pose['reason'],evidence='BODY_RING_POSE_CERTIFICATE_AUDIT.json'))
    for r in rows:
        if r['projection_gate']!='PASS':failures.append(dict(code='RING_PROJECTION_GATE',category='data_identity_error',source_id=r['source_id'],reason='Frozen native camera projection does not meet predeclared support/boundary tolerances',evidence=r['figure']))
    if not distinct:failures.append(dict(code='TRAJECTORY_IDENTITY',category='data_identity_error',reason='Trajectories indistinguishable',evidence='G0_SCENE_METRICS.json'))
    summary={v:dict(frames=sum(r['video']==v for r in rows),passed=sum(r['video']==v and r['projection_gate']=='PASS'for r in rows),
        support_median=float(np.median([r['support_within2px']for r in rows if r['video']==v])),
        boundary_p95_median_px=float(np.median([r['observed_to_CAD_boundary_p95_px']for r in rows if r['video']==v])))for v in ['004','005']}
    save_json(attempt/'G0_SCENE_METRICS.json',dict(rows=rows,summary=summary,failures=failures,distinct_trajectories=distinct,
        body_cache_matches_fresh_export=True,Body_to_Ring=pose,all_conditions={s:'NOT_RUN'for s in task['dualvideo']['condition_order']},injection_performed=False))
    from .visualize import create_scene
    create_scene(attempt,manifest,fresh)
    return outputs(attempt,dict(status='FAIL'if failures else'PASS',reason='; '.join(sorted({f['code']for f in failures})),
        rows=rows,summary=summary,scene_failures=failures,GT_read_by_scene_auditor=True,injection_performed=False))


def dispatch(stage,task,attempt):
    if stage=='dualvideo_regression':return regression(attempt)
    if stage=='G0_scene_audit':return audit(task,attempt)
    raise PolicyError('HANDLER_NOT_REGISTERED','G1–G4 require passed real-scene G0; no speculative algorithm registered')
