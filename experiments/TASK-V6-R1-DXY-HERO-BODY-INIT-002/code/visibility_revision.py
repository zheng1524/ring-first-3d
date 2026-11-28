"""Post-freeze actual triangle visibility and fixed-domain depth evidence."""
from common import *
from consume_revision import load_configuration,load_views
from observations import scene,cast,o3d,cv2,CFG
from geometry import *
import argparse

def evaluate_mesh(folder):
    folder=Path(folder);data=load_configuration(folder/'RESULT.json');r=data['record'];body=data['body'];frames,sources=load_views(r);cad=np.load(r['cad']['path']);cadscene=scene(cad['V'],cad['F']);bs=scene(body['V'],body['F_solid']);tol=CFG['cad_tolerance_mm']
    key=digest([sha(folder/'BODY.npz'),sha(folder/'RESULT.json'),sha(Path(__file__)),sha(T/'config.json')])
    if (folder/'VISIBILITY.json').exists() and read(folder/'VISIBILITY.json').get('key')==key:
        for it in read(folder/'VISIBILITY.json')['files']:asset(it['path'],it['sha256'])
        return read(folder/'VISIBILITY.json')
    records=[];visible=[];compatible=[]
    for f in frames:
        lab=cv2.imread(f['Mask'],0);yy,xx=np.mgrid[:lab.shape[0],:lab.shape[1]];uv=np.c_[xx.ravel(),yy.ravel()];rr=rays(uv,f['K'],f['C']);z,fid=cast(bs,rr);cz,_=cast(cadscene,rr)
        valid=np.isfinite(z)&(fid>=0)&(fid<len(body['F_solid']))&(z<cz-tol);target=lab.ravel()==1;known=lab.ravel()!=2;pred=valid&known
        vf=np.zeros(len(body['F_solid']),bool);cf=vf.copy();vf[fid[valid]]=True;cf[fid[valid&target]]=True;visible.append(vf);compatible.append(cf)
        records.append(dict(case=f['case'],frame=f['id'],role=f['role'],full_canvas_N=lab.size,foreground_fixed_N=int(target.sum()),foreground_hit_N=int((target&pred).sum()),foreground_miss_N=int((target&~pred).sum()),false_positive_N=int((~target&pred).sum()),full_mesh_IoU=float((target&pred).sum()/max(1,(target|pred).sum())),cap_pixels_N=int(body['inferred_base_faces'][fid[valid]].sum())))
    plane=np.array(data['base']['plane']) if r['base_applied'] else None;depth=[];bias={x['source_id']:x['b_mm'] for x in r['bias']}
    for s in sources:
        z,fid=cast(bs,s['rays']);cz,_=cast(cadscene,s['rays']);finite=np.isfinite(z)&(fid>=0)&(fid<len(body['F_solid']));cap=np.zeros(len(z),bool);cap[finite]=body['inferred_base_faces'][fid[finite]];hit=finite&~cap&(z<cz-tol);b=bias[s['meta']['source_id']];err=np.abs(z[hit]+b-s['D'][hit]);az,ah,ac=clipped_depth(np.array(r['p']),s['rays'],plane);both=finite&~cap&ah;delta=np.abs(z[both]-az[both]);corrected=s['D']-b
        depth.append(dict(source_id=s['meta']['source_id'],fixed_N=len(z),valid_N=int(hit.sum()),invalid_N=int((~hit).sum()),cap_only_N=int(cap.sum()),MAE_mm=float(err.mean()) if len(err) else None,p95_mm=float(np.percentile(err,95)) if len(err) else None,analytic_mesh_p95_mm=float(np.percentile(delta,95)) if len(delta) else None,original_CAD_conflict_N=int((s['D']>=cz-tol).sum()),corrected_CAD_conflict_N=int((corrected>=cz-tol).sum()),corrected_negative_Z_N=int((corrected<=0).sum())))
    signed=cadscene.compute_signed_distance(o3d.core.Tensor(body['V'].astype(np.float32)),nthreads=1).numpy()
    np.savez_compressed(folder/'VISIBILITY.npz',visible_model_faces_by_frame=np.array(visible),Mask_compatible_model_faces_by_frame=np.array(compatible),inferred_base_faces=body['inferred_base_faces'])
    result=dict(key=key,frames=records,depth=depth,CAD_inside_vertex_N=int((signed<0).sum()),CAD_beyond_tolerance_vertex_N=int((signed< -tol).sum()),CAD_penetration_max_mm=float(max(0,-signed.min())),CAD_check='vertices only, not exhaustive triangle collision',GT='NOT_EVALUABLE',files=[asset(folder/'VISIBILITY.npz')]);save(folder/'VISIBILITY.json',result);return result

if __name__=='__main__':
    pa=argparse.ArgumentParser();pa.add_argument('--group');args=pa.parse_args()
    for group in sorted((T/'runs/results').glob('*/GROUP_RESULT.json')):
        if args.group and group.parent.name!=args.group:continue
        for r in read(group)['results']:evaluate_mesh(group.parent/r['configuration'])
        print('VISIBILITY',group.parent.name,flush=True)
