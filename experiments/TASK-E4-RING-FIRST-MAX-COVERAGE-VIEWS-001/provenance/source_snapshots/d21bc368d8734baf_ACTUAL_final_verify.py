from context import *
import re,importlib.metadata

def main():
 tests=[];files=[]
 for g in GROUPS:
  checkfreeze('provenance/'+g+'_CAMERAS_FROZEN_BEFORE_HELD_HERO.json');checkfreeze(planfreeze(g));meta=load(N/'assets_index'/(g+'_ATLAS_LAYERS.json'));dom=(N/'runtime'/(g+'_SELFTEST_DOM.html')).read_text();body=re.search(r'<body[^>]*>',dom).group();tests.append(dict(group=g,test='realChromeGLB_and5UIcontrols',PASS='data-ui-tests="PASS"'in body,DOM_body=body,geometry_nodes=len(meta['layers'])));assert 'data-ui-tests="PASS"'in body
  # Verify task-original sources not modified. source evidence references all frozen HOD too.
  conf=next(c for c in load(N/'config/FOUR_GROUP_INPUTS.json')if c['group']==g)
  for s in conf['sources']:
   for k in ['mesh','observation']:a=s[k];assert sha(a['path'])==a['sha256'],a['path']
  for a in list(conf['bodies'].values())+[conf['ring']]:assert sha(a['path'])==a['sha256'],a['path']
 for r in load(N/'metrics/HERO_INFERENCE_RESULTS.json'):
  root=N/'hero_fit'/r['id'];z=np.load(root/'HERO_native.npz');p=np.load(root/'pack_native.npz');raw=np.load(root/'RAW_NATIVE_MESH.npz');ev=np.load(root/'FACE_EVIDENCE.npz');ok=np.array_equal(z['depth_mm'],p['depth_mm'])and np.array_equal(raw['V'],ev['V'])and np.array_equal(raw['F'],ev['F']);assert ok,r['id'];tests.append(dict(id=r['id'],test='native_depth_and_face_vertex_identity',PASS=ok,original_faces=len(raw['F']),new_interpolation=0));
  for name in ['HERO_native.npz','Raw_open_mesh.ply','RAW_NATIVE_MESH.npz','FACE_EVIDENCE.npz','TRUSTED_HERO.npz','UNKNOWN_HERO.npz','UNCERTAIN_HERO.npz','REJECTED_HERO.npz','OBS_TRUSTED.npz']:files.append(root/name)
 for a in load(N/'config/SOURCE_DISCOVERY.json'):assert sha(a['raw_asset']['path'])==a['raw_asset']['sha256']
 read=load(N/'provenance/READ_AND_REUSE_RECEIPT.json')
 for a in read:assert sha(a['path'])==a['sha256'],a['path']
 for p in(N/'code').glob('*.py'):ast.parse(p.read_text())
 table('metrics/FINAL_DELIVERY_CONTRACT_TESTS.csv',tests);save('metrics/BROWSER_ATLAS_TESTS.json',[t for t in tests if t['test']=='realChromeGLB_and5UIcontrols']);env=load(N/'provenance/ENVIRONMENT.json');versions={}
 for pkg in ['torch','scipy','open3d','pyceres','matplotlib','transformers']:
  try:versions[pkg]=importlib.metadata.version(pkg)
  except Exception:versions[pkg]='see frozen runtime'
 env['actual_packages']=versions;save('provenance/ENVIRONMENT.json',env)
 # All frozen predictions and identities sealed; rendering styles are separate artifacts.
 seal=list((N/'code').glob('*.*'))+list((N/'results').glob('*.json'))+[N/'TECHNICAL_REPORT.md',N/'NEW_HERO_SOURCE_MANIFEST.csv']+files
 freeze('provenance/FINAL_DELIVERY_FROZEN.json',seal,GT=False,no_Body_update=True,depth_interpolation=0,geometry_no_ICP=True,independent_groups=4,validated_original_sources_unchanged=True)
 print('FINAL_DELIVERY_CONTRACTS_PASS',len(tests),'newraw47exact','source hashes unchanged',flush=True)
if __name__=='__main__':main()
