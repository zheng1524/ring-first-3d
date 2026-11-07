"""One missing real case, using existing segmentation/Ring-First/HERO pipeline unchanged."""
from common import *
import importlib.util,ast,subprocess,traceback,gc,argparse
BASE=Path('/home/liu/polyp_research/ring_anchor_3d/experiments');BATCH=BASE/'multigroup_ring_hero_visual_audit_v1';V6=BASE/'ring_first_v6_local_reconstruction';DXY=Path('/home/liu/new-polyp-dxy');LEGACY=Path('/home/liu/polyp_research')
def extract(path,names,ns):
 tree=ast.parse(Path(path).read_text());nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
def main():
 import torch
 torch.set_num_threads(4);ap=argparse.ArgumentParser();ap.add_argument('case');gid=ap.parse_args().case;work=R/'new_input_pipeline'/gid;work.mkdir(parents=True,exist_ok=True);(work/'inputs').mkdir(exist_ok=True);(work/'metrics').mkdir(exist_ok=True);(work/'reproducibility').mkdir(exist_ok=True);(work/'logs').mkdir(exist_ok=True);case=load(R/'config'/('NEW_CASE_LOCK_'+gid+'.json'));g=case['pipeline_case'];cfg=load(BATCH/'config.json');(work/'config.json').write_text(json.dumps(cfg,indent=2));(work/'inputs/cases.json').write_text(json.dumps([g],indent=2));d=work/'groups'/g['id'];d.mkdir(parents=True,exist_ok=True)
 for n in['inputs','observations','predictions','metrics','meshes','scenes','visualizations','logs','scripts']:(d/n).mkdir(exist_ok=True)
 (d/'config.json').write_text(json.dumps(cfg,indent=2))
 # Isolate legacy module named common from the task-local IO module.
 sys.modules['bodybase_task_common']=sys.modules['common'];lspec=importlib.util.spec_from_file_location('common',BASE/'surface_fusion_v1/scripts/common.py');lmod=importlib.util.module_from_spec(lspec);sys.modules['common']=lmod;lspec.loader.exec_module(lmod)
 sys.path.insert(0,str(BATCH/'scripts'));spec=importlib.util.spec_from_file_location('bodybase_existing_geometry',BATCH/'scripts/run_geometry.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
 def localload(p):return load(work/p)
 def localsave(p,x):save(work/p,x)
 def freeze(n,ps):localsave('reproducibility/'+n+'.json',dict(files=[asset(p)for p in ps],algorithm_changed=False,GT_used=False))
 ns=dict(b.__dict__);ns.update(R=work,REPO=LEGACY,DXY=DXY,subprocess=subprocess,gc=gc,traceback=traceback,load=localload,save=localsave,freeze=freeze);extract(BATCH/'scripts/prepare_batch.py',['main'],ns)
 if not(d/'inputs/ledger005.json').exists():ns['main']()
 # Free segmentation GPU allocations before any future model; the routine returns model references only locally.
 gc.collect();torch.cuda.empty_cache()
 ctx=b.context(d)
 if not(d/'predictions/ring_candidates005.json').exists():b.rings(ctx)
 if not(d/'observations/tracks005.npz').exists():extract(V6/'scripts/track005.py',['main'],ctx);ctx['main']()
 if not(d/'metrics/local_validation.json').exists():
  if not b.cameras(ctx):raise RuntimeError('Existing two fixed Ring-First camera initializations both failed; no replacement or synthetic poses')
  b.validate(ctx)
 # The exact official existing HERO wrapper; first-time prediction for this new specimen only.
 if not(d/'predictions/HERO_native.npz').exists():
  sys.path.insert(0,str(BASE/'surface_fusion_v1/scripts'));import run_mvs_adapter3 as adapter
  hns=dict(b.__dict__);hns.update(R=work,load=localload,save=localsave,torch=torch,adapter=adapter,time=time,traceback=traceback,gc=gc,freeze=freeze);extract(BATCH/'scripts/run_hero.py',['main'],hns);hns['main']()
 if not(d/'predictions/HERO_native.npz').exists():raise RuntimeError('New case depth pipeline did not produce native HERO; preserve failure, no fallback')
 save('assets_index/NEW_PIPELINE_RESULT_'+gid+'.json',dict(status='COMPLETED',new_specimen=g['id'],new_HERO=True,existing_eight_HERO_not_rerun=True,outputs=[asset(p)for p in[d/'predictions/HERO_native.npz',d/'predictions/local005_camera_0.npz',d/'inputs/ledger005.json',d/'inputs/MVS_cases.json']],source_files=[asset(BATCH/'scripts'/n)for n in['prepare_batch.py','run_geometry.py','run_hero.py']],coordinate='same frozen K, Ring-local mm, native axial HERO mm'))
if __name__=='__main__':main()
