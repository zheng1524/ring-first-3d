"""Frozen M4 for previously unaudited zero-HERO videos; never change old transforms."""
import core
from core import *
import importlib,traceback
def main():
 rel='experiments/TASK-V6-R1-M4-REGISTRATION-MAINLINE-002/'
 for p in ['code/pinned.py','code/context.py','code/audit.py','code/run.py','code/connections.py','config/PROTOCOL.json','config/DECISION.json']:snapshot(BASE,rel+p)
 boot=snapshot(BASE,rel+'code/context.py').parents[1];sys.path.insert(0,str(boot/'code'))
 ctx=importlib.import_module('context');ctx.CFG['regression_groups']=[]
 aud=importlib.import_module('audit');runner=importlib.import_module('run')
 # Original matches eagerly resolves an unused legacy path even with regression=[];
 # supply its existing read-only location. No legacy observations are consumed.
 runner.prior_run=lambda:M4/'runtime/regression/runs/R1_001/real'
 rows=[]
 for item in read(M4/'GROUP_INDEX.json')['groups']:
  g=item['group'];group=read(item['path']);old=read(Path(item['path']).with_name('ASSETS.json'));out=T/'runs/inputs'/g;record=out/'AUDIT.json'
  if record.exists():
   prior=read(record)
   if not prior['errors']:rows.append(prior);continue
   save(out/'PREVIOUS_INTERFACE_FAILURE.json',prior['errors'])
  vs=list(old['videos']);files={x['path']:x for x in old['files']};errors=[]
  for st in old['all_video_states']:
   if st['case']in[v['case']for v in vs]:continue
   try:
    v,ss,ff=aud.video_asset(st['upstream']);assert len(ss)==0;vs.append(v);files.update({x['path']:x for x in ff})
   except Exception as e:errors.append(dict(case=st['case'],error=repr(e),traceback=traceback.format_exc()))
  transforms={v['case']:v['T_local_to_common']for v in group['videos']};original=dict(transforms)
  reference=group['reference']or(vs[0]['case']if vs else None)
  if reference and reference not in transforms:transforms[reference]=np.eye(4).tolist()
  assetrec=dict(old,videos=vs,reference=reference,files=list(files.values()))
  supplemental=[]
  missing=[v['case']for v in vs if v['case']not in transforms]
  if missing:
   bout=ctx.group_out(g);ctx.save(bout/'ASSETS.json',assetrec);ctx.save(ctx.T/'config'/g/'ASSETS.json',assetrec)
   try:
    runner.matches(g,assetrec,bout);frames=ctx.read(bout/'FRAMES.json');C=np.load(bout/'CAMERAS.npz')['c2w'];tr=dict(np.load(bout/'tracks/observations/tracks005.npz'))
    for child in missing:
     for parent in list(transforms):
      edge=runner.solve_edge(g,assetrec,bout,frames,C,tr,parent,child);supplemental.append(edge)
      if edge['results']['M4']['T']is not None:
       transforms[child]=(np.array(transforms[parent])@np.array(edge['results']['M4']['T'])).tolist();break
   except Exception as e:errors.append(dict(stage='M4_SUPPLEMENT',error=repr(e),traceback=traceback.format_exc()))
  assert all(np.array_equal(transforms[k],v)for k,v in original.items())
  rec=dict(group=g,reference=reference,videos=vs,sources=group['sources'],source_metadata=old['sources'],files=list(files.values()),transforms=transforms,old_transforms_unchanged=True,old_group=asset(item['path'],item['sha256']),errors=errors,supplement_edges=supplemental,all_video_states=old['all_video_states'])
  save(record,rec);rows.append(rec);print('AUDITED',g,len(vs),len(transforms),len(errors),flush=True)
 save(T/'evidence/FULL_INPUT_INDEX.json',[dict(group=r['group'],videos=len(r['videos']),connected=len(r['transforms']),hero_sources=len(r['sources']),errors=r['errors'],audit=str(T/'runs/inputs'/r['group']/'AUDIT.json'))for r in rows])
if __name__=='__main__':main()
