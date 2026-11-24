import sys,json,pathlib
import numpy as np,pandas as pd,trimesh,matplotlib
matplotlib.use('Agg');import matplotlib.pyplot as plt
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path.insert(0,str(WS/'src'))
from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
O=WS/'runs/m2e_historical_method_integration';A=O/'a_to_b';V=O/'visualization';V.mkdir(parents=True,exist_ok=True)
a2=pd.read_csv(A/'A_TO_B_METRICS.csv');exe=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');exe=exe[exe.status!='FAIL']
g=exe.groupby('group_id').agg(n=('target_id','size')).reset_index();gm=a2.groupby('group_id').agg(cov=('target_coverage','median'),mae=('RGB_MAE_0_255','median')).reset_index();gm=gm.merge(g,on='group_id').sort_values(['cov','mae'])
# auto 8: extremes + ring/morphology spread
sel=pd.concat([gm.head(3),gm.tail(3),gm[gm.group_id.str.contains('R5')].head(1),gm[gm.group_id.str.contains('R10')].head(1)]).drop_duplicates('group_id').head(8)
sel['selection_rule']='auto: coverage/MAE extremes + R5/R10 spread';sel.to_csv(O/'analysis/REPRESENTATIVE_CASE_SELECTION.csv',index=False)
views=[(20,-60),(20,60),(20,180),(0,0),(0,90),(0,180)]; titles=['real-ish 1','real-ish 2','real-ish 3','world X','world Y','world Z']
for _,row in sel.iterrows():
 gid=row.group_id; sub=exe[exe.group_id==gid].head(1); r=sub.iloc[0]; out=pathlib.Path(r.output_dir)
 raw=np.load(out/'RAW_NATIVE_MESH.npz');Vv=raw['V'];Ff=raw['F'];cleanp=out/'Conservative_cleaned_mesh.ply'
 cad=np.load(O/'cad'/(('R5.npz') if 'R5' in gid else 'R10.npz'));RV,RF=cad['V'],cad['F']
 imgs=[]
 for label,v,f in [('Raw',Vv,Ff),('Cleaned',None,None)]:
  if label=='Cleaned':
   if not cleanp.exists():continue
   m=trimesh.load(cleanp,process=False);v=m.vertices;f=m.faces
  for e,a in views:
   img,_=actual_mesh_image(v,f,RV,RF,Vv,e,a,'#d98989' if label=='Raw' else '#5aa6d8');imgs.append((f'{label} {titles[len(imgs)%6]}',img))
 if not imgs:continue
 fig,ax=plt.subplots(2,6,figsize=(18,6))
 for k,(t,img) in enumerate(imgs[:12]): ax[k//6,k%6].imshow(img);ax[k//6,k%6].set_title(t,fontsize=8);ax[k//6,k%6].axis('off')
 fig.suptitle(f'{gid} | Raw vs Conservative Cleaned | actual triangles | Ring CAD black | fixed mm bounds');fig.tight_layout();fig.savefig(V/'six_view'/f'{gid}.png',dpi=110) if (V/'six_view').mkdir(parents=True,exist_ok=True) is None else None;plt.close(fig)
print('selected',sel.group_id.tolist());print('six',len(list((V/'six_view').glob('*.png'))))
