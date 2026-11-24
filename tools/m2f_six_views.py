import sys,json,pathlib
import numpy as np,pandas as pd,trimesh,matplotlib
matplotlib.use('Agg');import matplotlib.pyplot as plt
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path.insert(0,str(WS/'src'));from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
O=WS/'runs/m2f_metric_depth_diagnosis';M=WS/'runs/m2e_historical_method_integration';V=O/'visualization';V.mkdir(parents=True,exist_ok=True)
GROUPS=['GP_Ip_12.0mm_closed_R10_single_refY','GP_Is_9.79mm_closed_R10_single_refY','GP_Is_14.0mm_closed_R10_single_refY']
exe=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');exe=exe[exe.group_id.isin(GROUPS)&(exe.status!='FAIL')];S=pd.read_csv(O/'selection/T13_SUPPORT_SELECTION_M2E.csv');S['video_id']=S.video_id.astype(int).map(lambda x:f'{x:03d}');S=S.set_index(['group_id','video_id','target_id'])
D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
def cams(g,v):
 cr=np.load(pathlib.Path(dmap[(g,v)].output_path)/'camera_result.npz');return {str(i):np.asarray(c,float) for i,c in zip(cr['ids'],cr['c2w'])}
def dir_view(C,center):
 d=center-C[:3,3];d/=np.linalg.norm(d);return np.degrees(np.arcsin(d[2])),np.degrees(np.arctan2(d[1],d[0]))
def render(v,f,cad,allv,e,a):
 img,_=actual_mesh_image(v,f,cad['V'],cad['F'],allv,e,a,'#d98989');return img
for g in GROUPS:
 sub=exe[exe.group_id==g];allv=np.concatenate([np.asarray(np.load(pathlib.Path(e.output_dir)/'RAW_NATIVE_MESH.npz')['V']) for _,e in sub.iterrows()],0);only=trimesh.Trimesh(allv,np.zeros((0,3),int)) if False else None;cad=np.load(WS/f'runs/m2e_historical_method_integration/cad/{"R5" if "R5" in g else "R10"}.npz')
 for _,e in sub.iterrows():
  gid,v,target=g,f'{int(e.video_id):03d}',e.target_id;out=pathlib.Path(e.output_dir);raw=np.load(out/'RAW_NATIVE_MESH.npz');Vv=raw['V'];Ff=raw['F'];cleanp=out/'Conservative_cleaned_mesh.ply';Cmap=cams(g,v);s=S.loc[(g,v,target)];sups=str(s.support_ids).split(';');center=Vv.mean(0);views=[('View 1 target',*dir_view(Cmap[target],center)),('View 2 support1',*dir_view(Cmap[sups[0]],center)),('View 3 support2',*dir_view(Cmap[sups[1]],center)),('World X',0,0),('World Y',0,90),('World Z',89.9999,0)];imgs=[]
  for label,v,f in [('Raw',Vv,Ff),('Cleaned',None,None)]:
   if label=='Cleaned':
    if not cleanp.exists():continue
    m=trimesh.load(cleanp,process=False);v=m.vertices;f=m.faces
   for name,el,az in views:imgs.append((f'{label} {name}',render(v,f,cad,allv,el,az)))
  fig,ax=plt.subplots(2,6,figsize=(18,6))
  for k,(t,img) in enumerate(imgs[:12]):ax[k//6,k%6].imshow(img);ax[k//6,k%6].set_title(t,fontsize=8);ax[k//6,k%6].axis('off')
  fig.suptitle(f'{g} | {target} | fixed group metric bounds | black Ring CAD | 6 real/X/Y/Z views');fig.tight_layout();fig.savefig(V/'original_19_surfaces'/f'{g}_{target}.png',dpi=100) if (V/'original_19_surfaces').mkdir(parents=True,exist_ok=True) is None else None;plt.close(fig)
 # multisurface contact
 Vs=[];Fs=[];cols=[]
 palette=[(.86,.36,.36),(.25,.55,.82),(.28,.72,.45),(.86,.67,.15),(.55,.35,.75),(.15,.75,.75),(.8,.4,.7),(.5,.5,.2)]
 for k,(_,e) in enumerate(sub.iterrows()):
  d=np.load(pathlib.Path(e.output_dir)/'RAW_NATIVE_MESH.npz');Vs.append(d['V']);Fs.append(d['F']+sum(len(x) for x in Vs[:-1]));cols.append(np.tile(palette[k%len(palette)],(len(d['F']),1)))
 Vc=np.concatenate(Vs);Fc=np.concatenate(Fs);fc=np.concatenate(cols);fig,ax=plt.subplots(1,3,figsize=(12,4))
 for k,(name,el,az) in enumerate([('real',20,-60),('World X',0,0),('World Z',89.9999,0)]):
  img,_=actual_mesh_image(Vc,Fc,cad['V'],cad['F'],allv,el,az,'#d98989',face_colors=fc);ax[k].imshow(img);ax[k].set_title(name);ax[k].axis('off')
 fig.suptitle(f'{g} | {len(sub)} HERO surfaces in one video world | colours=source target');fig.tight_layout();(V/'multisurface_six_views').mkdir(parents=True,exist_ok=True);fig.savefig(V/'multisurface_six_views'/f'{g}.png',dpi=110);plt.close(fig)
print('targets',len(list((V/'original_19_surfaces').glob('*.png'))),'multi',len(list((V/'multisurface_six_views').glob('*.png'))))
