"""Scientific figures from actual RGB, CAD, landmarks and frozen pose outputs."""
from common import *
from ring020 import CADCurves,canonical,tensor,torch,ellipse_points,evidence
from visual_base import actual_mesh_image,edge,finish,plt,matplotlib
from scipy.spatial.transform import Rotation
P19=REPO/'experiments/TASK-E4-RING-POLYP-REGISTRATION-019'
VIEWS=load(R/'config/VIEWS.json');VV={v['id']:v for v in VIEWS}
CUR=CADCurves();RING=dict(np.load(R/'inputs/G01/RING.npz'))
COL={'inner':'#26de68','mid':'#36b4ff','outer':'#ffb323'}
F4={a['view_id']:a for a in load(REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018/metrics/FRAME_BINDING_AUDIT.json')};F5={a['view']:a for a in load(P19/'metrics/VIDEO005_FRAME_BINDING.json')['rows']}
SOURCE_COLORS={x['id']:x['color']for x in load(P19/'derived/HERO_SCENE_SOURCE_INDEX.json')['sources']}
def actual_frame(v):
 a=F4[v['id']]if v['video']=='004'else F5[v['id']];q=a.get('exact_content_matches',[])+a.get('JPEG_chain_matches',[])if v['video']=='004'else a['exact_raw_matches'];return q[0].get('raw_index_zero_based',q[0].get('raw_index'))if q else v.get('raw_frame',0)
def P(X,C,K):
 q=(X-C[:3,3])@C[:3,:3]@K.T;return q[...,:2]/q[...,2:]
def cad_curves(H,v):
 C=canonical(tensor(H@v['T'],torch.float64)).cpu().numpy();K=np.asarray(v['K']);ss,aux=CUR.segments(C,K,True);out={k:P(CUR.V[e],C,K)for k,e in ss.items()};out['mid']=P(CUR.mid,C,K);return out
def curve_overlay(ax,v,H,zoom=False,show_fit=False):
 d=np.load(v['cache']);ax.imshow(d['RGB']);e=evidence(v);pred=cad_curves(H,v)
 for k in ['inner','outer']:
  c=COL[k];ax.scatter(*e[k].T,c=c,s=3,label='observed '+k);q=pred[k];j=load(R/'ring'/(v['id']+'.json'))
  from ring020 import ellipse_phase
  bins=np.unique(np.floor(ellipse_phase(j[k],e[k])/(2*np.pi)*72).astype(int));qb=np.floor(ellipse_phase(j[k],q.mean(1))/(2*np.pi)*72).astype(int)
  for z,supported in zip(q,np.isin(qb,bins)):ax.plot(z[:,0],z[:,1],c=c if supported else'#999999',lw=.8,ls='-'if supported else':')
 mid=e['mid'];cl=e['mid_support_class'];ax.scatter(*mid[cl==2].T,c=COL['mid'],s=1.4);ax.scatter(*mid[cl==1].T,c='#b4e1ff',s=1.2);ax.scatter(*mid[cl==0].T,c='#999999',s=.6);ax.plot(*pred['mid'].T,c=COL['mid'],lw=.7,ls='--')
 if show_fit:
  j=load(R/'ring'/(v['id']+'.json'))
  for k in ['inner','outer']:q=ellipse_points(j[k],np.arange(720)*2*np.pi/720);ax.plot(*q.T,c='#bbbbbb',ls=':',lw=.7)
 if zoom:
  yy,xx=np.nonzero(d['labels']==2);ax.set_xlim(xx.min()-12,xx.max()+12);ax.set_ylim(yy.max()+12,yy.min()-12)
 else:ax.set_xlim(0,639);ax.set_ylim(359,0)
 ax.axis('off')

def fig1():
 ids=['G01_v004_raw00152','G01_005_raw00057','G01_005_raw00745'];H=np.asarray(load(R/'results/R0.json')['T']);fig,axs=plt.subplots(3,2,figsize=(12,10))
 for i,cid in enumerate(ids):
  v=VV[cid];a=np.load(v['cache']);axs[i,0].imshow(a['RGB']);edge(axs[i,0],a['labels']==1,'lime');edge(axs[i,0],a['labels']==2,'cyan');axs[i,0].axis('off');axs[i,0].set_title(cid+' | real RGB, original Polyp/Ring Masks');curve_overlay(axs[i,1],v,H if v['video']=='005'else np.eye(4),True,True);e=evidence(v);axs[i,1].set_title('DXY observed dots vs actual CAD edges (solid)\nI=%d O=%d; Mid dual=%d single=%d unknown=%d'%(len(e['inner']),len(e['outer']),(e['mid_support_class']==2).sum(),(e['mid_support_class']==1).sum(),(e['mid_support_class']==0).sum()),fontsize=8)
 fig.suptitle('Fig1 | Real visible Inner green / Outer orange; auxiliary Mid blue\nActual CAD tube occluding edges, not three planar circles. Gray dotted full ellipse = fitted/inferred, NOT observed.\nMid blue=dual-side support; light blue=single-side inference; gray=no support (zero loss weight).');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Fig1_Ring_Observed_CAD_Curves.png')

def fig2():
 tags=['R0','R3_MASK_ONLY','R3_INNER_OUTER','R3'];ids=['G01_005_raw00057','G01_005_raw00745','G01_v005_raw00509'];fig,axs=plt.subplots(3,4,figsize=(14,9));met={(x['method'],x['view']):x for x in load(R/'metrics/ALL005_FRAME_METRICS.json')}
 for i,cid in enumerate(ids):
  for j,tag in enumerate(tags):
   H=np.asarray(load(R/'results'/(tag+'.json'))['T']);curve_overlay(axs[i,j],VV[cid],H,True);m=met[tag,cid];axs[i,j].set_title(tag+' | '+VV[cid]['role']+'\nI %.2f / Mid %.2f / O %.2f px'%(m['Inner_px']['MAE'],m['Mid_px']['MAE'],m['Outer_px']['MAE']),fontsize=8)
 fig.suptitle('Fig2 | Same RGB / same Ring crop / same cameras: Ring channel ablation\nOnly observed Inner/Outer dots supervise; missing arcs are not extrapolated observations. Mid is correlated auxiliary evidence.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig2_Ring_Channel_Ablation.png')

def fig3():
 H=np.asarray(load(R/'results/R3.json')['T']);A=np.load(R/'landmarks/CROSS_004.npz')['X'];B=np.load(R/'landmarks/INDEPENDENT_005.npz')['X'];B=B@H[:3,:3].T+H[:3,3];pairs=load(R/'features/CROSS_NAMED_3D_TRACK_PAIRS.json')['matches'];fig=plt.figure(figsize=(15,10));gs=fig.add_gridspec(2,2);ax=fig.add_subplot(gs[0,0],projection='3d');ax.scatter(*A.T,s=8,c='#1b7aba',label='004 independent153');ax.scatter(*B.T,s=4,c='#df8d31',alpha=.45,label='005 independent980 (mapped by R3)');ax.plot_trisurf(*RING['V'].T,triangles=RING['F'],color='black',linewidth=0)
 for q in pairs:
  a=np.asarray(q['X004']);b=np.asarray(q['X005'])@H[:3,:3].T+H[:3,3];ax.plot(*np.stack([a,b]).T,c='green',lw=.7)
 ax.legend(fontsize=7);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm');ax.set_title('18 actual named track pairs; no nearest-point identity\nTriangulated3D is uncertain, NOT GT',fontsize=9)
 # Forward and reverse use actual UVs and predicted reprojections, not schematic arrows.
 for i,(name,reverse)in enumerate([('CROSS',False),('REVERSE',True)]):
  rec=max([x for x in load(R/'features'/(name+'_PNP.json'))if x['success']],key=lambda x:x['inliers']);v=VV[rec['target']];C=np.asarray(v['T']);X=np.asarray(rec['landmark_X']);
  if reverse:X=X@H[:3,:3].T+H[:3,3]
  else:C=H@C
  uv=P(X,C,np.asarray(v['K']));obs=np.asarray(rec['uv']);ax=fig.add_subplot(gs[i,1]);ax.imshow(np.load(v['cache'])['RGB']);ax.scatter(*obs.T,c='lime',s=10,label='actual UV');ax.scatter(*uv.T,c='red',s=12,marker='x',label='R3 reprojected');idx=np.linspace(0,len(obs)-1,min(24,len(obs))).astype(int)
  for k in idx:ax.annotate('',xy=uv[k],xytext=obs[k],arrowprops=dict(arrowstyle='->',color='yellow',lw=.7))
  ax.axis('off');ax.legend(fontsize=7);ax.set_title(('005 landmark ->004'if reverse else'004 landmark ->005')+' | '+rec['target']+'\nactual independently verified correspondences',fontsize=9)
 ax=fig.add_subplot(gs[1,0]);pair=max(load(R/'features/CROSS_EPI.json'),key=lambda x:len(x['p']));a,b=VV[pair['a']],VV[pair['b']];m=np.load(R/'matches'/(a['id']+'__'+b['id']+'.npz'));ax.imshow(np.concatenate([np.load(a['cache'])['RGB'],np.load(b['cache'])['RGB']],1));
 for flag,col in [(True,'lime'),(False,'red')]:
  ix=np.flatnonzero(m['RGB_RANSAC']==flag)
  for k in ix[np.linspace(0,len(ix)-1,min(20,len(ix))).astype(int)]if len(ix)else[]:
   p=m['p'][k];q=m['q'][k]+[640,0];ax.plot([p[0],q[0]],[p[1],q[1]],c=col,lw=.6)
 ax.axis('off');ax.set_title('Real SIFT matches: RGB-RANSAC green / rejected red\nDisplay subsample; all original feature IDs are retained',fontsize=9)
 fig.suptitle('Fig3 | Two independent metric landmark sets + symmetric image constraints\nLandmarks use only each video own FIT RGB/cameras. Ring black. No body/HERO used in R0-R3.');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig3_Independent_Symmetric_SIFT.png')

def fig4():
 fit=sorted([v for v in VIEWS if v['video']=='005'and v['role']=='FIT'],key=lambda x:x.get('raw_frame')or 0);ids=[fit[0]['id'],fit[len(fit)//2]['id'],fit[-1]['id']]+[v['id']for v in VIEWS if v['video']=='005'and v['role']=='HOLDOUT'];met={(x['method'],x['view']):x for x in load(R/'metrics/ALL005_FRAME_METRICS.json')}
 def page(ids,name):
  fig,axs=plt.subplots(len(ids),6,figsize=(18,2.7*len(ids)),squeeze=False)
  for i,cid in enumerate(ids):
   a=np.load(VV[cid]['cache'])
   for j,tag in enumerate(['RGB','R0','R1','R2','R3','R4']):
    ax=axs[i,j];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan');t=tag+' | '+cid+' '+VV[cid]['role']
    if tag!='RGB':
     p=np.load(R/'evaluation'/tag/(cid+'.npz'));edge(ax,p['pred'],'#f64c8b');edge(ax,np.isfinite(p['Ring_z_mm']),'black');t+='\nIoU %.3f / contour %.2f px'%(met[tag,cid]['IoU'],met[tag,cid]['contour_px']['MAE'])
    ax.axis('off');ax.set_title(t,fontsize=7)
  fig.suptitle('Real005 multi-view comparison | green actualPolyp / cyan actualRing / pink fixed018body / blackCAD\nR0-R3 never use body in registration. R4 alone adds body. Every protected005 HOLDOUT appears in the core figure.');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,name)
 page(ids,'Fig4_R0_R4_Actual_Reprojection.png');allids=[v['id']for v in VIEWS if v['video']=='005']
 for i in range(0,len(allids),7):page(allids[i:i+7],'details/All005_%02d.png'%(i//7+1))

def scene_parts(H):
 body=np.load(R/'inputs/G01/BODY018.npz');parts=[(body['V'],body['F_solid'],'#8158a5')]
 for s in load(R/'config/HERO_EVALUATION_SOURCES.json'):
  m=np.load(s['mesh']['path']);G=H if s['video']=='005'else np.eye(4);parts.append((m['V']@G[:3,:3].T+G[:3,3],m['F'],SOURCE_COLORS[s['id']]))
 return parts
def render_parts(ax,parts,bounds,angle):
 V=[];F=[];col=[];off=0
 for p,f,c in parts:V.append(p);F.append(f+off);col.append(np.tile(matplotlib.colors.to_rgb(c),(len(f),1)));off+=len(p)
 V=np.concatenate(V);F=np.concatenate(F);col=np.concatenate(col);im,sc=actual_mesh_image(V,F,RING['V'],RING['F'],bounds,*angle,'#8158a5',col);ax.imshow(im);ax.plot([18,18+2*sc],[375,375],c='black');ax.text(18,363,'2 mm at viewer center',fontsize=7);ax.axis('off')
def fig5():
 H=np.asarray(load(R/'results/R3.json')['T']);tags=['R0','R3','R4'];parts=[scene_parts(np.asarray(load(R/'results'/(tag+'.json'))['T']))for tag in tags];bounds=np.concatenate([V[np.unique(F)]for group in parts for V,F,c in group]);fig=plt.figure(figsize=(15,10));gs=fig.add_gridspec(2,3)
 for j,tag in enumerate(tags):ax=fig.add_subplot(gs[0,j]);render_parts(ax,parts[j],bounds,(22,-65));ax.set_title(tag+' | same mm bounds / actual full TRUSTED faces',fontsize=9)
 A=np.load(R/'landmarks/CROSS_004.npz')['X'];B=np.load(R/'landmarks/INDEPENDENT_005.npz')['X'];B=B@H[:3,:3].T+H[:3,3]
 for j,ang in enumerate([(25,-65),(10,20),(75,-65)]):
  ax=fig.add_subplot(gs[1,j],projection='3d');b=np.load(R/'inputs/G01/BODY018.npz');ax.plot_trisurf(*b['V'].T,triangles=b['F_solid'],color='#8158a5',linewidth=0);ax.plot_trisurf(*RING['V'].T,triangles=RING['F'],color='black',linewidth=0);ax.scatter(*A.T,s=3,c='#2678af',alpha=.3);ax.scatter(*B.T,s=2,c='#e59236',alpha=.2)
  for video,c in [('004','#2678af'),('005','#e59236')]:
   vv=sorted([v for v in VIEWS if v['video']==video],key=actual_frame);C=np.array([(H@v['T']if video=='005'else np.asarray(v['T']))[:3,3]for v in vv]);ax.plot(*C.T,'o-',ms=2,c=c,label=video+' cameras')
  ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm');ax.view_init(*ang);ax.legend(fontsize=7);ax.set_title('R3 shared004 world + both independent landmark sets',fontsize=8)
 fig.suptitle('Fig5 | Diagnostic shared coordinate scene, NOT surface fusion\nBlack=ONE fixedCAD, purple=018body, blue=13 native004 TRUSTED sources, orange=8 native005 TRUSTED sources\nLower panels include complete landmark extents; all original meshes and face IDs are unchanged.');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Fig5_Shared_World_NOT_FUSION.png')

def fig6():
 rows=load(R/'metrics/ENDPOINT_GRADIENT_RELATIONSHIPS.json');lookup={x['arm']:x for x in rows};fig,axs=plt.subplots(2,3,figsize=(15,9));keys=['M','I','C','O','F'];ax=axs[0,0]
 for j,k in enumerate(['R0','R3','R4']):ax.bar(np.arange(len(keys))+(j-1)*.25,[lookup[k]['gradient_norms'][x]for x in keys],width=.25,label=k)
 ax.set_xticks(range(len(keys)),keys);ax.set_yscale('log');ax.set_ylabel('norm in shared [.6mm,5deg] left tangent');ax.legend();ax.set_title('Component gradients (unweighted)')
 ax=axs[0,1];g=lookup['R3']['component_gradient_normalized_pose'];ks=['M','I','C','O','F_forward','F_reverse'];G=np.array([g[k]for k in ks]);cos=G@G.T/np.maximum(np.linalg.norm(G,axis=1)[:,None]*np.linalg.norm(G,axis=1)[None],1e-20);im=ax.imshow(cos,vmin=-1,vmax=1,cmap='coolwarm');ax.set_xticks(range(len(ks)),ks,rotation=40,ha='right');ax.set_yticks(range(len(ks)),ks);fig.colorbar(im,ax=ax);ax.set_title('R3 endpoint gradient cosine')
 for tag,c in [('R1','#aaaaaa'),('R2','#e69839'),('R3','#287ebc'),('R4','#9869b9')]:
  x=load(R/'optimization'/tag/'HISTORY.json');axs[0,2].plot([a['iteration']for a in x],[a['loss']for a in x],c=c,label=tag);T0=np.asarray(load(R/'results/R0.json')['T']);delta=[np.asarray(a['T'])@np.linalg.inv(T0)for a in x];axs[1,0].plot([a['iteration']for a in x],[np.linalg.norm(a[:3,3])for a in delta],c=c,label=tag);axs[1,1].plot([a['iteration']for a in x],[np.degrees(Rotation.from_matrix(a[:3,:3]).magnitude())for a in delta],c=c,label=tag)
 axs[0,2].set_title('Actual FIT objective trajectories');axs[0,2].legend();axs[1,0].set_title('Actual correction from full RoMa (mm)');axs[1,1].set_title('Actual correction from full RoMa (deg)')
 for ax in [axs[0,2],axs[1,0],axs[1,1]]:ax.set_xlabel('candidate iteration')
 ax=axs[1,2];reg=load(R/'metrics/REGISTRATION_COMPARISON.json');tags=['R0','R1','R2','R3','R4'];rr={a['method']:a for a in reg}
 for j,k in enumerate(['Inner_px','Mid_px','Outer_px']):ax.bar(np.arange(5)+(j-1)*.25,[rr[t]['HOLDOUT_'+k+'_MAE']for t in tags],width=.25,label=k)
 ax.set_xticks(range(5),tags);ax.set_ylabel('protected005 mean native-pixel residual');ax.legend(fontsize=7);ax.set_title('Independent curve error; Mid is correlated')
 fig.suptitle('Fig6 | Ring/SIFT component gradients, accepted trajectories and independent boundary errors\nGradient is not Adam displacement. Endpoint left-tangent audit uses the same physical parameter scale for every method.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig6_Gradients_and_SE3_Changes.png')

def export():
 H=np.asarray(load(R/'results/R3.json')['T']);save('derived/T004_from005_R3.json',dict(T004_from005=H,T005_from004=np.linalg.inv(H),R=H[:3,:3],t_mm=H[:3,3],scale=1.,convention='X004=H X005; c2w004=H c2w005; column OpenCV; mm',status='RESEARCH_CANDIDATE_AWAITING_REVIEW',no_Body_in_R3=True));save('derived/VIDEO005_CAMERAS_R3.json',[dict(id=v['id'],role=v['role'],K=v['K'],c2w_native=v['T'],c2w_in004=H@v['T'],original_qualification=v.get('qualification'))for v in VIEWS if v['video']=='005'])
 sc=trimesh.Scene();parts=scene_parts(H)+[(RING['V'],RING['F'],'#060606')];source=[];names=['fixed018body']+[s['id']for s in load(R/'config/HERO_EVALUATION_SOURCES.json')]+['ONE_R10_CAD']
 for i,(V,F,c)in enumerate(parts):
  u,remap=np.unique(F,return_inverse=True);m=trimesh.Trimesh(V[u],remap.reshape(-1,3),process=False);m.visual.face_colors=np.r_[np.array(matplotlib.colors.to_rgb(c))*255,255].astype(np.uint8);m.apply_scale(.001);sc.add_geometry(m,geom_name=names[i]);source.append(dict(component=i,id=names[i],color=c,triangles=len(F),preview_vertices=len(u),original_triangles_unchanged=True))
 for video,col in [('004','#2678af'),('005','#e59236')]:
  lm=np.load(R/'landmarks'/('CROSS_004.npz'if video=='004'else'INDEPENDENT_005.npz'))['X'];lm=lm@H[:3,:3].T+H[:3,3]if video=='005'else lm;pc=trimesh.points.PointCloud(lm*.001,colors=np.tile(np.r_[np.array(matplotlib.colors.to_rgb(col))*255,255].astype(np.uint8),(len(lm),1)));sc.add_geometry(pc,geom_name='independent_SIFT_landmarks_'+video)
  vv=sorted([v for v in VIEWS if v['video']==video],key=actual_frame);C=np.array([(H@v['T']if video=='005'else np.asarray(v['T']))[:3,3]for v in vv])
  for k,p in enumerate(C):
   sphere=trimesh.creation.icosphere(subdivisions=1,radius=.13);sphere.apply_translation(p);sphere.visual.face_colors=np.r_[np.array(matplotlib.colors.to_rgb(col))*255,255].astype(np.uint8);sphere.apply_scale(.001);sc.add_geometry(sphere,geom_name='camera_'+vv[k]['id'])
  for k,(a,b)in enumerate(zip(C[:-1],C[1:])):
   if np.linalg.norm(a-b)<1e-9:continue
   line=trimesh.creation.cylinder(radius=.035,segment=np.array([a,b]),sections=6);line.visual.face_colors=np.r_[np.array(matplotlib.colors.to_rgb(col))*255,255].astype(np.uint8);line.apply_scale(.001);sc.add_geometry(line,geom_name='trajectory_'+video+'_'+str(k))
 path=R/'derived/G01_R3_DIAGNOSTIC_NOT_FUSION.glb';sc.export(path);save('derived/SCENE_INDEX.json',dict(scene=asset(path),parts=source,unit='GLB meter only(.001); all computation mm; scale estimated=1',fused=False,preview_removed_only_unreferenced_vertex_entries=True))

def main():
 while not(R/'provenance/FINAL_INTEGRITY.json').exists():time.sleep(5)
 for p in load(R/'provenance/ALL_POSES_FROZEN_BEFORE_EVALUATION.json')['files']:assert sha(p['path'])==p['sha256']
 for fn in [fig1,fig2,fig3,fig4,fig5,fig6]:fn();print('FIG020_DONE',fn.__name__,flush=True)
 export();save('runtime/FIGURES_COMPLETE.json',dict(epoch=time.time(),figures=[asset(p)for p in(R/'figures').glob('Fig*.png')],GT=False));print('FIGURES020_COMPLETE',flush=True)
if __name__=='__main__':main()
