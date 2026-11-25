"""Stage runner for original H004 ancestry. Only IO/config/source adapters live here."""
import os,sys,json,ast,time,traceback,types,argparse
from pathlib import Path
from historical_io import E,H,W,SOURCES,sha,common,load,firewall
import numpy as np,cv2
BASE=W/'runs/m2f12_historical004/H004_RAW_BASELINE'
MODEL=Path('/home/liu/polyp_research/experiments/v8_5_cross_ring_pipeline_audit_20261014/freeze/model')
DECODE=E/'ring_first_v2_real_ba/runs/continuous16/scripts/decode_segment.py'

def prep(R,c,cfg):
 # Execute the original RAW/JPEG95/INIT implementation, changing only schedule and output bindings.
 c.REPO=Path('/home/liu/polyp_research');c.OLD=Path('/home/liu/polyp_research/ring_anchor_3d')
 t=ast.parse(DECODE.read_text())
 for node in ast.walk(t):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='linspace' and len(node.args)==3:
   node.args=[ast.Constant(cfg['nominal_frames'][0]),ast.Constant(cfg['nominal_frames'][-1]),ast.Constant(16)]
  if isinstance(node,ast.keyword) and node.arg=='ring_mm':node.value=ast.Constant(cfg['ring_inner_mm'])
 ns={'__name__':'h004_decode','__file__':str(DECODE)}
 # Original freeze named scripts/common.py: bind its receipt to the actual source, never copy code.
 original_freeze=c.freeze
 def bound_freeze(name,files):
  files=[SOURCES['common'] if str(p)==str(R/'scripts/common.py') else p for p in files]
  return original_freeze(name,files)
 c.freeze=bound_freeze
 exec(compile(ast.fix_missing_locations(t),str(DECODE),'exec'),ns)
 c.freeze=original_freeze
 # Verify exact JPEG payload identity against sequential raw decode; preserve old requested IDs.
 from frame_identity import bind_frames
 rows=json.loads((R/'inputs/manifest.json').read_text());identities=bind_frames(cfg['video'],[r['frame_index']for r in rows],[sha(R/f'inputs/images/{i:03d}.jpg')for i in range(16)])
 for row,identity in zip(rows,identities):row.update(identity)
 c.save('preparation/LOSSLESS_FRAME_IDENTITY.json',identities)
 c.save('inputs/manifest.json',rows);cfg['raw_frames']=[r['frame_index']for r in rows];c.save('config.json',cfg)
 # The V3 tracker reads a provenance record under preparation/reuse.json.
 provenance=json.loads((R/'preparation/segmentation_provenance.json').read_text());c.save('preparation/reuse.json',dict(segmentation_provenance=provenance,raw_recomputed=True))
 adapter=load('adapter',R,cfg['R_mm']);fits=[]
 for i,row in enumerate(rows):
  image=cv2.imread(str(R/f'inputs/images/{i:03d}.jpg'));labels=cv2.imread(str(R/f'inputs/masks/{i:03d}.png'),0)
  ob,status=adapter.adapt(image,labels,row['source_id']);np.savez_compressed(R/f'observations/native_{i:03d}.npz',**ob);fits.append(status)
 c.save('observations/dxy_original_fits.json',fits)
 # Existing V5 half-pixel conversion and positive sampling, with old-source SHA asserts removed
 # only because inputs are fresh. Scientific conversion statements are executed verbatim.
 source=E/'ring_first_v5_real_validation/scripts/prepare.py';tree=ast.parse(source.read_text())
 loop=next(n for n in tree.body if isinstance(n,ast.For));loop.body=loop.body[1:]
 ns=dict(c.__dict__,manifest=rows,counts=[])
 exec(compile(ast.Module(body=[loop],type_ignores=[]),str(source),'exec'),ns)
 c.save('metrics/observation_contract.json',ns['counts']);print('PREPARED_FROM_RAW',cfg['group'],cfg['video_id'],cfg['raw_frames'],flush=True)

def seed(R,c,cfg):
 tracker=load('track_scene',R);tracker.main()
 load('geometry_safe',R,cfg['R_mm']);init=load('visual_initialize',R);init.main()
 ring=load('ring_candidates',R,cfg['R_mm']);ring.main()
 load('ba_safe',R,cfg['R_mm']);runner=load('run_real',R,cfg['R_mm'])
 tr=np.load(R/'observations/tracks.npz');x=np.load(R/'predictions/visual_init_F980_0.npz');P=x['c2w'];X=x['points'];ids=x['point_ids'];mask=x['observation_mask'];K=x['K']
 if len(X)<20 or not np.isfinite(P[8,0,0]):raise ValueError('VISUAL_INITIALIZATION_FAILED')
 P,X,h=runner.optimize(P,X,tr['xy'],ids,mask,K,False);runner.packsave('common_F980_0',P,X,ids,mask,K);c.save('metrics/common_F980_0.json',h)
 P,X,align=runner.align_ring(P,X,K,'F980');runner.packsave('shared_F980_0',P,X,ids,mask,K);c.save('metrics/alignment_F980_0.json',align)
 P,X,h=runner.optimize(P.copy(),X.copy(),tr['xy'],ids,mask,K,True)
 yaw=-np.arctan2(P[8,1,0],P[8,0,0]);P,X=runner.transform(P,X,runner.Rotation.from_rotvec([0,0,yaw]).as_matrix(),1.,np.zeros(3))
 runner.packsave('C_F980_0',P,X,ids,mask,K,ring_scale=True);c.save('metrics/C_F980_0_history.json',h)
 evaluator=load('evaluate_real',R,cfg['R_mm']);pack=np.load(R/'predictions/C_F980_0.npz');held=np.flatnonzero(~tr['train_track']&tr['holdout_eligible']);g=evaluator.geometry(pack,tr['xy'],tr['category']);ho=evaluator.holdout(P,K,tr['xy'],held,tr['category']);rg=evaluator.ring_eval(P,K)
 c.save('metrics/SEED_EVALUATION.json',dict(geometry=g,heldout=ho,ring=rg,scale='Ring candidate mm',full_9_initialization_reliability_test=False,not_pose_GT=True))
 print('SEED_COMPLETE',len(g['registered']),len(X),'held_MAE',ho['error_px']['MAE'],flush=True)

def main():
 a=argparse.ArgumentParser();a.add_argument('stage',choices=['prepare','seed']);a.add_argument('case');args=a.parse_args();R=BASE/args.case;cfg=json.loads((R/'config.json').read_text());c=common(R)
 sys.path[:0]=[str(E/'surface_fusion_v3/vendor'),'/home/liu/new-polyp-dxy/src'];sys.dont_write_bytecode=True
 for name in ['HF_HOME','HF_MODULES_CACHE','TORCH_HOME','MPLCONFIGDIR','XDG_CACHE_HOME']:os.environ[name]=str(R/'runtime'/name)
 os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
 events=firewall(R,[cfg['video']],[str(MODEL),str(R/'runtime')]);start=time.time();result=dict(stage=args.stage,status='STARTED',independent_raw=True)
 try:
  {'prepare':prep,'seed':seed}[args.stage](R,c,cfg);result['status']='COMPLETED'
 except Exception as ex:result.update(status='FAILED',error=repr(ex),traceback=traceback.format_exc());print(result['traceback'],flush=True)
 finally:
  result.update(seconds=time.time()-start,consumers=events,code={str(p):sha(p) for p in list(SOURCES.values())+[Path(__file__),DECODE]});c.save('STAGE_'+args.stage+'.json',result)
 if result['status']!='COMPLETED':raise SystemExit(1)
if __name__=='__main__':main()
