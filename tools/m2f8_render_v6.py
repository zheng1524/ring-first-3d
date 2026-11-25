import sys,json,pathlib
import numpy as np,trimesh
from matplotlib import pyplot as plt
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');BASE=WS/'runs/m2f8_v6_general';V=BASE/'v6';OUT=BASE/'visualization/v6_six_views';OUT.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(WS/'src')]
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
for root in sorted(V.glob('*_*')):
 g=root.name.rsplit('_',1)[0];v=root.name.rsplit('_',1)[1];kind='R5' if '_R5_' in g else 'R10';cad=dict(np.load(WS/f'runs/m2f5_unified/cad/{kind}.npz'));cam=np.load(root/'predictions/local005_camera_0.npz')['c2w'];ledger=json.loads((root/'inputs/ledger_actual.json').read_text());idx={x['id']:i for i,x in enumerate(ledger)};cases=[]
 for fn in ['MVS_supported_cases.json','MVS_cases.json']:
  p=root/'inputs'/fn
  if p.exists():cases+=json.loads(p.read_text())
 by={x['tag']:x for x in cases};meshes={}
 for p in sorted((root/'meshes').glob('*_Polyp.ply')):
  try:meshes[p.stem.replace('_Polyp','')]=trimesh.load(p,process=False)
  except:pass
 if not meshes:continue
 Vall=np.concatenate([m.vertices for m in meshes.values()])
 for tag,m in meshes.items():
  c=by.get(tag);ids=[c['reference_id']]+[ledger[i]['id'] for i in c['sources'][:2]] if c else [ledger[len(ledger)//2]['id']];center=m.vertices.mean(0);views=[]
  for k,vid in enumerate(ids):
   C=cam[idx[vid]];d=C[:3,3]-center;d/=np.linalg.norm(d);views.append((f'camera{k+1}',float(np.degrees(np.arcsin(d[2]))),float(np.degrees(np.arctan2(d[1],d[0])))))
  views += [('WorldX',0,0),('WorldY',0,90),('WorldZ',89.9999,0)]
  fig,ax=plt.subplots(1,6,figsize=(15,3))
  for k,(name,e,a) in enumerate(views):
   im,_=actual_mesh_image(m.vertices,m.faces,cad['V'],cad['F'],Vall,e,a,'#d98989');ax[k].imshow(im);ax[k].set_title(name,fontsize=8);ax[k].axis('off')
  fig.suptitle(f'V6-GENERALIZED {g}/{v}/{tag} | {kind} CAD');fig.tight_layout();fig.savefig(OUT/f'{g}_{v}_{tag}.png',dpi=90);plt.close(fig)
print('rendered',len(list(OUT.glob('*.png'))))
