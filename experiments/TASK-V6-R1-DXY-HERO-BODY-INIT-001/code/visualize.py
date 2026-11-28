"""Chinese actual-camera review and genuine triangle/plane intersections; no artistic reconstruction."""
from observations import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection,Line3DCollection
from matplotlib.collections import LineCollection
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_manager.fontManager.addfont(FONT);plt.rcParams['font.family']='Noto Sans CJK JP';plt.rcParams['axes.unicode_minus']=False
COL=dict(raw='#d89445',corrected='#00a5ab',parent='#667b9e',body='#4baf71',cut='#df5666',cap='#9254c8',missing='#a80000')
def load_views(g,r):
 a=read(T/'runs/inputs'/g/'AUDIT.json');frames=[];sources=[]
 for case in r['videos']:
  root=T/'runs/observations'/g/case;index=read(root/'INDEX.json');v=next(v for v in a['videos']if v['case']==case)
  for row in index['frames']:
   x=dict(np.load(root/(row['id']+'_2D.npz')));f=v['frames'][row['index']];x.update(case=case,id=row['id'],role=row['role'],RGB=f['RGB_path'],Mask=f['Mask_path'],DXY=read(root/(row['id']+'_DXY.json')));frames.append(x)
  for s in index['sources']:
   x=dict(np.load(root/(s['source']['tag']+'_OBS.npz')));x['meta']=s;sources.append(x)
 return frames,sources
def show_mesh(ax,V,F,color,alpha=.35,maxfaces=1000):
 if len(F):ax.add_collection3d(Poly3DCollection(V[F[::max(1,len(F)//maxfaces)]],facecolor=color,edgecolor='none',alpha=alpha))
def section(V,F,n,origin):
 try:return trimesh.intersections.mesh_plane(trimesh.Trimesh(V,F,process=False),n,origin)
 except ValueError:return np.zeros((0,2,3))
def hero_meshes(sources,bias):
 selected=[]
 for case in sorted({s['meta']['case']for s in sources}):
  same=[(i,s)for i,s in enumerate(sources)if s['meta']['case']==case]
  selected.extend([same[k]for k in np.unique(np.linspace(0,len(same)-1,min(2,len(same))).astype(int))])
 meshes=[]
 for i,s in selected:
  m=trimesh.load(s['meta']['source']['raw_mesh'],process=False);V=np.asarray(m.vertices);F=np.asarray(m.faces);sel=np.load(s['meta']['source']['selection'])['trusted_original_face_id'];D=np.array(s['meta']['source']['T_local_to_common']);V=V@D[:3,:3].T+D[:3,3];C=s['C'];q=(V-C[:3,3])@C[:3,:3];z=q[:,2];Q=(q*(1-bias[i]/np.where(abs(z)>1e-12,z,np.inf))[:,None])@C[:3,:3].T+C[:3,3];meshes.append((V,F[sel],Q))
 return meshes
def image_panels(g,r,folder):
 fs,ss=load_views(g,r);p=np.array(r['p']);p0=np.array(r['initial_p']);base=read(folder/'BASE.json');plane=np.array(base['plane'])if r['base_applied']else None;selected=[]
 for case in r['videos']:
  ff=[f for f in fs if f['case']==case];fit=[f for f in ff if f['role']=='FIT'];held=[f for f in ff if f['role']=='HOLDOUT'];selected+=([fit[0],fit[len(fit)//2]]if fit else[])+(held[:1])
 fig,axes=plt.subplots(len(r['videos']),3,figsize=(12,3.15*len(r['videos'])),squeeze=False)
 for ax,f in zip(axes.flat,selected):
  rgb=cv2.imread(f['RGB'])[:,:,::-1];labels=cv2.imread(f['Mask'],0);ax.imshow(rgb);ax.contour(labels==1,levels=[.5],colors=['#ffcf00'],linewidths=.7)
  y,x=np.mgrid[1:rgb.shape[0]:2,1:rgb.shape[1]:2];uv=np.c_[x.ravel(),y.ravel()];rr=rays(uv,f['K'],f['C']);z,hit,cap=clipped_depth(p,rr,plane);pred=np.isfinite(z).reshape(y.shape);initial=np.isfinite(ellipsoid_depth(p0,rr)).reshape(y.shape)
  if pred.any()and not pred.all():ax.contour(x,y,pred,levels=[.5],colors=[COL['body']],linewidths=1.5)
  if initial.any()and not initial.all():ax.contour(x,y,initial,levels=[.5],colors=['white'],linewidths=.6,linestyles='dashed')
  d=f['DXY']
  if d['available']:
   t=np.linspace(0,2*np.pi,100);q=np.array(d['center_px'])+np.c_[np.cos(t),np.sin(t)]@np.array(d['basis_px']).T;ax.plot(q[:,0],q[:,1],color='#e989f0',lw=.8)
  ax.set_xlim(0,rgb.shape[1]);ax.set_ylim(rgb.shape[0],0);ax.set_title(f"{f['case'].rsplit('_',1)[-1]} / {f['id']} / {'留出'if f['role']=='HOLDOUT'else'拟合'}",fontsize=9);ax.axis('off')
 fig.suptitle(f"{r['configuration']}：原相机 RGB 投影｜黄 Mask / 紫 DXY / 白 虚线起点 / 绿 交付主体\n{r['input_kind']}；基底 {r['base_status']}；真实 GT 不可评价",fontsize=11);fig.tight_layout(rect=(0,0,1,.91));fig.savefig(folder/'RGB_PROJECTIONS.png',dpi=120);plt.close(fig)
 return fs,ss
def geometry_panels(g,r,folder,limits):
 fs,ss=load_views(g,r);raw=np.load(folder/'CORRECTED_OBSERVATIONS.npz');body=np.load(folder/'BODY.npz');parent=np.load(folder/'FINAL_UNCUT.npz');base=read(folder/'BASE.json');plane=np.array(base['plane'])if base.get('plane')is not None else None;V,F=parent['V'],parent['F'];b=np.array([x['b_mm']for x in r['bias']]);meshes=hero_meshes(ss,b)
 n=plane[:3]if plane is not None else fs[0]['C'][:3,2];n=n/np.linalg.norm(n);u=basis(n)[:,0];v=np.cross(n,u);center=np.array(r['p'][:3]);origin=center
 cut=(V[F].mean(1)@n+plane[3]<0)if plane is not None else np.zeros(len(F),bool)
 fig=plt.figure(figsize=(13,8));ax1=fig.add_subplot(221,projection='3d');ax2=fig.add_subplot(222,projection='3d');ax3=fig.add_subplot(223);ax4=fig.add_subplot(224)
 audit=read(T/'runs/inputs'/g/'AUDIT.json');cadfile=next((s['cad_path']for s in audit['source_metadata']),None)
 if cadfile is None:
  a=read(T/'runs/inputs'/g/'AUDIT.json');rad=a['videos'][0]['ring_radius_mm'];cadfile=WORK/'runs/m2f5_unified/cad'/('R5.npz'if rad<4 else'R10.npz')
 cad=np.load(cadfile)
 for ax,near in [(ax1,False),(ax2,True)]:
  show_mesh(ax,V,F[~cut],COL['parent'],.08);show_mesh(ax,V,F[cut],COL['cut'],.2);show_mesh(ax,body['V'],body['F'],COL['body'],.25)
  show_mesh(ax,body['V'],body['F_solid'][body['inferred_base_faces']],COL['cap'],.7)
  for RV,RF,CV in meshes:show_mesh(ax,RV,RF,COL['raw'],.10,500);show_mesh(ax,CV,RF,COL['corrected'],.13,500)
  show_mesh(ax,cad['V'],cad['F'],'#303030',.5,1500)
  if len(raw['raw_X']):
   ax.scatter(*raw['raw_X'][::6].T,s=1,c=COL['raw'],alpha=.35)
   if plane is not None:
    miss=raw['raw_X']@plane[:3]+plane[3]<0;ax.scatter(*raw['raw_X'][miss].T,s=4,c=COL['missing'],marker='x')
  if plane is not None:
   anchor=center-(center@n+plane[3])*n;radius=max(2,float(np.max(np.exp(np.array(r['p'])[6:]))));corners=anchor+np.array([[-1,-1],[1,-1],[1,1],[-1,1]])@np.c_[u,v].T*radius;ax.add_collection3d(Poly3DCollection([corners],facecolor='#aaaaaa',alpha=.16));ax.quiver(*anchor,*n,length=2,color='#222222')
  lo,hi=limits
  if near:rad=max(2,np.max(np.ptp(V,axis=0))*.65);lo=center-rad;hi=center+rad
  ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect((1,1,1));ax.view_init(18,-65);ax.set(xlabel='X / mm',ylabel='Y / mm',zlabel='Z / mm');ax.set_title('统一尺度全范围'if not near else'基底邻域近景（全范围保留于左图）',fontsize=10)
 for ax,normal,label in [(ax3,v,'沿基底法向的真实三角面剖面'),(ax4,n,'平行基底的真实三角面剖面')]:
  B=np.c_[u,n]if ax is ax3 else np.c_[u,v]
  for VV,FF,col,lw in [(V,F,COL['parent'],1),(body['V'],body['F'],COL['body'],1.5),(body['V'],body['F_solid'][body['inferred_base_faces']],COL['cap'],2)]:
   seg=section(VV,FF,normal,origin);ax.add_collection(LineCollection((seg-origin)@B,colors=col,linewidths=lw))
  for RV,RF,CV in meshes:
   for VV,col in [(RV,COL['raw']),(CV,COL['corrected'])]:ax.add_collection(LineCollection((section(VV,RF,normal,origin)-origin)@B,colors=col,linewidths=.7,alpha=.65))
  if ax is ax3 and plane is not None:ax.axhline(-(origin@n+plane[3]),color='#333333',ls='--',lw=.8)
  ax.autoscale();ax.set_aspect('equal');ax.set(xlabel='截面水平 / mm',ylabel='截面垂直 / mm',title=label);ax.grid(alpha=.2)
 fig.suptitle(f"{r['configuration']} | {r['base_status']} {'实际裁切'if r['base_applied']else'母体保留；弱基底仅候选'if plane is not None else'无可用基底'}\n橙 原始 HERO / 青 校正 HERO / 蓝 未裁母体 / 绿 主体 / 红 被切部分与切侧可信点 / 紫 推断底盖\nHERO 三角面显示每视频均匀选 2 来源；指标保留全部来源；固定 CAD 黑色；GT 不可评价",fontsize=10);fig.tight_layout(rect=(0,0,1,.89));fig.savefig(folder/'GEOMETRY_SECTIONS.png',dpi=115);plt.close(fig)
def main():
 import argparse
 pa=argparse.ArgumentParser();pa.add_argument('--group');args=pa.parse_args();links=[]
 for idx in read(M4/'GROUP_INDEX.json')['groups']:
  g=idx['group'];folder=T/'runs/results'/g
  if args.group and args.group!=g:continue
  if not(folder/'GROUP_RESULT.json').exists():continue
  rec=read(folder/'GROUP_RESULT.json');P=[]
  for r in rec['results']:
   root=folder/r['configuration'];a=np.load(root/'FINAL_UNCUT.npz');P.append(a['V']);q=np.load(root/'CORRECTED_OBSERVATIONS.npz');P.extend([q['raw_X'],q['corrected_X']])
  if not P:continue
  P=np.concatenate(P);lo=P.min(0);hi=P.max(0);center=(lo+hi)/2;rad=max((hi-lo).max()/2,6)*1.1;limits=(center-rad,center+rad)
  cols=[]
  for r in rec['results']:
   root=folder/r['configuration'];image_panels(g,r,root);geometry_panels(g,r,root,limits)
   cols.append(f'<section><h2>{r["configuration"]}</h2><p>{r["input_kind"]}；{r["base_status"]}；留出 IoU {r["held_IoU_mean"]:.3f}</p><a href="{r["configuration"]}/RESULT.json">参数、偏置与来源</a><br><img src="{r["configuration"]}/RGB_PROJECTIONS.png"><img src="{r["configuration"]}/GEOMETRY_SECTIONS.png"></section>')
  html='<meta charset="utf-8"><style>body{font-family:sans-serif;background:#fafafa}main{display:flex;gap:10px}section{min-width:500px;flex:1}img{width:100%}pre{white-space:pre-wrap}</style><h1>'+g+'</h1><p>本轮新算粗初始化。真实 GT 不可评价；数值完成不等于形状已验证。单视频各用自身观测，联合重新优化。</p><main>'+''.join(cols)+'</main><pre>'+json.dumps(rec['failures'],ensure_ascii=False,indent=2)+'</pre>'
  (folder/'index.html').write_text(html);links.append(f'<li><a href="{g}/index.html">{g}</a></li>');print('FIGURE',g,flush=True)
 (T/'runs/results/index.html').write_text('<meta charset="utf-8"><h1>39 组主体初始化审阅</h1><p>单位 mm；原始 R1/M4 只读。黄色 Mask、紫色 DXY、绿色主体。失败和弱基底均保留。</p><ul>'+''.join(links)+'</ul>')
if __name__=='__main__':main()
