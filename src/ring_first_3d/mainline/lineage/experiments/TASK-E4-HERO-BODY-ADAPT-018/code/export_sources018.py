"""Complete original-face normal/label exports; derived metadata only, no geometry edits."""
from common import *
def main():
 rows=[]
 for r in load(R/'config/VIEW_PLAN.json'):
  folder=R/('hero_fit'if r['role']=='FIT'else'holdout/hero')/r['view_id'];a=np.load(folder/'FACE_EVIDENCE.npz');V,F=a['V'],a['F'];norm=trimesh.Trimesh(V,F,process=False).face_normals.copy();T=a['T'];ctr=V[F].mean(1);norm[((T[:3,3]-ctr)*norm).sum(1)<0]*=-1;np.savez_compressed(folder/'ORIGINAL_FACE_NORMALS.npz',face_id=np.arange(len(F)),normal=norm,camera_facing=True,source_F_sha256=sha(folder/'FULL_HERO.npz'));area=trimesh.triangles.area(V[F]);c=load(folder/'CLEANING.json');row=dict(group=r['group'],view_id=r['view_id'],role=r['role'],original_faces=len(F),original_area_mm2=float(area.sum()),native_FULL_N=c['full_native_observations'],native_TRUSTED_N=c['trusted_native_observations'],TRUSTED_component_N=c['trusted_components'],largest_TRUSTED_component_mm2=c['largest_trusted_component_area_mm2'])
  for code,name in enumerate(['TRUSTED','UNCERTAIN','REJECTED','UNKNOWN']):row[name+'_faces']=int((a['state']==code).sum());row[name+'_area_mm2']=float(area[a['state']==code].sum())
  rows.append(row)
 save('metrics/ALL_SOURCE_AREAS_LABELS_AND_CONTINUITY.json',rows);table('metrics/ALL_SOURCE_AREAS_LABELS_AND_CONTINUITY.csv',rows)
 save('config/DERIVED_SOURCE_EXPORT_RULE.json',dict(label_codes={'0':'TRUSTED','1':'UNCERTAIN','2':'REJECTED','3':'UNKNOWN'},face_id='original Raw triangle index, no vertex welding or coordinate changes',FULL='original native positive Polyp depth before CAD, including original Raw-mesher orphan pixels',TRUSTED='exact original Raw face subset state0',normals='original triangle normals, flipped only as vectors toward source camera; no vertex/face geometry change',quality_metrics='FACE_EVIDENCE.npz uses original017 metrics/reason_bits; FINAL_CLEANING_RULE source is original017',source_area_caveat='per-source area, not union area across overlapping views'))
 print('ALL43_ORIGINAL_NORMALS_AND_LABEL_TABLES_EXPORTED',flush=True)
if __name__=='__main__':main()
