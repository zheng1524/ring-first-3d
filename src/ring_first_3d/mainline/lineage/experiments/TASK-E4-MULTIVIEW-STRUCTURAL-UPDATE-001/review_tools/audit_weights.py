"""Independent read-only comparison to actually frozen historical multiview weights."""
from pathlib import Path
from types import SimpleNamespace
import ast,json,sys
import yaml
ROOT=Path(__file__).resolve().parents[3];TD=Path(__file__).resolve().parents[1];sys.path.insert(0,str(TD/'code'))
from body_update import balanced_weights
from data_adapter import real_data,simulation_data
from ring_first_3d.synthetic.io import save_json
from ring_first_3d.contracts.identities import sha256
T=yaml.safe_load((TD/'TASK.yaml').read_text());p=Path(T['structural']['assets']['legacy_multiview']['path']);tree=ast.parse(p.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='weights');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),ns)
rows=[]
for case in ['C0']+T['structural']['real_cases']:
 initial,views,ring,base,chart=simulation_data(T,'FIT') if case=='C0' else real_data(T,case,'FIT')
 c=SimpleNamespace(views={v['id']:dict(meta=v) for v in views});expected=ns['weights'](c,list(c.views));actual=balanced_weights(views);assert expected==actual
 rows.append(dict(case=case,original_weights_equal=True,weights=actual,sum_weights=sum(actual.values()),video_totals={vid:sum(actual[v['id']] for v in views if v['video']==vid) for vid in ['004','005']}))
save_json(TD/'evidence/EXACT_HISTORICAL_WEIGHTS_COMPARISON.json',dict(rows=rows,legacy_sha256=sha256(p),GT_read=False,new_view_selection=False));print([(r['case'],r['video_totals']) for r in rows])
