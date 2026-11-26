"""Chinese evidence: original triangle ray casting and exact plane intersections."""
from common2 import *
from evaluate_real2 import load_geometry,combined
from ring_first_3d.sim.geometry import scene,transform
from ring_first_3d.multisurface.geometry import mesh_sections,plane_coordinates
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.collections import LineCollection
import open3d as o3d
import cv2,gc,html
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
matplotlib.font_manager.fontManager.addfont(FONT);plt.rcParams.update({'font.family':FontProperties(fname=FONT).get_name(),'axes.unicode_minus':False,'font.size':9})
COLORS=np.array([[.12,.55,.85],[.95,.48,.16],[.58,.60,.64]])
VIEWS=[(0,20),(60,20),(120,20),(180,20),(240,20),(300,20)]

def build(packs,cad,T0,clean=False,excluded=False):
 vv=[];ff=[];labels=[];off=0
 for i,s in enumerate(['A','B']):
  V,F=combined(packs,s,T0,clean,excluded);vv.append(V);ff.append(F+off);labels.append(np.full(len(F),i));off+=len(V)
 vv.append(cad['V']);ff.append(cad['F']+off);labels.append(np.full(len(cad['F']),2))
 return np.concatenate(vv),np.concatenate(ff),np.concatenate(labels)

def render(sc,lab,bounds,angle,size=180):
 lo,hi=bounds;center=(lo+hi)/2;span=np.linalg.norm(hi-lo)*1.05;az,el=np.deg2rad(angle);forward=-np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward);x=np.linspace(-span/2,span/2,size);xx,yy=np.meshgrid(x,x[::-1]);orig=center-forward*span*2+xx[...,None]*right+yy[...,None]*up;rays=np.concatenate([orig,np.broadcast_to(forward,orig.shape)],axis=2).astype(np.float32);r=sc.cast_rays(o3d.core.Tensor(rays),nthreads=1);face=r['primitive_ids'].numpy();distance=r['t_hit'].numpy();valid=np.isfinite(distance);hit=orig+np.where(valid,distance,0)[...,None]*forward;valid&=((hit>=lo)&(hit<=hi)).all(2);rgb=np.ones((size,size,3));norm=r['primitive_normals'].numpy();shade=.45+.55*np.abs(norm@(-forward));rgb[valid]=COLORS[lab[face[valid]]]*shade[valid,None];return rgb,span

def panel(ax,rgb,span,title):
 ax.imshow(rgb,extent=[-span/2,span/2,-span/2,span/2]);ax.set_title(title,fontsize=9);ax.set_xlabel('mm');ax.set_ylabel('mm')

def figures(group):
 folder=RUN/'real'/group;dest=T/'visuals'/group;dest.mkdir(parents=True,exist_ok=True);stage_freeze('VISUALIZE',folder,[folder/'PREDICTION_FREEZE.json',folder/'EVALUATION.json']);packs=load_geometry(folder);asset=read(T/'config'/group/'ASSETS.json');cad=np.load(asset['sources'][0]['cad_path']);pred=read(folder/'PREDICTIONS.json');eva=read(folder/'EVALUATION.json');boundsV=[cad['V']]
 for r in pred.values():
  if r['T']is None:continue
  for p in packs:
   V=transform(p['V'][np.unique(p['F'])],np.array(r['T']))if p['source']['side']=='B'else p['V'][np.unique(p['F'])];boundsV.extend([V.min(0)[None],V.max(0)[None]])
 boundsV=np.concatenate(boundsV);full=(boundsV.min(0),boundsV.max(0));radius=asset['videos'][0]['ring_radius_mm'];near=(np.full(3,-2.5*radius),np.full(3,2.5*radius));clipped={};pages=[]
 for range_name,bounds in [('完整范围',full),('固定近景',near)]:
  fig,axs=plt.subplots(3,6,figsize=(17,9));fig.suptitle(group+'\n真实数据，无三维GT；蓝=A、橙=B、灰=固定CAD；'+range_name+'；全部原三角面参与光线求交')
  for row,(name,clean,label)in enumerate([('M0',False,'配准前 Raw'),('M4',False,'M4 Raw'),('M4',True,'M4 TRUSTED-only')]):
   if pred[name]['T']is None:
    for ax in axs[row]:ax.text(.5,.5,'拒绝：无变换',ha='center');ax.axis('off')
    continue
   V,F,lab=build(packs,cad,np.array(pred[name]['T']),clean);sc=scene(V,F);outside=np.any((V<bounds[0])|(V>bounds[1]),1);n=int(np.any(outside[F],1).sum());clipped[range_name+'_'+label]=n
   for col,ang in enumerate(VIEWS):rgb,span=render(sc,lab,bounds,ang);panel(axs[row,col],rgb,span,label+f' / 方位{ang[0]}°\n框外相交面计数 {n}')
   del sc,V,F,lab;gc.collect()
  fig.tight_layout(rect=(0,0,1,.94));name='six_full.png'if range_name=='完整范围'else'six_near.png';fig.savefig(dest/name,dpi=105);plt.close(fig);pages.append(name)
 # Mandatory crossed display: fixed bounds and view, neither row reclassifies faces.
 fig,axs=plt.subplots(2,2,figsize=(9,9));fig.suptitle(group+'\n支持筛选的变换 × Raw/Clean；蓝A、橙B、灰CAD；完整共同范围')
 for row,method in enumerate(['M4_raw_support','M4_clean_support']):
  for col,clean in enumerate([False,True]):
   ax=axs[row,col];T0=pred[method]['T']
   if T0 is None:ax.text(.5,.5,'支持不足 / 无变换');continue
   V,F,lab=build(packs,cad,np.array(T0),clean);sc=scene(V,F);rgb,span=render(sc,lab,full,(45,30),220);panel(ax,rgb,span,method+' × '+('Clean'if clean else'Raw'));del sc,V,F,lab;gc.collect()
 fig.tight_layout(rect=(0,0,1,.93));fig.savefig(dest/'support_2x2.png',dpi=115);plt.close(fig);pages.append('support_2x2.png')
 # Two fixed physical planes; original triangle intersections, no point/curve fit.
 fig,axs=plt.subplots(2,3,figsize=(13,8));fig.suptitle(group+'\n真实三角面截面：固定 x=0 与 y=0 mm；各栏同一完整范围；排除面单列，非补面')
 T0=np.array(pred['M4']['T'])if pred['M4']['T']is not None else np.eye(4)
 for axis in [0,1]:
  coords=[j for j in range(3)if j!=axis]
  for col,(clean,excluded,label)in enumerate([(False,False,'M4 Raw'),(True,False,'M4 Clean'),(False,True,'M4 被排除区域')]):
   ax=axs[axis,col];count=0
   for s,color in zip(['A','B'],COLORS):
    V,F=combined(packs,s,T0,clean,excluded);seg=plane_coordinates(mesh_sections(V,F,axis,0),axis)if len(F)else np.empty((0,2,2));count+=len(seg);ax.add_collection(LineCollection(seg,colors=[color],linewidths=.4,alpha=.55))
   seg=plane_coordinates(mesh_sections(cad['V'],cad['F'],axis,0),axis);ax.add_collection(LineCollection(seg,colors='gray',linewidths=.6));ax.set_xlim(full[0][coords[0]],full[1][coords[0]]);ax.set_ylim(full[0][coords[1]],full[1][coords[1]]);ax.set_aspect('equal');ax.set_title(label+f' / {"xy"[axis]}=0 / {count} 段');ax.set_xlabel('xyz'[coords[0]]+' (mm)');ax.set_ylabel('xyz'[coords[1]]+' (mm)')
 fig.tight_layout(rect=(0,0,1,.92));fig.savefig(dest/'sections.png',dpi=120);plt.close(fig);pages.append('sections.png')
 # True RGB, deterministic first/middle/last temporal frame pairs, all matched tracks.
 frames=read(folder/'FRAMES.json');tr=np.load(folder/'tracks/observations/tracks005.npz');held=read(folder/'evaluation/M4_HELD.json');fig,axs=plt.subplots(3,3,figsize=(16,9));fig.suptitle(group+'\n真实 RGB：左为自动轨迹（绿FIT，紫HOLDOUT）；中/右为双向独立源DLT留出投影（绿观测、红预测）')
 for row,k in enumerate([0,2,5]):
  a=k;b=k+6;rgbA=cv2.imread(frames[a]['RGB_path'])[:,:,::-1];rgbB=cv2.imread(frames[b]['RGB_path'])[:,:,::-1];ax=axs[row,0];ax.imshow(np.concatenate([rgbA,rgbB],axis=1));ids=np.flatnonzero(np.isfinite(tr['xy'][:,[a,b]]).all((1,2)))
  for tid in ids:
   u,v=tr['xy'][tid,a];x,y=tr['xy'][tid,b];ax.plot([u,x+640],[v,y],c='#9a54cb'if tr['held'][tid]else'#32bf76',lw=.4,alpha=.6)
  ax.set_title(f'A RAW{frames[a]["raw_frame"]} / B RAW{frames[b]["raw_frame"]}；轨迹{len(ids)}');ax.axis('off')
  for col,j,rgb in [(1,b,rgbB),(2,a,rgbA)]:
   ax=axs[row,col];ax.imshow(rgb);rows=[r for r in held if r['frame']==j];invalid=0
   for r in rows:
    xy=tr['xy'][r['track'],j];ax.plot(*xy,'+',c='#32bf76',ms=4)
    if r['status']!='VALID':invalid+=1;continue
    q=r['projection'];ax.plot(*q,'x',c='red',ms=3);ax.plot([xy[0],q[0]],[xy[1],q[1]],c='yellow',lw=.4)
   ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_title(('A→B'if col==1 else'B→A')+f' M4；全观测{len(rows)}；失效/越界{invalid}');ax.axis('off')
 fig.tight_layout(rect=(0,0,1,.92));fig.savefig(dest/'rgb_held.png',dpi=115);plt.close(fig);pages.append('rgb_held.png')
 # Worst held record explicitly selected AFTER evaluation, never used as representative or tuning.
 finite=[r for r in held if r['error_px']is not None];worst=max(finite,key=lambda r:r['error_px'])if finite else None
 fig,ax=plt.subplots(figsize=(9,5))
 if worst:
  j=worst['frame'];ax.imshow(cv2.imread(frames[j]['RGB_path'])[:,:,::-1]);xy=tr['xy'][worst['track'],j];ax.plot(*xy,'o',mfc='none',mec='lime',ms=12);q=worst['projection'];ax.plot(*q,'rx',ms=12);ax.annotate('预测在此；越界不删除',q,xytext=(25,25),textcoords='offset points',arrowprops={'arrowstyle':'->'});ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_title(f'评价后标注的最差留出：track {worst["track"]} / {worst["direction"]}\n{worst["error_px"]:.1f}px；{worst["status"]}；真实RGB；非选优帧')
 else:ax.text(.1,.5,'全部留出失效，不能评价')
 fig.tight_layout();fig.savefig(dest/'worst.png',dpi=115);plt.close(fig);pages.append('worst.png');save(dest/'VIEW_MANIFEST.json',dict(full_bounds_mm=full,near_bounds_mm=near,clipped_faces=clipped,views_azimuth_elevation_deg=VIEWS,planes='x=0,y=0',representative_pool_indices=[0,2,5],GT='NONE',worst=worst))
 st=eva['stages'];rows=[]
 for method,r in eva['methods'].items():
  b=r['bidir'];rows.append('<tr><td>'+method+'</td>'+''.join('<td>'+str(x)+'</td>'for x in [r['numerical'],r['quality'],round(b['A_to_B']['conditional_MAE'],2)if b['A_to_B']['conditional_MAE']is not None else'不可评',round(b['B_to_A']['conditional_MAE'],2)if b['B_to_A']['conditional_MAE']is not None else'不可评',b['denominators']['two_sided_DLT_tracks'],b['denominators']['evidence_sufficient']])+'</tr>')
 body=f'<h1>{group}</h1><p>'+html.escape('；'.join(v['side']+'='+v['case']for v in asset['videos']))+'</p>'+f'<p>Raw来源{st["sources"]}；Clean缺失{st["clean_missing"]}；复用{st["clean_reused"]}；FIT {st["fit_valid"]} / 全轨迹 {st["track_total"]}；全留出 {st["held_total"]}。无真实三维GT。下表仅有限投影的条件MAE，完整分母及失效见结果JSON；不是完整留出均值。</p><table border="1"><tr><th>方法</th><th>数值</th><th>求解质量标记</th><th>A→B px</th><th>B→A px</th><th>双侧独立DLT轨迹</th><th>最低支持量</th></tr>'+''.join(rows)+'</table><p>所有方法完整留出包含不可三角化观测，完整MAE不可评价。M4两支持分支集合未改变，T完全相同；不能宣称Clean提升位姿。</p>'+''.join(f'<h2>{x}</h2><img src="{x}" style="width:100%;max-width:1800px">'for x in pages)
 (dest/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>'+group+'</title><body style="font-family:sans-serif;max-width:1800px;margin:auto">'+body+'</body>');print('VISUALIZED',group,flush=True)
if __name__=='__main__':
 for r in read(T/'config/SELECTION.json')['groups']:figures(r['group'])
