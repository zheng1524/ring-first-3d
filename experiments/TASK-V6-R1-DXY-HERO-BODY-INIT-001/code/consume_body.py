"""Read-only coarse initializer interface. Reconstruct trusted work copies without editing Raw/Clean."""
from core import *
import trimesh
def load_configuration(result_path):
 result_path=Path(result_path);r=read(result_path);folder=result_path.parent
 for item in read(folder/'COMPLETE.json')['files']:asset(item['path'],item['sha256'])
 if r['status']!='COARSE_INIT_COMPLETE':raise ValueError('Configuration is not a completed initializer')
 result=dict(record=r,parent=dict(np.load(folder/'PARENT.npz')),uncut=dict(np.load(folder/'FINAL_UNCUT.npz')),body=dict(np.load(folder/'BODY.npz')),base=read(folder/'BASE.json'))
 if(folder/'VISIBILITY.json').exists():
  vr=read(folder/'VISIBILITY.json')
  for item in vr['files']:asset(item['path'],item['sha256'])
  result['visibility']=dict(np.load(folder/'VISIBILITY.npz'));result['visibility_metadata']=vr
 return result
def corrected_source(result_path,source_id):
 data=load_configuration(result_path);r=data['record'];bias=next(v['b_mm']for v in r['bias']if v['source_id']==source_id)
 sources=[]
 for p in r['source_indices']:sources+=read(p)['sources']
 s=next(x for x in sources if x['source_id']==source_id);source=s['source']
 for f in s['source_files']:asset(f['path'],f['sha256'])
 mesh=trimesh.load(source['raw_mesh'],process=False);V=np.asarray(mesh.vertices);F=np.asarray(mesh.faces);ids=np.load(source['selection'])['trusted_original_face_id'];Tlocal=np.array(source['T_local_to_common']);native=np.load(source['native_depth']);C=Tlocal@native['c2w'][source['reference']]
 raw=V@Tlocal[:3,:3].T+Tlocal[:3,3];corrected=raw.copy();used=np.unique(F[ids]);q=(raw[used]-C[:3,3])@C[:3,:3];Z=q[:,2]
 if not np.all(Z>0):raise ValueError('Nonpositive trusted vertex depth')
 q*=((Z-bias)/Z)[:,None];corrected[used]=q@C[:3,:3].T+C[:3,3]
 return dict(V=corrected,F=F[ids],original_V_common=raw,original_face_id=ids,bias_mm=bias,c2w_common=C,K_native=native['K_index_native'],units='mm',coordinate_frame='COMMON',correction='trusted vertices only, along their original target rays; background/CAD unchanged',source=source)
