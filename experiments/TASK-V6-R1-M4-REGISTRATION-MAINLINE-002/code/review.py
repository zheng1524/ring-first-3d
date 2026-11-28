"""Three-state visual review from the same M4 GROUP entry consumed downstream."""
from context import *
from evaluate_real2 import load_geometry,geometric
import visualize2 as vis
from visualize2 import plt,render,panel,VIEWS,LineCollection
from ring_first_3d.sim.geometry import transform,scene
from ring_first_3d.multisurface.geometry import mesh_sections,plane_coordinates
from ring_first_3d.mainline.native.ring_cad import project_contours
from connections import pair_view
import itertools,gc,cv2,html,argparse,traceback

def world_packs(packs,reg,registered):
 out=[]
 for p in packs:
  t=reg['videos'][p['source']['case']]['T']
  if registered and t is None:continue
  tv=np.array(t)if registered else np.eye(4);out.append(dict(p,V=transform(p['V'],tv),points=transform(p['points'],tv)))
 return out

def joined(packs,case=None,clean=False):
 vv=[];ff=[];offset=0
 for p in packs:
  if case is not None and p['source']['case']!=case:continue
  F=p['F']
  if clean:
   if p['state']is None:continue
   F=F[p['state']==0]
  if not len(F):continue
  vv.append(p['V']);ff.append(F+offset);offset+=len(p['V'])
 return (np.concatenate(vv),np.concatenate(ff))if vv else(np.empty((0,3)),np.empty((0,3),int))

def render_mesh(packs,cases,cad,clean=False):
 vv=[];ff=[];labels=[];offset=0
 for i,case in enumerate(cases):
  v,f=joined(packs,case,clean);vv.append(v);ff.append(f+offset);labels.append(np.full(len(f),i));offset+=len(v)
 vv.append(cad['V']);ff.append(cad['F']+offset);labels.append(np.full(len(cad['F']),len(cases)))
 return np.concatenate(vv),np.concatenate(ff),np.concatenate(labels)

def review(g):
 out=group_out(g);asset,reg=verify_registration(out);group=read(out/'GROUP.json');assert group['registration_sha256']==sha(out/'REGISTRATION.json'),'GROUP_TRANSFORM_DRIFT';dest=T/'visuals'/g;dest.mkdir(parents=True,exist_ok=True)
 for rec in read(out/'CLEAN_INDEX.json'):
  if rec.get('status')=='COMPLETE':assert sha(rec['raw_domain'])==rec['raw_domain_sha256'],'RAW_DOMAIN_DRIFT';assert sha(rec['selection_path'])==rec['selection_sha256'],'SELECTION_DRIFT'
 if not asset['sources']:
  (dest/'index.html').write_text('<meta charset="utf-8"><h1>'+g+'</h1><p>无可用 HERO 输出；保留所有视频的终态原因，未伪造共同几何。</p>');save(out/'REVIEW_COMPLETE.json',dict(no_output=True));return
 assert (out/'CONSUMER_CHECK.json').exists();key=cache_key(dict(group=sha(out/'GROUP.json'),code=sha(__file__),source_kernel=sha(OLD/'code/visualize2.py')))
 if (out/'REVIEW_COMPLETE.json').exists()and read(out/'REVIEW_COMPLETE.json').get('key')==key:return
 freeze('REVIEW',out,[out/'GROUP.json',out/'CONSUMER_CHECK.json']);packs=load_geometry(out);cases=[v['case']for v in asset['videos']];cad=dict(np.load(asset['sources'][0]['cad_path']));before=world_packs(packs,reg,False);after=world_packs(packs,reg,True)
 vis.COLORS=np.array([[.12,.55,.85],[.95,.48,.16],[.35,.7,.35],[.7,.3,.7]][:len(cases)]+[[.58,.60,.64]])
 # Same frozen raw sample ids, irrespective of Clean or method.
 pairs=[]
 for a,b in itertools.combinations(cases,2):
  metrics={}
  for label,pp,clean in [('before',before,False),('M4_raw',after,False),('M4_clean',after,True)]:
   pair=[dict(p,source=dict(p['source'],side='A'if p['source']['case']==a else'B'))for p in pp if p['source']['case']in[a,b]]
   metrics[label]=geometric(pair,np.eye(4),clean)if all(reg['videos'][x]['T']is not None for x in [a,b])or label=='before'else dict(status='UNCONNECTED')
  pairs.append(dict(A=a,B=b,metrics=metrics))
 save(out/'SURFACE_EVALUATION.json',dict(pairs=pairs,domain='same 96 original area-sampled faces/source; removed samples stay uncovered; not GT accuracy',sources=len(packs),raw_faces=sum(len(p['F'])for p in packs),trusted_faces=sum(int((p['state']==0).sum())for p in packs if p['state']is not None),clean_missing=sum(p['state']is None for p in packs),domains=[dict(path=p['record']['raw_domain'],sha256=sha(p['record']['raw_domain']))for p in packs if p['record'].get('raw_domain')]))
 bounds=[cad['V']]
 for pp in [before,after]:
  for p in pp:
   v=p['V'][np.unique(p['F'])]
   if len(v):bounds.extend([v.min(0)[None],v.max(0)[None]])
 bounds=np.concatenate(bounds);full=(bounds.min(0),bounds.max(0));radius=asset['videos'][0]['ring_radius_mm'];near=(np.full(3,-2.5*radius),np.full(3,2.5*radius));images=[];clips={};states=[('配准前 Raw',before,False),('M4 配准后 Raw',after,False),('M4 可信 Clean',after,True)];legend='；'.join(('蓝','橙','绿','紫')[i]+'='+c.rsplit('_',1)[-1]+'('+str(sum(p['source']['case']==c for p in packs))+'源)'for i,c in enumerate(cases))
 for filename,limits in [('six_full.png',full),('six_near.png',near)]:
  fig,axes=plt.subplots(3,6,figsize=(17,9));fig.suptitle(g+'\n'+legend+'；灰=固定Ring CAD；无三维GT；'+('完整共同范围'if filename=='six_full.png'else'固定近景：盒外面保留在完整图'))
  for row,(label,pp,clean)in enumerate(states):
   v,f,lab=render_mesh(pp,cases,cad,clean);sc=scene(v,f);n=int(np.any(np.any((v<limits[0])|(v>limits[1]),axis=1)[f],axis=1).sum());clips[filename+label]=n
   for col,angle in enumerate(VIEWS):rgb,span=render(sc,lab,limits,angle,180);panel(axes[row,col],rgb,span,label+f' / {angle[0]}°\n盒外相交面 {n}')
   del sc,v,f,lab;gc.collect()
  fig.tight_layout(rect=(0,0,1,.93));fig.savefig(dest/filename,dpi=100);plt.close(fig);images.append(filename)
 fig,axes=plt.subplots(2,3,figsize=(13,8));fig.suptitle(g+'\n真实三角面截面；固定 x=0 / y=0 mm；同一完整范围；未补面')
 for axis in [0,1]:
  coords=[k for k in range(3)if k!=axis]
  for col,(label,pp,clean)in enumerate(states):
   ax=axes[axis,col];n=0
   for i,case in enumerate(cases):
    v,f=joined(pp,case,clean);seg=plane_coordinates(mesh_sections(v,f,axis,0),axis)if len(f)else np.empty((0,2,2));n+=len(seg);ax.add_collection(LineCollection(seg,colors=[vis.COLORS[i]],linewidths=.35,alpha=.6))
   seg=plane_coordinates(mesh_sections(cad['V'],cad['F'],axis,0),axis);ax.add_collection(LineCollection(seg,colors='gray',linewidths=.6));ax.set_xlim(full[0][coords[0]],full[1][coords[0]]);ax.set_ylim(full[0][coords[1]],full[1][coords[1]]);ax.set_aspect('equal');ax.set_xlabel('xyz'[coords[0]]+' mm');ax.set_ylabel('xyz'[coords[1]]+' mm');ax.set_title(label+f' / {n}段')
 fig.tight_layout(rect=(0,0,1,.93));fig.savefig(dest/'sections.png',dpi=110);plt.close(fig);images.append('sections.png')
 # Whole camera trajectories, fixed common axes, no per-frame adjustments.
 fig,axes=plt.subplots(2,2,figsize=(10,8));limits=[]
 for col,registered in enumerate([False,True]):
  for i,v in enumerate(asset['videos']):
   cam=np.load(v['camera'])['c2w'];tv=reg['videos'][v['case']]['T']
   if registered and tv is None:continue
   cam=np.array(tv)@cam if registered else cam;limits.append(cam[:,:3,3])
   for row,coords in enumerate([[0,1],[0,2]]):
    ax=axes[row,col];P=cam[:,coords,3];Q=P+3*cam[:,coords,2];ax.plot(P[:,0],P[:,1],'o-',c=vis.COLORS[i],ms=3)
    for p,q in zip(P,Q):ax.plot([p[0],q[0]],[p[1],q[1]],c=vis.COLORS[i],alpha=.4)
    theta=np.linspace(0,2*np.pi,200);ring=np.c_[radius*np.cos(theta),radius*np.sin(theta),np.zeros(len(theta))][:,coords];ax.plot(ring[:,0],ring[:,1],c='gray');ax.set_aspect('equal');ax.set_xlabel('xyz'[coords[0]]+' mm');ax.set_ylabel('xyz'[coords[1]]+' mm');ax.set_title('M4 共同坐标'if registered else'配准前局部坐标叠放')
 lim=np.concatenate(limits+[cad['V']]);lo=lim.min(0)-3;hi=lim.max(0)+3
 for row,coords in enumerate([[0,1],[0,2]]):
  for ax in axes[row]:ax.set_xlim(lo[coords[0]],hi[coords[0]]);ax.set_ylim(lo[coords[1]],hi[coords[1]])
 fig.suptitle(g+'\n'+legend+'；全视频相机中心/光轴，mm');fig.tight_layout(rect=(0,0,1,.92));fig.savefig(dest/'cameras.png',dpi=110);plt.close(fig);images.append('cameras.png')
 if reg['edges']:
  # Actual automatic correspondences; deterministic first/mid/last pool index, not score selection.
  frames=read(out/'FRAMES.json');C=np.load(out/'CAMERAS.npz')['c2w'];tr=dict(np.load(out/'tracks/observations/tracks005.npz'))
  for ei,edge in enumerate(reg['edges']):
   a,b=edge['parent'],edge['child'];ff,cc,tt=pair_view(frames,C,tr,a,b);ix={s:[i for i,f in enumerate(ff)if f['side']==s]for s in ['A','B']};held=read(Path(edge['folder'])/'M4_HELD.json');t=edge['results']['M4']['T'];fig,axes=plt.subplots(3,4,figsize=(17,10));reps=np.rint(np.linspace(0,min(len(ix['A']),len(ix['B']))-1,3)).astype(int)
   for row,k in enumerate(reps):
    ja,jb=ix['A'][k],ix['B'][k];ra=cv2.imread(ff[ja]['RGB_path'])[:,:,::-1];rb=cv2.imread(ff[jb]['RGB_path'])[:,:,::-1];ax=axes[row,0];ax.imshow(np.concatenate([ra,rb],1));ids=np.flatnonzero(np.isfinite(tt['xy'][:,[ja,jb]]).all((1,2)))
    for tid in ids:
     u,v=tt['xy'][tid,ja];x,y=tt['xy'][tid,jb];ax.plot([u,x+640],[v,y],c='purple'if tt['held'][tid]else'green',lw=.4,alpha=.5)
    ax.set_title(f'RAW {ff[ja]["raw_frame"]}/{ff[jb]["raw_frame"]} 自动轨迹{len(ids)}');ax.axis('off')
    for col,j,rgb in [(1,jb,rb),(2,ja,ra)]:
     ax=axes[row,col];ax.imshow(rgb);items=[r for r in held if r['frame']==j]
     for r in items:
      uv=tt['xy'][r['track'],j];ax.plot(*uv,'+',c='lime',ms=4)
      if r['status']=='VALID':q=r['projection'];ax.plot(*q,'rx',ms=3);ax.plot([uv[0],q[0]],[uv[1],q[1]],c='yellow',lw=.4)
     ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_title(('A→B'if col==1 else'B→A')+f' 留出{len(items)} / 失效越界{sum(r["status"]!="VALID"for r in items)}');ax.axis('off')
    ax=axes[row,3];ax.imshow(rb);R=Path(next(v['run']for v in asset['videos']if v['case']==b));ob=np.load(R/'observations'/(ff[jb]['id'].split('__',1)[1]+'_ring.npz'));q=ob['q_held'];ax.scatter(q[:,0],q[:,1],s=2,c='lime')
    for tv,color in [(np.eye(4),'yellow'),(t,'red')]:
     if tv is not None:
      try:
       for curve in project_contours(np.array(tv)@cc[jb],np.array(ff[jb]['K']),2*(radius-.6),n=256):ax.plot(curve[:,0],curve[:,1],c=color,lw=.7)
      except Exception:ax.text(5,20,'CAD不可投影',c=color)
    ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_title('Ring：绿held 黄配准前 红M4');ax.axis('off')
   fig.suptitle(g+'\n边 '+a.rsplit('_',1)[-1]+' / '+b.rsplit('_',1)[-1]+'：绿FIT 紫held；双向独立DLT投影，失效不删除；图像非GT');fig.tight_layout(rect=(0,0,1,.93));name=f'rgb_ring_{ei}.png';fig.savefig(dest/name,dpi=100);plt.close(fig);images.append(name)
 save(dest/'VIEWS.json',dict(full_bounds_mm=full,near_bounds_mm=near,clipped_faces=clips,views=VIEWS,source_count=len(packs),cases=cases,all_raw_faces=sum(len(p['F'])for p in packs)))
 body='<h1>'+g+'</h1><p>'+legend+'</p><p>状态：'+reg['status']+'。配准后所有视角共用同一个视频级变换。无三维GT；曲面更整洁不等于位姿更准确。</p>'+''.join('<h2>'+n+'</h2><img style="width:100%" src="'+n+'">'for n in images)
 (dest/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>M4 '+g+'</title><body style="max-width:1800px;margin:auto;font-family:sans-serif">'+body+'</body>');save(out/'REVIEW_COMPLETE.json',dict(key=key,images=[dict(path=str(dest/n),sha256=sha(dest/n))for n in images]));print('REVIEW',g,len(images),flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group');p.add_argument('--ready',action='store_true');a=p.parse_args()
 for row in read(T/'config/INVENTORY.json')['groups']:
  g=row['group']
  if a.group and a.group!=g:continue
  if a.ready and not(group_out(g)/'CONSUMER_CHECK.json').exists():continue
  try:review(g)
  except Exception as e:save(group_out(g)/'REVIEW_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));print('REVIEW FAILURE',g,repr(e),flush=True)
