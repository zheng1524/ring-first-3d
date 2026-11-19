"""Full-path, input identity, fairness, isolation and resume acceptance."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
from PIL import Image
import pipeline as p
import run,standard
from ring_first_3d.mainline.native.io import save_json,sha256
from ring_first_3d.mainline.native.geometry import unproject
T=p.TASK

def main():
    p.verify();run.freeze_code();standard.freeze();assert p.read(T/'logs/TESTS.json')['status']=='PASS'
    # Historical reports, predictions, source and selected evidence are immutable.
    original=p.read(p.OLD/'RUN_MANIFEST.json');verified=0
    for r in original['files']:
        f=Path(r['path']);assert f.is_file() and sha256(f)==r['sha256'],r['relative'];verified+=1
    for r in p.read(T/'audit/MATURE_CALIBRATION_SOURCE_LOCK.json')['files']:assert sha256(r['copy'])==r['sha256'] and sha256(r['original'])==r['sha256']
    source_versions=list(csv.DictReader((T/'audit/VERSION_SOURCES.csv').open()))
    for r in source_versions:assert sha256(r['path'])==r['sha256'],r['path']
    held={v['meta']['RGB_content_sha'] for v in p.views() if v['meta']['role']!='FIT'};banks=[];camera_pass=0;hero_count=0;fair=[];new_bodies=0
    for freeze in (T/'audit/REFERENCE_DENSITY_REV2').glob('G*/005/INPUT_FREEZE.json'):
        data=p.read(freeze);g=freeze.parents[1].name;assert data['Body_views_unchanged']==[v['meta']['id'] for v in p.instance_views(g,'005') if v['meta']['role']=='FIT']
        for v in data['calibration_views']:
            a=p.check_input(v);assert v['meta']['role']=='FIT' and v['meta']['video']=='005';assert p.arraysha(a['RGB']) not in held
            for k,mk in [('RGB_source','RGB_sha'),('Mask_source','Mask_sha')]:
                if v['meta'].get(mk):assert sha256(v['meta'][k])==v['meta'][mk]
    assert p.read(T/'audit/CLI_RESUME_VALIDATION.json')['all_SHA256_unchanged']
    for c in p.cases():
        g=c['case']
        for vi in ['004','005']:
            root=p.OLD/'runs/RF_ONLY_V1'/g/vi if p.inherited(g,vi) else p.OUT/g/vi;bank=p.read(p.OUT/g/vi/'bank/ADMISSION.json')
            assert bank['status']=='PASS','All ten banks must now be constructed or explicitly reclassified'
            assert sha256(bank['bank'])==bank['sha256']
            for ref in bank.get('reference_RGB',[]):
                assert ref['role']=='FIT' and ref['video']==vi;assert sha256(ref['RGB_source'])==ref['sha256'];assert ref['pixel_sha256'] not in held
            banks.append(dict(group=g,video=vi,bank=bank['bank'],points=bank.get('points'),execution=bank['execution']))
            for v in p.instance_views(g,vi):
                d=root/'camera'/v['meta']['id'];new=p.OUT/g/vi/'camera'/v['meta']['id']
                if (new/'ADMISSION.json').exists():d=new
                ad=p.read(d/'ADMISSION.json')
                if ad['status']=='PASS':
                    r=p.read(d/'CAMERA_RESULT.json');assert r['candidate_source']=='originalRF5DoF_RGB_yaw' and not r.get('PnP_used_as_final_camera',False);assert r['ring_boundary_MAE_px']<=3.
                    original=p.read(d/'ALL_CANDIDATES.json') if (d/'ALL_CANDIDATES.json').exists() else p.read(r['original_result']);legal=[q for q in original['candidates'] if q['source']=='originalRF5DoF_RGB_yaw'];chosen=min(legal,key=lambda q:q['FIT_objective']);assert np.array_equal(np.array(chosen['C']),np.array(r['c2w_mm']));camera_pass+=1
            for d in root.glob('hero/*'):
                if not (d/'ADMISSION.json').exists() or p.read(d/'ADMISSION.json')['status']!='PASS':continue
                native=dict(np.load(d/'HERO_native.npz'));mesh=dict(np.load(d/'RAW_NATIVE_MESH.npz'));uv=mesh['uv'];X=unproject(native['depth_mm'][uv[:,1],uv[:,0]],native['reference_pose_mm'],uv,native['K_index_native']);assert np.max(abs(X-mesh['V']))<1e-5;assert not p.read(d/'INFERENCE.json')['reused_historical_depth'];source=p.read(d/'SOURCE.json')
                for cid in source['frames']:
                    v=next(v for v in p.views() if v['meta']['id']==cid);assert v['meta']['case']==g and v['meta']['video']==vi and v['meta']['role']=='FIT'
                for receipt in source['camera_results']:assert sha256(receipt['path'])==receipt['sha256']
                assert np.array_equal(native['reference_pose_mm'],np.array(p.read(source['camera_results'][0]['path'])['c2w_mm']))
                assert sha256(d/'SOURCE.json')==p.read(d/'ADMISSION.json')['source_SHA256'];hero_count+=1
            if p.inherited(g,vi):continue
            armroot=root/'body'
            if not all((armroot/a/'TASK_PREDICTION_FROZEN.json').exists() for a in ['B1','B2']):continue
            a=p.read(armroot/'CONTRACT_B1/RUN_FREEZE.json');b=p.read(armroot/'CONTRACT_B2/RUN_FREEZE.json');reference=p.read(p.OLD/'runs/RF_ONLY_V1/G01/004/body/CONTRACT_B1/RUN_FREEZE.json')
            assert a['configuration']==b['configuration']==reference['configuration'];assert a['adapter_sha256']==b['adapter_sha256']==reference['adapter_sha256'];assert a['initial']==b['initial']==c['initial'];assert a['views']==b['views'];assert not a['depth_enabled'] and b['depth_enabled'];assert a['depth_lambda']==b['depth_lambda']==.01;assert a['video']==b['video']==vi
            expected={v['meta']['id'] for v in p.instance_views(g,vi) if v['meta']['role']=='FIT'};assert {v['id'] for v in a['views']}==expected
            for view in a['views']:assert np.array_equal(np.array(view['C']),np.array(p.read(root/'camera'/view['id']/'CAMERA_RESULT.json')['c2w_mm']))
            initial=dict(np.load(c['initial']['path']))
            for arm in ['B1','B2']:
                folder=armroot/arm;f=p.read(folder/'TASK_PREDICTION_FROZEN.json');assert sha256(folder/'FINAL.npz')==f['sha256'];assert np.array_equal(np.load(folder/'INITIAL.npz')['V'],initial['V']);assert len(p.read(folder/'UPDATES.json')['iterations'])==36;contract=p.read(folder/'INPUT_CONTRACT.json');assert not contract['camera_optimized'] and not contract['GT_read'] and set(contract['FIT'])==expected
            fair.append(dict(group=g,video=vi,optimizer_identical_to_G01_004=True,only_depth_enabled_differs=True,FIT_count=8,GT_not_used=True));new_bodies+=1
    freeze=p.read(p.OUT/'ALL_PREDICTIONS_FROZEN_BEFORE_GT.json');assert freeze['all_new_training_complete']
    for r in freeze['records']:
        if r['path']:assert sha256(r['path'])==r['sha256'],'World prediction changed after GT'
    for r in csv.DictReader((T/'report/PIPELINE_STAGE_RECORDS.csv').open()):
        assert r['Status'] in ['PASS','PARTIAL','FAIL','NOT_RUN']
        if r['Status']=='PASS':
            for key in ['Input','Output','SourceVersion','Log','Evidence','Protocol']:assert r[key] and Path(r[key]).exists(),(r['Group'],r['Video'],r['Stage'],key)
    # No new prediction is permitted for a video with an incomplete FIT camera set.
    for g in p.GROUPS:
        for vi in ['004','005']:
            if p.inherited(g,vi):continue
            fit=[v for v in p.instance_views(g,vi) if v['meta']['role']=='FIT'];valid=all(p.read(p.OUT/g/vi/'camera'/v['meta']['id']/'ADMISSION.json')['status']=='PASS' for v in fit)
            if not valid:assert not any((p.OUT/g/vi/'body'/a/'TASK_PREDICTION_FROZEN.json').exists() for a in ['B1','B2'])
    pngs=list((T/'visualization').rglob('*.png'));assert len(pngs)>=150
    for q in pngs:
        with Image.open(q) as im:im.verify()
    assert not list(T.rglob('*.html')) and not list(T.rglob('*.js'))
    raw=p.read(T/'audit/RAW_DATA_INVENTORY.json');z=raw['ZIP'];f=Path(z['path']);assert f.stat().st_size==z['size'] and f.stat().st_mtime_ns==z['mtime_ns'];assert sha256(f)==z['sha256']
    for r in raw['files']:
        f=Path(r['path']);assert f.stat().st_size==r['size'] and f.stat().st_mtime_ns==r['mtime_ns']
    for name in ['TASK.yaml','TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json','audit/INPUT_FREEZE.json','report/PIPELINE_COMPLETENESS.csv','visualization/README.md']:assert (T/name).is_file(),name
    size=sum(f.stat().st_size for f in T.rglob('*') if f.is_file());assert size<2147483648,size
    result=dict(status='PASS',scientific_pipeline_status=p.read(T/'metrics/SUMMARY.json')['status'],engineering_acceptance_not_reconstruction_accuracy=True,tests=p.read(T/'logs/TESTS.json'),historical_001_files_unchanged=verified,bank_count=len(banks),camera_PASS=camera_pass,HERO_including_frozen_reference=hero_count,new_body_instances=new_bodies,fair_ablation=fair,PNG_files=len(pngs),ZIP_SHA256_unchanged=True,world_predictions_unchanged=True,all_PASS_paths_exist=True,HTML=False,output_bytes=size);save_json(T/'ARTIFACT_VALIDATION.json',result)
    exclusions={'RUN_MANIFEST.json','DELIVERY_COMMIT.json'};files=[]
    for f in sorted(T.rglob('*')):
        if not f.is_file() or f.name in exclusions or '__pycache__' in f.parts or f==T/'logs/ARTIFACT_CHECK.log':continue
        files.append(dict(path=str(f.resolve()),relative=str(f.relative_to(T)),bytes=f.stat().st_size,sha256=sha256(f)))
    save_json(T/'RUN_MANIFEST.json',dict(task_id=T.name,scientific_status=result['scientific_pipeline_status'],source_baseline_commit='2fe2c3cbda40bd4d0f8a15a3d71dad3f494a1c7f',workspace=str(p.ROOT),branch='exp/'+T.name,visualization=str((T/'visualization').resolve()),static_index=str((T/'visualization/README.md').resolve()),explicit_exclusions=['self manifest','post-commit DELIVERY_COMMIT.json','still-open logs/ARTIFACT_CHECK.log','runtime __pycache__'],files=files))
    print('ARTIFACT_ACCEPTANCE_PASS',len(files),'files;',len(pngs),'PNG;',new_bodies,'new Body videos',flush=True)
if __name__=='__main__':main()
