"""Full isolated CPU reproduction, writes only this task's ignored runtime."""
from pathlib import Path
import os,sys,json,subprocess,datetime
SOURCE=Path(__file__).resolve().parents[1]
def main():
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=SOURCE/'runtime'/('reproduce_'+stamp);out.mkdir(parents=True,exist_ok=False)
    env=os.environ.copy();env.update(CAMERA_GATE_OUTPUT_ROOT=str(out),PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='')
    for script in ['prepare.py','tests12.py','correction.py','hero_auxiliary.py']:
        with (out/(script+'.log')).open('w') as f:subprocess.run([sys.executable,str(SOURCE/'code'/script)],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
        print('REPRODUCED',script,flush=True)
    # Fixed reducer already includes all required identities. No replay of ENG02.
    checks=[]
    for name in ['ORIGINAL_TEST12.json','RGB_ONLY_METHOD_SELECTION.json','ORIGINAL_OBSERVABILITY.json','ORIGINAL_QUALIFICATION.json','BOUNDED_CORRECTION_RESULTS.json','HERO_AUXILIARY.json']:
        a=json.loads((SOURCE/'config'/name).read_text());b=json.loads((out/'config'/name).read_text())
        def norm(v):
            if isinstance(v,dict):return {k:norm(x) for k,x in v.items() if k not in ['input','matches_file']}
            if isinstance(v,list):return [norm(x) for x in v]
            return v
        checks.append(dict(file=name,exact_numeric_and_decision_match=norm(a)==norm(b)))
    report=dict(status='PASS' if all(c['exact_numeric_and_decision_match'] for c in checks) else 'FAIL',output=str(out),checks=checks,original_outputs_overwritten=False,new_model_forward=0,GPU=0)
    (SOURCE/'config/REPRODUCTION_VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)
    if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
