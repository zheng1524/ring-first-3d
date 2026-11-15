"""Portable scientific output bundle; no raw videos, checkpoint weights or environment."""
from context import *
import tarfile,gzip

def main():
 out=N/'local_results';dest=out/'selected_inputs';dest.mkdir(exist_ok=True);plans=[];selected={}
 for g in GROUPS:
  plans+=load(selpath(g,'_HERO_PLAN.json'))
 for r in plans:
  for v in [r['target']]+r['support_views']:selected[v['id']]=v
 cacheindex=[]
 for cid,v in selected.items():
  src=Path(v['cache']);p=dest/(cid+'.npz')
  if not p.exists():shutil.copyfile(src,p)
  cacheindex.append(dict(id=cid,group=v['group'],RGB_original_SHA256=v['RGB_SHA256'],cache=asset(p),RGB_source=v['RGB_source'],Mask_source=v['Mask_source'],C=v['C'],K=v['K']))
 save('assets_index/FROZEN_HERO_INPUT_CACHES.json',cacheindex);portable=[];extra=[]
 for conf in load(N/'config/FOUR_GROUP_INPUTS.json'):
  g=conf['group']
  for k,b in conf['bodies'].items():extra.append((Path(b['path']),f'portable_inputs/{g}/{k}_BODY.npz'))
  extra.append((Path(conf['ring']['path']),f'portable_inputs/{g}/RING.npz'))
  for s in conf['sources']:
   row=dict(group=g,id=s['id'],role=s['role'],video=s['video'],evaluation_only=s.get('evaluation_only',False))
   for key in ['mesh','observation']:
    a=s[key];arc=f'portable_inputs/{g}/{s["id"]}/{key}.npz';extra.append((Path(a['path']),arc));row[key]=dict(original=a,archive_path=arc)
   portable.append(row)
 for g in GROUPS:
  for vid in ['004','005']:
   p=G/'landmarks'/(g+'_'+vid+'.npz');o=p.with_name(p.stem+'_OBSERVATIONS.json')
   if p.exists():extra.append((p,'portable_inputs/RGB_MAPS/'+p.name));extra.append((o,'portable_inputs/RGB_MAPS/'+o.name))
 save('assets_index/PORTABLE_BASELINE_GEOMETRY.json',portable)
 own=[]
 for folder in ['hero_fit','local_results/interactive','local_results/selected_inputs','local_results/diagnostic_evaluation','registration','inputs','features','ring_evidence','selection','selection_verified','evaluation','optimization']:
  own +=[p for p in(N/folder).rglob('*')if p.is_file()and not p.is_symlink()]
 rows=[dict(path=str(p),relative=str(p.relative_to(N)),bytes=p.stat().st_size,sha256=sha(p),archive_member=N.name+'/'+str(p.relative_to(N)),kind='generated scientific output / cached RGB inputs, no weights/video')for p in sorted(set(own))]
 rows +=[dict(path=str(p),relative=arc,bytes=p.stat().st_size,sha256=sha(p),archive_member=N.name+'/'+arc,kind='read-only frozen baseline/realRGBmap copied only into transport bundle')for p,arc in extra]
 table('assets_index/LARGE_ASSET_MANIFEST.csv',rows);save('assets_index/LARGE_ASSET_MANIFEST.json',rows)
 # Package exact scientific outputs and logs; original raw videos/weights excluded.
 pack=out/(N.name+'_SCIENTIFIC_OUTPUTS.tar.gz');public=[]
 for folder in ['code','config','provenance','metrics','results','figures','assets_index']:public +=[p for p in(N/folder).rglob('*')if p.is_file()and not p.is_symlink()and p.name!='SCIENTIFIC_OUTPUT_BUNDLE.json']
 public +=[p for p in N.iterdir()if p.is_file()and p.suffix in ['.md','.csv','.html','.json']]
 public +=[p for p in(N/'runtime/logs').glob('*.log')if p.is_file()]
 paths=sorted(set(own+public));start=time.time()
 with pack.open('wb')as f:
  with gzip.GzipFile(filename='',fileobj=f,mode='wb',compresslevel=1,mtime=0)as gz:
   with tarfile.open(fileobj=gz,mode='w|')as tar:
    for p in paths:tar.add(p,arcname=N.name+'/'+str(p.relative_to(N)),recursive=False)
    for p,arc in extra:tar.add(p,arcname=N.name+'/'+arc,recursive=False)
 save('assets_index/SCIENTIFIC_OUTPUT_BUNDLE.json',dict(bundle=asset(pack),file_count=len(paths)+len(extra),archive_top=N.name,archive_format='tar.gz, file/data hashes in LARGE_ASSET_MANIFEST',raw_videos_included=False,model_weights_included=False,environments_included=False,originals_modified=False,created_seconds=time.time()-start,recovery='REPRODUCE.md: local cp or authenticated scp from research workstation, verify SHA256 then tar -xzf; no public cloud link fabricated'))
 print('SCIENTIFIC_BUNDLE_DONE',pack,pack.stat().st_size,flush=True)
if __name__=='__main__':main()
