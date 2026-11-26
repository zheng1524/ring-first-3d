"""Cohort authorization, A-priority resource checks, and existing-stage orchestration."""
import os
from pathlib import Path
import subprocess
import time


def authorized_cases(cohort):
    from .run import CASES
    from ring_first_3d.v6_raw.route import GROUPS
    if cohort=='pilot':return list(CASES)
    if cohort=='expanded':return [g+'_'+v for g in GROUPS for v in ['004','005']]
    raise ValueError('UNKNOWN_COHORT')


def inference_limit(cohort):
    if cohort=='pilot':return 8
    if cohort=='expanded':return 40
    raise ValueError('UNKNOWN_COHORT')


def active_priority_jobs(proc_root=Path('/proc'),own_pid=None):
    own_pid=os.getpid() if own_pid is None else own_pid
    found=[]
    for p in Path(proc_root).iterdir():
        if not p.name.isdigit() or int(p.name)==own_pid:continue
        try:args=(p/'cmdline').read_bytes().decode(errors='replace').split('\0')
        except (OSError,PermissionError):continue
        if 'ring_first_3d.v6_raw.full_run' in args and any(x in args for x in ['run','worker']):
            found.append(dict(pid=int(p.name),command=' '.join(args).strip()))
    return found


def verify_s_cache(case):
    from .run import BASE,read,sha
    root=BASE/case/'S';r=read(root/'receipt.json')
    assert r['status'] in ['COMPLETED','NOT_EVALUABLE'],'PRIOR_S_FAILED_NEEDS_INSPECTION'
    for p,h in r['input_sha256'].items():assert sha(p)==h,'S_INPUT_DRIFT '+p
    for p,h in r['outputs_sha256'].items():assert sha(p)==h,'S_OUTPUT_DRIFT '+p
    return r


def batch(phase,cases=None,source_hashes=None):
    from .run import BASE,WT,PY,read,save,verify_common,sha
    cases=cases or authorized_cases('expanded')
    logroot=BASE/'logs_expanded';logroot.mkdir(parents=True,exist_ok=True)
    ledger=BASE/('EXPANSION_'+phase.upper()+'_STATUS.json')
    state=read(ledger) if ledger.exists() else dict(phase=phase,cases={},started_epoch=time.time())
    stages=['prepare','R','S','evaluate','poses','ring'] if phase=='cpu' else ['hero']
    for case in cases:
        if source_hashes:verify_queue_sources(source_hashes)
        print('EXPANSION_CASE',phase,case,flush=True)
        state['cases'][case]=dict(status='RUNNING',stages=[]);save(ledger,state)
        for stage in stages:
            root=BASE/case;reuse=False
            if stage=='S' and (root/'S/receipt.json').exists():verify_s_cache(case);reuse=True
            if stage=='evaluate' and (root/'CAMERA_RESULTS.json').exists():
                verify_common(case)
                for arm in ['R','S']:
                    r=read(root/arm/'receipt.json')
                    if arm=='R':assert sha(root/arm/'cameras.npz')==r['camera_sha256']
                    else:verify_s_cache(case)
                reuse=True
            if stage=='hero' and (root/'HERO_DEPTH_RESULTS.json').exists():
                finished=all((root/a/'hero/RESULT.json').exists() and read(root/a/'hero/RESULT.json')['status']=='COMPLETED' for a in ['R','S'])
                if finished:
                    for arm in ['R','S']:
                        for path,h in read(root/arm/'hero/RESULT.json')['outputs'].items():assert sha(path)==h,'HERO_OUTPUT_DRIFT '+path
                    reuse=True
            if source_hashes:verify_queue_sources(source_hashes)
            if reuse:code=0
            else:
                cmd=[PY,str(WT/'tools/ring_sift_comparison.py'),'--cohort','expanded','--case',case,'--stage',stage]
                log=logroot/(case+'_'+stage+'.log')
                with log.open('a') as f:code=subprocess.call(cmd,cwd=WT,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1'))
            if source_hashes:verify_queue_sources(source_hashes)
            state['cases'][case]['stages'].append(dict(stage=stage,returncode=code,reused=reuse))
            if code:
                state['cases'][case]['status']='FAILED_STAGE';state['cases'][case]['failed_stage']=stage;break
            save(ledger,state)
        else:state['cases'][case]['status']='COMPLETED'
        if phase=='hero':
            state['cases'][case]['arm_statuses']={a:read(BASE/case/a/'hero/RESULT.json')['status'] if (BASE/case/a/'hero/RESULT.json').exists() else 'NOT_EXECUTED' for a in ['R','S']}
            if state['cases'][case]['status']!='FAILED_STAGE' and any(s=='NOT_EXECUTED_GPU_BUSY' for s in state['cases'][case]['arm_statuses'].values()):state['cases'][case]['status']='QUEUED_A_PRIORITY'
        save(ledger,state)
    state['finished_epoch']=time.time();save(ledger,state)
    print('EXPANSION_BATCH_COMPLETE',phase,{k:v['status'] for k,v in state['cases'].items()},flush=True)
    return state


def verify_queue_sources(hashes):
    from .run import sha
    for path,digest in hashes.items():
        if not Path(path).exists() or sha(path)!=digest:raise RuntimeError('QUEUED_SOURCE_DRIFT: '+path)


def classify_hero_batch(result):
    states=[x['status'] for x in result['cases'].values()]
    if 'FAILED_STAGE' in states:return 'FAILED_STAGE_NO_RETRY'
    if 'QUEUED_A_PRIORITY' in states:return 'WAITING_FOR_GPU'
    return 'FINISHED'


def gpu_queue(max_wait_seconds=86400,poll_seconds=30):
    """One-shot local queue: await A, run remaining frozen tuples, refresh local report."""
    import fcntl
    import traceback
    from .run import BASE,REPORT,read,save,sha,WT
    state_path=BASE/'EXPANSION_GPU_QUEUE.json';lock_path=BASE/'EXPANSION_GPU_QUEUE.lock'
    with lock_path.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        files=list((WT/'src/ring_first_3d/sift_comparison').glob('*.py'))
        files += [WT/'src/ring_first_3d/v6_raw/route.py',WT/'src/ring_first_3d/v6_raw/policy.py',WT/'tools/ring_sift_comparison.py',REPORT/'EXPANSION_PROTOCOL.md']
        hashes={str(p):sha(p) for p in files}
        state=dict(pid=os.getpid(),status='WAITING_FOR_A',started_epoch=time.time(),max_wait_seconds=max_wait_seconds,poll_seconds=poll_seconds,source_hashes=hashes,automatic_git_publication=False)
        save(state_path,state)
        try:
            while True:
                verify_queue_sources(hashes)
                jobs=active_priority_jobs();state.update(active_A_jobs=jobs,updated_epoch=time.time())
                if time.time()-state['started_epoch']>max_wait_seconds:
                    state['status']='WAIT_LIMIT_REACHED_NOT_EXECUTED';save(state_path,state);return state
                if jobs:
                    state['status']='WAITING_FOR_A';save(state_path,state);time.sleep(poll_seconds);continue
                state['status']='RUNNING_REMAINING_HERO';save(state_path,state)
                result=batch('hero',source_hashes=hashes)
                verify_queue_sources(hashes)
                outcome=classify_hero_batch(result)
                if outcome=='FAILED_STAGE_NO_RETRY':
                    state.update(status=outcome,finished_epoch=time.time());save(state_path,state);return state
                if outcome=='WAITING_FOR_GPU':
                    state['status']='WAITING_FOR_GPU';save(state_path,state);time.sleep(poll_seconds);continue
                state['status']='REFRESHING_LOCAL_REPORT';save(state_path,state)
                from .expanded_report import report_expanded
                report_expanded()
                state.update(status='FINISHED',finished_epoch=time.time(),hero_state_path=str(BASE/'EXPANSION_HERO_STATUS.json'),report_path=str(REPORT/'EXPANDED_COMPARISON.html'))
                save(state_path,state);return state
        except Exception as error:
            state.update(status='FAILED_NO_SILENT_RETRY',error=repr(error),traceback=traceback.format_exc(),finished_epoch=time.time());save(state_path,state);raise
