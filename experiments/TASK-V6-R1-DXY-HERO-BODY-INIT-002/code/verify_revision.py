"""Verify all independent groups, coordinate isolation, frozen inputs and retained denominators."""
from common import *
from consume_revision import load_configuration,load_views,corrected_source
from geometry import *
from collections import Counter
import csv

def main():
    frozen=read(T/'evidence/FULL_RUN_FREEZE.json');assert frozen['scientific_key']==revision_key();assert frozen['config_sha256']==sha(T/'config.json');asset(frozen['qualification']['path'],frozen['qualification']['sha256'])
    q=read(T/'evidence/REGISTRATION_QUALIFICATION.json');dxy=read(T/'evidence/DXY_FRAME_INDEX.json');assert len(q['groups'])==39 and dxy['completed']==1700 and not dxy['failures']
    failures=[];rows=[];nsteps=0;cuts=0;dependencies={x['path']:x['sha256'] for x in q['source_files']};consumer_check=None
    for group in q['groups']:
        g=group['group'];folder=T/'runs/results'/g;rec=read(folder/'GROUP_RESULT.json');failures+=rec['failures'];a=read(T/'runs/inputs'/g/'AUDIT.json')
        expected={v['case'].rsplit('_',1)[-1] for v in a['videos']}|{c['name'] for c in group['joint_components']}
        assert {r['configuration'] for r in rec['results']}==expected,(g,'CONFIGURATION_ROUTE_MISMATCH')
        for r in rec['results']:
            out=folder/r['configuration'];data=load_configuration(out/'RESULT.json');frames,sources=load_views(r);allowed=set(r['videos'])
            assert {f['case'] for f in frames}==allowed
            assert all(s['meta']['case'] in allowed for s in sources)
            assert {x['source_id'] for x in r['bias']}=={s['meta']['source_id'] for s in sources}
            if len(allowed)==1:assert r['coordinate_frame']=='VIDEO_LOCAL'
            for src in sources:
                np.testing.assert_allclose(src['raw_X'],corrected_points(src['rays'],src['D'],0),atol=1e-8)
                for item in src['meta']['source_files']:dependencies[item['path']]=item['sha256']
            for path in r['source_indices']:
                vi=read(path)
                for it in [vi['camera'],vi['cad'],vi['historical_index']]:dependencies[it['path']]=it['sha256']
                for f in vi['frames']:
                    for k in ['RGB','Mask','DXY','curves','observations_2D']:dependencies[f[k]['path']]=f[k]['sha256']
            for x in r['bias']:assert abs(x['b_mm'])<=x['bound_mm']+1e-8
            for trial in read(out/'STARTS.json')['trials']:
                for log in trial['stages']:
                    assert log['objective_after']<=log['objective_before']+1e-7;nsteps+=1
            for log in read(out/'STAGES.json'):
                assert log['objective_after']<=log['objective_before']+1e-7
            body=data['body'];base=data['base'];assert len(body['F_solid'])==len(body['inferred_base_faces']);assert not body['inferred_base_faces'][:len(body['F'])].any()
            if r['base_applied']:
                pl=np.asarray(base['plane']);assert np.min(body['V'][np.unique(body['F_solid'])]@pl[:3]+pl[3])>=-1e-6;cuts+=1
            if base.get('source_ids'):assert set(base['source_ids'])<={s['meta']['source_id'] for s in sources}
            ev=read(out/'VISIBILITY.json')
            for x in ev['depth']:assert x['fixed_N']==x['valid_N']+x['invalid_N']
            for x in ev['frames']:assert x['foreground_fixed_N']==x['foreground_hit_N']+x['foreground_miss_N']
            assert (out/'RGB_PROJECTIONS.png').exists() and (out/'GEOMETRY_SECTIONS.png').exists()
            if consumer_check is None and sources:
                x=corrected_source(out/'RESULT.json',sources[0]['meta']['source_id']);used=np.unique(x['F']);A=(x['original_V'][used]-x['C'][:3,3])@x['C'][:3,:3];B=(x['V'][used]-x['C'][:3,3])@x['C'][:3,:3];rayerr=np.max(np.abs(A[:,:2]/A[:,2,None]-B[:,:2]/B[:,2,None]));zerr=np.max(np.abs(B[:,2]-A[:,2]+x['bias_mm']));assert rayerr<1e-10 and zerr<1e-10;consumer_check=dict(source=sources[0]['meta']['source_id'],ray_error=rayerr,axial_error=zerr)
            rows.append(dict(group=g,configuration=r['configuration'],videos=r['videos'],coordinate_frame=r['coordinate_frame']))
    for item in read(T/'evidence/DXY_INPUT_INDEX.json')['rows']:
        for path,h in [(item['RGB'],item['RGB_sha256']),(item['Mask'],item['Mask_sha256'])]:dependencies[path]=h
    for p in sorted((T/'runs/dxy').glob('*/*/COMPLETE.json')):
        for item in read(p)['files']:dependencies[item['path']]=item['sha256']
    for p,h in dependencies.items():asset(p,h)
    assert len(rows)==93 and sum(len(r['videos'])==1 for r in rows)==79 and not failures
    with (T/'evidence/PRESERVE_DEPENDENCIES.csv').open('w',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(['path','sha256','policy']);w.writerows((p,h,'RETAIN_READONLY_UPSTREAM_OR_TASK_UNIQUE_PROCESS') for p,h in sorted(dependencies.items()))
    save(T/'evidence/FINAL_VERIFICATION.json',dict(groups=39,videos=79,configurations=len(rows),singles=79,joints=14,failures=failures,monotone_trial_steps=nsteps,clip_checks=cuts,files_rehashed=len(dependencies),DXY_frames=1700,consumer_check=consumer_check,scientific_key=revision_key(),config_sha256=sha(T/'config.json'),results=rows))
    print('VERIFIED',len(rows),len(dependencies),nsteps,flush=True)
if __name__=='__main__':main()
