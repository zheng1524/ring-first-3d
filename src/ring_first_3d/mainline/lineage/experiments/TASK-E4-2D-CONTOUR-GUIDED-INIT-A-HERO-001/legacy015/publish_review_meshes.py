"""Compact exact geometry copies for review; no source observations/weights."""
from common import *

def main():
 marker=load(R/'provenance/ALL_PREDICTIONS_AND_SCALE_FROZEN_BEFORE_GT.json');records=[]
 for model in load(R/'config/EVAL_MODELS.json'):
  src=Path(model['source']);n,t=model['case'],model['label'];z=np.load(src);out=R/'review_meshes'/n/(t+'.npz');out.parent.mkdir(parents=True,exist_ok=True);keys=['V','F','F_solid','inferred_base_faces','boundary_vertex'];data={k:z[k]for k in keys if k in z};np.savez_compressed(out,**data);b=np.load(out);assert all(np.array_equal(b[k],z[k])for k in data);records.append(dict(case=n,label=t,source=asset(src),review_copy=asset(out),coordinates='original unaligned Ring-First mm',geometry_identical=True,postprocessing='none; removed only non-geometric optimizer/basis arrays'))
 for c in load(R/'provenance/FROZEN_FINAL_BODIES_FIT_ONLY.json')['bodies']:
  z=np.load(c['path']);n=c['case'];out=R/'review_meshes'/n/'BODY_FINAL_mm.ply';trimesh.Trimesh(z['V'],z['F_solid'],process=False).export(out);records.append(dict(case=n,label='FIT_ONLY_BODY_FINAL',source=c,review_PLY=asset(out),inferred_cap_marked_in_corresponding_NPZ=True,scale_changed=False))
 save('metrics/REVIEW_MESH_COPY_INDEX.json',records);print('EXACT_REVIEW_MESH_COPIES',len(records),flush=True)
if __name__=='__main__':main()
