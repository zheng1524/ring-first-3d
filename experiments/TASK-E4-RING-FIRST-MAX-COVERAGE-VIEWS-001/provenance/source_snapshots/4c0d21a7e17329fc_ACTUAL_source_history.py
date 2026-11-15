"""Preserve code-version receipts; reconstruct only when SHA matches prior freeze.
Never claim an approximate reconstruction is the code that ran.
"""
from context import *
def main():
 wanted=collections.defaultdict(set)
 for p in(N/'provenance').glob('*.json'):
  try:r=load(p)
  except Exception:continue
  for a in r.get('files',[])if isinstance(r,dict)else[]:
   if isinstance(a,dict)and str(N/'code')in a.get('path',''):wanted[Path(a['path']).name].add(a['sha256'])
 variants={}
 for p in(N/'code').glob('*.py'):variants[p.name]=[p.read_text()]
 ca=variants['cameras.py'][0];ca=ca.replace("def sample(a,n):\n idx=np.linspace(0,len(a)-1,min(n,len(a)),dtype=int) if len(a) else []\n return [a[i] for i in idx] if isinstance(a,list) else a[idx] if len(a) else a", "def sample(a,n):return a[np.linspace(0,len(a)-1,min(n,len(a)),dtype=int)]if len(a)else a");variants['cameras.py'].append(ca)
 s=variants['rgb.py'][0];start=s.index("X=np.array([r['X']for r in rs]);native005=");end=s.index("out[role]=",start);variants['rgb.py'].append(s[:start]+"X=np.array([r['X']for r in rs]);uv,z=projection(X,C,np.array(v['K']));"+s[end:]);variants['rgb.py'].append(s.replace("D=np.array(v.get('evaluation_map_H',reg['source_H']['005']));map004","D=np.array(reg['source_H']['005']);map004"))
 s=variants['register.py'][0];s=s.replace("getattr(self,'label',self.mode)","self.mode");variants['register.py'].append(s);s=s.replace("load(v.get('rgb_geometry_path',N/'inputs'/c/'RGB_GEOMETRY.json'))","load(N/'inputs'/c/'RGB_GEOMETRY.json')");s=s.replace("rp=Path(v.get('rgb_geometry_path',N/'inputs'/v['id']/'RGB_GEOMETRY.json'));rr=load(rp)if rp.exists()else dict(matches=[],fit_pnp_inliers=[])","rr=load(N/'inputs'/v['id']/'RGB_GEOMETRY.json')if(N/'inputs'/v['id']/'RGB_GEOMETRY.json').exists()else dict(matches=[],fit_pnp_inliers=[])");variants['register.py'].append(s)
 rows=[]
 for name,hashes in wanted.items():
  found={hashlib.sha256(s.encode()).hexdigest():s for s in variants.get(name,[])}
  for h in hashes:
   text=found.get(h);path=N/'provenance/source_snapshots'/(h[:16]+'_ACTUAL_'+name)
   if text is not None:path.write_text(text)
   rows.append(dict(file=name,expected_frozen_sha256=h,exact_source_recovered=text is not None,archive=str(path.relative_to(N))if text is not None else None,unrecovered_not_claimed_equivalent=text is None))
 # Always snapshot final reproducible candidate source under its exact hash.
 for p in(N/'code').glob('*.*'):
  if p.suffix not in ['.py','.html']:continue
  d=N/'provenance/source_snapshots'/('FINAL_'+sha(p)[:16]+'_'+p.name);shutil.copyfile(p,d)
 save('provenance/CODE_VERSION_HISTORY_RECOVERY.json',rows);print('EXACT_SOURCE_RECOVERED',sum(r['exact_source_recovered']for r in rows),'/',len(rows),flush=True)
if __name__=='__main__':main()
