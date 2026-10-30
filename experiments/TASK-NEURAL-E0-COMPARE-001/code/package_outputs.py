"""Small local GLBs, final status and gallery; no prediction or training."""
from audit import *
import trimesh
from importlib import metadata

def main():
 registry=load(R/'provenance/INPUT_ELIGIBILITY.json');rows=[];maprows=load(R/'provenance/MAP_RUN_RESULT.json')['rows']+load(R/'provenance/MAP_M3_SUPPLEMENT_RESULT.json')['rows'];passed={x['mode']:x for x in maprows if x['status'].startswith('SMOKE_PASS')};sdf=load(R/'provenance/SDF_RUN_RESULT.json');glbs=[]
 for mode in ['M0','M1','M2','M3']:
  r=passed[mode];rows.append(dict(arm='M',configuration=mode,scene='G01_005',final_status='NUMERIC_OUTPUT_PASS_GEOMETRY_NOT_PROVEN',model_forward_attempts=3 if mode=='M0' else 2 if mode=='M3' else 1,numeric_output=True,points=r['points'],observed_supported_surface='source-mask conditioned, not independently certified',forward_seconds=r['forward_seconds'],total_call_seconds=r['seconds'],peak_GPU_allocated_bytes=r['peak_GPU_allocated_bytes'],peak_GPU_reserved_bytes=r['peak_GPU_reserved_bytes']))
 rows.append(dict(arm='S',configuration='S0',scene='G01_005',final_status='OPTIMIZATION_COMPLETED_ADAPTER_DOMAIN_FAILED',model_forward_attempts=400,numeric_output=True,points=sdf['zero_level_vertices'],observed_supported_surface=0,forward_seconds=None,total_call_seconds=sdf['total_seconds'],optimization_seconds=sdf['optimization_seconds'],optimizer_steps=sdf['optimizer_steps'],peak_GPU_allocated_bytes=sdf['peak_GPU_allocated_bytes'],peak_GPU_reserved_bytes=sdf['peak_GPU_reserved_bytes']))
 table('metrics/ARM_FINAL_STATUS.csv',rows)
 for mode in ['M0','M1','M2','M3','SDF_PRIOR_ONLY_FAILED']:
  path=R/f'local_results/map/{mode}/surface.npz'if mode.startswith('M')else R/'local_results/sdf_scene/surface.npz';a=np.load(path);P=a['XYZ_mm'];F=a['faces'];C=a['RGB']if mode.startswith('M')else np.full_like(P,.55)
  sc=trimesh.Scene();m=trimesh.Trimesh(P/1000,F,vertex_colors=np.rint(C*255).astype(np.uint8),process=False);m.metadata.update(method=mode,coordinate_frame='G01_005_LOCAL_RING_MM',glb_unit='m',source_npz=str(path),source_SHA256=sha(path),GT_used=False,cross_video_fused=False,observed_support='PRIOR_ONLY_FAILED'if not mode.startswith('M')else'input-mask predicted geometry; uncalibrated confidence')
  sc.add_geometry(m,node_name=mode);cad=trimesh.load(OLD/'surface_fusion_v2/inputs/R10_ring.obj',process=False);cad.vertices/=1000;cad.visual.face_colors=[12,12,12,255];sc.add_geometry(cad,node_name='FIXED_RING_CAD');folder=R/'local_results/glb';folder.mkdir(exist_ok=True);dest=folder/(mode+'_SINGLE_VIDEO_005_UNCERTIFIED.glb');sc.export(dest);glbs.append(dict(method=mode,path=str(dest),bytes=dest.stat().st_size,sha256=sha(dest),unit='m',status='LOCAL_ONLY_UNCERTIFIED'))
 table('provenance/NEW_GLB_INDEX.csv',glbs)
 installed=[]
 for d in metadata.distributions(path=[str(R/'runtime/python')]):installed.append(dict(name=d.metadata['Name'],version=d.version))
 save('provenance/ISOLATED_DEPENDENCIES.json',dict(directory=str(R/'runtime/python'),packages=sorted(installed,key=lambda x:x['name']),installation='pip --target --no-deps --no-cache-dir; existing Torch/CUDA environment not modified',torch=__import__('torch').__version__))
 # The final A->B cache record is a re-render after first evaluation, not a
 # new blind freeze. The immutable model-output freeze predates first B read.
 p=R/'provenance/ALL_PREDICTIONS_BEFORE_TARGET_RGB.json';a=load(p);a.update(scope='FINAL_CPU_RERENDER_CACHE_MANIFEST; target files not yet opened in that render pass',first_evaluation_already_occurred=True,immutable_pre_first_evaluation_freeze='ALL_MODEL_OUTPUTS_FROZEN_BEFORE_EVALUATION.json',model_predictions_changed_after_evaluation=False);save('provenance/ALL_PREDICTIONS_BEFORE_TARGET_RGB.json',a)
 # HTML indexes link every artifact without duplicating scientific inputs.
 paths=sorted((R/'figures').rglob('*.png'));html=['<meta charset="utf-8"><title>Phase E E0 local gallery</title><h1>TASK-NEURAL-E0-COMPARE-001</h1><p>4 groups audited; models only G01 video005. No winner, no cross-video fusion.</p>']
 for p in paths:
  rel=os.path.relpath(p,R/'visualizations');html.append('<p><a href="'+rel+'">'+p.name+'</a></p>')
 for x in glbs:html.append('<p><a href="../'+str(Path(x['path']).relative_to(R))+'">'+x['method']+' GLB (m; uncertified)</a></p>')
 folder=R/'visualizations';folder.mkdir(exist_ok=True);(folder/'index.html').write_text('\n'.join(html))
 save('metrics/PROTECTED_FINAL_CHECK.json',dict(protected_git_workspaces_unchanged=protected()==load(R/'provenance/PROTECTED_START.json'),explicit_cleanup_exception='58 invalid V8 download artifacts, user authorized; see USER_AUTHORIZED_CLEANUP.json',frozen_inputs_changed=False))
 print('PACKAGED',len(rows),'arm rows',len(glbs),'new local GLBs',len(paths),'PNG files',flush=True)
if __name__=='__main__':main()
