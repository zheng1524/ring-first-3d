"""Only direct read access: no upstream cache/scheduler/packager entrypoints."""
from common2 import *
import re

def select():
 resource();snapshot=FULL/'snapshots/da92d8ddfaf9a3fc266b518e56e2d3a6c2ed056a';config=snapshot/'experiments/TASK-V6-FULL-RUN-AND-SURFACE-CLEAN-001/config/FULL_RUN.json';fullcfg=read(config);manifest=read(fullcfg['manifest']);progress=read(FULL/'PROGRESS.json');states={};groups={}
 for v in manifest['videos']:
  case=v['case'];p=FULL/'states'/(case+'.json');s=read(p)if p.exists()else {};states[case]=s
  if s.get('status')=='DONE' and s.get('native_success',0)>0 and s.get('renderable',0)>0 and s.get('origin')in ['NEW','REUSED']:
   assert s['group']==v['group'];groups.setdefault(v['group'],[]).append(s)
 eligible={g:sorted(ss,key=lambda s:s['case'])[:2]for g,ss in groups.items()if len(ss)>=2};old=read(CLEAN_T/'config/SOURCES_FROZEN.json')['cases'];clean_groups={r['group']for r in old};selected=[];types=set();rings=set();sizes=set()
 while len(selected)<min(CFG['groups'],len(eligible)):
  def key(g):
   typ=g.split('_')[1];ring=re.search(r'_R(5|10)_',g)[1];size=g.split('_')[2];return (-(int(typ not in types)+int(ring not in rings)),-int(size not in sizes),-int(g in clean_groups),g)
  g=min((g for g in eligible if g not in selected),key=key);selected.append(g);types.add(g.split('_')[1]);rings.add(re.search(r'_R(5|10)_',g)[1]);sizes.add(g.split('_')[2])
 rows=[dict(group=g,A=eligible[g][0],B=eligible[g][1])for g in selected]
 save(T/'config/SELECTION.json',dict(before_registration=True,rule='greedy new morphology+Ring, then new size, reusable_clean, groupID; pair caseID sorted first2',full_config=str(config),full_config_sha256=sha(config),dataset_manifest=str(fullcfg['manifest']),dataset_manifest_sha256=sha(fullcfg['manifest']),eligible_groups=sorted(eligible),progress_reference_only=progress,groups=rows,resource=resource(),no_Is_available=not any('_Is_'in g for g in eligible)))
 print('SELECTED',selected,flush=True)

def freeze_group(g):
 row=next(x for x in read(T/'config/SELECTION.json')['groups']if x['group']==g);frozen=[];sources=[];videos=[]
 def add(p,expected=None):
  p=Path(p);h=sha(p);assert expected is None or h==expected,('SOURCE_HASH',p);frozen.append(dict(path=str(p),sha256=h,bytes=p.stat().st_size));return h
 for side in ['A','B']:
  resource();s=row[side];R=Path(s['run_path']);cc=read(R/'CAMERA_COMPLETE.json');plan=read(R/'PLAN_FROZEN.json');hero=read(R/'HERO_COMPLETE.json')
  assert cc['variant']==plan['variant']==hero['variant']=='HIST';assert cc['case']==plan['case']==hero['case']==s['case'];assert hero['plan_sha256']==sha(R/'PLAN_FROZEN.json');assert plan['parent_sha256']==sha(R/'CAMERA_COMPLETE.json')
  primary=read(R/'predictions/local005_primary.json')['primary_version'];cam=R/f'predictions/local005_camera_{primary}.npz';assert plan['cameras_sha256']==sha(cam);ledger=read(R/'inputs/ledger005.json');a=np.load(cam);assert str(a['units'])=='mm';assert list(a['ids'])==[f['id']for f in ledger]
  pool=np.rint(np.linspace(0,len(ledger)-1,CFG['frames_per_video'])).astype(int).tolist();assert len(set(pool))==CFG['frames_per_video'];cfg=read(R/'config.json');cad=WORK/'runs/m2f5_unified/cad'/('R5.npz'if '_R5_'in s['case']else'R10.npz')
  for rel in ['CAMERA_COMPLETE.json','PLAN_FROZEN.json','HERO_COMPLETE.json','config.json','inputs/ledger005.json','inputs/INPUT_IDENTITY.json','predictions/local005_primary.json','predictions/ring_candidates005.json','observations/tracks005.npz','metrics/GATES.json']:add(R/rel,cc.get('outputs',{}).get(str(R/rel)))
  add(cam,plan['cameras_sha256']);add(cad)
  # Every ledger image is a genuine retained source, but no full RAW/video reads.
  for f in ledger:
   add(f['RGB_path'],f['RGB_SHA256']);add(f['Mask_path'],f['Mask_SHA256'])
  for i in pool:
   ring=R/'observations'/(ledger[i]['id']+'_ring.npz');add(ring)
  selected=[]
  for item in plan['all_targets']:
   tag=item['tag'];native=R/'raw'/(tag+'.npz');mesh=R/'meshes'/(tag+'_Polyp.ply')
   if not native.exists()or not mesh.exists():continue
   hn=add(native,hero['outputs'].get(str(native)));hm=add(mesh,hero['outputs'].get(str(mesh)));nat=np.load(native);ref=int(nat['reference']);assert ref==item['reference'];assert np.array_equal(nat['sources'],item['sources']);assert np.array_equal(nat['c2w'],a['c2w']);assert np.array_equal(nat['K_full'],a['K'])
   rec=dict(group=g,side=side,case=s['case'],run=str(R),tag=tag,reference=ref,raw_target=ledger[ref]['raw_frame'],raw_support=[ledger[j]['raw_frame']for j in item['sources']],sources=item['sources'],mesh_sha256=hm,native_sha256=hn,camera_path=str(cam),camera_sha256=sha(cam),cad_path=str(cad),cad_sha256=sha(cad),input_sha256=item.get('input_sha256'),model_sha256='00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d');sources.append(rec);selected.append(tag)
  assert len(selected)>0
  videos.append(dict(side=side,case=s['case'],run=str(R),camera=str(cam),pool=pool,frames=ledger,source_tags=selected,ring_radius_mm=cfg['ring_R_mm'],ring_wire_mm=cfg['ring_r_mm'],origin=s['origin']))
 seen={r['path']:r for r in frozen};frozen=list(seen.values());verify(frozen);save(T/'config'/g/'ASSETS.json',dict(group=g,videos=videos,sources=sources,files=frozen,verified_before_use=True));print('FROZEN',g,'sources',len(sources),'files',len(frozen),flush=True)
if __name__=='__main__':
 import sys
 if sys.argv[1]=='select':select()
 else:
  for row in read(T/'config/SELECTION.json')['groups']:freeze_group(row['group'])
