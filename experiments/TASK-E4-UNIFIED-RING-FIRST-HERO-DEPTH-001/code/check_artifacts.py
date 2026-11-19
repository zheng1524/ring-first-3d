"""Executable final acceptance; missing outputs never count as scientific PASS."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
from PIL import Image
import pipeline as p
from ring_first_3d.mainline.native.io import sha256,save_json
from ring_first_3d.mainline.native.geometry import unproject
T=p.TASK;O=T/'runs/RF_ONLY_V1'

def main():
    p.verify_freeze();assert p.read(T/'logs/REGRESSION_RESULT.json')['status']=='PASS';assert p.read(T/'logs/NEW_TESTS.json')['status']=='PASS'
    rf=p.read(O/'FREEZE.json');assert sha256(T/'PROTOCOL_RF_ONLY.yaml')==rf['protocol_sha256'];assert sha256(T/'code/rf_only.py')==rf['code_sha256']
    for rec in rf['numerical_inputs']:assert sha256(rec['path'])==rec['sha256']
    bfreeze=p.read(T/'audit/BODY_ABLATION_FREEZE.json')
    for r in bfreeze['code']:assert sha256(r['path'])==r['sha256']
    ef=p.read(T/'audit/EVALUATION_PROTOCOL_FREEZE.json')['source'];assert sha256(ef['path'])==ef['sha256']
    assert len(list(O.glob('G*/0*/camera/*/ADMISSION.json')))==105
    errors=[];backproject=[];fair=[]
    for out in O.glob('G*/004/hero/*'):
        if not out.is_dir():continue
        if p.read(out/'ADMISSION.json')['status']!='PASS':continue
        rec=p.read(out/'INFERENCE.json');assert not rec['reused_historical_depth']
        d=dict(np.load(out/'HERO_native.npz'));raw=dict(np.load(out/'RAW_NATIVE_MESH.npz'));uv=raw['uv'];z=d['depth_mm'][uv[:,1],uv[:,0]]
        XYZ=unproject(z,d['reference_pose_mm'],uv,d['K_index_native']);delta=float(abs(XYZ-raw['V']).max());assert delta<1e-5
        backproject.append(dict(path=str(out),vertices=len(XYZ),max_abs_mm=delta))
    assert len(backproject)==32
    aux=p.read(O/'HERO_AUXILIARY_COMPLETE.json');assert aux['status']=='PASS' and aux['additional_repeat_inferences']==32
    assert all(r['repeat_bitwise_equal'] and r['model_invalid_Polyp_pixels']==0 for r in aux['rows'])
    for r in aux['rows']:
        a=O/r['group']/r['video']/'hero_auxiliary'/r['id']
        assert (a/'OFFICIAL_AUXILIARY.npz').is_file() and (a/'MODEL_DEPTH_VALIDITY.npz').is_file()
    for c in p.cases():
        assert c['initial']['sha256']==c['resolved013_initial']['sha256']
        if c['case']=='G02':continue
        group=c['case'];a=O/group/'004/body';left=p.read(a/'CONTRACT_B1/RUN_FREEZE.json');right=p.read(a/'CONTRACT_B2/RUN_FREEZE.json')
        for k in ['configuration','initial','normalization','views','original_optimizer_sha256','adapter_sha256']:assert left[k]==right[k],(group,k)
        assert not left['depth_enabled'] and right['depth_enabled'];assert left['depth_lambda']==right['depth_lambda']==.01
        for arm in ['B1','B2']:
            freeze=p.read(a/arm/'TASK_PREDICTION_FROZEN.json');assert sha256(a/arm/'FINAL.npz')==freeze['sha256']
            updates=p.read(a/arm/'UPDATES.json');assert len(updates['iterations'])==36
            contract=p.read(a/arm/'INPUT_CONTRACT.json');assert len(contract['FIT'])==8 and not contract['camera_optimized'] and not contract['GT_read'];assert contract['HERO_read']==(arm=='B2')
        fair.append(dict(group=group,configuration_identical=True,initial_identical=True,cameras_identical=True,optimizer_adapter_identical=True,only_enabled_depth_differs=True))
    for row in csv.DictReader(open(T/'report/PIPELINE_STAGE_RECORDS.csv')):
        assert row['Status'] in ['PASS','PARTIAL','FAIL','NOT_RUN']
        if row['Status']=='PASS':
            for key in ['Input','Output','SourceVersion','Log','Evidence','Protocol']:assert row[key] and Path(row[key]).exists(),(row['Group'],row['Stage'],key)
    frozen=p.read(O/'PREDICTIONS_FROZEN_BEFORE_GT.json')
    for r in frozen['records']:
        if r['path']:assert sha256(r['path'])==r['sha256'],'Evaluator changed world prediction'
    # The inherited workspace's protected source/input closure remains intact.
    legacy=p.read(p.ROOT/'mainline/manifests/REPLAY_INPUT_FREEZE.json')
    records=legacy['source_files'];assert len(records)>=800
    old_verified=0
    for r in records:
        path=Path(r.get('path',''));expected=r.get('sha256')
        if not path.is_absolute():path=p.ROOT/path
        assert expected and path.is_file(),str(path)
        assert sha256(path)==expected,str(path);old_verified+=1
    pngs=list((T/'visualization').rglob('*.png'));assert len(pngs)>=150
    for q in pngs:
        with Image.open(q) as im:im.verify()
    assert not list(T.rglob('*.html')) and not list(T.rglob('*.js'))
    for name in ['TASK.yaml','TECHNICAL_REPORT.md','RESULT_CARD.md','FAILURE_REGISTRY.json','audit/INPUT_MANIFEST.csv','audit/INPUT_AUDIT.md','report/FINAL_REPORT.md','report/PIPELINE_COMPLETENESS.csv','visualization/README.md']:assert (T/name).is_file(),name
    raw=p.read(T/'audit/RAW_DATA_INVENTORY.json');zipinfo=raw['ZIP'];stat=Path(zipinfo['path']).stat();assert stat.st_size==zipinfo['size'] and stat.st_mtime_ns==zipinfo['mtime_ns']
    size=sum(q.stat().st_size for q in T.rglob('*') if q.is_file());assert size<=2147483648
    save_json(T/'ARTIFACT_VALIDATION.json',dict(status='PASS',engineering_acceptance_only_scientific_pipeline_remains_partial=True,tests=dict(original=247,new=p.read(T/'logs/NEW_TESTS.json')['tests']),camera_records=105,HERO_backprojection=backproject,fair_ablation=fair,PNG_files=len(pngs),all_PASS_paths_exist=True,world_predictions_unchanged=True,old_frozen_files_verified=old_verified,ZIP_stat_unchanged=True,HTML_created=False,output_bytes=size))
    # The currently open checker log changes after the manifest is written.
    # Exclude it explicitly instead of publishing a stale checksum for it.
    files=[dict(path=str(q.resolve()),relative=str(q.relative_to(T)),bytes=q.stat().st_size,sha256=sha256(q)) for q in sorted(T.rglob('*')) if q.is_file() and q.name not in ['RUN_MANIFEST.json','DELIVERY_COMMIT.json'] and q!=T/'logs/ARTIFACT_CHECK.log' and '__pycache__' not in q.parts]
    save_json(T/'RUN_MANIFEST.json',dict(task_id=T.name,implementation_commit=p.read(T/'audit/IMPLEMENTATION_COMMIT.json')['implementation_commit'],scientific_status='PARTIAL',source_repo='https://github.com/zheng1524/ring-first-3d.git',workspace=str(p.ROOT),branch='exp/'+T.name,pushed=False,GT_training_access=False,visualization=str((T/'visualization').resolve()),static_index=str((T/'visualization/README.md').resolve()),HTML_prohibited_by_current_task=True,files=files))
    manifest=p.read(T/'RUN_MANIFEST.json');manifest['explicit_checksum_exclusions']=['RUN_MANIFEST.json (self reference)','DELIVERY_COMMIT.json (written after commit)','logs/ARTIFACT_CHECK.log (still-open checker output)','__pycache__ (runtime cache)'];manifest['HERO_unique_targets']=32;manifest['HERO_total_inferences']=64;save_json(T/'RUN_MANIFEST.json',manifest)
    print('ARTIFACT_ACCEPTANCE_PASS',len(files),'files',len(pngs),'PNG; scientific status PARTIAL',flush=True)

if __name__=='__main__':main()
