"""Checkpoint-continuation engineering pipeline; no new scientific optimization."""
import argparse,subprocess,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();out=a.out.resolve()
if out.exists():raise FileExistsError(out)
out.mkdir(parents=True)
modules=['ring-first','hero','body-initialization','body-update','stalk-growth-g01','stalk-growth-g03','a-to-b','depth-supervised-pytorch'];records=[]
for m in modules:
 with(out/(m+'.log')).open('w')as log:
  code=subprocess.call([sys.executable,'-m','ring_first_3d.mainline.cli',m,'--out',str(out/m)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
 path=out/m/'RESULT.json';r=json.loads(path.read_text())if path.exists()else dict(status='ENGINEERING_FAILURE',returncode=code)
 records.append(dict(module=m,status=r['status'],result=str(path),returncode=code))
result=dict(status='PASS'if all(r['status']=='PASS'for r in records)else'INCOMPLETE_OR_FAILED',mode='FIXED_CHECKPOINT_CONTINUATION; camera/HERO sample and Body checkpoint chain remain explicit independent blocks',new_optimization_steps=0,records=records,scientific_certification=False)
(out/'PIPELINE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(0 if result['status']=='PASS'else 1)
