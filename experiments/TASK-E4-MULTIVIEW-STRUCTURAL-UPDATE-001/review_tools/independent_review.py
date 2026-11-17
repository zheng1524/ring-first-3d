"""Post-freeze diagnostics only. No fitting, no checkpoint selection."""
from pathlib import Path
import sys,json
import numpy as np,yaml
TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from data_adapter import real_data,sources
from body_update import growth_quality,legacy_geometry
from experiment import shape_metrics
from ring_first_3d.synthetic.io import save_json

task=yaml.safe_load((TD/'TASK.yaml').read_text());run=TD/'runs/STRUCTURAL_004'
body=next(run.glob('attempts/0009-*'));evaluation=next(run.glob('attempts/0011-*'))
ns=legacy_geometry(task['structural']['assets']['legacy_geometry']['path']);results=[]
for case in task['structural']['real_cases']:
    initial,views,ring,base,chart=real_data(task,case)
    src=next(r for r in sources(task)['cases'] if r['case']==case);gt=dict(np.load(src['GT']['path']))
    initialT=np.load(evaluation/case/'INITIAL_GT_ALIGNED.npz')['T']
    for arm in ['INITIAL','DEFORM_ONLY','DEFORM_GROW']:
        m=initial if arm=='INITIAL' else dict(np.load(body/case/arm/'FINAL.npz'))
        why,g=growth_quality(m,initial,ring,ns,base,chart)
        aligned=dict(m,V=m['V']@initialT[:3,:3].T+initialT[:3,3])
        results.append(dict(case=case,arm=arm,geometry=g,geometry_violations=why,
             diagnostic_same_INITIAL_alignment_shape=shape_metrics(aligned,gt),
             diagnostic_note='Apply identical initial evaluation SE3 to all arms; no registration rerun, no selection or feedback'))
p=TD/'evidence/POST_FREEZE_GEOMETRY_AND_FIXED_ALIGNMENT.json';assert not p.exists();save_json(p,results)
print(json.dumps([dict(case=r['case'],arm=r['arm'],geometry=r['geometry'],violations=r['geometry_violations'],fixed_alignment_MAE=r['diagnostic_same_INITIAL_alignment_shape']['Chamfer_mm']['MAE'])for r in results],indent=2))
