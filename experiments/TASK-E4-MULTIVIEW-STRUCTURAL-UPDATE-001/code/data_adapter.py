"""Only domain adapter: exact 013 Mesh, original poses/splits/weights. No shape fit."""
import json
from pathlib import Path
import numpy as np
from ring_first_3d.policy.contracts import require
from ring_first_3d.contracts.identities import sha256
from ring_first_3d.synthetic.io import save_json
from body_update import initialize


def load_json(rec):return json.loads(Path(rec['path']).read_text())


def sources(task):return load_json(task['structural']['assets']['real_sources'])


def real_row(task,case):return next(r for r in sources(task)['cases'] if r['case']==case)


def common_initial(task,case,ring):
    row=real_row(task,case);ref=dict(np.load(row['static']['RING.npz']['path']))
    body=initialize(row['resolved013_initial']['path'],ring,ref)
    base=load_json(row['static']['BASE_SELECTION.json']);chart=load_json(row['static']['CHART.json'])
    return body,base,chart


def real_data(task,case,only_role=None):
    row=real_row(task,case);ring=dict(np.load(row['static']['RING.npz']['path']));views=[]
    for role in ('FIT','HOLDOUT'):
        if only_role and role!=only_role:continue
        for v in row[role]:
            a=np.load(v['cache']['path']);m=v['meta']
            views.append(dict(id=m['id'],video=m['video'],role=role,direction_block=m.get('direction_block',0),
                              K=a['K'],C=a['T'],labels=a['labels'],RGB=a['RGB']))
    body,base,chart=common_initial(task,case,ring)
    return body,views,ring,base,chart


def simulation_data(task,only_role=None):
    cfg=task['structural'];manifest=load_json(cfg['assets']['simulation_views']);public=Path(cfg['simulation_public'])
    ring=dict(np.load(cfg['assets']['ring']['path']));views=[]
    # Existing 16FIT +8HOLDOUT identities and independent no-error images remain unchanged.
    for r in manifest['selected']+manifest['HOLDOUT']:
        if only_role and r['role']!=only_role:continue
        cid=r['view_id'];a=np.load(public/'observations'/(cid+'.npz'));cache=np.load(r['cache']['path'])
        require(np.array_equal(a['K'],np.asarray(r['K'])),'CAMERA','Frozen native intrinsics')
        require(np.allclose(np.asarray(r['Camera_to_Ring']),cache['T'],atol=1e-10),'CAMERA','True C0 Camera-to-Ring')
        # No depth/GT/latent material identity key enters Body updater.
        meta=next((v['meta'] for v in real_row(task,'G01')['FIT']+real_row(task,'G01')['HOLDOUT'] if v['meta']['id']==cid),{})
        # Old simulation view manifest lacks direction bins for added FITs. Reuse
        # their frozen native pose source metadata bin if present, otherwise 0 (historical weights default).
        views.append(dict(id=cid,video=r['video'],role=r['role'],direction_block=meta.get('direction_block',0),
                          K=a['K'],C=np.asarray(r['Camera_to_Ring']),labels=a['labels'],RGB=a['RGB']))
    body,base,chart=common_initial(task,'G01',ring)
    return body,views,ring,base,chart


def audit(task,attempt):
    cfg=task['structural'];rows=[]
    sim=simulation_data(task);initial,views,ring,base,chart=sim
    for case in cfg['real_cases']:
        b,v,r,_,_=real_data(task,case);src=real_row(task,case)
        rows.append(dict(case=case,initial=src['resolved013_initial'],vertices=len(b['V']),faces=len(b['F']),
                         FIT=[x['id'] for x in v if x['role']=='FIT'],HOLDOUT=[x['id'] for x in v if x['role']=='HOLDOUT'],
                         initial_mesh_definition='EXACT_013_INPUT_MESH_V_F_SOLID_CAP',initializer='body_update.initialize',
                         coordinate_conversion=np.eye(4).tolist(),camera_optimized=False))
    E=[]
    for name in ('E1_initializer','E2_initializer'):
        p=cfg['assets'][name]['path'];a=np.load(p)
        E.append(dict(name=name,asset=cfg['assets'][name],vertices=len(a['V']),faces=len(a['F']),
                      nine_parameter_ellipsoid=True,used_for_new_prediction=False))
    save_json(attempt/'INITIALIZATION_AUDIT.json',dict(real=rows,simulation=dict(case='G01_LIKE_C0',vertices=len(initial['V']),faces=len(initial['F']),
                same_G01_initial_sha256=real_row(task,'G01')['resolved013_initial']['sha256'],same_loader=True,same_configuration=True,
                deterministic_Ring_conversion=np.eye(4),Ring_byte_identical=True,FIT=[v['id'] for v in views if v['role']=='FIT'],
                HOLDOUT=[v['id'] for v in views if v['role']=='HOLDOUT']),
                previous_simulation_initializers=E,new_GT_fitting=False,history_measurement_fallback=0))
    save_json(attempt/'SOURCE_VERSION_TABLE.json',cfg['assets'])
    return dict(status='PASS',real_cases=len(rows),simulation_conditions=['C0'],same_initializer=True,GT_read=False)
