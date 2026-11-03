"""Stop only the recorded local job immediately after its next complete checkpoint."""
from pathlib import Path
import os,sys,time,json,signal,hashlib,shutil,datetime
R=Path(__file__).resolve().parents[1]
OLD=Path('/home/liu/ring_first_3d_e3_sdf_multi/experiments/TASK-E3-SDF-LOCAL-MULTIPOLYP-EXPLORATORY-001')
launch=json.loads((OLD/'provenance/LAUNCH.json').read_text())
parent=int(launch['supervisor_pid']);child=19413
commands={pid:Path(f'/proc/{pid}/cmdline').read_bytes().decode().replace('\0',' ')for pid in [parent,child]}
assert str(OLD)in commands[parent]and'run_all.py'in commands[parent]
assert str(OLD)in commands[child]and'train_full.py M1'in commands[child]
index=OLD/'groups/G01_004/checkpoints/single_M1/LATEST.json'
initial=json.loads(index.read_text());target=(initial['step']//1000+1)*1000
assert target<=10000
os.kill(parent,signal.SIGSTOP)
print('WAIT_OWN_COMPLETE_CHECKPOINT',target,flush=True)
while True:
    state=json.loads(index.read_text())
    if state['step']>=target:break
    time.sleep(.1)
os.kill(child,signal.SIGSTOP)
state=json.loads(index.read_text());source=Path(state['path'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==state['sha256']
target_file=R/'checkpoints'/f'M1_HANDOFF_G01_step{state["step"]:06d}.pt'
assert not target_file.exists();shutil.copy2(source,target_file)
assert hashlib.sha256(target_file.read_bytes()).hexdigest()==state['sha256']
record=dict(timestamp_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='migrate same M1 chain to authorized4090; avoid duplicate optimization',
    baseline_reference_step=2000,primary_target_per_group=20000,handoff_complete_step=state['step'],
    source=state,destination=str(target_file),sha256=state['sha256'],owned_commands=commands,
    other_user_tasks_signalled=0,exact_live_step_after_checkpoint='may be at next forward; only complete checkpoint claimed')
(R/'provenance/LOCAL_M1_HANDOFF.json').write_text(json.dumps(record,indent=2)+'\n')
for pid in [child,parent]:
    os.kill(pid,signal.SIGTERM);os.kill(pid,signal.SIGCONT)
print('OWN_LOCAL_JOB_HANDED_OFF',state['step'],state['sha256'],flush=True)
