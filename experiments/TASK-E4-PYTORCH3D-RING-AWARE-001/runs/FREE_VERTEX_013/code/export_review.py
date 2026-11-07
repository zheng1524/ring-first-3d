from common import *
import shutil

def main():
 assert(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json').exists();index=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];out=R/'review_models'/n;out.mkdir(parents=True,exist_ok=True);rr=np.load(R/'inputs'/n/'RING.npz')
  for tag in ['FINAL011','FINAL012','FINAL013']:
   p=R/'local_results/metric'/n/(tag+'.npz');z=dict(np.load(p));np.savez_compressed(out/(tag+'_mm.npz'),**z);trimesh.Trimesh(z['V'],z['F_solid'],process=False).export(out/(tag+'_mm.ply'));sc=trimesh.Scene();body=trimesh.Trimesh(z['V']*.001,z['F_solid'],process=False);body.visual.face_colors=np.tile([157,83,175,255],(len(z['F_solid']),1));body.visual.face_colors[z['inferred_base_faces']]=[160,160,160,255];sc.add_geometry(body,node_name='polyp_body_inferred_base_gray');ring=trimesh.Trimesh(rr['V']*.001,rr['F'],process=False);ring.visual.face_colors=[8,8,8,255];sc.add_geometry(ring,node_name='fixed_CAD_Ring');(out/(tag+'_scene_m.glb')).write_bytes(sc.export(file_type='glb'));index.extend(asset(q)for q in out.glob(tag+'*'))
 save('assets_index/REVIEW_MODEL_INDEX.json',dict(files=index,NPZ_PLY_unit='mm',GLB_unit='m',GLB_presentation_conversion=.001,science_geometry_no_postprocessing=True));print('REVIEW_EXPORTED',len(index))
if __name__=='__main__':main()
