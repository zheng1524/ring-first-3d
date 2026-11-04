"""Final audit of preserved data and observed outputs; no optimization."""
from postprocess import *
import datetime,platform,importlib.metadata,subprocess

def astats(a):
    d=stats(a);d['median_absolute']=float(np.median(abs(a)))if len(a)else None;return d

def main():
    src=load(R/'assets_index/SOURCES.json');freeze=load(R/'metrics/INPUT_FREEZE.json');checks=[]
    def walk(x):
        if isinstance(x,dict):
            if 'path'in x and'sha256'in x:checks.append(dict(path=x['path'],expected=x['sha256'],actual=sha(x['path'])))
            else:
                for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(src);walk(freeze);assert all(x['actual']==x['expected']for x in checks)
    h,p,m=restore('G01_004');last=dict(np.load(R/'local_results/G01_004/LAST_SAFE.npz'));meshchecks=[]
    for name,cp in [('HISTORICAL',h),('P0',p),('LAST_SAFE',last)]:
        me=trimesh.Trimesh(cp['V'],cp['F'],process=False);rt=mesh_scene(cp['V'],cp['F']);c=cp['V'].mean(0);sd=rt.compute_signed_distance(o3d.core.Tensor(np.array([c,c+[100,0,0]],np.float32))).numpy();shape=shape_quality(cp['V'],cp['F'],h['V'],volume(h['V'],h['F']))
        meshchecks.append(dict(stage=name,watertight=bool(me.is_watertight),winding_consistent=bool(me.is_winding_consistent),positive_volume_mm3=volume(cp['V'],cp['F']),inside_outside_signed_mm=sd,quality_reasons=shape[0],quality=shape[1]));assert me.is_watertight and me.is_winding_consistent and sd[0]<0 and sd[1]>0 and not shape[0]
    pairrows=[];pooled={n:[]for n in ['HISTORICAL','P0','LAST_SAFE']}
    for cid in protocol()['scenes']['G01_004']['P2']:
        o=obs(cid);arrays=[evaluate('G01_004',cp['V'],cp['F'],cid)[1]for cp in [h,p,last]];common=np.logical_and.reduce([ar['pair_hit']for ar in arrays]);pp=o['pairs'][common]
        for name,ar in zip(pooled,arrays):
            err=ar['z'][pp[:,0]]-ar['z'][pp[:,1]]-o['delta'][common];pooled[name].append(err);pairrows.append(dict(source=cid,stage=name,fixed_pair_N=256,joint_common_pair_N=int(common.sum()),**astats(err)))
    table('metrics/COMMON_PAIR_DEPTH.csv',pairrows);save('metrics/COMMON_PAIR_DEPTH.json',dict(fixed_pair_N=7*256,joint_common_pair_N=sum(x['joint_common_pair_N']for x in pairrows if x['stage']=='P0'),pooled={k:astats(np.concatenate(v))for k,v in pooled.items()},proxy='same-source HERO relative axial depth, NOT physical GT'))
    updates=load(R/'metrics/ALL_UPDATE_PROPOSALS.json');stop=load(R/'metrics/STOP_STATUS.json');assert len(updates)==10 and sum(x['accepted']for x in updates)==1 and stop['no_further_optimization_scheduled']
    for x in updates:
        if x['accepted']:assert not x['collision']['collision']and not x['geometry']['folded_face_N']
    assert not(R/'local_results/G01_004/P2.npz').exists()and not(R/'local_results/G06_004').exists()
    frozen=load(R/'metrics/IMPLEMENTATION_FREEZE.json');sourcechecks=[]
    for item in frozen['source_files']:
        f=REPO/item['path'] if not Path(item['path']).is_absolute()else Path(item['path']);sourcechecks.append(dict(path=str(f),frozen_sha256=item['sha256'],current_sha256=sha(f),equal=sha(f)==item['sha256']))
    changed=[x for x in sourcechecks if not x['equal']];assert len(changed)==1 and changed[0]['path'].endswith('/code/run.py')
    started=datetime.datetime.fromisoformat((R/'runtime/formal_started.txt').read_text().strip());ended=datetime.datetime.fromtimestamp((R/'metrics/STOP_STATUS.json').stat().st_mtime,started.tzinfo)
    env=dict(Python=platform.python_version(),platform=platform.platform(),CPU=Path('/proc/cpuinfo').read_text().split('model name')[1].splitlines()[0].split(':',1)[1].strip(),packages={n:importlib.metadata.version(n)for n in ['numpy','scipy','torch','trimesh','python-fcl']},Open3D=o3d.__version__,Blender='5.0.1 a3db93c5b259',GPU_used=False,formal_started=started.isoformat(),formal_stop_written=ended.isoformat(),wall_seconds=(ended-started).total_seconds())
    save('metrics/ENVIRONMENT.json',env);save('metrics/FINAL_INTEGRITY.json',dict(asset_sha_checks=checks,all_source_SHA_unchanged=True,mesh_checks=meshchecks,stop_exactly_at_10_candidates=True,stage_P2_and_second_case_NOT_RUN=True,source_hashes=sourcechecks,post_stop_source_difference='run.py filename-only output fix; no optimization rerun',GT='NOT_EVALUABLE',MRE='NOT_EVALUABLE',data_used_to_choose_algorithm=False))
    local=[asset(x)for folder in ['inputs','local_results']for x in sorted((R/folder).rglob('*'))if x.is_file()];save('assets_index/LOCAL_RESULTS.json',dict(files=local,large_outputs_uploaded=False,coordinates='NPZ/PLY millimetres; GLB metres',final_mesh=str(R/'local_results/G01_004/LAST_SAFE.ply'),no_false_P2_output=True));print('INTEGRITY',len(checks),'hashes PASS; preserved last safe geometry; no further run',flush=True)

if __name__=='__main__':main()
