"""Read-only Open3D comparison; never a prediction input or new TSDF run."""
from common import *
from evaluate import observations,full_p95
def main():
    path=D0/'previews/G1_mm.glb';ALLOWED.add(str(path.resolve()));m=trimesh.load(path,force='mesh',process=False);ds=mesh_scene(m.vertices,m.faces);rr=[];ff=[]
    for cid in protocol()['orders']['G01_004']:
        s=observations(cid);hit,_=cast(ds,s['native_uv'],s['Kn'],s['T']);v=s['visible'];e=hit-s['z'];ok=v&np.isfinite(hit);p95,status=full_p95(e[v]);d=distance(ds,s['X'])
        rr.append(dict(source=cid,fixed_native_N=len(hit),CAD_visible_N=int(v.sum()),hit_N=int(ok.sum()),miss_N=int((v&~np.isfinite(hit)).sum()),agree_N=int((ok&(abs(e)<=.25)).sum()),hit_only_error_mm=stats(e[ok]),p95_including_misses_mm=p95,p95_status=status,point_retention_0p25=float((d[v]<=.25).mean())))
        a=original(cid);dr=distance(ds,a['P'][a['F']].mean(1));ff.append(dict(source=cid,original_face_N=len(a['F']),original_area_mm2=float(a['area'].sum()),area_retention_0p25=float(a['area'][dr<=.25].sum()/a['area'].sum())))
    denom=sum(a['CAD_visible_N']for a in rr);area=sum(a['original_area_mm2']for a in ff)
    result=dict(method='HISTORICAL_OPEN3D_D0_G1',scene='G01_004',asset=asset(path),voxel_mm=.1,input_source_N=6,inputs='original native, pre-A2 cleanup, not matched to new8 or newdomain',fixed_visible_N=denom,hit_fraction=sum(a['hit_N']for a in rr)/denom,agree_fraction=sum(a['agree_N']for a in rr)/denom,Raw_area_retention=sum(a['original_area_mm2']*a['area_retention_0p25']for a in ff)/area,mesh_area_mm2=float(m.area),rays=rr,raw_faces=ff,geometry_used_for_new_prediction=False,new_TSDF_run=False,GT=False)
    save('metrics/HISTORICAL_OPEN3D_COMPARISON.json',result);table('metrics/HISTORICAL_OPEN3D_RAYS.csv',rr);print('HISTORICAL_COMPARISON',result['agree_fraction'],flush=True)
if __name__=='__main__':main()
