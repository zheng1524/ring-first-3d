"""Actual immutable triangles and cameras. Direct Open3D compositor reused from018."""
from geometry021 import *
from visual_base import plt,finish,edge
import matplotlib
from scipy.spatial.transform import Rotation
plt.rcParams.update({'font.size':8,'axes.titlesize':9})
P19=REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019'
FRAME4={a['view_id']:a for a in load(P18/'metrics/FRAME_BINDING_AUDIT.json')}
FRAME5={a['view']:a for a in load(P19/'metrics/VIDEO005_FRAME_BINDING.json')['rows']}
def temporal_frame(c):
 cid=c.get('id',c.get('view_id'));v=c.get('meta',c);video=c.get('video',v.get('video','004'));a=FRAME5.get(cid,{})if video=='005'else FRAME4.get(cid,{});q=a.get('exact_raw_matches',[])if video=='005'else a.get('exact_content_matches',[])+a.get('JPEG_chain_matches',[]);return q[0].get('raw_index_zero_based',q[0].get('raw_index'))if q else v.get('raw_frame',0)


def layer(V,F,color,name):
 F=np.asarray(F);fc=np.tile(matplotlib.colors.to_rgb(color),(len(F),1))if isinstance(color,str)or np.asarray(color).ndim==1 else np.asarray(color);return dict(V=np.asarray(V),F=F,colors=fc,name=name)

def composite(layers):
 s=o3d.t.geometry.RaycastingScene(nthreads=2);data=[]
 for a in layers:
  s.add_triangles(o3d.core.Tensor(a['V'].astype(np.float32)),o3d.core.Tensor(a['F'].astype(np.uint32)));m=trimesh.Trimesh(a['V'],a['F'],process=False);data.append(a|dict(normals=m.face_normals,centers=m.triangles_center))
 return s,data

def render(prepared,C,K,size):
 s,layers=prepared;h,w=size;y,x=np.mgrid[:h,:w];rs=rays(np.c_[x.ravel(),y.ravel()],K,C);hit=s.cast_rays(rs);gid=hit['geometry_ids'].numpy();fid=hit['primitive_ids'].numpy();im=np.full((h*w,3),.96)
 for i,a in enumerate(layers):
  mask=gid==i;f=fid[mask];light=C[:3,3]-a['centers'][f];light/=np.maximum(np.linalg.norm(light,axis=1)[:,None],1e-12);shade=.45+.55*abs((a['normals'][f]*light).sum(1));im[mask]=a['colors'][f]*shade[:,None]
 return np.clip(im.reshape(h,w,3),0,1)

def free_camera(bounds,elev,azim):
 lo,hi=bounds.min(0),bounds.max(0);center=(lo+hi)/2;rad=np.linalg.norm(bounds-center,axis=1).max();el,az=np.radians([elev,azim]);pos=center+rad*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);forward=(center-pos)/np.linalg.norm(center-pos);right=np.cross(forward,[0,0,1.]);right/=np.linalg.norm(right);down=np.cross(forward,right);C=np.eye(4);C[:3,:3]=np.array([right,down,forward]).T;C[:3,3]=pos;return C,np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]]),(400,400)

def panel(ax,prepared,view,bounds,title):
 C,K,size=view;ax.imshow(render(prepared,C,K,size));center=(bounds.min(0)+bounds.max(0))/2;depth=((center-C[:3,3])@C[:3,:3])[2];pix=2*K[0,0]/max(depth,1e-6);h,w=size;ax.plot([15,15+pix],[h-20,h-20],c='black',lw=2);ax.text(15,h-30,'2 mm at view-center depth',fontsize=5);ax.axis('off');ax.set_title(title)

def colors(n):return plt.get_cmap('turbo')(np.linspace(.06,.94,n))[:,:3]

def full_context(ax,cams,src,rv,bounds):
 layers=[layer(a['V'],a['F'],a['color'],a['id'])for a in src]+[layer(rv['V'],rv['F'],'black','CAD')]
 for c in cams:
  uv=np.array([[0,0],[639,0],[639,359],[0,359]]);p=np.c_[uv,np.ones(4)]@np.linalg.inv(c['K']).T;p=p@c['C'][:3,:3].T+c['C'][:3,3];V=np.r_[c['C'][:3,3][None],p];F=np.array([[0,1,2],[0,2,3],[0,3,4],[0,4,1]]);layers.append(layer(V,F,'#2474b5'if c['video']=='004'else'#dc841e',c['id']))
 for video in ['004','005']:
  cc=sorted([v for v in cams if v['video']==video],key=temporal_frame)
  for a,b in zip(cc,cc[1:]):
   x,y=a['C'][:3,3],b['C'][:3,3]
   if np.linalg.norm(x-y)>1e-8:
    m=trimesh.creation.cylinder(radius=.025,segment=np.array([x,y]),sections=6);layers.append(layer(m.vertices,m.faces,'#2474b5'if video=='004'else'#dc841e','trajectory'))
 extra=[]
 if any(c['video']=='005'for c in cams):
  X=np.asarray(load(R/'results/B3.json')['X']);extra.extend(X)
  for i,x in enumerate(X):
   m=trimesh.creation.icosphere(subdivisions=1,radius=.10);m.apply_translation(x);layers.append(layer(m.vertices,m.faces,'lime','SIFT_glyph_'+str(i)))
 ext=np.r_[bounds,np.array([c['C'][:3,3]for c in cams]),np.asarray(extra).reshape(-1,3)];panel(ax,composite(layers),free_camera(ext,25,-65),ext,'All actual cameras/frusta/trajectories\nblack CAD; green glyph centers=common SIFT (if005)')

def base_layer(group,b):
 p=load(P18/'inputs'/group/'BASE_SELECTION.json');plane=np.asarray(p['plane'],float);plane/=np.linalg.norm(plane[:3]);n=plane[:3];u=np.cross(n,[1.,0,0]);u/=np.linalg.norm(u);v=np.cross(n,u);c=b['V'].mean(0);c-=n*(c@n+plane[3]);r=np.linalg.norm(b['V']-b['V'].mean(0),axis=1).max()*.8;V=c+r*np.array([-u-v,u-v,u+v,-u+v]);return layer(V,np.array([[0,1,2],[0,2,3]]),[.83,.83,.78],'ESTIMATED_BASE_'+p.get('base_status','UNKNOWN')),p

def body_layer(z,name):
 fc=np.tile([.48,.35,.77]if name=='B2'else[.5,.56,.63],(len(z['F_solid']),1));fc[z['inferred_base_faces']]=[.65,.65,.65];return layer(z['V'],z['F_solid'],fc,name)

def camera_views(conf,H,bounds):
 vv=conf['views']
 if conf['group']=='G01':vv=[dict(view_id=v['id'],cache=v['cache'],role=v['role'],video=v['video'],meta=v)for v in load(R/'config/VIEWS.json')]
 c=[]
 for v in vv:
  a=np.load(v['cache']);C=H@a['T']if v['video']=='005'else a['T'];c.append(dict(id=v['view_id'],role=v['role'],video=v['video'],C=C,K=a['K'],cache=v['cache'],meta=v['meta']))
 first=next(v for v in c if v['role']=='FIT'and v['video']=='004');u=first['C'][:3,3]/np.linalg.norm(first['C'][:3,3]);second=max(c,key=lambda v:np.arccos(np.clip(u@v['C'][:3,3]/np.linalg.norm(v['C'][:3,3]),-1,1)));views=[(first['C'],first['K'],(360,640)),(second['C'],second['K'],(360,640))]+[free_camera(bounds,*a)for a in [(89.5,-65),(0,-90),(0,90),(-89.5,-65)]];names=['actual '+first['id'],'complementary '+second['id'],'world top','world side','world opposite side','world underside'];return c,views,names


def export_glb(group,src,bodies,ring,cams):
 sc=trimesh.Scene();index=[]
 def add(a,name,alpha=255):
  # Compact unreferenced vertices for export only; no original triangle removed.
  used,inv=np.unique(a['F'],return_inverse=True);m=trimesh.Trimesh(a['V'][used],inv.reshape(-1,3),process=False);col=np.c_[np.clip(a['colors']*255,0,255).astype(np.uint8),np.full(len(a['F']),alpha,np.uint8)];m.visual.face_colors=col;sc.add_geometry(m,node_name=name,geom_name=name)
 add(layer(ring['V'],ring['F'],'black','Ring'),'Ring_CAD_FIXED')
 for n,z in bodies.items():add(body_layer(z,n),'BODY_'+n+'_INFERRED_CAP_GRAY',180)
 if load(P18/'inputs'/group/'CHART.json')['cap']:
  a,p=base_layer(group,bodies['B2']);add(a,'BACKGROUND_BASE_ESTIMATE_'+p.get('base_status','UNKNOWN')+'_NOT_GT',45)
 for a in src:
  add(layer(a['V'],a['F'],a['color'],a['id']),'HERO_'+a['id']);index.append(dict(source_id=a['id'],video=a['video'],origin=a['source']['origin'],mesh=a['source']['mesh'],observation=a['source']['observation'],color_rgb=a['color'],original_face_count=len(a['F']),source_mesh_with_original_face_ids_sha256=sha(a['source']['mesh']['path']),original_face_id_array_sha256=hashlib.sha256(np.asarray(a['mesh']['original_face_id'],np.int64).tobytes()).hexdigest(),object='HERO_'+a['id']))
 for c in cams:
  # Actual calibrated image frustum at 1mm axial depth, fixed camera geometry.
  uv=np.array([[0,0],[639,0],[639,359],[0,359]]);p=np.c_[uv,np.ones(4)]@np.linalg.inv(c['K']).T;p=p@c['C'][:3,:3].T+c['C'][:3,3];V=np.r_[c['C'][:3,3][None],p];F=np.array([[0,1,2],[0,2,3],[0,3,4],[0,4,1]]);col='#2474b5'if c['video']=='004'else'#dc841e';add(layer(V,F,col,c['id']),'CAMERA_'+c['id'])
 for video in ['004','005']:
  cc=sorted([v for v in cams if v['video']==video],key=temporal_frame)
  for j,(a,b)in enumerate(zip(cc,cc[1:])):
   p,q=a['C'][:3,3],b['C'][:3,3]
   if np.linalg.norm(p-q)<1e-8:continue
   m=trimesh.creation.cylinder(radius=.025,segment=np.array([p,q]),sections=6);m.visual.face_colors=[36,116,181,255]if video=='004'else[220,132,30,255];sc.add_geometry(m,node_name='TRAJECTORY_'+video+'_'+str(j))
 if group=='G01':
  X=np.asarray(load(R/'results/B3.json')['X']);sc.add_geometry(trimesh.points.PointCloud(X,colors=np.tile([0,200,80,255],(len(X),1))),node_name='COMMON_SIFT_B3_NOT_HERO')
 sc.apply_transform(np.diag([.001,.001,.001,1.]));dest=R/'derived'/group;dest.mkdir(exist_ok=True);path=dest/(group+'_INDEPENDENT_LAYERS_NOT_FUSION.glb');sc.export(path);save('derived/'+group+'/SOURCE_LAYER_INDEX.json',dict(group=group,layers=index,bodies={k:asset(Path(next(g for g in load(R/'config/FOUR_GROUP_INPUTS.json')if g['group']==group)['bodies'][k]['path']))for k in bodies},cameras=[dict(id=c['id'],video=c['video'],C=c['C'],K=c['K'],temporal_frame_index=temporal_frame(c))for c in cams],GLB=asset(path),geometry_unit='mm; export-only exact .001 conversion to GLB meters',no_ICP_no_fusion_no_repair=True));return path

def group_figures(group):
 H=np.array(load(R/'results/B3.json')['T'])if group=='G01'else np.eye(4);conf,src=group_data(group,H);rv=dict(np.load(conf['ring']['path']));bodies={n:dict(np.load(a['path']))for n,a in conf['bodies'].items()};cols=colors(len(src));bounds=np.r_[rv['V'],*[a['V'][np.unique(a['F'])]for a in src],*[b['V']for b in bodies.values()]]
 for a,col in zip(src,cols):a['color']=col
 cams,views,names=camera_views(conf,H,bounds);ring=layer(rv['V'],rv['F'],'black','CAD');hero=[layer(a['V'],a['F'],a['color'],a['id'])for a in src];evidence=[];error=[]
 for a in src:
  d=np.load(R/'evaluation/groups'/group/(a['id']+'_SOURCE_EVIDENCE.npz'));evidence.append(layer(a['V'],a['F'],VIS_COLORS[d['face_class']],a['id']));fc=plt.get_cmap('viridis')(np.clip(d['B2_surface_distance_mm']/2,0,1))[:,:3];error.append(layer(a['V'],a['F'],fc,a['id']))
 scenes=[composite(hero+[ring]),composite(hero+[body_layer(bodies['B0'],'B0'),ring]),composite(hero+[body_layer(bodies['B2'],'B2'),ring]),composite(evidence+[ring])];titles=['A: all original TRUSTED HERO','B: same HERO + frozen B0','B: same HERO + frozen B2','C: actual per-source visibility evidence']
 fig,axs=plt.subplots(6,4,figsize=(17,22))
 for i,(v,label)in enumerate(zip(views,names)):
  for j in range(4):panel(axs[i,j],scenes[j],v,bounds,group+' | '+label+'\n'+titles[j])
 from matplotlib.patches import Patch
 fig.legend(handles=[Patch(facecolor=a['color'],label=a['id'])for a in src],loc='lower center',ncol=3,fontsize=5.5)
 fig.suptitle(group+' six fixed views, original metric coordinates, all source triangles; NO fusion / ICP / repair\nEvidence: green support; red front disagreement PROXY; blue deeper (may self-occlude); purple CAD occluded; gray unknown; orange mixed\nSource IDs/colors and all calibrated cameras in SOURCE_LAYER_INDEX.json and independent GLB nodes. Same extent in each view row.');fig.tight_layout(rect=[0,.06,1,.95]);finish(fig,'groups/'+group+'/Six_View_HERO_Body_Evidence.png',115)
 fig,axs=plt.subplots(6,2,figsize=(10,22))
 for i,(v,label)in enumerate(zip(views,names)):
  for j,n in enumerate(['B0','B2']):panel(axs[i,j],composite([body_layer(bodies[n],n),ring]),v,bounds,n+' body only | '+label+'\ninferred bottom cap gray, not observed tissue')
 fig.tight_layout();finish(fig,'groups/'+group+'/Six_View_B0_B2_Body_Only.png',105)
 # Explicit mm error on actual HERO faces and actual body triangles.
 fig,axs=plt.subplots(2,3,figsize=(15,9));side=views[3];oblique=free_camera(bounds,25,-65)
 panel(axs[0,0],composite(error+[ring]),side,bounds,group+' actual HERO face-centroid → B2 distance\nviridis 0..2 mm, saturated above2; no surface moved')
 fig.colorbar(plt.cm.ScalarMappable(norm=matplotlib.colors.Normalize(0,2),cmap='viridis'),ax=axs[0,0],shrink=.6,label='surface distance mm (clipped display)')
 panel(axs[0,1],scenes[3],side,bounds,'Actual source disagreement classes\nnot physical truth labels')
 q=np.load(R/'evaluation/groups'/group/'B2_QUALITY.npz');fc=plt.get_cmap('magma')(np.clip((q['edge_stretch']-1)/.5,0,1))[:,:3];panel(axs[0,2],composite([layer(bodies['B2']['V'],bodies['B2']['F_solid'],fc,'stretch'),ring]),oblique,bounds,'Actual B2 edge stretch relativeB0\n1..1.5 magma, no smoothed display')
 for j,n in enumerate(['B0','B2']):panel(axs[1,j],scenes[j+1],oblique,bounds,'Original HERO + '+n+' at identical view')
 full_context(axs[1,2],cams,src,rv,bounds)
 fig.suptitle(group+' quantitative geometry shown on actual triangles; mm residual is geometric proxy, not GT\nBlackCAD. Self-occlusion and Unknown retained; gray body cap is inferred. Camera glyphs/context do not participate in evaluation.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'groups/'+group+'/Actual_3D_Error_Distribution.png',125)
 # Required dedicated detailed failure zoom: largest actual B2-source residual source, deterministic.
 sources=load(R/'metrics/groups'/f'{group}_BODY_NATIVE_DEPTH.json');worst=max((a for a in sources if a['body']=='B2'),key=lambda a:a['axial_depth_error_mm']['p95']or-1);a=next(a for a in src if a['id']==worst['source']);ev=np.load(R/'evaluation/groups'/group/(a['id']+'_SOURCE_EVIDENCE.npz'));face=ev['B2_surface_distance_mm'];take=np.flatnonzero(face>=np.quantile(face,.9));zz=a['V'][a['F'][take]].reshape(-1,3);zoom=free_camera(zz,15,-105);rgb=np.load(a['cache']);fig,axs=plt.subplots(2,4,figsize=(18,9));axs[0,0].imshow(rgb['RGB']);edge(axs[0,0],rgb['labels']==1,'lime');edge(axs[0,0],rgb['labels']==2,'cyan');axs[0,0].axis('off');axs[0,0].set_title(group+' | '+a['id']+' | actualRGB / originalMasks')
 for j,(p,title)in enumerate([(scenes[0],'All TRUSTED source meshes'),(composite([body_layer(bodies['B0'],'B0'),ring]),'Frozen B0 only'),(composite([body_layer(bodies['B2'],'B2'),ring]),'Frozen B2 only')],1):panel(axs[0,j],p,side,bounds,title)
 panel(axs[1,0],composite(error+[ring]),zoom,zz,'Detail ROI: highest source-surface residual decile\nactual triangles, viridis 0..2mm; CAD may be outside ROI')
 panel(axs[1,1],scenes[2],zoom,zz,'Same detail: all HERO + B2\nno topology changed')
 panel(axs[1,2],scenes[3],zoom,zz,'Same detail: visibility classes\nfront/deeper/unknown distinct')
 q=np.load(R/'evaluation/groups'/group/'B2_QUALITY.npz');fc=plt.get_cmap('coolwarm')(np.clip(q['area_ratio']/2,0,1))[:,:3];panel(axs[1,3],composite([layer(bodies['B2']['V'],bodies['B2']['F_solid'],fc,'area'),ring]),oblique,bounds,'B2/B0 actual per-face area ratio\ncoolwarm 0..2, gray cap identity retained in layer index')
 if group=='G05':
  b,p=base_layer(group,bodies['B2']);panel(axs[1,3],composite([body_layer(bodies['B2'],'B2'),b,ring]),oblique,bounds,'Frozen independent background base: '+p.get('base_status','UNKNOWN')+'\nlightgray reference plane; NOT Ring plane or true base GT')
 if group=='G01':full_context(axs[1,3],cams,src,rv,bounds)
 if group=='G01':figname='Fig5_G01_Crossvideo_Actual_Geometry.png'
 else:figname={'G03':'Fig6_G03_Stalk_And_Source_Geometry.png','G05':'Fig7_G05_Body_Base_And_HERO.png','G06':'Fig8_G06_Local_Deformation_And_Ring.png'}[group]
 fig.suptitle(group+' original native HERO and frozen018 bodies; errors and defects preserved | NO fusion\nLargest source p95 residual chosen for diagnosis only after prediction freeze, never used for training/model selection. Side and detail views explicitly distinguished.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,figname,125)
 # Actual source and body error locations, traceable to original face IDs.
 cases=[]
 for a in src:
  ev=np.load(R/'evaluation/groups'/group/(a['id']+'_SOURCE_EVIDENCE.npz'));order=np.argsort(ev['B2_surface_distance_mm'])[::-1][:10];cent=a['V'][a['F']].mean(1)
  for k in order:cases.append(dict(group=group,source=a['id'],original_face_id=int(ev['original_face_id'][k]),source_face_index=int(k),XYZ_mm=cent[k],B2_surface_distance_mm=float(ev['B2_surface_distance_mm'][k]),B0_surface_distance_mm=float(ev['B0_surface_distance_mm'][k]),visibility_class=VIS_NAMES[int(ev['face_class'][k])],source_RGB=a['meta'].get('RGB_source'),source_camera=a['C']))
 save('metrics/groups/'+group+'_FAILURE_LOCATIONS.json',cases);table('metrics/groups/'+group+'_FAILURE_LOCATIONS.csv',cases);save('derived/'+group+'/VISUAL_VIEW_CONFIG.json',dict(bounds_mm=[bounds.min(0),bounds.max(0)],names=names,views=[dict(C=C,K=K,image_size=size)for C,K,size in views],all_methods_same_view_and_bounds=True));path=export_glb(group,src,bodies,rv,cams);save('runtime/'+group+'_FIGURES_COMPLETE.json',dict(epoch=time.time(),GLB=asset(path)));print('GROUP021_FIGURES_GLB_COMPLETE',group,str(path),flush=True)

def sift_figures():
 tr=load(R/'observations/CROSS_COMMON_TRACKS.json');H0=np.array(load(R/'results/B0_RoMa.json')['T']);H=np.array(load(R/'results/B3.json')['T']);XA=np.array([t['X004_independent']for t in tr]);XB=np.array([t['X005_independent']for t in tr]);XB0=XB@H0[:3,:3].T+H0[:3,3];X=np.array(load(R/'results/B3.json')['X']);rv=np.load(R/'inputs/G01/RING.npz');fig=plt.figure(figsize=(15,10));ax=fig.add_subplot(2,2,1,projection='3d');ax.scatter(*XA.T,c='tab:blue',label='004 independently triangulated');ax.scatter(*XB0.T,c='tab:orange',label='005 independent mapped by fullRoMa')
 for i,(a,b)in enumerate(zip(XA,XB0)):ax.plot(*np.array([a,b]).T,c='gray',lw=.8);ax.text(*a,str(i),fontsize=5)
 from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 ax.add_collection3d(Poly3DCollection(rv['V'][rv['F']],facecolors='black',edgecolors='none'));ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm');ax.legend(fontsize=6);ax.set_title('18 actual named tracks; independent positions, NOT GT');ax.set_box_aspect([np.ptp(ax.get_xlim()),np.ptp(ax.get_ylim()),np.ptp(ax.get_zlim())])
 ax=fig.add_subplot(2,2,2);d=np.linalg.norm(XA-XB0,axis=1);ax.bar(np.arange(len(tr)),d);ax.axhline(.75,c='red',ls='--',label='old 0.75mm diagnostic, NOT rejection rule');ax.set(ylabel='independent 3D separation at RoMa (mm)');ax.set_xticks(np.arange(len(tr)));ax.tick_params(axis='x',labelsize=7);ax.legend(fontsize=6)
 for j,k in enumerate([0,9]):
  ax=fig.add_subplot(2,2,3+j);t=tr[k];obs=[next(o for o in t['observations']if o['side']==s)for s in [0,1]];strips=[]
  for o in obs:
   im=np.array(Image.open(o['RGB_source']).convert('RGB'));u,v=np.rint(o['uv']).astype(int);left=max(0,u-45);top=max(0,v-45);crop=im[top:min(im.shape[0],v+46),left:min(im.shape[1],u+46)];crop=cv2.resize(crop,(240,240));strips.append(crop)
  ax.imshow(np.concatenate(strips,axis=1));ax.axis('off');ax.set_title('Track '+str(k)+' actual RGB neighborhoods (display resized)\n'+obs[0]['view']+' → '+obs[1]['view']+' | featureIDs '+str([o['feature_id']for o in obs]))
 fig.suptitle('Fig1 | 020 independent triangulations can disagree despite real multiview descriptor/RANSAC identities\nNo spatial-nearest identity, no 3D-consistency pruning. Old robust3D proposal had5/18 inliers; bars use fullRoMa, a different transform.');fig.tight_layout(rect=[0,0,1,.93]);fig.subplots_adjust(hspace=.32);finish(fig,'Fig1_020_Named_Track_Problem.png')
 fig,axs=plt.subplots(2,3,figsize=(17,10));axs[0,0].remove();ax=fig.add_subplot(2,3,1,projection='3d');ax.scatter(*XA.T,c='tab:blue',s=10,label='004 independent');ax.scatter(*XB0.T,c='tab:orange',s=10,label='005 independent atRoMa');ax.scatter(*X.T,c='green',s=14,label='one optimized X per identity')
 for a,b,c in zip(XA,XB0,X):ax.plot(*np.array([a,c,b]).T,c='gray',lw=.5)
 ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm');ax.legend(fontsize=6)
 from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 ax.add_collection3d(Poly3DCollection(rv['V'][rv['F']],facecolors='black',edgecolors='none'))
 for vid,col in [('004','#2474b5'),('005','#dc841e')]:
  cc=[v for v in load(R/'config/VIEWS.json')if v['video']==vid];cc=sorted(cc,key=temporal_frame);c=np.array([((H@np.asarray(v['T']))if vid=='005'else np.asarray(v['T']))[:3,3]for v in cc]);ax.plot(*c.T,'.-',c=col,ms=2,label=vid+' cameras')
 ax.legend(fontsize=5);ax.set_box_aspect([np.ptp(ax.get_xlim()),np.ptp(ax.get_ylim()),np.ptp(ax.get_zlim())])
 vv=load(R/'config/VIEWS.json')
 for j,side in enumerate([0,1],1):
  cid=max(collections.Counter(o['view']for t in tr for o in t['observations']if o['side']==side),key=lambda cid:sum(o['view']==cid for t in tr for o in t['observations']));v=next(v for v in vv if v['id']==cid);im=np.load(v['cache']);ax=axs[0,j];ax.imshow(im['RGB']);C=np.asarray(v['T']);C=H@C if side else C
  for t,x in zip(tr,X):
   for o in t['observations']:
    if o['view']!=cid:continue
    p=(x-C[:3,3])@C[:3,:3];uv=p@np.asarray(v['K']).T;uv=uv[:2]/uv[2];ax.scatter(*o['uv'],s=8,c='lime');ax.scatter(*uv,s=10,c='red',marker='x');ax.annotate('',xy=uv,xytext=o['uv'],arrowprops=dict(arrowstyle='->',color='yellow',lw=.5))
  ax.set_title(cid+' actualUV green / B3 predicted red\nyellow = actual reprojection residual');ax.axis('off')
 for j,arm in enumerate(['B1','B2','B3']):
  a=load(R/'results'/(arm+'.json'));hist=load(R/'optimization'/arm/'HISTORY.json');ax=axs[1,j];ax.plot([h['iteration']for h in hist],[h['parts']['reprojection']for h in hist],label='joint-image objective');ax.plot([h['iteration']for h in hist],[h['max_point_displacement_mm']for h in hist],label='max X displacement mm');ax.set(title=arm+' actual candidate trajectory',xlabel='candidate iteration');ax.legend(fontsize=6);ax.grid(alpha=.2)
 fig.suptitle('Fig2 | Shared physical landmark parameters, actual 004/005 images and real optimizer updates\nGT / HERO / body absent from BA. Low image residual is not proof of accurate pose; uncertainty and Schur spectrum reported separately.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig2_Common_BA_Actual_Mechanism.png')

def comparison_figures():
 metrics=load(R/'metrics/REGISTRATION_COMPARISON.json');mi={m['method']:m for m in metrics};names=['B0_RoMa','B0_020_R2','B0_020_R3','B0_020_MASK','B1','B2','B3'];fig,axs=plt.subplots(2,3,figsize=(17,9));xx=np.arange(len(names))
 for ax,key,label in [(axs[0,0],'HOLDOUT_IoU','independent body HOLDOUT IoU'),(axs[0,1],'HOLDOUT_Inner_px_MAE','HOLDOUT Inner px'),(axs[0,2],'HOLDOUT_Outer_px_MAE','HOLDOUT Outer px'),(axs[1,1],'correction_from_RoMa_rotation_deg','rotation change from fullRoMa deg')]:ax.bar(xx,[mi[n][key]for n in names]);ax.set_xticks(xx,names,rotation=35,ha='right');ax.set_title(label)
 ss={a['method']:a for a in load(R/'metrics/SYMMETRIC_SIFT_EVALUATION.json')if a['role']=='HOLDOUT'};ax=axs[1,0];ax.bar(xx-.18,[ss[n]['forward']['error_px']['MAE']for n in names],.36,label='004 →005');ax.bar(xx+.18,[ss[n]['reverse']['error_px']['MAE']for n in names],.36,label='005 →004');ax.set_xticks(xx,names,rotation=35,ha='right');ax.set_title('Independent fixed-anchor SIFT HOLDOUT px');ax.legend(fontsize=6)
 ax=axs[1,2]
 for n in ['B1','B2','B3']:
  h=load(R/'optimization'/n/'HISTORY.json');ax.plot([a['iteration']for a in h],[a['loss']for a in h],label=n+' total');acc=[a for a in h if a['accepted']];ax.scatter([a['iteration']for a in acc],[a['loss']for a in acc],s=3)
 ax.set(xlabel='candidate iteration',ylabel='actual FIT objective');ax.legend(fontsize=6);fig.suptitle('Fig3 | Frozen historical B0 references and actual B1–B3 optimization\nB2 vsB1 releases shared X only; B3 adds I/O deadzone only. Different targets are not compared as identical objective values.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig3_B0_B3_Pose_And_Residuals.png')
 vv=[v for v in load(R/'config/VIEWS.json')if v['video']=='005'];fit=[v for v in vv if v['role']=='FIT'];selected=[fit[0],fit[len(fit)//2],fit[-1]]+[v for v in vv if v['role']=='HOLDOUT'];methods=['B0_RoMa','B0_020_R3','B0_020_MASK','B2','B3'];fig,axs=plt.subplots(len(selected),6,figsize=(22,3*len(selected)));per={(x['method'],x['view']):x for x in load(R/'metrics/ALL005_FRAME_METRICS.json')}
 for i,v in enumerate(selected):
  a=np.load(v['cache']);axs[i,0].imshow(a['RGB']);edge(axs[i,0],a['labels']==1,'lime');edge(axs[i,0],a['labels']==2,'cyan');axs[i,0].axis('off');axs[i,0].set_title(v['id']+' '+v['role']+'\noriginal RGB/Mask')
  for j,m in enumerate(methods,1):
   d=np.load(R/'evaluation'/m/(v['id']+'.npz'));ax=axs[i,j];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,d['pred'],'#dc73d9');edge(ax,np.isfinite(d['Ring_z_mm']),'black');x=per[m,v['id']];ax.set_title(m+' | IoU %.3f / contour %.2fpx'%(x['IoU'],x['contour_px']['MAE']));ax.axis('off')
 fig.suptitle('Fig4 | Same actual RGB/camera/pixel coordinates, frozen018 body (pink) and actual CAD (black)\nAll three protected005 HOLDOUT views shown. Body is evaluation-only for all021 routes.');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Fig4_Crossvideo_Actual_Reprojection.png',120)
 # G01 dedicated before020/after020/after021 same-view world geometry comparison.
 poses=[('before020/fullRoMa','B0_RoMa'),('after020/R3','B0_020_R3'),('after021/B3','B3')];datasets=[];B=[]
 for label,n in poses:
  conf,s=group_data('G01',load(R/'results'/(n+'.json'))['T']);datasets.append((label,conf,s));B.extend(a['V'][np.unique(a['F'])]for a in s)
 rv=dict(np.load(datasets[0][1]['ring']['path']));b=np.load(datasets[0][1]['bodies']['B2']['path']);bounds=np.r_[*B,rv['V'],b['V']];view=free_camera(bounds,20,-80);fig,axs=plt.subplots(1,3,figsize=(16,6))
 for ax,(label,conf,s)in zip(axs,datasets):
  col=colors(len(s));layers=[layer(a['V'],a['F'],c,a['id'])for a,c in zip(s,col)];layers+=[body_layer(b,'B2'),layer(rv['V'],rv['F'],'black','Ring')];panel(ax,composite(layers),view,bounds,label+'\nsame sources / viewpoint / mm extent')
 fig.suptitle('G01 actual crossvideo geometry before020 → after020 → after021\nAll native source surfaces remain separate; apparent overlap does not establish fusion or physical accuracy.');fig.tight_layout(rect=[0,0,1,.9]);finish(fig,'groups/G01/Before020_After020_After021.png')

def main():
 wait_freeze()
 while not(R/'runtime/BA_INDEPENDENT_EVALUATION_COMPLETE.json').exists()or not(R/'runtime/FOUR_GROUP_QUANTITATIVE_COMPLETE.json').exists()or not(R/'runtime/SOURCE_GEOMETRY_COMPLETE.json').exists():time.sleep(5)
 sift_figures();comparison_figures()
 for g in GROUPS:
  if not(R/'runtime'/(g+'_FIGURES_COMPLETE.json')).exists():group_figures(g)
 save('runtime/ALL_FIGURES_COMPLETE.json',dict(epoch=time.time(),groups=GROUPS,core_figures_N=8));print('021_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':main()
