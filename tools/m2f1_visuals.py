import sys,json,pathlib
import numpy as np,pandas as pd,trimesh,matplotlib
matplotlib.use('Agg');import matplotlib.pyplot as plt
WS=pathlib.Path('/home/liu/ring_first_3d_workspace');sys.path.insert(0,str(WS/'src'));from ring_first_3d.mainline.native._mesh_renderer import actual_mesh_image
O=WS/'runs/m2f1_w0_admission_restoration';V=O/'visualization';V.mkdir(parents=True,exist_ok=True);G=['GP_Ip_12.0mm_closed_R10_single_refY','GP_Is_9.79mm_closed_R10_single_refY','GP_Is_14.0mm_closed_R10_single_refY'];e=pd.read_csv(O/'hero/HERO_EXECUTION_RESULTS.csv');e=e[e.group_id.isin(G)];S=pd.read_csv(O/'selection/FINAL_HERO_TUPLES.csv');S['video_id']=S.video_id.astype(int).map(lambda x:f'{x:03d}');S=S.set_index(['group_id','video_id','arm','target_id']);D=pd.read_csv(WS/'runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv');dmap={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
def cams(g,v):
 cr=np.load(pathlib.Path(dmap[(g,v)].output_path)/'camera_result.npz');return {str(i):np.asarray(c,float) for i,c in zip(cr['ids'],cr['c2w'])}
def view_from_cam(C,center):
 d=C[:3,3]-center;d/=np.linalg.norm(d);return np.degrees(np.arcsin(d[2])),np.degrees(np.arctan2(d[1],d[0]))
for g in G:
 sub=e[e.group_id==g]; cad=np.load(O/'cad'/('R5.npz' if 'R5' in g else 'R10.npz'));Vall=np.concatenate([np.load(pathlib.Path(r.output_dir)/'RAW_NATIVE_MESH.npz')['V'] for _,r in sub.iterrows()],0)
 for video in sorted(sub.video_id.unique()):
  vv=f'{int(video):03d}';sv=sub[sub.video_id==video];r=sv.iloc[0];out=pathlib.Path(r.output_dir);raw=np.load(out/'RAW_NATIVE_MESH.npz');Vv=raw['V'];Ff=raw['F'];Cmap=cams(g,vv);st=S.loc[(g,vv,r.arm,r.target_id)];sup=str(st.support_ids).split(';');center=Vv.mean(0);views=[('View 1 target',*view_from_cam(Cmap[r.target_id],center)),('View 2 support',*view_from_cam(Cmap[sup[0]],center)),('View 3 support',*view_from_cam(Cmap[sup[1]],center)),('World X',0,0),('World Y',0,90),('World Z',89.9999,0)];img=[]
  for k,(name,el,az) in enumerate(views):img.append((name,actual_mesh_image(Vv,Ff,cad['V'],cad['F'],Vall,el,az,'#d98989')[0]))
  fig,ax=plt.subplots(1,6,figsize=(18,3.5))
  for k,(name,im) in enumerate(img):ax[k].imshow(im);ax[k].set_title(name,fontsize=8);ax[k].axis('off')
  fig.suptitle(f'{g}/{vv} | new gated HERO {r.target_id} | correct viewer directions | black Ring CAD');fig.tight_layout();(V/'representative_three_groups').mkdir(parents=True,exist_ok=True);fig.savefig(V/'representative_three_groups'/f'{g}_{vv}.png',dpi=100);plt.close(fig)
  # multisurface same video
  if len(sv)>1:
   Vs=[];Fs=[];cols=[];pal=[(.86,.36,.36),(.25,.55,.82),(.28,.72,.45),(.86,.67,.15),(.55,.35,.75)]
   for k,(_,x) in enumerate(sv.iterrows()):
    d=np.load(pathlib.Path(x.output_dir)/'RAW_NATIVE_MESH.npz');off=sum(len(a) for a in Vs);Vs.append(d['V']);Fs.append(d['F']+off);cols.append(np.tile(pal[k%len(pal)],(len(d['F']),1)))
   Vc=np.concatenate(Vs);Fc=np.concatenate(Fs);fc=np.concatenate(cols);fig,ax=plt.subplots(1,3,figsize=(12,4))
   for k,(name,el,az) in enumerate([('real',*view_from_cam(Cmap[r.target_id],center)),('World X',0,0),('World Z',89.9999,0)]):
    im,_=actual_mesh_image(Vc,Fc,cad['V'],cad['F'],Vall,el,az,'#d98989',face_colors=fc);ax[k].imshow(im);ax[k].set_title(name);ax[k].axis('off')
   fig.suptitle(f'{g}/{vv} | {len(sv)} new surfaces | colours=target');fig.tight_layout();(V/'multisurface_by_video').mkdir(parents=True,exist_ok=True);fig.savefig(V/'multisurface_by_video'/f'{g}_{vv}.png',dpi=110);plt.close(fig)
print('three',len(list((V/'representative_three_groups').glob('*.png'))),'multi',len(list((V/'multisurface_by_video').glob('*.png'))))
