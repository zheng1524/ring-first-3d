"""Actual original-face ray renders and frozen shared-body renders; no GT/postprocessing."""
from visual_base import *
from matplotlib.colors import ListedColormap
import argparse
ROOT=Path(__file__).resolve().parents[1]
GROUPS=['G06','G05','G01','G03']
LABEL_COLORS=np.array([[.16,.72,.32],[1.,.72,.12],[.88,.12,.12],[.66,.66,.66]])
plt.rcParams.update({'font.size':8,'axes.titlesize':9})

def srcroot(r):return ROOT/('hero_fit'if r['role']=='FIT'else'holdout/hero')/r['view_id']
def body(g,arm=None):
 p=ROOT/'inputs'/g/'INITIAL.npz'if arm is None else ROOT/'arms'/arm/'local_results'/g/'FINAL.npz'
 return dict(np.load(p))
def body_bounds(g):
 return np.r_[body(g)['V'],np.load(ROOT/'inputs'/g/'RING.npz')['V']]
def bounds(g):
 rr=[r for r in load(ROOT/'config/VIEW_PLAN.json')if r['group']==g and r['role']=='FIT'];p=[body(g)['V']]
 for r in rr:
  a=np.load(srcroot(r)/'FULL_HERO.npz');p.append(a['V'][np.unique(a['F'])])
 return np.vstack(p)
def raw_panel(ax,r,kind,limit):
 a=np.load(srcroot(r)/'FACE_EVIDENCE.npz');rr=np.load(ROOT/'inputs'/r['group']/'RING.npz');V,F,st=a['V'],a['F'],a['state'];col=LABEL_COLORS[np.minimum(st,3)]
 if kind=='TRUSTED':take=st==0;F=F[take];col=col[take]
 if kind=='EXCLUDED':take=st!=0;F=F[take];col=col[take]
 if kind=='RAW':col=np.tile([.40,.59,.76],(len(F),1))
 im,sc=actual_mesh_image(V,F,rr['V'],rr['F'],limit,25,-65,'#6699bb',col);ax.imshow(im);ax.plot([20,20+2*sc],[375,375],c='black');ax.text(20,365,'2 mm at view center',fontsize=6);ax.axis('off')
def overlay_panel(ax,g,z,r,limit,angle=(25,-65),hero=True):
 V=z['V'];F=z.get('F_solid',z['F']);color=np.tile([.48,.36,.76],(len(F),1));color[z.get('inferred_base_faces',np.zeros(len(F),bool))]=[.65,.65,.65]
 if hero:
  a=np.load(srcroot(r)/'TRUSTED_HERO.npz');F=np.r_[F,a['F']+len(V)];V=np.r_[V,a['V']];color=np.r_[color,np.tile([.15,.75,.35],(len(a['F']),1))]
 rr=np.load(ROOT/'inputs'/g/'RING.npz');im,sc=actual_mesh_image(V,F,rr['V'],rr['F'],limit,*angle,'#7755aa',color);ax.imshow(im);ax.plot([20,20+2*sc],[375,375],c='black');ax.text(20,365,'2 mm at view center',fontsize=6);ax.axis('off')
def source_render(ax,g,z,r,with_hero=True):
 d=np.load(r['cache']);K,T=d['K'],d['T'];rv=np.load(ROOT/'inputs'/g/'RING.npz');V=z['V'];F=z.get('F_solid',z['F']);fc=np.tile([.5,.35,.8],(len(F),1));fc[z.get('inferred_base_faces',np.zeros(len(F),bool))]=[.65,.65,.65]
 if with_hero:
  a=np.load(srcroot(r)/'TRUSTED_HERO.npz');F=np.r_[F,a['F']+len(V)];V=np.r_[V,a['V']];fc=np.r_[fc,np.tile([.15,.75,.35],(len(a['F']),1))]
 rt=o3d.t.geometry.RaycastingScene(nthreads=2)
 for v,f in [(V,F),(rv['V'],rv['F'])]:rt.add_triangles(o3d.core.Tensor(v.astype(np.float32)),o3d.core.Tensor(f.astype(np.uint32)))
 yy,xx=np.mgrid[:360,:640];ray=np.c_[xx.ravel(),yy.ravel(),np.ones(360*640)]@np.linalg.inv(K).T;rays=np.c_[np.broadcast_to(T[:3,3],ray.shape),ray@T[:3,:3].T].astype(np.float32);hit=rt.cast_rays(o3d.core.Tensor(rays));gid=hit['geometry_ids'].numpy();fid=hit['primitive_ids'].numpy();im=np.full((360*640,3),.96)
 for idx,(v,f,col)in enumerate([(V,F,fc),(rv['V'],rv['F'],np.tile([.03,.03,.03],(len(rv['F']),1)))]):
  sel=gid==idx;norm=trimesh.Trimesh(v,f,process=False).face_normals;light=T[:3,3]-(v[f].mean(1));light/=np.maximum(np.linalg.norm(light,axis=1)[:,None],1e-12);shade=.5+.5*abs((norm*light).sum(1));im[sel]=col[fid[sel]]*shade[fid[sel],None]
 ax.imshow(im.reshape(360,640,3));ax.axis('off')
def source_residual_3d(ax,g,r,o,e,limit):
 a=np.load(srcroot(r)/'FACE_EVIDENCE.npz');F,V=a['F'],a['V'];fid=o['face_id'];act=e['active'];N=len(F);count=np.bincount(fid[act],minlength=N);total=np.bincount(fid[act],weights=abs(e['z'][act]-o['z'][act]),minlength=N);bad=np.bincount(fid[~act],minlength=N);v=total/np.maximum(count,1);fc=plt.get_cmap('viridis')(np.clip(v/2,0,1))[:,:3];fc[count==0]=[.68,.68,.68];fc[(count==0)&(bad>0)]=[.9,.1,.75];keep=a['state']==0;rv=np.load(ROOT/'inputs'/g/'RING.npz');im,sc=actual_mesh_image(V,F[keep],rv['V'],rv['F'],limit,25,-65,'green',fc[keep]);ax.imshow(im);ax.plot([20,20+2*sc],[375,375],c='black');ax.text(20,365,'2 mm at view center',fontsize=6);ax.axis('off')
def target_rgb(ax,r):
 d=np.load(r['cache']);ax.imshow(d['RGB']);edge(ax,d['labels']==1,'lime');edge(ax,d['labels']==2,'cyan');ax.axis('off')
def inputs():
 plan=load(ROOT/'config/VIEW_PLAN.json');fig,axs=plt.subplots(4,4,figsize=(16,15))
 for i,g in enumerate(GROUPS):
  rr=[r for r in plan if r['group']==g];fit=[r for r in rr if r['role']=='FIT'];r=fit[0];lim=bounds(g);c=load(srcroot(r)/'CLEANING.json');target_rgb(axs[i,0],r);axs[i,0].set_title(g+' '+r['view_id']+'\n'+str(len(fit))+' FIT + '+str(len(rr)-len(fit))+' HOLDOUT, all native HERO ready')
  for j,k in enumerate(['RAW','TRUSTED','EXCLUDED'],1):raw_panel(axs[i,j],r,k,lim);axs[i,j].set_title(k+' original source faces\n'+('no coordinates changed'if k=='RAW'else('green original Face subset'if k=='TRUSTED'else'yellow uncertain / gray unknown / red rejected')))
  f,aa=plt.subplots(len(rr),4,figsize=(14,2.7*len(rr)),squeeze=False)
  for k,src in enumerate(rr):
   c=load(srcroot(src)/'CLEANING.json');target_rgb(aa[k,0],src);aa[k,0].set_title(src['view_id']+' '+src['role']+'\n'+('reused native'if load(srcroot(src)/'SOURCE.json')['reused']else'new official HERO'))
   for j,key in enumerate(['RAW','TRUSTED','EXCLUDED'],1):raw_panel(aa[k,j],src,key,lim);aa[k,j].set_title(key+(' | '+str(c['trusted_faces'])+' faces'if key=='TRUSTED'else''))
  f.suptitle(g+' all target-source identities, actual unchanged original HERO faces | native mm\nHOLDOUT assets are evaluation-only. Black fixed CAD Ring. Full tables list all43 views.');f.tight_layout(rect=[0,0,1,.97]);finish(f,'full/'+g+'/Fig1_2_All_Sources_And_Cleaning.png',110)
  f,aa=plt.subplots(1,3,figsize=(12,4))
  for j,ang in enumerate([(25,-65),(10,-150),(65,25)]):overlay_panel(aa[j],g,body(g),r,lim,ang);aa[j].set_title('Shared frozen016 body + own-view TRUSTED\n'+str(ang)+' | blue/green are distinct meshes')
  f.tight_layout();finish(f,'full/'+g+'/Fig3_Initial_Body_And_Trusted.png')
 fig.suptitle('018: actual per-source Raw /017 TRUSTED-only /excluded original-face subsets\n29 FIT +14 protected HOLDOUT; 4 reused +39 genuine official HERO inferences; no projected substitutes\nRepresentative source = first frozen FIT view for each group; detailed sheets show every target view. All Ring surfaces black.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig1_All_View_HERO_And_Trusted.png',125)

def results():
 assert(ROOT/'provenance/ALL_OPTIMIZED_PREDICTIONS_FROZEN.json').exists();plan=load(ROOT/'config/VIEW_PLAN.json');metrics=load(ROOT/'evaluation/metrics/COMPARISON.json');mi={(r['group'],r['arm']):r for r in metrics};fig,axs=plt.subplots(4,4,figsize=(16,16));routes=['B0_FROZEN','B1_FULL_COH16','B2_TRUSTED_COH16','OLD_D2_COH16']
 for i,g in enumerate(GROUPS):
  lim=bounds(g);rr=[r for r in plan if r['group']==g and r['role']=='FIT'];r=rr[0]
  for j,arm in enumerate(routes):
   z=body(g,None if arm=='B0_FROZEN'else arm);model_panel(axs[i,j],g,z,body_bounds(g));row=mi[g,arm];axs[i,j].set_title(g+' '+arm.replace('_COH16','')+'\nHERO MAE %.3f mm | miss %.1f%%\nFIT/HOLD IoU %.3f / %.3f'%(row['HERO_MAE_mm'],100*row['FIT_miss_fraction'],row['FIT_IoU'],row['HOLDOUT_IoU']))
  # Each group: same source camera and two same-metric free-view pairs.
  f,aa=plt.subplots(3,3,figsize=(13,11))
  for rowidx,src in enumerate([rr[0],rr[len(rr)//2]]):
   target_rgb(aa[rowidx,0],src);aa[rowidx,0].set_title(src['view_id']+' | actual RGB /Mask')
   for j,arm in enumerate(['B0_FROZEN','B2_TRUSTED_COH16'],1):
    e=np.load(ROOT/'evaluation/local_results'/g/arm/(src['view_id']+'_EVAL.npz'));target_rgb(aa[rowidx,j],src);edge(aa[rowidx,j],e['pred'],'#c756ff');aa[rowidx,j].set_title(arm+' predicted contour purple')
  for j,(z,label)in enumerate([(body(g),'B0'),(body(g,'B2_TRUSTED_COH16'),'B2'),(body(g,'B1_FULL_COH16'),'B1')]):overlay_panel(aa[2,j],g,z,r,lim,(10,-150));aa[2,j].set_title(label+' + frozen TRUSTED at identical side view')
  detail,dd=plt.subplots(2,3,figsize=(13,7))
  for rowidx,src in enumerate([rr[0],rr[len(rr)//2]]):
   target_rgb(dd[rowidx,0],src);dd[rowidx,0].set_title(src['view_id']+' actual RGB')
   for jj,(zz,ll)in enumerate([(body(g),'B0'),(body(g,'B2_TRUSTED_COH16'),'B2')],1):source_render(dd[rowidx,jj],g,zz,src);dd[rowidx,jj].set_title(ll+' at exact native source camera\nshared body purple /fixed TRUSTED green /CAD black')
  detail.suptitle(g+' source-camera actual triangle render, original K and c2w; no rigid alignment or view substitution');detail.tight_layout(rect=[0,0,1,.94]);finish(detail,'full/'+g+'/Source_Camera_Actual_3D_Projection.png')
  f.suptitle(g+' actual common-view Mesh update. Green=TRUSTED source; purple=one shared body\nOverlay is a diagnostic, not a fused two-Mesh output. No smoothing, filling, trimming or scale adjustment.');f.tight_layout(rect=[0,0,1,.94]);finish(f,'full/'+g+'/Fig4_Actual_Projection_And_Mesh.png')
 fig.suptitle('Identical mm world frame, fixed camera and display extent within each case | actual raw shared Mesh outputs\nHERO error conditioned on hits; missing is shown separately. No GT used, no physical-accuracy claim. Black Ring CAD.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig2_Four_Group_Shared_Body_Comparison.png',135)
 # Every source ray: residuals/misses are actual native pixel arrays.
 fig,axs=plt.subplots(4,5,figsize=(20,14))
 for i,g in enumerate(GROUPS):
  rr=[r for r in plan if r['group']==g and r['role']=='FIT'];src=rr[0];cid=src['view_id'];e=np.load(ROOT/'evaluation/local_results'/g/'B2_TRUSTED_COH16'/(cid+'_EVAL.npz'));o=np.load(srcroot(src)/'OBS_TRUSTED.npz');shape=tuple(o['native_shape']);active=e['active'];heat=np.full(shape,np.nan);uv=o['uv'];heat[uv[active,1],uv[active,0]]=e['z'][active]-o['z'][active];missing=np.zeros(shape);missing[uv[~active,1],uv[~active,0]]=1
  target_rgb(axs[i,0],src);axs[i,0].set_title(g+' '+cid+'\nfirst frozen FIT source')
  im=axs[i,1].imshow(heat,cmap='coolwarm',vmin=-2,vmax=2);axs[i,1].set_title('Actual active-ray axial residual (mm)');axs[i,1].axis('off');fig.colorbar(im,ax=axs[i,1],shrink=.65)
  axs[i,2].imshow(np.zeros(shape),cmap='gray',vmin=0,vmax=1);axs[i,2].imshow(np.ma.masked_where(missing==0,missing),cmap=ListedColormap(['red']),vmin=0,vmax=1);axs[i,2].set_title('TRUSTED rays without valid body hit: red\n%d / %d; no missing-depth gradient'%(int((~active).sum()),len(active)));axs[i,2].axis('off')
  z=body(g,'B2_TRUSTED_COH16');disp=np.linalg.norm(z['V']-body(g)['V'],axis=1);ff=z['F_solid'];colors=plt.get_cmap('viridis')(np.clip(disp[ff].mean(1)/max(disp.max(),1e-12),0,1))[:,:3];model_panel(axs[i,3],g,z,body_bounds(g),face_colors=colors);axs[i,3].set_title('Actual total vertex displacement\nmax %.6f mm; per-case 0..max color scale'%disp.max())
  source_residual_3d(axs[i,4],g,src,o,e,bounds(g));axs[i,4].set_title('Actual TRUSTED source faces: mean |dz|\n0..2 mm viridis; magenta no active ray')
  f,aa=plt.subplots(1,3,figsize=(13,4));
  for j,ang in enumerate([(25,-65),(10,-150),(65,25)]):model_panel(aa[j],g,z,body_bounds(g),angle=ang,face_colors=colors);aa[j].set_title('Actual displacement colored | '+str(ang))
  f.suptitle(g+' no geometry hidden; cap gray inferred, black fixed CAD');f.tight_layout();finish(f,'full/'+g+'/Fig5_Displacement_And_Ring.png')
 fig.suptitle('Actual source ray correspondence and geometry: residual /missing /vertex displacement\nNo arbitrary backside nearest-point attraction. High miss fractions remain a scientific failure/limitation.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig3_Native_Correspondence_And_Actual_Update.png')
 # Multisource ablations and actual gradient-to-delta vectors for G03.
 fig,axs=plt.subplots(2,4,figsize=(17,9));g='G01';lim=bounds(g)
 for j,arm in enumerate(['B0_FROZEN','SINGLE_TRUSTED_COH16','TWO_TRUSTED_COH16','B2_TRUSTED_COH16']):
  z=body(g,None if arm=='B0_FROZEN'else arm);model_panel(axs[0,j],g,z,body_bounds(g));row=mi[g,arm];axs[0,j].set_title('G01 '+arm.replace('_COH16','')+'\nHERO %.3f mm, miss %.1f%%'%(row['HERO_MAE_mm'],100*row['FIT_miss_fraction']))
 g='G03';lim=bounds(g)
 for j,arm in enumerate(['B0_FROZEN','B1_FULL_COH16','B2_TRUSTED_COH16']):model_panel(axs[1,j],g,body(g,None if arm=='B0_FROZEN'else arm),body_bounds(g),(10,-150));axs[1,j].set_title('G03 '+arm.replace('_COH16','')+' | side')
 hist=load(ROOT/'arms/B2_TRUSTED_COH16/metrics/G03_TRAINING.json');axs[1,3].plot([x['attempt']for x in hist],[x['max_total_mm']for x in hist],c='purple');axs[1,3].set(xlabel='candidate iteration',ylabel='actual max total displacement (mm)',title='G03 actual geometric progress, not IoU');axs[1,3].grid(alpha=.25)
 fig.suptitle('G01 uses the same8 FIT silhouettes and one common initial Mesh for source-count ablations\nG03 uses the identical method; no Ip-specific stalk prior, no topology change, no hidden completion claim.');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Fig4_G01_Multisource_And_G03_Difficult_Geometry.png')
 # Component gradients are measured gradients, arrows are the separately recorded Adam/projection update.
 fig,axs=plt.subplots(2,3,figsize=(14,9),subplot_kw={'projection':'3d'})
 for i,g in enumerate(['G06','G03']):
  folder=ROOT/'arms/B2_TRUSTED_COH16/local_results'/g;z=body(g);V,F=z['V'],z['F'];comp=np.load(folder/'INITIAL_COMPONENT_GRADIENTS.npz');h=sum((comp[k]for k in comp.files if k.startswith('hero_')),np.zeros_like(V));s=sum((comp[k]for k in comp.files if k.startswith('silhouette_')),np.zeros_like(V));final=body(g,'B2_TRUSTED_COH16');delta=final['V']-V;rr=np.load(ROOT/'inputs'/g/'RING.npz');lim=body_bounds(g)
  for j,(vec,label)in enumerate([(-h,'negative HERO component gradient'),(-s,'negative silhouette component gradient'),(delta,'actual accepted cumulative displacement (mm)')]):
   ax=axs[i,j];ax.add_collection3d(Poly3DCollection(V[F],facecolor=(.6,.65,.75,.14),edgecolor=(.4,.4,.4,.12),linewidth=.15));ax.add_collection3d(Poly3DCollection(rr['V'][rr['F']],facecolor=(0,0,0,.6),linewidth=0));ix=np.argsort(np.linalg.norm(vec,axis=1))[-40:];length=np.linalg.norm(vec,axis=1).max();scale=1. if j==2 else .7/max(length,1e-30);ax.quiver(*V[ix].T,*(vec[ix]*scale).T,color=['green','orange','purple'][j],linewidth=.8,arrow_length_ratio=.15);ax.set_title(g+' '+label+'\n'+('gradient arrows display-scaled %.3g'%scale if j<2 else'actual delta, no gradient substitution'));lo,hi=lim.min(0),lim.max(0);cc=(lo+hi)/2;rad=(hi-lo).max()/2;ax.set(xlim=(cc[0]-rad,cc[0]+rad),ylim=(cc[1]-rad,cc[1]+rad),zlim=(cc[2]-rad,cc[2]+rad),xlabel='X mm',ylabel='Y mm',zlabel='Z mm');ax.set_box_aspect((1,1,1));ax.view_init(20,-65)
 fig.suptitle('Measured per-view autograd contributions vs actual accepted update, all world-mm vertices\nSobolev/contact proposal and Adam change update direction; delta is not attributed to one component gradient.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig5_Actual_Gradient_And_Displacement.png')
 print('ALL_ACTUAL_MESH_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs-only',action='store_true');a=p.parse_args();inputs()
 if not a.inputs_only:results()
