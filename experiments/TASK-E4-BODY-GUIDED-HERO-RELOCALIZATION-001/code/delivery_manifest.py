"""Review-sized delivery; large local native meshes and caches indexed honestly."""
from common import *
import ast

def main():
 assert (R/'provenance/FINAL_IMMUTABILITY_CHECK.json').exists()
 code=[]
 for p in sorted((R/'code').glob('*.py')):
  t=ast.parse(p.read_text());code.append('- `'+p.name+'`: '+', '.join(n.name+' @ L'+str(n.lineno)for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))))
 (R/'CODE_MAP.md').write_text('# 实际源码位置\n\n'+'\n'.join(x.rstrip() for x in code)+'\n')
 # Index archived engineering evidence; not all local archives are uploaded.
 archived=[asset(p)for p in (R/'runtime').rglob('*')if p.is_file()and any(k in str(p)for k in ['CONTRACT_FIX','BOUND_CONTRACT_FIX','IMPORT_AND_SPLIT_FIX'])];save('assets_index/ENGINEERING_ARCHIVES_LOCAL.json',archived)
 files=[]
 for pattern in ['*.md','.gitignore','code/*.py','config/*.json','provenance/*.json','assets_index/*.json','metrics/*.csv','metrics/*.json','controls/*.json','figures/*.png','local_results/G*/Body-?.npz','local_results/G*/Body-E_FIT.json','local_results/G*/Body-E_mm.ply','local_results/G*/Body-*/*/CANDIDATES_FROZEN.json','controls/results/*/*/CANDIDATES_FROZEN.json']:
  for p in sorted(R.glob(pattern)):
   if p.stat().st_size<=5_000_000 and p.name not in ['PER_PAIR.json','GIT_DELIVERY_MANIFEST.json']:files.append(p)
 files=sorted(set(files));save('assets_index/GIT_DELIVERY_MANIFEST.json',dict(epoch=time.time(),files=[asset(p)for p in files],not_uploaded=['full original RGB/HERO/Mask','large per-seed binary traces','derived complete HERO meshes','GLB','most runtime archives'],large_local_assets_index=str(R/'assets_index/LOCAL_RESULT_FILES.json')))
 # The manifest itself is included, without attempting a self-SHA fixed point.
 files.append(R/'assets_index/GIT_DELIVERY_MANIFEST.json');(R/'runtime/GIT_EXPLICIT_PATHS.txt').write_text('\n'.join(str(p.relative_to(REPO))for p in sorted(set(files)))+'\n');print('DELIVERY_FILES',len(set(files)),'MiB',sum(p.stat().st_size for p in set(files))/2**20)
if __name__=='__main__':main()
