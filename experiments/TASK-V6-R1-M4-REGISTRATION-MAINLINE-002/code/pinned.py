"""Resolve committed kernels, without requiring historical worktrees."""
from pathlib import Path
import subprocess,hashlib,json
T=Path(__file__).resolve().parents[1]; ROOT=T.parents[1]
PINS={
 '002':('efa0adfb09f23f355d3d55180f2becfb1036f35c','experiments/TASK-V6-REGISTRATION-NOISE-AND-RAW-CLEAN-002'),
 '001':('537c20701f6a7a8f2de150a87357195e0d5118a0','experiments/TASK-V6-VIRTUAL-POLYP-REGISTRATION-001'),
 'clean':('2d34cc866cd175d4d770a3e09d07b31a5c3662d7','experiments/TASK-V6-RESTORE-TRUSTED-ONLY-CLEAN-001')}
def resolve(key,rel):
 sha,base=PINS[key];p=T/'runtime/pinned'/sha/base/rel
 data=subprocess.check_output(['git','show',sha+':'+base+'/'+rel],cwd=ROOT)
 if p.exists():assert p.read_bytes()==data,('PIN_DRIFT',p)
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 return p
def prepare():
 for rel in ['common2.py','solver2.py','real2.py','metrics2.py','evaluate_real2.py','visualize2.py','clean2.py','worker.py']:
  resolve('002','code/'+rel)
 resolve('002','config/PROTOCOL.json')
 for rel in ['code/registration.py','config.json','inputs/V6_KERNELS/track005.py','inputs/V6_KERNELS/v6_common.py']:resolve('001',rel)
 resolve('clean','config/SOURCES_FROZEN.json')
 return resolve('002','code/worker.py')
if __name__=='__main__':print(prepare())
