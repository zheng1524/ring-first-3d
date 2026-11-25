"""Render original-membership panels with own-target qualification stated explicitly."""
import ast
from common import *
p=T/'code/render_all.py';tree=ast.parse(p.read_text());prefix=[]
for n in tree.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name)and t.id=='rows'for t in n.targets):break
 prefix.append(n)
exec(compile(ast.Module(body=prefix,type_ignores=[]),str(p),'exec'))
rows=read(B/'ALL_UNIQUE_SOURCES.json');index=read(T/'evidence/VISUALIZATION_INDEX.json')
for entry in index:
 rr=sorted([r for r in rows if r['case']==entry['case']and r['route']==entry['route']and r['renderable']],key=lambda r:(r['input_identity'][0]['raw_frame'],r['source_id']));ss=[r for r in rr if r['formal']]
 inner=next(r['ring_inner_mm']for r in read(P12/'evidence/INPUT_REGISTRY.json')if r['case']==entry['case']);cad=dict(np.load(W/'runs/m2f5_unified/cad'/('R10.npz'if inner==10 else'R5.npz')));data={r['source_id']:mesh(r)for r in rr};bounds=np.concatenate([cad['V']]+[data[r['source_id']][0]for r in rr]);title=entry['case']+' / '+entry['route']+f" | ORIGINAL MEMBERS {len(ss)}, own-target qualified {sum(r['target_qualified']for r in ss)} | original gates, NOT common independent quality PASS"
 for colored in [False,True]:six(ss,data,cad,bounds,F/(entry['route']+'__'+entry['case']+'__FORMAL'+('__SOURCE'if colored else'__RGB')+'.png'),title,colored)
 print('RELABEL',entry['case'],entry['route'],flush=True)
