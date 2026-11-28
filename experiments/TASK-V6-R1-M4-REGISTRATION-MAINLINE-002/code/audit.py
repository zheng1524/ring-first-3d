"""Full terminal inventory; all groups/videos retained, upstream read-only."""
from context import *
import traceback

def video_asset(s):
 R=Path(s['run_path']);assert FULL in R.parents
 cc=read(R/'CAMERA_COMPLETE.json');plan=read(R/'PLAN_FROZEN.json');he=read(R/'HERO_COMPLETE.json');identity=read(FULL/'RUN_IDENTITY.json');files={}
 def add(p,expected=None):
  p=Path(p);h=sha(p);assert expected is None or h==expected,('DRIFT',p);files[str(p)]=dict(path=str(p),sha256=h,bytes=p.stat().st_size);return h
 for rec in [cc,plan,he]:assert rec['execution_commit']==identity['execution_commit']and rec['case']==s['case']and rec['variant']=='HIST'
 assert he['plan_sha256']==sha(R/'PLAN_FROZEN.json')and plan['parent_sha256']==sha(R/'CAMERA_COMPLETE.json')
 for rec in [cc,he]:
  for path,h in rec['outputs'].items():add(path,h)
 primary=read(R/'predictions/local005_primary.json')['primary_version'];cam=R/f'predictions/local005_camera_{primary}.npz';cams=np.load(cam);assert str(cams['units'])=='mm';add(cam,plan['cameras_sha256'])
 ledger=read(R/'inputs/ledger005.json');assert list(cams['ids'])==[f['id']for f in ledger]
 cfg=read(R/'config.json');cad=WORK/'runs/m2f5_unified/cad'/('R5.npz'if '_R5_'in s['case']else'R10.npz');add(cad)
 for f in ledger:add(f['RGB_path'],f['RGB_SHA256']);add(f['Mask_path'],f['Mask_SHA256'])
 pool=np.unique(np.rint(np.linspace(0,len(ledger)-1,min(len(ledger),CFG['frames_per_video']))).astype(int)).tolist()
 for j in pool:add(R/'observations'/(ledger[j]['id']+'_ring.npz'))
 for rel in ['CAMERA_COMPLETE.json','PLAN_FROZEN.json','HERO_COMPLETE.json','FRONTEND_KERNELS.json','COMPONENT.json','inputs/REFERENCE_RECEIPT.json','config.json','inputs/ledger005.json','inputs/INPUT_IDENTITY.json','predictions/local005_primary.json','predictions/ring_candidates005.json','observations/tracks005.npz','metrics/GATES.json']:add(R/rel)
 front=read(R/'FRONTEND_KERNELS.json');track=next(v for k,v in front['functions'].items()if k.endswith('track005.main'));assert sha(V6/'track005.py')==track['disk_sha256']
 sources=[]
 for item in plan['legal']:
  tag=item['tag'];native=R/'raw'/(tag+'.npz');mesh=R/'meshes'/(tag+'_Polyp.ply');hn=add(native,he['outputs'][str(native)]);hm=add(mesh,he['outputs'][str(mesh)]);nat=np.load(native);ref=int(nat['reference']);assert ref==item['reference'];assert np.array_equal(nat['sources'],item['sources']);assert np.array_equal(nat['c2w'],cams['c2w'])and np.array_equal(nat['K_full'],cams['K']);assert nat['depth_mm'].shape[-2:]==(352,640)
  sources.append(dict(group=s['group'],side=s['case'],case=s['case'],run=str(R),tag=tag,source_id=s['case']+'__'+tag,reference=ref,raw_target=ledger[ref]['raw_frame'],raw_support=[ledger[j]['raw_frame']for j in item['sources']],sources=item['sources'],mesh_sha256=hm,native_sha256=hn,camera_path=str(cam),camera_sha256=sha(cam),cad_path=str(cad),cad_sha256=sha(cad),input_sha256=item.get('input_sha256'),model_sha256='00878bab903b1d384cd6bb9ea092e247a9036d429cb8bcc3d6dcbb81f67e556d'))
 assert len(sources)==plan['budget']==s['native_success']==s['renderable']
 video=dict(side=s['case'],case=s['case'],run=str(R),camera=str(cam),camera_sha256=sha(cam),pool=pool,frames=ledger,source_tags=[x['tag']for x in sources],ring_radius_mm=cfg['ring_R_mm'],ring_wire_mm=cfg['ring_r_mm'],origin=s['origin'],execution_commit=identity['execution_commit'])
 return video,sources,list(files.values())

def main():
 freeze('AUDIT',T/'evidence');identity=read(FULL/'RUN_IDENTITY.json');launch=read(FULL/'LAUNCH.json');cfgpath=Path(launch['command'][-1]);assert sha(cfgpath)==identity['config_sha256'];upcfg=read(cfgpath);assert upcfg['task']=='TASK-V6-R1-MAINLINE-AND-FULL-RUN-B-001'and upcfg['reuse_old_results']is False;assert sha(upcfg['manifest'])==identity['manifest_sha256'];manifest=read(upcfg['manifest']);progress=read(FULL/'PROGRESS.json');assert progress['status']=='COMPLETE'
 groups={}
 for v in manifest['videos']:groups.setdefault(v['group'],[]).append(v)
 summary=[]
 for g,videos in sorted(groups.items()):
  out=group_out(g);state_rows=[];vv=[];ss=[];ff={}
  for v in sorted(videos,key=lambda v:v['case']):
   state=read(FULL/'states'/(v['case']+'.json'));record=dict(case=v['case'],upstream=state,status='NO_OUTPUT',error=None)
   if state.get('native_success',0)>0:
    try:
     video,sources,files=video_asset(state);vv.append(video);ss+=sources;ff.update({r['path']:r for r in files});record['status']='AVAILABLE'
    except Exception as e:record.update(status='ASSET_ERROR',error=repr(e),traceback=traceback.format_exc())
   state_rows.append(record)
  ref=vv[0]['case']if vv else None;asset=dict(group=g,reference=ref,videos=vv,sources=ss,files=list(ff.values()),all_video_states=state_rows,R1_contract_verified=True)
  assert len({s['source_id']for s in ss})==len(ss)
  save(out/'ASSETS.json',asset);save(T/'config'/g/'ASSETS.json',asset)
  row=dict(group=g,reference=ref,videos=len(videos),available_videos=len(vv),sources=len(ss),status='MULTIVIDEO'if len(vv)>1 else'SINGLE_VIDEO'if vv else'NO_OUTPUT',asset_errors=[r['case']for r in state_rows if r['status']=='ASSET_ERROR']);summary.append(row);save(T/'config/INVENTORY.json',dict(identity=identity,upstream_config=str(cfgpath),manifest=upcfg['manifest'],progress=progress,groups=summary));print('AUDIT',g,len(vv),len(ss),row['asset_errors'],flush=True)
 save(T/'evidence/UPSTREAM_TERMINAL.json',dict(identity=identity,progress=progress,files=[dict(path=str(p),sha256=sha(p))for p in [cfgpath,Path(upcfg['manifest']),FULL/'PROGRESS.json',FULL/'FINAL_COVERAGE_REPORT.md',FULL/'RUN_IDENTITY.json']]))
 print('FULL AUDIT',len(summary),sum(r['videos']for r in summary),sum(r['available_videos']for r in summary),sum(r['sources']for r in summary),flush=True)
if __name__=='__main__':main()
