"""Cumulative reversible ID ledger and exact restoration from original observations."""
from common import *
import argparse
def export_ledger():
    out=[]
    for scene,ii in protocol()['orders'].items():
        for cid in ii:
            n=native(cid);p=np.load(R/'frozen_inputs/native'/(cid+'.npz'));pixel=np.flatnonzero(n['valid']&~p['valid']);u,v=pixel%n['depth'].shape[1],pixel//n['depth'].shape[1];uv=np.c_[u,v];xyz=unproject(n['depth'][v,u].astype(float),n['T'],uv,n['Kn'])
            for k,pid in enumerate(pixel):out.append(dict(scene=scene,source=cid,original_native_pixel_ID=int(pid),native_u=int(u[k]),native_v=int(v[k]),X_mm=float(xyz[k,0]),Y_mm=float(xyz[k,1]),Z_mm=float(xyz[k,2]),original_HERO_Z_mm=float(n['depth'].flat[pid]),phase='HISTORICAL_ACCEPTED_V6'if p['historical_excluded'].flat[pid]else'CURRENT_FIXED_A2_AND_B',original_HERO_modified=False))
    table('metrics/CUMULATIVE_INPUT_SUPPRESSION.csv',out);print('CUMULATIVE_LEDGER',len(out))
def restore():
    assert not (R/'frozen_inputs').exists(),'DO_NOT_OVERWRITE_FROZEN_INPUTS_USE_ISOLATED_REPLAY'
    ledger=rows(R/'metrics/CUMULATIVE_INPUT_SUPPRESSION.csv');checks=[]
    for row in protocol()['input_geometry']:
        cid=row['source'];n=native(cid);historical=np.zeros(n['depth'].shape,bool);incremental=historical.copy()
        for x in ledger:
            if x['source']!=cid:continue
            pid=int(x['original_native_pixel_ID']);assert n['valid'].flat[pid];assert float(n['depth'].flat[pid])==float(x['original_HERO_Z_mm'])
            target=historical if x['phase']=='HISTORICAL_ACCEPTED_V6'else incremental;target.flat[pid]=True
        assert not (historical&incremental).any();valid=n['valid']&~historical&~incremental;depth=np.where(valid,n['depth'],0).astype(np.float32);path=R/'frozen_inputs/native'/(cid+'.npz');path.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(path,depth_mm=depth,valid=valid,original_native_id=np.arange(depth.size).reshape(depth.shape),historical_excluded=historical,incremental_excluded=incremental)
        assert sha(path)==row['native']['sha256'],('NATIVE_SERIALIZATION_NOT_IDENTICAL',cid)
        s=cleaned(cid);cp=make_crop(s);path2=R/'frozen_inputs/crops'/(cid+'.npz');path2.parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path2,**cp);assert sha(path2)==row['crop']['sha256'],('CROP_SERIALIZATION_NOT_IDENTICAL',cid)
        checks.append(dict(source=cid,native_SHA_exact=True,crop_SHA_exact=True,native_N=int(valid.sum()),from_original_HERO_and_ID_ledger=True))
    save('provenance/RESTORE_INPUTS_CHECK.json',dict(status='PASS',sources=checks,raw_HERO_modified=False,new_GPU_forwards=0));print('RESTORED_EXACT',len(checks),'sources /26 derived files; no GPU')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--export-ledger',action='store_true');a=parser.parse_args();export_ledger()if a.export_ledger else restore()
