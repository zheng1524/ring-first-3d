"""Inventory small published deliverables and local artifacts, excluding itself."""
from audit import *
def main():
 rows=[]
 for p in sorted(R.rglob('*')):
  if not p.is_file():continue
  rel=p.relative_to(R).as_posix()
  if rel in ['provenance/FINAL_MANIFEST.json']or rel.startswith(('runtime/','local_results/','figures/local/','visualizations/','provenance/official_sources/')):continue
  rows.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p),public=True))
 local=[]
 for p in sorted((R/'local_results').rglob('*')):
  if p.is_file():local.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),status='LOCAL_ONLY'))
 save('provenance/FINAL_MANIFEST.json',dict(task='TASK-NEURAL-E0-COMPARE-001',time=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rows,local_model_and_geometry_artifacts=local,scientific_status='REPORTED_NO_EFFECTIVE_DUAL_ARM_COMPARISON',model_weights='LOCAL_ONLY, see MAP_DOWNLOAD_RECOVERY_RESULT and FROZEN_WEIGHT_LOCAL_SHA',self_hash_excluded=True,source_commits=load(R/'provenance/READING_AND_SOURCE_COMMITS.json')['source_commits'],mainline_modified=False,GT_mode='DENY',authorized_cleanup_exception='USER_AUTHORIZED_CLEANUP.json'))
 # Regenerate exact current image/index hashes after layout-only re-renders.
 gallery=[]
 for p in sorted((R/'figures').rglob('*.png')):gallery.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,kind='core'if p.parent==R/'figures'else'LOCAL_ONLY'))
 for p in sorted((GROW/'local_results/glb').glob('G01*.glb')):gallery.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,kind='HISTORICAL_LOCAL_ONLY_NOT_NEW_OUTPUT'))
 for p in sorted((R/'local_results/glb').glob('*.glb')):gallery.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,kind='NEW_LOCAL_ONLY_UNCERTIFIED'))
 table('provenance/GALLERY_AND_GLB_INDEX.csv',gallery)
 # The gallery table is updated above; bind its actual latest hash.
 data=load(R/'provenance/FINAL_MANIFEST.json')
 for x in data['files']:
  if x['path']=='provenance/GALLERY_AND_GLB_INDEX.csv':x.update(bytes=(R/x['path']).stat().st_size,sha256=sha(R/x['path']))
 save('provenance/FINAL_MANIFEST.json',data)
 print('MANIFEST',len(rows),'public small files',sum(x['bytes']for x in rows),'bytes',len(local),'local model files',flush=True)
if __name__=='__main__':main()
