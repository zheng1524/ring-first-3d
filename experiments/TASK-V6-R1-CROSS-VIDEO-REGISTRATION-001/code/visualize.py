from context import *
from evaluate_real2 import load_geometry,combined
from visualize2 import plt,build,render,panel,COLORS,VIEWS,LineCollection
from ring_first_3d.sim.geometry import scene,transform
from ring_first_3d.multisurface.geometry import mesh_sections,plane_coordinates
from ring_first_3d.mainline.native.ring_cad import project_contours
import cv2,gc,html

def figures(group):
 out=RUN/'real'/group;dest=T/'visuals'/group;dest.mkdir(parents=True,exist_ok=True);freeze('VISUALIZE',out,[out/'EVALUATION.json']);asset=read(T/'config'/group/'ASSETS.json');pred=read(out/'PREDICTIONS.json');e=read(out/'EVALUATION.json');packs=load_geometry(out);cad=np.load(asset['sources'][0]['cad_path']);lim=[cad['V']]
 for m in ['M0','M4','M5']:
  if pred[m]['T']is None:continue
  for p in packs:
   V=p['V'][np.unique(p['F'])];V=transform(V,np.array(pred[m]['T']))if p['source']['side']=='B'else V;lim.extend([V.min(0)[None],V.max(0)[None]])
 lim=np.concatenate(lim);full=(lim.min(0),lim.max(0));radius=asset['videos'][0]['ring_radius_mm'];near=(np.full(3,-2.5*radius),np.full(3,2.5*radius));clipped={};images=[]
 for name,bounds in [('six_full.png',full),('six_near.png',near)]:
  fig,axes=plt.subplots(4,6,figsize=(17,11));fig.suptitle(group+' / R1\n蓝=A，橙=B，灰=共同固定CAD；真实三角面，无三维GT；'+('完整共同范围'if name=='six_full.png'else'固定盒近景，盒外交点不显示'))
  for row,(method,clean)in enumerate([('M0',False),('M4',False),('M5',False),('M5',True)]):
   t=pred[method]['T'];label=method+(' 配准后Clean'if clean else' Raw')
   if t is None or(clean and e['stages']['clean_missing']):
    for ax in axes[row]:ax.text(.1,.5,'不可评价：变换/来源缺失');ax.axis('off')
    continue
   V,F,lab=build(packs,cad,np.array(t),clean);sc=scene(V,F);outside=np.any((V<bounds[0])|(V>bounds[1]),axis=1);count=int(np.any(outside[F],axis=1).sum());clipped[name+'_'+label]=count
   for col,view in enumerate(VIEWS):rgb,span=render(sc,lab,bounds,view,190);panel(axes[row,col],rgb,span,label+f' / 方位{view[0]}°\n盒外相交面{count}')
   del sc,V,F,lab;gc.collect()
  fig.tight_layout(rect=(0,0,1,.94));fig.savefig(dest/name,dpi=105);plt.close(fig);images.append(name)
 # Exact triangle/plane intersections, fixed x=0 and y=0.
 fig,axes=plt.subplots(2,4,figsize=(16,8));fig.suptitle(group+' / R1\n原三角面与固定 x=0 / y=0 mm 截面；全部来源，同坐标范围；不拟合轮廓、不补面')
 for axis in [0,1]:
  coords=[k for k in range(3)if k!=axis]
  for col,(method,clean)in enumerate([('M0',False),('M4',False),('M5',False),('M5',True)]):
   ax=axes[axis,col];t=pred[method]['T'];count=0
   if t is None:ax.text(.1,.5,'无变换');continue
   for side,color in zip(['A','B'],COLORS):
    V,F=combined(packs,side,np.array(t),clean);seg=plane_coordinates(mesh_sections(V,F,axis,0),axis)if len(F)else np.empty((0,2,2));count+=len(seg);ax.add_collection(LineCollection(seg,colors=[color],linewidths=.35,alpha=.55))
   seg=plane_coordinates(mesh_sections(cad['V'],cad['F'],axis,0),axis);ax.add_collection(LineCollection(seg,colors='gray',linewidths=.6));ax.set_xlim(full[0][coords[0]],full[1][coords[0]]);ax.set_ylim(full[0][coords[1]],full[1][coords[1]]);ax.set_aspect('equal');ax.set_xlabel('xyz'[coords[0]]+' mm');ax.set_ylabel('xyz'[coords[1]]+' mm');ax.set_title(method+(' Clean'if clean else' Raw')+f' / {"xy"[axis]}=0 / {count}段')
 fig.tight_layout(rect=(0,0,1,.93));fig.savefig(dest/'sections.png',dpi=115);plt.close(fig);images.append('sections.png')
 frames=read(out/'FRAMES.json');C=np.load(out/'CAMERAS.npz')['c2w'];tr=np.load(out/'tracks/observations/tracks005.npz');held={m:read(out/'evaluation'/(m+'_HELD.json'))for m in ['M4','M5']};ix={side:[i for i,f in enumerate(frames)if f['side']==side]for side in ['A','B']};reps=[0,len(ix['A'])//2,len(ix['A'])-1]
 fig,axes=plt.subplots(3,3,figsize=(16,9));fig.suptitle(group+' / R1 真实RGB\n左：自动跨视频轨迹（绿FIT，紫held）；中/右：绿观测、黄M4、红M5，独立源DLT投影；失效/越界保留计数')
 for row,k in enumerate(reps):
  a,b=ix['A'][k],ix['B'][k];rgbA=cv2.imread(frames[a]['RGB_path'])[:,:,::-1];rgbB=cv2.imread(frames[b]['RGB_path'])[:,:,::-1];ax=axes[row,0];ax.imshow(np.concatenate([rgbA,rgbB],1));ids=np.flatnonzero(np.isfinite(tr['xy'][:,[a,b]]).all((1,2)))
  for tid in ids:
   uv=tr['xy'][tid,a];q=tr['xy'][tid,b];ax.plot([uv[0],q[0]+640],[uv[1],q[1]],c='purple'if tr['held'][tid]else'green',lw=.4,alpha=.6)
  ax.set_title(f'A RAW{frames[a]["raw_frame"]} / B RAW{frames[b]["raw_frame"]}，轨迹{len(ids)}');ax.axis('off')
  for col,j,rgb in [(1,b,rgbB),(2,a,rgbA)]:
   ax=axes[row,col];ax.imshow(rgb);items=[r for r in held['M5']if r['frame']==j]
   for r in items:ax.plot(*tr['xy'][r['track'],j],'+',c='lime',ms=4)
   for method,color in [('M4','yellow'),('M5','red')]:
    for r in held[method]:
     if r['frame']!=j or r['status']!='VALID':continue
     xy=tr['xy'][r['track'],j];q=r['projection'];ax.plot(*q,'x',c=color,ms=3);ax.plot([xy[0],q[0]],[xy[1],q[1]],color=color,lw=.4)
   ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_title(('A→B'if col==1 else'B→A')+f' 全观测{len(items)} / M5失效或越界{sum(r["status"]!="VALID"for r in items)}');ax.axis('off')
 fig.tight_layout(rect=(0,0,1,.93));fig.savefig(dest/'rgb_held.png',dpi=115);plt.close(fig);images.append('rgb_held.png')
 fig,axes=plt.subplots(1,3,figsize=(15,4));fig.suptitle('固定共同CAD投影到B视频原图：绿=真实Ring留出边界；黄=M4；红=M5；不移动CAD')
 R=Path(next(v['run']for v in asset['videos']if v['side']=='B'))
 for ax,k in zip(axes,reps):
  j=ix['B'][k];f=frames[j];ax.imshow(cv2.imread(f['RGB_path'])[:,:,::-1]);ob=np.load(R/'observations'/(f['id'].split('__',1)[1]+'_ring.npz'));q=ob['q_held'];ax.scatter(q[:,0],q[:,1],c='lime',s=3)
  for m,color in [('M4','yellow'),('M5','red')]:
   if pred[m]['T']is None:continue
   try:
    curves=project_contours(np.array(pred[m]['T'])@C[j],np.array(f['K']),2*(radius-.6),n=256)
    for curve in curves:ax.plot(curve[:,0],curve[:,1],c=color,lw=.8)
   except Exception:ax.text(10,20,m+'不可投影',color=color)
  ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_title('B RAW'+str(f['raw_frame']));ax.axis('off')
 fig.tight_layout(rect=(0,0,1,.9));fig.savefig(dest/'ring.png',dpi=115);plt.close(fig);images.append('ring.png')
 # Camera layout is separate from the full-resolution mesh figures.
 fig,axes=plt.subplots(2,3,figsize=(12,8));fig.suptitle(group+'\n相机中心、光轴与固定Ring中心线；全视频相机同步T，非逐帧调整')
 allcams={v['side']:np.load(v['camera'])['c2w']for v in asset['videos']};limcam=[]
 for col,m in enumerate(['M0','M4','M5']):
  if pred[m]['T']is None:continue
  for side,color in zip(['A','B'],COLORS):
   cams=allcams[side]if side=='A'else np.array(pred[m]['T'])@allcams[side];limcam.append(cams[:,:3,3])
   for row,coords in enumerate([[0,1],[0,2]]):
    ax=axes[row,col];P=cams[:,coords,3];Q=P+3*cams[:,coords,2];ax.plot(P[:,0],P[:,1],'o-',c=color,ms=3)
    for p,q in zip(P,Q):ax.plot([p[0],q[0]],[p[1],q[1]],color=color,alpha=.5)
    th=np.linspace(0,2*np.pi,200);ring=np.c_[radius*np.cos(th),radius*np.sin(th),np.zeros(len(th))][:,coords];ax.plot(ring[:,0],ring[:,1],c='gray');ax.set_title(m);ax.set_xlabel('xyz'[coords[0]]+' mm');ax.set_ylabel('xyz'[coords[1]]+' mm');ax.set_aspect('equal')
 limcam=np.concatenate(limcam+[cad['V']]);lo=limcam.min(0)-3;hi=limcam.max(0)+3
 for row,coords in enumerate([[0,1],[0,2]]):
  for ax in axes[row]:ax.set_xlim(lo[coords[0]],hi[coords[0]]);ax.set_ylim(lo[coords[1]],hi[coords[1]])
 fig.tight_layout(rect=(0,0,1,.92));fig.savefig(dest/'cameras.png',dpi=115);plt.close(fig);images.append('cameras.png')
 finite=[r for r in held['M5']if r['error_px']is not None];worst=max(finite,key=lambda r:r['error_px'])if finite else None;fig,axes=plt.subplots(1,2,figsize=(12,4))
 if worst:
  j=worst['frame'];axes[0].imshow(cv2.imread(frames[j]['RGB_path'])[:,:,::-1]);axes[0].plot(*tr['xy'][worst['track'],j],'o',mfc='none',mec='lime',ms=12);axes[0].set_title('评价后标注最差留出：观测位置');axes[0].axis('off');axes[1].text(.02,.9,f'{group}\ntrack {worst["track"]} / {worst["direction"]}\nRAW {frames[j]["raw_frame"]}\n误差 {worst["error_px"]:.3f}px\n状态 {worst["status"]}\n预测像素 {worst["projection"]}\n本图仅失败诊断，未用于选帧/调参。\n完整分母含不可DLT与负深度，不缩小分母。',va='top');axes[1].axis('off')
 fig.tight_layout();fig.savefig(dest/'worst.png',dpi=115);plt.close(fig);images.append('worst.png');save(dest/'VIEWS.json',dict(bounds_full_mm=full,bounds_near_mm=near,clipped_faces=clipped,views=VIEWS,representative_pool_indices=reps,planes='x=0,y=0',worst=worst,GT='NOT_AVAILABLE'))
 st=e['stages'];body=f'<h1>{group} / R1</h1><p>'+html.escape('；'.join(v['side']+'='+v['case']for v in asset['videos']))+f'</p><p>来源{st["sources"]}；Clean缺失{st["clean_missing"]}；轨迹{st["all_tracks"]}；M4 FIT {st["M4_fit"]}；M5 FIT {st["M5_fit"]}；全held {st["all_held_tracks"]}。真实图，无独立三维GT。优化收敛不是质量批准。</p>'+''.join(f'<h2>{name}</h2><img src="{name}" style="width:100%">'for name in images)
 (dest/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>R1 '+group+'</title><body style="max-width:1800px;margin:auto;font-family:sans-serif">'+body+'</body>');print('VISUALIZED',group,flush=True)
if __name__=='__main__':
 for row in read(T/'config/SELECTION.json')['groups']:figures(row['group'])
