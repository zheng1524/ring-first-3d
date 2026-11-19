"""Review-only ellipse vs actual Mesh region evidence from frozen native mappings."""
from pathlib import Path
import json,csv,html
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
TD=Path.cwd()/'experiments/TASK-E4-2D-CONTOUR-GUIDED-INIT-A-HERO-001';VIS=TD/'visualization';source=json.loads((TD/'inputs/SOURCES.json').read_text());rows=[];figures=[]
for group in source['real_groups']:
 g=group['group'];fit=[v for v in group['views']if v['role']=='FIT'];available=[]
 for v in fit:
  for method in ['H1','H2','H3','H4']:
   path=VIS/'HERO_CORRESPONDENCES'/g/method/(v['id']+'.npz')
   if not path.is_file():continue
   p=dict(np.load(path));ok=p['accepted'];delta=np.linalg.norm(p['mapped_uv']-p['original_uv'],axis=1);rows.append(dict(case=g,view=v['id'],video=v['video'],method=method,target_N=len(ok),accepted_N=int(ok.sum()),coverage=float(ok.mean()),native_pixel_shift_MAE=float(delta.mean()),unique_accepted_Body_faces=len(np.unique(p['face'][ok])),boundary_candidate_N=len(p['boundary_accepted'])if 'boundary_accepted'in p else None,boundary_accepted_N=int(p['boundary_accepted'].sum())if 'boundary_accepted'in p else None,Body_tolerance_mm=.5))
 selected=[]
 for video in ['004','005']:
  view=next((v for v in fit if v['video']==video and(VIS/'HERO_CORRESPONDENCES'/g/'H4'/(v['id']+'.npz')).is_file()),None)
  if view:selected.append(view)
 if not selected:continue
 fig,axes=plt.subplots(len(selected),4,figsize=(18,4*len(selected)),squeeze=False,layout='constrained')
 for row,v in enumerate(selected):
  cache=np.load(v['assets']['cache']['path']);pack=np.load(v['assets']['pack']['path']);A=cache['K']@np.linalg.inv(pack['K'])
  def transport(uv):
   q=np.c_[uv,np.ones(len(uv))]@A.T;return q[:,:2]/q[:,2:]
  for col,method in enumerate(['H1','H2','H3','H4']):
   ax=axes[row,col];path=VIS/'HERO_CORRESPONDENCES'/g/method/(v['id']+'.npz')
   if not path.is_file():ax.text(.1,.5,method+' NOT_EVALUABLE');ax.axis('off');continue
   p=dict(np.load(path));ax.imshow(cache['RGB']);ax.contour(cache['labels']==1,levels=[.5],colors='lime',linewidths=.7);ax.contour(cache['labels']==2,levels=[.5],colors='black',linewidths=.7);uv=transport(p['original_uv']);mapped=transport(p['mapped_uv']);ok=p['accepted'];take=np.flatnonzero(ok);take=take[np.linspace(0,len(take)-1,min(8,len(take)),dtype=int)]if len(take)else take
   for k in take:
    ax.annotate('',xy=mapped[k],xytext=uv[k],arrowprops=dict(arrowstyle='->',color='yellow',lw=.9));ax.text(*mapped[k],str(int(p['face'][k])),color='white',fontsize=5)
   bad=np.flatnonzero(~ok);bad=bad[np.linspace(0,len(bad)-1,min(30,len(bad)),dtype=int)]if len(bad)else bad
   if len(bad):ax.scatter(uv[bad,0],uv[bad,1],c='red',marker='x',s=10)
   if 'boundary_body_uv'in p:
    q=transport(p['boundary_body_uv']);bb=p['boundary_accepted'];ax.scatter(q[bb,0],q[bb,1],c='cyan',s=2,alpha=.6)
   ax.set_title(method+' / '+('ellipse'if method in ['H1','H2']else'actual visible Mesh contour')+'\n'+v['id']+'\naccepted %d/%d; labels=Body FaceID'%(ok.sum(),len(ok)),fontsize=8);ax.axis('off')
 fig.suptitle(g+' | Frozen native HERO pixels → frozen Body regions; arrows are candidate mappings, NOT image deformations\nRed X rejected; cyan actual accepted Mesh boundary; source image/calibrated pixel transport unchanged. Actual 3D barycentric points in NPZ.',fontsize=10);path=VIS/'figures'/(g+'_HERO_MAPPING_EVIDENCE.png');fig.savefig(path,dpi=115);plt.close(fig);figures.append(str(path.relative_to(VIS)))
(VIS/'MAPPING_DIAGNOSTICS.json').write_text(json.dumps(rows,indent=2)+'\n')
with(VIS/'MAPPING_DIAGNOSTICS.csv').open('w',newline='')as f:
 if rows:w=csv.DictWriter(f,list(rows[0]));w.writeheader();w.writerows(rows)
p=VIS/'index.html';text=p.read_text();text+='\n<h2>Additional frozen mapping evidence</h2><ul>'
for rel in ['MAPPING_DIAGNOSTICS.json','MAPPING_DIAGNOSTICS.csv']+figures:text+='<li><a href="'+html.escape(rel)+'">'+html.escape(rel)+'</a></li>'
p.write_text(text+'</ul>\n');print('Frozen mapping rows',len(rows),'PNG groups',len(figures))
