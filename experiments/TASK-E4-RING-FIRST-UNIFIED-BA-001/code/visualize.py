"""True native triangles under explicitly indexed rigid/counterfactual transforms."""
from hero_evaluate import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import to_rgb
COL={'B0':'#737373','B1':'#3a9c70','B2':'#de8f31','B3':'#8063bb'};STATE=np.array([[.18,.72,.36],[.9,.15,.15],[.2,.45,.88],[.65,.3,.7],[.65,.65,.65]])
def finish(fig,name,dpi=130):
 fig.savefig(N/'figures'/name,dpi=dpi,bbox_inches='tight');plt.close(fig)
def edge(ax,mask,color):
 q=contour(mask)
 if len(q):ax.scatter(q[:,0],q[:,1],s=.3,c=color)
def palette(i,n):return np.array(plt.get_cmap('tab20')(i%20)[:3])
def bounds(data,ring):return np.r_[ring['V'],*[s['V'][np.unique(s['F'])]for s in data if'V'in s]]
def viewer(B,el=25,az=-65):
 center=(B.min(0)+B.max(0))/2;radius=max(np.linalg.norm(B-center,axis=1).max(),1);el,az=np.radians([el,az]);pos=center+radius*3.4*np.array([np.cos(el)*np.cos(az),np.cos(el)*np.sin(az),np.sin(el)]);f=(center-pos)/np.linalg.norm(center-pos);right=np.cross(f,[0,0,1]);right/=np.linalg.norm(right);down=np.cross(f,right);C=np.eye(4);C[:3,:3]=np.array([right,down,f]).T;C[:3,3]=pos;K=np.array([[490.,0,199.5],[0,490.,199.5],[0,0,1.]]);return C,K,490/np.linalg.norm(pos-center)
def render(parts,ring,B,angle=(25,-65),camera=None):
 if camera is None:C,K,scale=viewer(B,*angle);h=w=400
 else:C,K=camera;h,w=360,640;scale=K[0,0]/np.linalg.norm(C[:3,3]-(B.min(0)+B.max(0))/2)
 r=o3d.t.geometry.RaycastingScene(nthreads=1);items=parts+[(ring['V'],ring['F'],np.array([.025]*3))]
 for V,F,c in items:r.add_triangles(o3d.core.Tensor(np.asarray(V,np.float32)),o3d.core.Tensor(np.asarray(F,np.uint32)))
 y,x=np.mgrid[:h,:w];dd=np.c_[x.ravel(),y.ravel(),np.ones(h*w)]@np.linalg.inv(K).T;hit=r.cast_rays(o3d.core.Tensor(np.c_[np.broadcast_to(C[:3,3],dd.shape),dd@C[:3,:3].T].astype(np.float32)));gid=hit['geometry_ids'].numpy();fid=hit['primitive_ids'].numpy();out=np.full((h*w,3),.965);light=-C[:3,2]
 for j,(V,F,c)in enumerate(items):
  sel=gid==j;normal=trimesh.triangles.normals(V[F])[0];shade=.45+.55*abs(normal[fid[sel]]@light);c=np.asarray(c);out[sel]=(c if c.ndim==1 else c[fid[sel]])*shade[:,None]
 return np.clip(out.reshape(h,w,3),0,1),scale

def show(ax,im,scale,title):
 ax.imshow(im);ax.axis('off');ax.plot([15,15+2*scale],[im.shape[0]-20]*2,c='black',lw=2);ax.text(15,im.shape[0]-26,'2 mm at view center',fontsize=6);ax.set_title(title,fontsize=8)
def sourceparts(data,video_colors=False):
 return[(s['V'],s['F'],np.array([.22,.5,.85])if s['video']=='004'else np.array([.95,.5,.14]))if video_colors else(s['V'],s['F'],palette(i,len(data)))for i,s in enumerate(data)if'V'in s]

def figures():
 checkfreeze('provenance/ALL_FINAL_CAMERA_CANDIDATES_FROZEN_BEFORE_HERO.json');res=getresults();vv=load(N/'config/VIEWS.json');metrics=load(N/'metrics/PER_VIEW_CAMERA_GEOMETRY.json');mindex={(r['group'],r['method'],r['id']):r for r in metrics};db={};rings={};B={}
 for g in GROUPS:
  for method in ['B0','B1','B2','B3']:
   if res[g,method].get('poses'):conf,data=sources(g,res,method);db[g,method]=data
  rings[g]=dict(np.load(conf['ring']['path']));B[g]=bounds(db[g,'B0'],rings[g])
 # Figure1 uses actualG01cameras/landmarks, never illustrative/randompoints.
 fig=plt.figure(figsize=(14,6));ax=fig.add_subplot(121,projection='3d');g='G01';rv=rings[g];ax.add_collection3d(Poly3DCollection(rv['V'][rv['F']],facecolor='black',linewidth=0));lim=[]
 for method in ['B0','B3']:
  r=res[g,method];C=np.array(list(r['poses'].values()));ax.scatter(*C[:,:3,3].T,s=8,c=COL[method],label=method+'actualcamera');ax.quiver(*C[:,:3,3].T,*C[:,:3,2].T,length=2,color=COL[method]);lim.append(C[:,:3,3])
 X=np.array(list(res[g,'B3']['X'].values()));ax.scatter(*X.T,s=1,c='seagreen',alpha=.3,label='actualRGBXYZ');L=np.r_[*lim,X,rv['V']];ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm');ax.set_box_aspect(np.maximum(np.ptp(L,axis=0),1));ax.legend(fontsize=7);ax.set_title('Actual shared Ring world; H004=I, scale locked')
 ax=fig.add_subplot(122);ax.axis('off');info=load(N/'metrics/G01_JOINT_INFORMATION.json');summ=load(N/'optimization/G01/B3/OUTER_0/CERES_SUMMARY.json');ax.text(.02,.98,f"REAL joint problem (G01)\n\nRF TorusR=5.6mm, tube r=0.6mm fixed\nT=H exp(local delta) RF; no Sim(3)\n\n{info['active_camera_chart_dimension']} camera-chart variables + {info['active_XYZ_dimension']} XYZ variables\n{info['data_residual_dimension']} data residual components\nLandmark-marginalized rank {info['marginal_camera_information_rank']}/{info['marginal_camera_information_dimension']}\n\nCeres {summ['linear_solver_type_used']}\nShared H005 + commonXYZ + all qualified FIT cameras\nHOLDOUT: no independent local camera fitting\n\nHERO only after all candidate poses frozen",va='top',fontsize=11);fig.suptitle('Figure1 | Original physical Torus + actual shared RGB landmarks + Ceres joint BA');fig.tight_layout();finish(fig,'Figure1_Actual_Unified_BA.png')
 # Figure2 allgroups allroute slots, NAneverfilledwithbaseline.
 fig,axs=plt.subplots(4,5,figsize=(20,11))
 for i,g in enumerate(GROUPS):
  groupfit=[v for v in vv if v['group']==g and v['role']=='FIT'];anchors={video:next(v['id']for v in groupfit if v['video']==video)for video in {v['video']for v in groupfit}};v=next(v for v in groupfit if v['id']!=anchors[v['video']]);d=np.load(v['cache']);ob,_=qualified(v)
  for j,method in enumerate(METHODS):
   ax=axs[i,j];C=getpose(res,g,method,v['id']);ax.imshow(d['RGB']);edge(ax,d['labels']==1,'lime');edge(ax,d['labels']==2,'cyan')
   if C is not None:
    cr=curves(C,np.array(v['K']));
    near=cv2.dilate((d['labels']==1).astype(np.uint8),np.ones((5,5),np.uint8))>0
    for key,color in [('inner','yellow'),('outer','magenta')]:
     p=cr[key].copy();px=np.clip(np.floor(p+.5).astype(int),[0,0],[639,359]);p[near[px[:,1],px[:,0]]]=np.nan;ax.plot(*p.T,c=color,lw=.7);ax.scatter(*ob[key].T,s=1,c=color)
    cadq=contour(np.isfinite(cast(ray_scene(v['ring_path'])[0],C,np.array(v['K']))));px=np.clip(np.floor(cadq+.5).astype(int),[0,0],[639,359]);cadq=cadq[~near[px[:,1],px[:,0]]];ax.scatter(*cadq.T,s=.15,c='black')
    r=mindex.get((g,method,v['id']),{});ax.set_title(g+' '+method+' | RingIoU '+str(round(r.get('Ring_IoU',0),3)),fontsize=8)
   else:ax.text(.03,.04,'NOT RUN / NOT APPLICABLE\nNO POSE FALLBACK',transform=ax.transAxes,color='red',fontsize=7);ax.set_title(g+' '+method,fontsize=8)
   ax.axis('off')
 fig.suptitle('Figure2 | First non-anchor FIT per group (canonical order, no output ranking), actual RGB / Masks\nAnalytic Torus and actual I/O; Polyp-adjacent UNKNOWN not drawn. Black: independent CAD boundary.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Figure2_Four_Group_Ring_Projection.png')
 # Figure3 fourseparateworlds, actualcamera trajectory bounds.
 fig=plt.figure(figsize=(13,11))
 for i,g in enumerate(GROUPS):
  ax=fig.add_subplot(2,2,i+1,projection='3d');rv=rings[g];ax.add_collection3d(Poly3DCollection(rv['V'][rv['F']],facecolor='black',linewidth=0));L=[rv['V']]
  for method in ['B0','B3']:
   cams=np.array(list(res[g,method]['poses'].values()));ax.scatter(*cams[:,:3,3].T,c=COL[method],s=7,label=method);ax.quiver(*cams[:,:3,3].T,*cams[:,:3,2].T,length=2,color=COL[method]);L.append(cams[:,:3,3])
  X=np.array(list(res[g,'B3']['X'].values()));ax.scatter(*X.T,s=1,alpha=.3,c='seagreen');L.append(X);L=np.r_[*L];ax.set_box_aspect(np.maximum(np.ptp(L,axis=0),1));ax.set(title=g+' independent metric world',xlabel='X mm',ylabel='Y mm',zlabel='Z mm');ax.legend(fontsize=7)
 fig.suptitle('Figure3 | All98 actual cameras / directions and shared RGB landmarks; black fixed Ring CAD');fig.tight_layout(rect=[0,0,1,.96]);finish(fig,'Figure3_Four_Group_Actual_Cameras.png')
 # Figure4 G01core required true native meshes before/shared/joint, identicalviewsandbounds.
 fig,axs=plt.subplots(2,3,figsize=(14,9))
 for j,method in enumerate(['B0','B2','B3']):
  for i,angle in enumerate([(25,-65),(0,-90)]):
   im,scale=render(sourceparts(db['G01',method],True),rings['G01'],B['G01'],angle);show(axs[i,j],im,scale,method+' | 004 blue / 005 orange\n'+('shared rigid video transform'if method=='B2'else'counterfactual olddepth/newcamera'if method=='B3'else'frozen native RF + predeterminedRoMa'))
 fig.suptitle('Figure4 | G01 actual TRUSTED HERO surfaces; same millimeter frame, cameras and display bounds\nNo ICP, no repair, no fusion, no HERO reinference. Conflicting source layers retained.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Figure4_G01_Real_HERO_Before_Shared_Joint.png')
 # Figure5 realoverlap samples: same first-visible query and native pixel IDs all methods.
 fig,axs=plt.subplots(2,3,figsize=(14,9));g='G01';base=np.load(N/'local_results/HERO_DIAGNOSTICS'/f'{g}_B0_REAL_PAIR.npz');known=base['known'];ids=np.flatnonzero(known&np.isfinite(base['normal_angle_deg'])&(abs(base['dz_mm'])<.75));ids=ids if len(ids)else np.flatnonzero(known);idx=ids[len(ids)//2];center=base['source_X'][idx];localB=np.array([center+[-1.5,-1.5,-1.5],center+[1.5,1.5,1.5]])
 for j,method in enumerate(['B0','B2','B3']):
  a=np.load(N/'local_results/HERO_DIAGNOSTICS'/f'{g}_{method}_REAL_PAIR.npz');parts=[]
  for s in db[g,method]:
   if s['id']not in [str(a['source_id']),str(a['target_id'])]:continue
   F=s['F'];keep=np.linalg.norm(s['V'][F].mean(1)-center,axis=1)<=3.;parts.append((s['V'],F[keep],np.array([.22,.5,.85])if s['id']==str(a['source_id'])else np.array([.95,.5,.14])))
  im,scale=render(parts,rings[g],localB,(15,-60));show(axs[0,j],im,scale,method+' | fixed real overlap neighborhood')
  co=a['known']&known;near=np.linalg.norm(base['source_X']-center,axis=1)<=1.5;use=co&near
  for s in db[g,method]:
   if s['id']not in [str(a['source_id']),str(a['target_id'])]:continue
   seg=trimesh.intersections.mesh_plane(trimesh.Trimesh(s['V'],s['F'],process=False),[0,1,0],center);seg=seg[np.linalg.norm(seg.mean(1)-center,axis=1)<=2.5]
   for line in seg:axs[1,j].plot(line[:,0],line[:,2],c='steelblue'if s['id']==str(a['source_id'])else'darkorange',lw=.8)
  na=stats(a['normal_angle_deg'][use]);axs[1,j].set(xlabel='world X mm',ylabel='world Z mm',title=method+' exact native-triangle cut Y='+str(round(center[1],3))+'mm\nfixedpixel common N='+str(int(use.sum()))+', axial MAE='+str(round(stats(a['dz_mm'][use])['MAE']or 0,3))+'mm\nsupported-normal MAE='+str(round(na['MAE']or 0,2))+'deg, N='+str(na['N']));axs[1,j].grid(alpha=.2)
 xl=[ax.get_xlim()for ax in axs[1]];yl=[ax.get_ylim()for ax in axs[1]]
 for ax in axs[1]:ax.set_xlim(min(a[0]for a in xl),max(a[1]for a in xl));ax.set_ylim(min(a[0]for a in yl),max(a[1]for a in yl));ax.set_aspect('equal',adjustable='box')
 fig.suptitle('Figure5 | Actual native triangle plane sections, common metric axes\nBlue '+str(base['source_id'])+' / orange '+str(base['target_id'])+' | pair chosen by B0 coverage; deeper may be legal occlusion.');fig.tight_layout(rect=[0,0,1,.91]);finish(fig,'Figure5_Actual_HERO_Layer_Zoom.png')
 # Figure6 originalfacescoloredbyknownnativefaceIDs, unknowngray.
 fig,axs=plt.subplots(4,2,figsize=(10,17))
 for i,g in enumerate(GROUPS):
  for j,method in enumerate(['B0','B3']):
   q=np.load(N/'local_results/HERO_DIAGNOSTICS'/(g+'_'+method+'_REAL_PAIR.npz'));s=next(s for s in db[g,method]if s['id']==str(q['source_id']));orig=s['mesh']['original_face_id'];mapping={int(k):j for j,k in enumerate(orig)};fc=np.tile(STATE[4],(len(s['F']),1));matched=0
   for fid,cls in zip(q['original_face_id'],q['class_id']):
    if int(fid)in mapping:fc[mapping[int(fid)]]=STATE[int(cls)];matched+=1
   im,scale=render([(s['V'],s['F'],fc)],rings[g],B[g]);show(axs[i,j],im,scale,g+' '+method+' | exact nativefacebinding '+str(matched)+'/'+str(len(q['class_id'])))
 fig.suptitle('Figure6 | Actual HERO face evidence: green support / red frontproxy / blue deeper-possibleocclusion\npurple CAD occlusion / gray UNKNOWN. Evidence labels are not physical truth.');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Figure6_Native_HERO_Evidence_Heatmap.png')
 # Figure7 native sources bysource, independentworlds andidenticalwithingroup frames.
 fig,axs=plt.subplots(4,3,figsize=(14,17))
 for i,g in enumerate(GROUPS):
  for j,method in enumerate(['B0','B1','B3']):im,scale=render(sourceparts(db[g,method]),rings[g],B[g]);show(axs[i,j],im,scale,g+' '+method+' | all'+str(len(db[g,method]))+' native sources')
 fig.suptitle('Figure7 | Four independent Ring worlds, all native TRUSTED HERO layers retained\nSame group view/scale/crop, no fusion or posthoc geometry repair. Individualsource IDs in GLB index.');fig.tight_layout(rect=[0,0,1,.96]);finish(fig,'Figure7_Four_Group_All_Native_HERO.png')
 # Figure8 independentmetrics and all fixed denominators.
 summ=load(N/'metrics/FOUR_GROUP_POSE_SCORECARD.json');hs=load(N/'metrics/HERO_SURFACE_ALIGNMENT_SCORECARD.json');fig,axs=plt.subplots(2,3,figsize=(15,8))
 for i,g in enumerate(GROUPS):
  ms=['B0','B1','B3'];s=[next(x for x in summ if x['group']==g and x['method']==m and x['role']=='FIT')for m in ms]
  for ax,key in [(axs[0,0],'Ring_IoU'),(axs[0,1],'descriptor_HELD_reprojection_px_MAE_macro'),(axs[0,2],'center_change_mm')]:ax.plot(ms,[r[key]for r in s],'-o',label=g+' FIT N='+str(s[0]['target_N']))
  scope='CROSS_VIDEO'if g=='G01'else'SAME_VIDEO';s=[next(x for x in hs if x['group']==g and x['method']==m and x.get('scope')==scope)for m in ms]
  for ax,key in [(axs[1,0],'depth_mm'),(axs[1,1],'support_fraction_fixed'),(axs[1,2],'front_fraction_fixed')]:ax.plot(ms,[r[key]['MAE']if key=='depth_mm'else r[key]for r in s],'-o',label=g+' '+scope+' fixedN='+str(s[0]['fixed_N']))
 for ax,title,y in zip(axs.ravel(),['Full CAD Ring IoU','Descriptor-HELD RGB reprojection','Camera center change','HERO pooled absolute axial difference','HERO support +/-0.5mm','HERO front discrepancy proxy'],['IoU','px','mm','mm','fraction fixedN','fraction fixedN']):ax.set(title=title,ylabel=y);ax.legend(fontsize=6);ax.grid(alpha=.2)
 fig.suptitle('Figure8 | Actual independent metrics, no GT; lower objective or RingIoU gain is not absolute pose accuracy');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Figure8_Frozen_Independent_Geometry_Metrics.png')
 # Six directions pergroup, fixed native bounds acrossallmethods.
 for g in GROUPS:
  fig,axs=plt.subplots(3,6,figsize=(22,11));v=[v for v in vv if v['group']==g and v['role']=='FIT'];v0=v[0];v1=max(v[1:],key=lambda a:np.linalg.norm(np.array(a['T'])[:3,3]-np.array(v0['T'])[:3,3]));dirs=[(np.array(v0['T']),np.array(v0['K'])),(np.array(v1['T']),np.array(v1['K'])),None,None,None,None];angles=[None,None,(89,-90),(0,-90),(0,90),(-89,-90)]
  for i,m in enumerate(['B0','B1','B3']):
   for j in range(6):im,scale=render(sourceparts(db[g,m]),rings[g],B[g],angles[j]if angles[j]else(25,-65),dirs[j]);show(axs[i,j],im,scale,m+' | '+['originalrealview','complementaryrealview','top','side','oppositeside','bottom'][j])
  fig.suptitle(g+' full six-view native HERO comparison | one fixed original camera/metric range percolumn');fig.tight_layout(rect=[0,0,1,.96]);finish(fig,g+'_SIX_VIEW_ATLAS.png',110)
 print('ALL8_FIGURES_AND4_SIXVIEW_ATLASES_COMPLETE',flush=True)

if __name__=='__main__':figures()
