"""One existing static Blender Ip control, no real GT and no new rendering data."""
from common import *
from prepare016 import link
from evaluate import area_samples,distance
import open3d as o3d

SRC=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/BOUNDARY_RELATIVE_DEPTH_D2_001'

def main():
 n='virtual_Ip';out=R/'inputs'/n;out.mkdir(exist_ok=True)
 for p in (SRC/'inputs'/n).iterdir():
  if p.is_file()and p.name not in ['INITIAL.npz','CASE.json']:link(p,out/p.name)
 a=np.load(SRC/'inputs'/n/'INITIAL.npz');old=trimesh.Trimesh(a['V'],a['F'],process=False);base=o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(a['V']),o3d.utility.Vector3iVector(a['F']));small=base.simplify_quadric_decimation(1280);V,F=np.asarray(small.vertices),np.asarray(small.triangles);np.savez_compressed(out/'INITIAL.npz',V=V,F=F,F_solid=F,inferred_base_faces=np.zeros(len(F),bool),boundary_vertex=np.zeros(len(V),bool))
 rg=np.load(out/'RING.npz');center=rg['V'].mean(0);save('inputs/'+n+'/NORMALIZATION.json',dict(center=center,scale_mm=10.,source='fixed CAD Ring R10; normalization only'));save('inputs/'+n+'/BASE_SELECTION.json',dict(selected_plane=[0,0,1,0],qualification='NO_OBSERVED_BASE_USED',plane_not_an_optimization_constraint=True));save('inputs/'+n+'/CHART.json',dict(D_mm=10.,tau_mm=.2))
 meta=load(SRC/'inputs'/n/'CASE.json')
 for i,v in enumerate(meta['views']):v.update(video='VIRTUAL_STATIC',direction_block=i+1)
 save('inputs/'+n+'/CASE.json',meta)
 gp=SRC/'audit_only'/n/'GT.npz';gt=np.load(gp);s=scene(gt['V'],gt['F']);cad=scene(rg['V'],rg['F']);gates=[]
 for v in meta['views']:
  z=np.load(out/(v['id']+'.npz'));zz=cast(s,z['K'],z['T'],360,640);rz=cast(cad,z['K'],z['T'],360,640);pred=np.isfinite(zz)&(zz<rz);target=z['labels']==1;iou=float((pred&target).sum()/max(1,(pred|target).sum()));gates.append(dict(view=v['id'],Open3D_native_GT_Mask_IoU=iou,pass_gate=iou>=.99))
 save('metrics/VIRTUAL_NATIVE_PROJECTION_GATE.json',dict(rows=gates,all_pass=all(x['pass_gate']for x in gates),GT_source=asset(gp),GT_use='virtual projection audit only; never optimizer input'))
 save('metrics/VIRTUAL_P0_RESOLUTION.json',dict(source=asset(SRC/'inputs'/n/'INITIAL.npz'),old_vertices=len(a['V']),old_faces=len(a['F']),new_vertices=len(V),new_faces=len(F),operation='one Open3D quadric decimation, target1280faces, no GT',native_surface_distance_mm=stats(np.r_[distance(scene(V,F),area_samples(a['V'],a['F'],4096)),distance(scene(a['V'],a['F']),area_samples(V,F,4096))]),new_watertight=trimesh.Trimesh(V,F,process=False).is_watertight))
 assert all(x['pass_gate']for x in gates),'Virtual projection gate failed; do not run optimization'
 fit=[v['id']for v in meta['views']if v['role']=='FIT'];one=[x for x in fit if'obs01'in x];held=[v['id']for v in meta['views']if v['role']!='FIT'];registry=[]
 for tag,ids,mode in [('V1_SINGLE',one,'COVERAGE'),('V3_SPREAD',fit,'COVERAGE'),('V3_COHERENT',fit,'COHERENT')]:
  root=R/'arms'/tag
  for d in ['inputs','config','local_results','metrics','runtime','provenance','depth_observations']:(root/d).mkdir(parents=True,exist_ok=True)
  dst=root/'inputs'/n;dst.mkdir(exist_ok=True)
  for p in out.iterdir():
   if p.is_file()and p.name!='CASE.json':link(p,dst/p.name)
  mm=dict(meta,views=[dict(v,role='FIT'if v['id']in ids else'UPDATE_HOLDOUT'if v['id']in held else'NOT_FIT_CONTROL')for v in meta['views']]);(dst/'CASE.json').write_text(json.dumps(mm,indent=2)+'\n')
  cfg=load(R/'config/PROTOCOL.json');budget=dict(max_proposals=10,max_accepted=5,consecutive_rejection_stop=5);(root/'config/PROTOCOL.json').write_text(json.dumps(cfg,indent=2)+'\n');(root/'config/ARM.json').write_text(json.dumps(dict(tag=tag,mode=mode,phase='virtual_control',loss='D0_013',budget=budget,depth_kind='NO_VIRTUAL_DEPTH_SUPERVISION'),indent=2)+'\n');registry.append(dict(case=n,tag=tag,kind='NEW_ROUTE',scene='virtual',script='train_virtual016.py',final=str(root/'local_results'/n/'FINAL.npz'),fit=ids,heldout=held))
 save('config/VIRTUAL_RUN_REGISTRY.json',registry);print('VIRTUAL_INPUTS_PREPARED',[(x['view'],x['Open3D_native_GT_Mask_IoU'])for x in gates],flush=True)
if __name__=='__main__':main()
