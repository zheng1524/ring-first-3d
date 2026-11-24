import pathlib,json,cv2,numpy as np,pandas as pd,subprocess
from pathlib import Path
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
O=Path('runs/m2d_w0_mvs_validation'); H=O/'hero'; V=O/'visualization'; V.mkdir(parents=True,exist_ok=True)
exe=pd.read_csv(H/'HERO_EXECUTION_RESULTS.csv'); met=pd.read_csv(H/'HERO_SURFACE_METRICS.csv'); a2b=pd.read_csv(O/'a_to_b/A_TO_B_METRICS.csv'); ind=pd.read_csv(O/'a_to_b/INDEPENDENT_VIEW_METRICS.csv')
D=pd.read_csv('runs/m2c_corrective_completion/W0_79_VIDEO_RESULTS.csv'); dm={(r.group_id,f'{int(r.video_id):03d}'):r for _,r in D.iterrows()}
# group MVS sheets: 2x2 tuple images, existing tuple images
sheetdir=V/'all_group_mvs_contact_sheets'; sheetdir.mkdir(parents=True,exist_ok=True)
for g,sub in exe[exe.status=='PASS'].groupby('group_id'):
 imgs=[]
 for _,r in sub.drop_duplicates('output_dir').head(4).iterrows():
  p=O/'visualization/all_group_mvs_contact_sheets'/f'{r.group_id}_{r.video_id}_{r.tuple_id}.png'
  if p.exists():
   im=cv2.imread(str(p)); imgs.append(cv2.resize(im,(640,220)))
 if not imgs: continue
 canvas=np.full((460,1280,3),255,np.uint8); cv2.putText(canvas,f'{g}  HERO targets {len(sub)}',(8,22),cv2.FONT_HERSHEY_SIMPLEX,.6,(0,0,0),1)
 for i,im in enumerate(imgs[:4]): y=35+(i//2)*210; x=(i%2)*640; canvas[y:y+im.shape[0],x:x+im.shape[1]]=im
 cv2.imwrite(str(sheetdir/f'{g}.png'),canvas)
# representative selection by group metrics from a2b
gm=a2b.groupby('group_id').agg(n_pairs=('tuple_id','size'),median_inside=('inside_polyp_fraction','median'),median_color=('color_median_abs','median'),median_cov=('coverage_fraction','median')).reset_index()
# select 8 groups spanning low/high color + coverage
sel=pd.concat([gm.sort_values('median_color').head(3),gm.sort_values('median_color').tail(3),gm.sort_values('median_cov').head(2)]).drop_duplicates('group_id').head(8)
sel.to_csv(O/'analysis/REPRESENTATIVE_CASE_SELECTION.csv',index=False)
# representative A2B overlays + 3D views
repdir=V/'representative_mvs'; repdir.mkdir(parents=True,exist_ok=True); a2dir=V/'representative_a_to_b'; a2dir.mkdir(parents=True,exist_ok=True)
for _,g in sel.iterrows():
 gid=g.group_id; rows=a2b[a2b.group_id==gid].sort_values('color_median_abs',ascending=False)
 r=rows.iloc[0]; g,v= r.group_id,f'{int(r.video_id):03d}'; ex=exe[(exe.group_id==gid)&(exe.video_id==int(r.video_id))&(exe.status=='PASS')].iloc[0]; mesh=str(Path(ex.output_dir)/'RAW_NATIVE_MESH.npz')
 if not Path(mesh).exists(): continue
 # find tuple mesh target and support image; use helper metadata
 p=Path(dm[(g,v)].output_path); cr=np.load(p/'camera_result.npz'); ids=[str(x) for x in cr['ids']]; cams={str(i):np.asarray(c,float) for i,c in zip(cr['ids'],cr['c2w'])}
 # load support RGB from prepared search
 by={}
 for root in [Path('runs/m1_final_39/prepared'),Path('runs/m2a_w0_recovery/prepared_c2b'),Path('runs/m2a_w0_recovery/prepared_c2'),Path('runs/m2a_w0_recovery/prepared_b1r'),Path('runs/m2a_w0_recovery/prepared_c3'),Path('runs/m2a_w0_recovery/prepared_c3b')]:
  q=root/f'{g}_{v}'/'PREPARED.json'
  if q.exists():
   for x in json.loads(q.read_text())['views']: by[x['view']]=x
 Vv=np.asarray(np.load(mesh)['V']); A=r.source_A; B=r.target_B; KB=np.asarray(np.load(by[B]['cache'])['K'],float); imgB=np.load(by[B]['cache'])['RGB']; cA=cams[A]; cB=cams[B]
 z=(Vv-cB[:3,3])@cB[:3,:3]; good=z[:,2]>0; uv=np.full((len(Vv),2),np.nan); uv[good]=(z[good,:2]/z[good,2:3])@KB[:2,:2].T+KB[:2,2]; h,w=imgB.shape[:2]; m=good&(uv[:,0]>=0)&(uv[:,0]<w)&(uv[:,1]>=0)&(uv[:,1]<h); pix=np.rint(uv[m]).astype(int); pix[:,0]=np.clip(pix[:,0],0,w-1); pix[:,1]=np.clip(pix[:,1],0,h-1)
 ov=imgB.copy()
 for x,y in pix: cv2.circle(ov,(int(x),int(y)),1,(0,0,255),-1)
 canvas=np.hstack([cv2.resize(imgB,(480,270)),cv2.resize(ov,(480,270))]); cv2.imwrite(str(a2dir/f'{gid}_A_to_B.png'),canvas)
 # 3D point surface, 3 fixed views
 fig=plt.figure(figsize=(10,3))
 for k,(e,a) in enumerate([(20,-60),(90,-90),(0,0)]):
  ax=fig.add_subplot(1,3,k+1,projection='3d'); ax.scatter(Vv[:,0],Vv[:,1],Vv[:,2],s=1,c=Vv[:,2],cmap='turbo'); ax.set_title(f'view {k}'); ax.set_box_aspect((1,1,1)); ax.view_init(e,a)
 fig.suptitle(f'{gid} HERO mesh {len(Vv)} vertices'); fig.tight_layout(); fig.savefig(repdir/f'{gid}_mesh.png',dpi=110); plt.close(fig)
print('groups',len(list(sheetdir.glob('*.png'))),'rep',len(list(repdir.glob('*.png'))),'a2b',len(list(a2dir.glob('*.png'))))
