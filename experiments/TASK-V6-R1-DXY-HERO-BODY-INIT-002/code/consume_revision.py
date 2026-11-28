"""Strict 002 consumer: rejected historical joint models cannot enter this interface."""
from common import *
from observations_revision import transform_samples
from geometry import *

def validate_inputs(r):
    for path,h in zip(r['source_indices'],r['source_index_sha256']):
        asset(path,h);vi=read(path)
        for item in [vi['camera'],vi['cad']]:asset(item['path'],item['sha256'])
        for f in vi['frames']:
            for k in ['RGB','Mask','DXY','curves','observations_2D']:asset(f[k]['path'],f[k]['sha256'])
            d=read(f['DXY']['path'])
            for item in read(Path(f['DXY']['path']).parent/'COMPLETE.json')['files']:asset(item['path'],item['sha256'])
        for meta in vi['sources']:
            for item in [meta['observations'],*meta['source_files']]:asset(item['path'],item['sha256'])
    asset(r['cad']['path'],r['cad']['sha256'])

def load_configuration(path):
    path=Path(path).resolve();assert T/'runs/results' in path.parents,'ONLY_002_RESULTS_ACCEPTED'
    r=read(path);folder=path.parent;receipt=read(folder/'COMPLETE.json')
    assert r['status']=='COARSE_INIT_COMPLETE'
    assert r['scientific_key']==revision_key() and r['config_sha256']==sha(T/'config.json'),'STALE_SCIENTIFIC_INPUTS'
    for item in receipt['files']:asset(item['path'],item['sha256'])
    q=next(g for g in read(T/'evidence/REGISTRATION_QUALIFICATION.json')['groups'] if g['group']==r['group'])
    if len(r['videos'])>1:
        c=next((c for c in q['joint_components'] if c['name']==r['configuration']),None)
        assert c and c['videos']==r['videos'],'JOINT_NOT_CURRENTLY_AUTHORIZED'
        for case in r['videos']:np.testing.assert_allclose(r['video_transforms'][case],c['T_local_to_joint'][case],atol=1e-12)
        assert r['qualification']['qualification_sha256']==sha(T/'evidence/REGISTRATION_QUALIFICATION.json')
    else:np.testing.assert_array_equal(r['video_transforms'][r['videos'][0]],np.eye(4))
    validate_inputs(r)
    return dict(record=r,body=dict(np.load(folder/'BODY.npz')),parent=dict(np.load(folder/'PARENT.npz')),uncut=dict(np.load(folder/'FINAL_UNCUT.npz')),base=read(folder/'BASE.json'))

def load_views(r):
    validate_inputs(r)
    frames=[];sources=[]
    for path in r['source_indices']:
        vi=read(path);case=vi['case'];M=np.asarray(r['video_transforms'][case]);root=Path(path).parent
        for fr in vi['frames']:
            x=dict(np.load(fr['observations_2D']['path']));d=read(fr['DXY']['path']);x=transform_samples(x,M)
            x.update(case=case,id=fr['id'],index=fr['index'],role=fr['role'],RGB=fr['RGB']['path'],Mask=fr['Mask']['path'],DXY_record=d,DXY_curve=np.load(fr['curves']['path'])['selected_curve']);frames.append(x)
        for meta in vi['sources']:
            x=transform_samples(dict(np.load(meta['observations']['path'])),M);x['meta']=copy_meta=__import__('copy').deepcopy(meta);copy_meta['source']['T_local_to_common']=M.tolist();sources.append(x)
    return frames,sources

def corrected_source(path,source_id):
    data=load_configuration(path);r=data['record'];meta=next(s for p in r['source_indices'] for s in read(p)['sources'] if s['source_id']==source_id);source=meta['source'];case=meta['case'];M=np.array(r['video_transforms'][case])
    for item in meta['source_files']:asset(item['path'],item['sha256'])
    mesh=trimesh.load(source['raw_mesh'],process=False);V=np.asarray(mesh.vertices);F=np.asarray(mesh.faces);ids=np.load(source['selection'])['trusted_original_face_id'];native=np.load(source['native_depth']);C=M@native['c2w'][source['reference']]
    raw=V@M[:3,:3].T+M[:3,3];out=raw.copy();used=np.unique(F[ids]);q=(raw[used]-C[:3,3])@C[:3,:3];z=q[:,2];assert np.all(z>0)
    b=next(x['b_mm'] for x in r['bias'] if x['source_id']==source_id);q*=((z-b)/z)[:,None];out[used]=q@C[:3,:3].T+C[:3,3]
    return dict(V=out,F=F[ids],original_V=raw,original_face_id=ids,C=C,K=native['K_index_native'],bias_mm=b,units='mm',coordinate_frame=r['coordinate_frame'],source=source,correction='trusted source vertices only; D-b on original rays; unused V not trusted')
