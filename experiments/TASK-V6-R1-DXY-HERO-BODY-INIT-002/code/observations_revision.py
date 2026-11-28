"""Read fixed 001 observations, remove its common frame, attach actual complete 2D evidence."""
from common import *
import copy
from observations import scene,cast,pick
from geometry import rays,project

def transform_samples(s,M):
    x={k:(v.copy() if isinstance(v,np.ndarray) else copy.deepcopy(v)) for k,v in s.items()}
    R=M[:3,:3];t=M[:3,3]
    for k in ['raw_X','bg_X']:
        if k in x:x[k]=x[k]@R.T+t
    for k in ['rays','boundary_rays']:
        if k in x:x[k]=np.c_[x[k][:,:3]@R.T+t,x[k][:,3:]@R.T]
    if 'C' in x:x['C']=M@x['C']
    return x

def cad_for(a,v):
    paths=[z for z in a['source_metadata'] if z['case']==v['case']]
    if paths:p=Path(paths[0]['cad_path']);asset(p,paths[0]['cad_sha256'])
    else:
        diameter=2*(v['ring_radius_mm']-v['ring_wire_mm'])
        assert min(abs(diameter-5),abs(diameter-10))<1e-6
        p=WORK/'runs/m2f5_unified/cad'/('R%d.npz'%round(diameter))
    d=dict(np.load(p));return dict(V=d['V'],F=d['F'],identity=asset(p))

def prepare_video(a,v):
    g=a['group'];case=v['case'];out=T/'runs/observations'/g/case;out.mkdir(parents=True,exist_ok=True)
    oldindex=OLD/'runs/observations'/g/case/'INDEX.json';idx=read(oldindex)
    asset(v['camera'],v['camera_sha256']);cam=dict(np.load(v['camera']));K=cam['K'];Cs=cam['c2w']
    inv=np.linalg.inv(np.array(idx['transform']));cad=cad_for(a,v);cadscene=scene(cad['V'],cad['F'])
    frames=[];frame_receipts=[]
    dxyindex=read(T/'evidence/DXY_INPUT_INDEX.json');dxyrows={(x['case'],x['frame_id']):x for x in dxyindex['rows']}
    import dxy_full
    for fr in idx['frames']:
        j=fr['index'];f=v['frames'][j];asset(fr['observations_2D']['path'],fr['observations_2D']['sha256'])
        for k in ['RGB','Mask']:asset(fr[k]['path'],fr[k]['sha256'])
        dxyfile=T/'runs/dxy'/case/f['id']/'FRAME.json';d=dxy_full.load_frame(case,f['id']);curvespath=dxyfile.parent/'CURVES.npz';curves=d.pop('data')
        assert d['cache_key']==digest([dxyrows[(case,f['id'])],dxyindex['source'],sha(T/'code/dxy_full.py')]),'STALE_DXY_PROCESS_CACHE'
        raw=dict(np.load(fr['observations_2D']['path']));raw['C']=Cs[j];raw['K']=K
        # Exact official P identities replace heuristic Mask-derived boundary.
        P=pick(curves.get('P',np.empty((0,2))),96).astype(float)
        Q=pick(curves.get('Q',np.empty((0,2))),96).astype(float)
        selected=d.get('selected') or {};available=bool(selected.get('center_px') is not None)
        DXY=dict(available=available,center_px=selected.get('center_px'),basis_px=selected.get('basis_px'),weight=selected.get('weight',.25),status=d['status'],selected_record_id=d.get('selected_record_id'))
        raw.update(case=case,index=j,id=f['id'],role=fr['role'],RGB=f['RGB_path'],Mask=f['Mask_path'],source_frame=f,DXY=DXY,boundary=P,boundary_P=P,boundary_Q=Q,DXY_record=str(dxyfile),DXY_sha256=sha(dxyfile),DXY_curve=curves.get('selected_curve',np.empty((0,2))))
        for k in ['Q_normals','Q_lo','Q_hi']:
            arr=curves.get(k,np.empty((0,2)));raw[k]=pick(arr,96)
        raw['rays']=rays(raw['uv'],K,Cs[j]);raw['boundary_rays']=rays(P,K,Cs[j]);raw['cad_z']=cast(cadscene,raw['rays'])[0]
        frames.append(raw)
        p=out/(f['id']+'_2D.npz');np.savez_compressed(p,**{k:val for k,val in raw.items() if isinstance(val,np.ndarray)})
        frame_receipts.append(dict(id=f['id'],index=j,role=fr['role'],RGB=fr['RGB'],Mask=fr['Mask'],DXY=asset(dxyfile),curves=asset(curvespath),observations_2D=asset(p),DXY_status=d['status']))
    sources=[];receipts=[]
    for m in idx['sources']:
        source=m['source'];p=oldindex.parent/(source['tag']+'_OBS.npz');asset(p,m['observations_sha256'])
        for item in m['source_files']:asset(item['path'],item['sha256'])
        x=transform_samples(dict(np.load(p)),inv);ref=source['reference']
        np.testing.assert_allclose(x['C'],Cs[ref],atol=1e-8)
        meta=copy.deepcopy(m);meta['source']['T_local_to_common']=np.eye(4).tolist();meta['coordinate_frame']='VIDEO_LOCAL';meta['historical_observations']=asset(p)
        x['cad_z']=cast(cadscene,x['rays'])[0];dst=out/(source['tag']+'_OBS.npz');np.savez_compressed(dst,**x)
        meta['observations']=asset(dst);meta['observations_sha256']=sha(dst);x['meta']=meta;sources.append(x);receipts.append(meta)
    save(out/'INDEX.json',dict(case=case,group=g,coordinate_frame='VIDEO_LOCAL',transform=np.eye(4),camera=asset(v['camera']),cad=cad['identity'],frames=frame_receipts,sources=receipts,historical_index=asset(oldindex),source_isolation=True))
    return dict(case=case,coordinate_frame='VIDEO_LOCAL',frames=frames,sources=sources,transform=np.eye(4),video=v,cad=cad,index=asset(out/'INDEX.json'))

def to_joint(video,M,anchor):
    vv={k:v for k,v in video.items() if k not in ['frames','sources']};vv['transform']=M;vv['coordinate_frame']='JOINT_ANCHOR:'+anchor
    vv['frames']=[];vv['sources']=[]
    for f in video['frames']:
        x=transform_samples(f,M);x['rays']=rays(x['uv'],x['K'],x['C']);x.pop('cad_z',None);vv['frames'].append(x)
    for s in video['sources']:
        x=transform_samples(s,M);x.pop('cad_z',None);x['meta']['source']['T_local_to_common']=M.tolist();x['meta']['coordinate_frame']=vv['coordinate_frame'];vv['sources'].append(x)
    return vv
