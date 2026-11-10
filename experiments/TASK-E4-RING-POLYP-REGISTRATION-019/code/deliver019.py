"""Post-freeze exports, manifest and scientific figures. No optimization or GT access."""
from common import *
from hero_diagnosis019 import sources
from evaluate019 import methods
from visual_base import actual_mesh_image, edge, finish, plt, matplotlib
from scipy.spatial.transform import Rotation
import collections

VIEWS=load(R/'config/VIEWS.json'); VV={v['id']:v for v in VIEWS}
BODY=dict(np.load(R/'inputs/G01/BODY018.npz')); RING=dict(np.load(R/'inputs/G01/RING.npz'))
H=np.asarray(load(R/'results/CROSS_A5_FINAL.json')['T'])
SS=sources()
FB4={a['view_id']:a for a in load(REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018/metrics/FRAME_BINDING_AUDIT.json')}
FB5={a['view']:a for a in load(R/'metrics/VIDEO005_FRAME_BINDING.json')['rows']}

def frame_index(v):
 a=FB4[v['id']]if v['video']=='004'else FB5[v['id']]
 records=a.get('exact_content_matches',[])+a.get('JPEG_chain_matches',[])if v['video']=='004'else a['exact_raw_matches']
 return records[0].get('raw_index_zero_based',records[0].get('raw_index'))if records else v.get('raw_frame',0)

def face_bounds(parts):
 # Native subset files retain the full original V array for identity. Unreferenced
 # rejected vertices are not part of these displayed TRUSTED triangles.
 return np.concatenate([m['V'][np.unique(m['F'])]for m,c in parts])

def transformed_mesh(s,G):
 m=s['mesh']; return dict(V=m['V']@G[:3,:3].T+G[:3,3],F=m['F'],original_face_id=m['original_face_id'])

def combine(parts):
 vs=[];fs=[];cs=[];offset=0
 for m,c in parts:
  vs.append(m['V']);fs.append(m['F']+offset);cs.append(np.tile(matplotlib.colors.to_rgb(c),(len(m['F']),1)));offset+=len(m['V'])
 return np.concatenate(vs),np.concatenate(fs),np.concatenate(cs)

def render_panel(ax,parts,bounds,angle=(22,-65),title=''):
 V,F,C=combine(parts);im,sc=actual_mesh_image(V,F,RING['V'],RING['F'],bounds,*angle,'#7955aa',C)
 ax.imshow(im);ax.plot([18,18+2*sc],[375,375],c='black',lw=2);ax.text(18,363,'2 mm at view-center depth',fontsize=7);ax.axis('off');ax.set_title(title,fontsize=9)

def show_rgb(ax,v,title=None):
 a=np.load(v['cache']);ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan');ax.set_xlim(0,639);ax.set_ylim(359,0);ax.axis('off');ax.set_title(title or v['id'],fontsize=8)

def export():
 frozen=load(R/'provenance/POSE_PREDICTIONS_FROZEN_BEFORE_HOLDOUT.json')
 for a in frozen['results']:assert sha(a['path'])==a['sha256'],a['path']
 assert sha(frozen['body']['path'])==frozen['body']['sha256']
 out=R/'derived';out.mkdir(exist_ok=True)
 f=load(R/'results/CROSS_A5_FINAL.json');save('derived/T004_from005.json',dict(T004_from005=H,T005_from004=np.linalg.inv(H),R=H[:3,:3],t_mm=H[:3,3],unit='mm',convention='column vectors, OpenCV c2w; X004=H@X005; C004=H@C005',scale=1.,status='RESEARCH_CANDIDATE_NOT_CERTIFIED_FOR_FUSION',selection='A4 FIT joint score top3 angular-separated proposals; A5 minimum full FIT objective, before HOLDOUT',initial=f['initial'],final_fit_loss=f['final_loss'],source_final=asset(R/'results/CROSS_A5_FINAL.json')))
 derived=[dict(id=v['id'],role=v['role'],K=v['K'],c2w_original=v['T'],c2w_in004=H@v['T'],original_qualification=v.get('qualification'),scale=1.,original_camera_modified=False)for v in VIEWS if v['video']=='005'];save('derived/VIDEO005_CAMERAS_IN004.json',derived)
 scene_glb=trimesh.Scene();meshdir=out/'HERO_in004';meshdir.mkdir(exist_ok=True)
 def addmesh(name,V,F,c):
  used,idx=np.unique(F,return_inverse=True);m=trimesh.Trimesh(V[used],idx.reshape(-1,3),process=False);m.visual.face_colors=np.r_[np.array(matplotlib.colors.to_rgb(c))*255,255].astype(np.uint8);m.apply_scale(.001);scene_glb.add_geometry(m,node_name=name,geom_name=name)
 addmesh('ONE_FIXED_R10_CAD',RING['V'],RING['F'],'#080808');addmesh('FIXED_018_BODY',BODY['V'],BODY['F_solid'],'#8657a7')
 palette={'004':plt.cm.Blues,'005':plt.cm.Oranges};counts=collections.Counter(s['video']for s in SS);indices=collections.Counter();ledger=[]
 for s in SS:
  G=H if s['video']=='005'else np.eye(4);m=transformed_mesh(s,G);idx=indices[s['video']];indices[s['video']]+=1;c=matplotlib.colors.to_hex(palette[s['video']](.40+.5*idx/max(1,counts[s['video']]-1)))
  addmesh(s['id'],m['V'],m['F'],c)
  if s['video']=='005':np.savez_compressed(meshdir/(s['id']+'.npz'),**m,K=s['mesh']['K'],T=H@s['mesh']['T'],source_SHA256=sha(s['root']/'TRUSTED_HERO.npz'),coordinate='004 world mm; rigid coordinate copy, not fusion')
  ledger.append(dict(id=s['id'],video=s['video'],color=c,source=asset(s['root']/'TRUSTED_HERO.npz'),derived_path=str(meshdir/(s['id']+'.npz'))if s['video']=='005'else str(s['root']/'TRUSTED_HERO.npz')))
 # Small actual camera-center spheres and trajectory cylinders, all in the same rigid scene.
 for video,col in [('004','#1f6aba'),('005','#db6b18')]:
  vv=sorted([v for v in VIEWS if v['video']==video],key=frame_index);cent=np.array([(H@v['T'] if video=='005'else np.asarray(v['T']))[:3,3]for v in vv])
  for i,p in enumerate(cent):
   m=trimesh.creation.icosphere(subdivisions=1,radius=.13);m.apply_translation(p);addmesh('camera_'+vv[i]['id'],m.vertices,m.faces,col)
  for i,(a,b)in enumerate(zip(cent[:-1],cent[1:])):
   if np.linalg.norm(a-b)<1e-8:continue
   m=trimesh.creation.cylinder(radius=.035,segment=np.array([a,b]),sections=6);addmesh(video+'_trajectory_'+str(i),m.vertices,m.faces,col)
 p=out/'G01_SHARED_SCENE_DIAGNOSTIC_NOT_FUSION.glb';scene_glb.export(p)
 save('derived/HERO_SCENE_SOURCE_INDEX.json',dict(sources=ledger,geometry_fused=False,computational_units='mm',GLB_units='meter (.001 export only; no estimated scale)',GLB_vertex_index='unreferenced original vertices removed for preview only; exact same triangles; original V,F,face IDs preserved in source and derived NPZ',scene=asset(p)))
 # Enriched 68-row manifest: missing auxiliary HERO is explicit, never invented.
 fb={x['view']:x for x in load(R/'metrics/VIDEO005_FRAME_BINDING.json')['rows']};p18=REPO/'experiments/TASK-E4-HERO-BODY-ADAPT-018';fb4={x['view_id']:x for x in load(p18/'metrics/FRAME_BINDING_AUDIT.json')};smap={s['id']:s for s in SS};rows=[]
 for v in VIEWS:
  cid=v['id'];s=smap.get(cid);native=s['root']/'HERO_native.npz'if s else next((Path(p)for p in v.get('HERO_sources',[])if Path(p).exists()and'depth_mm'in np.load(p).files),None)
  feature=R/'features'/(cid+'.npz');arc=R/'ring'/(cid+'.npz');bind=fb[cid]if v['video']=='005'else fb4[cid]
  rows.append(dict(id=cid,video=v['video'],role=v['role'],RGB=asset(v['RGB_source']),Mask=asset(v['Mask_source']),original_camera_source=v['old_pose_source'],native_c2w=v['T'],K=v['K'],camera_coordinates='OpenCV c2w, mm; native per-video world',frame_binding=bind,original_qualification=v.get('qualification','NOT_PROVIDED'),admission='current input integrity; no upgraded certification',Ring_visible_arcs=asset(arc),Ring_evidence=load(R/'ring'/(cid+'.json'))['valid'],body018=asset(R/'inputs/G01/BODY018.npz'),native_HERO=asset(native)if native is not None and native.exists()else None,HERO_status='EXISTING_NATIVE_DEPTH'if native is not None and native.exists()else'NOT_AVAILABLE_FOR_THIS_FRAME_AUXILIARY_ONLY',TRUSTED_geometry=asset(s['root']/'TRUSTED_HERO.npz')if s else None,SIFT_feature_cache=asset(feature),direction_block019=v['direction_block019'],GT=False))
 save('INPUT_MANIFEST_COMPLETE.json',rows);table('INPUT_MANIFEST_COMPLETE.csv',rows)
 save('metrics/EXPORT_COUNTS.json',dict(planned_views=len(VIEWS),video004=sum(v['video']=='004'for v in VIEWS),video005=len(derived),native_depth_available=sum(r['native_HERO']is not None for r in rows),TRUSTED_native_meshes=len(SS),Ring_evidence_valid=sum(r['Ring_evidence']for r in rows),RGB_SIFT_frames=len(rows),new_HERO_inference=0,body_updated=False))
 print('EXPORT_COMPLETE',len(rows),len(SS),flush=True)

def fig1():
 p4=[(dict(V=BODY['V'],F=BODY['F_solid']),'#8657a7')];p5=[(transformed_mesh(s,np.eye(4)),'#ee9b47')for s in SS if s['video']=='005'];bound=face_bounds(p4+p5)
 fig,axs=plt.subplots(2,3,figsize=(14,9))
 render_panel(axs[0,0],p4,bound,title='004 native world | fixed018 body + original R10 CAD')
 render_panel(axs[0,1],p5,bound,title='005 native world | all 8 original TRUSTED surfaces')
 render_panel(axs[0,2],p4+[(transformed_mesh(s,H),'#ee9b47')for s in SS if s['video']=='005'],bound,title='A5 shared004 world | diagnostic overlay, NOT fusion')
 for j,video in enumerate(['004','005']):
  ax=axs[1,j];q=load(R/'metrics/SHAPE_DIRECTION_PROXIES.json')['proxies'];q=[a for a in q if a['video']==video];theta=np.linspace(0,2*np.pi,300);ax.plot(5.6*np.cos(theta),5.6*np.sin(theta),c='black',lw=6,label='actual CAD centerline reference');ax.scatter([0],[0],c='black',s=30)
  for k,a in enumerate(q):
   xy=np.asarray(a['h'])[:2];color='#2283bb'if a['direction_informative']else'#aaaaaa';ax.quiver(0,0,*xy,angles='xy',scale_units='xy',scale=1,color=color,alpha=.65);ax.scatter(*xy,c=color,s=12)
  ax.set_aspect('equal');ax.set_xlim(-7,7);ax.set_ylim(-7,7);ax.set_xlabel('native world X (mm)');ax.set_ylabel('native world Y (mm)');ax.set_title(video+' Ring center=(0,0,0), normal=+Z\ncore locations are partial/model proxies, NOT true centers',fontsize=8)
 ax=axs[1,2];q=load(R/'metrics/SHAPE_DIRECTION_PROXIES.json')['candidates'];angles=[a.get('yaw_deg')for a in q];ax.hist(angles,bins=np.arange(0,365,5),color='#d99b40');ax.set_xlim(0,360);ax.set_xlabel('proposed yaw (deg)');ax.set_ylabel('geometry proposals');ax.set_title('All geometry direction proposals retained\nShort / uncertain directions are explicitly flagged',fontsize=9)
 fig.suptitle('Fig1 | Ring metric anchor + asymmetric geometry proxies\nSame mm bounds and viewer for top row; black solid Ring; no body/depth modification');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig1_Dual_Anchors.png')

def fig2():
 pair=max(load(R/'metrics/CROSS_004_TRIANGULATION.json')['pair_counts'],key=lambda a:a['known_pose_compatible_N']);a,b=pair['first'],pair['second'];cross=max(load(R/'features/CROSS_EPI.json'),key=lambda x:len(x['p']));c,d=cross['a'],cross['b'];fig=plt.figure(figsize=(15,10));grid=fig.add_gridspec(2,2)
 for i,(u,v,title)in enumerate([(a,b,'004 multi-frame real SIFT tracks'),(c,d,'004 to005 independent RGB-RANSAC matches')]):
  ax=fig.add_subplot(grid[i,0]);m=np.load(R/'matches'/(u+'__'+v+'.npz'));A=np.load(VV[u]['cache'])['RGB'];B=np.load(VV[v]['cache'])['RGB'];ax.imshow(np.concatenate([A,B],axis=1));ok=m['RGB_RANSAC'];idx=[]
  for good in [True,False]:
   ii=np.flatnonzero(ok==good);idx+=list(ii[np.linspace(0,len(ii)-1,min(32,len(ii))).astype(int)])if len(ii)else[]
  for k in idx:
   p=m['p'][k];q=m['q'][k]+[640,0];ax.plot([p[0],q[0]],[p[1],q[1]],c='#38ef74'if ok[k]else'#ee4545',lw=.6,alpha=.7)
  ax.axis('off');ax.set_title(title+'\n'+u+' / '+v+'\ngreen=RANSAC inlier; red=actual rejected match (display subsample)',fontsize=8)
 ax=fig.add_subplot(grid[0,1],projection='3d');lm=np.load(R/'landmarks/CROSS_004.npz')['X'];ax.scatter(*lm.T,s=8,c='#237cb6');ax.plot_trisurf(*RING['V'].T,triangles=RING['F'],color='black',linewidth=0,shade=True);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm');ax.set_box_aspect(np.maximum(np.ptp(lm,axis=0),1));ax.view_init(25,-65);ax.set_title('153 real multiframe triangulated landmarks\nFull spatial extent; Ring shown in black',fontsize=9)
 ax=fig.add_subplot(grid[1,1]);v=VV[a];show_rgb(ax,v,'Actual 004 track observations: source UV identities retained');obs=load(R/'landmarks/CROSS_004_OBSERVATIONS.json');shown=0
 for ob in obs:
  q=next((x for x in ob['observations']if x['view']==a),None)
  if q:ax.scatter(*q['uv'],s=8,c='yellow');shown+=1
 ax.text(.02,.03,'147 background-only / 4 Polyp-only / 2 mixed tracks\nBackground texture dominates direction evidence.\nCovariance is a unit-pixel proxy, not calibrated confidence.',transform=ax.transAxes,color='yellow',fontsize=8)
 fig.suptitle('Fig2 | Real SIFT correspondences and metric visual landmarks\nRGB-only triangulation with frozen004 cameras; no HERO depth or GT used to create landmarks');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig2_SIFT_Landmarks.png')

def fig3():
 g=load(R/'metrics/CROSS_FULL_SEARCH.json');sel=load(R/'results/CROSS_SEARCH_SELECTION.json');fig,axs=plt.subplots(2,3,figsize=(15,8))
 for parity,color in [(1,'#247cb8'),(-1,'#e89035')]:
  rows=sorted([x for x in g if x['parity']==parity],key=lambda x:x['yaw_deg']);x=[a['yaw_deg']for a in rows]
  for j,key in enumerate(['polyp','feature','total']):axs[0,j].plot(x,[a[key]*(.05 if key=='feature'else 1)for a in rows],c=color,label='normal gauge '+str(parity))
 for j,title in enumerate(['Ring-aware Polyp loss','0.05 x SIFT loss','Joint search loss']):
  axs[0,j].set_title(title);axs[0,j].set_xlabel('yaw deg');axs[0,j].set_yscale('log');axs[0,j].legend(fontsize=7)
 ax=axs[1,0];q=[x for x in g if x['parity']==1 and 250<=x['yaw_deg']<=290];ax.plot([x['yaw_deg']for x in q],[x['total']for x in q],'-o',label='joint grid')
 for key,col in [('A1','#44a85a'),('A2','#ab79aa'),('A3','#d78e22'),('A4','#247cbb')]:ax.axvline(sel[key]['yaw_deg'],color=col,ls='--',label=key+' %.2f'%sel[key]['yaw_deg'])
 ax.axvline(np.degrees(np.arctan2(H[1,0],H[0,0]))%360,c='black',label='A5 final');ax.set_xlabel('yaw deg');ax.legend(fontsize=7);ax.set_title('Competing geometry and SIFT directions')
 ax=axs[1,1];q=load(R/'results/CROSS_A5_ALL_INITIALIZATIONS.json');ax.bar(range(len(q)),[x['final_loss']for x in q],color=['#247cbb','#b4b4b4','#b4b4b4']);ax.set_xticks(range(len(q)),['seed '+str(x['seed_index'])for x in q]);ax.set_ylabel('final FIT objective');ax.set_title('All three refinement endpoints retained')
 ax=axs[1,2];p=load(R/'metrics/PROJECTION_AND_POSE_GRADIENT_GATE.json');ax.axis('off');ax.text(0,1,'Ring cannot identify yaw\n\nBoth proper-rotation normal gauges searched.\nRing rendering removes discrete-CAD yaw aliasing.\nMeasured pure-yaw Ring gradient = 0.\n\nFIT target halves: all choose 270 deg on 5 deg grid.\nSIFT match halves: all choose 270 deg.\n\nCandidate selection: angular-separated score NMS;\nnot an exhaustive set of strict local minima.\nNo HOLDOUT or GT used for selection.',va='top',fontsize=10)
 fig.suptitle('Fig3 | Complete 360 deg search + bounded shared-video SE(3) refinement\nNo new large-angle discovery claim: the historical candidates already included approximately -90 deg');fig.tight_layout(rect=[0,0,1,.93]);finish(fig,'Fig3_Full360_Search.png')

def overlays(ids,name):
 tags=['A0_HISTORICAL_FULL_RoMa','IDENTITY_CANONICAL_RING_ONLY','A2','A3','A5'];metrics={(a['method'],a['view']):a for a in load(R/'metrics/ALL_FRAME_METRICS.json')if a['scope']=='CROSS'};fig,axs=plt.subplots(len(ids),len(tags),figsize=(16,2.65*len(ids)),squeeze=False)
 for i,cid in enumerate(ids):
  v=VV[cid];a=np.load(v['cache'])
  for j,tag in enumerate(tags):
   ax=axs[i,j];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan');p=np.load(R/'evaluation/CROSS'/tag/(cid+'.npz'));edge(ax,p['pred'],'#fe4b73');edge(ax,np.isfinite(p['Ring_z_mm']),'#222222');m=metrics[(tag,cid)];ax.axis('off');ax.set_title(tag.replace('A0_HISTORICAL_FULL_','history ').replace('IDENTITY_CANONICAL_RING_ONLY','Ring canonical (yaw=0)')+'\n'+cid+' '+v['role']+'\nIoU %.3f | contour %.2f px'%(m['IoU'],m['contour_px']['MAE']),fontsize=7)
 fig.suptitle('Real005 projections | green actual Polyp, cyan actual Ring, pink predicted018 body, black CAD\nSame RGB pixels, frozen body and frame identities; all three protected005 HOLDOUT are shown in core figure');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,name)

def fig4():
 fit=sorted([v for v in VIEWS if v['video']=='005'and v['role']=='FIT'],key=frame_index);ids=[fit[0]['id'],fit[len(fit)//2]['id'],fit[-1]['id']]+[v['id']for v in VIEWS if v['video']=='005'and v['role']=='HOLDOUT'];overlays(ids,'Fig4_Real_Multiview_Reprojection.png')
 ids=[v['id']for v in VIEWS if v['video']=='005'];
 for i in range(0,len(ids),7):overlays(ids[i:i+7],'details/All005_Projection_%02d.png'%(i//7+1))

def fig5():
 parts=[(dict(V=BODY['V'],F=BODY['F_solid']),'#8657a7')];ledger=load(R/'derived/HERO_SCENE_SOURCE_INDEX.json')['sources'];color={s['id']:s['color']for s in ledger}
 for s in SS:parts.append((transformed_mesh(s,H if s['video']=='005'else np.eye(4)),color[s['id']]))
 bound=face_bounds(parts);fig=plt.figure(figsize=(15,9));gs=fig.add_gridspec(2,3)
 for j,ang in enumerate([(65,-65),(20,-65),(8,20)]):render_panel(fig.add_subplot(gs[0,j]),parts,bound,ang,'Full original TRUSTED faces | view '+str(j+1))
 for j,ang in enumerate([(30,-65),(10,20),(80,-65)]):
  ax=fig.add_subplot(gs[1,j],projection='3d');ax.plot_trisurf(*BODY['V'].T,triangles=BODY['F_solid'],color='#8657a7',linewidth=0,alpha=.8);ax.plot_trisurf(*RING['V'].T,triangles=RING['F'],color='black',linewidth=0)
  for video,col in [('004','#237cbb'),('005','#d87c24')]:
   vv=sorted([v for v in VIEWS if v['video']==video],key=frame_index);C=np.array([(H@v['T']if video=='005'else np.asarray(v['T']))[:3,3]for v in vv]);ax.plot(*C.T,'o-',ms=2,color=col,label=video+' actual trajectory');r=np.r_[bound,C];
  ax.set_xlim(-32,32);ax.set_ylim(-40,24);ax.set_zlim(-15,49);ax.set_box_aspect([64,64,64]);ax.view_init(*ang);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm');ax.legend(fontsize=7);ax.set_title('One Ring + fixed018 body + both camera trajectories',fontsize=8)
 fig.suptitle('Fig5 | Unified diagnostic scene in004 world millimeters | NOT surface fusion\nBlue shades: 13 native004 TRUSTED sources; orange shades: 8 native005 TRUSTED sources; purple: frozen018 body\nAll source face IDs preserved. Full trajectories + independent components are in the local GLB.');fig.tight_layout(rect=[0,0,1,.91]);finish(fig,'Fig5_Unified_Scene_NOT_FUSION.png')

def fig6():
 rows=load(R/'metrics/RING_HERO_DEPTH_DIAGNOSTIC.json')['rows'];# fixed representatives, not selected for apparent success
 ids=['G01_004_ref08','G01_004_ref13','G01_005_raw00057'];fig,axs=plt.subplots(3,6,figsize=(19,9))
 for i,cid in enumerate(ids):
  v=VV[cid];q=np.load(R/'ring_depth'/(cid+'.npz'));a=np.load(v['cache']);rec=next(x for x in rows if x['view']==cid);arc=np.load(R/'ring'/(cid+'.npz'));ax=axs[i,0];show_rgb(ax,v,cid+' real RGB + frozen Masks')
  for key,c in [('inner','yellow'),('outer','magenta')]:ax.scatter(*arc[key].T,c=c,s=.8)
  good=q['selected'];z=q['original_depth'];d=q['CAD_first_axial_mm'];valid=good&np.isfinite(z)&np.isfinite(d);lo,hi=np.quantile(np.r_[z[valid],d[valid]],[.02,.98])
  for j,(depth,title)in enumerate([(d,'Actual CAD first axial depth'),(z,'Original HERO Ring depth')],1):
   im=axs[i,j].imshow(np.ma.masked_where(~q['Ring']|~np.isfinite(depth),depth),cmap='viridis',vmin=lo,vmax=hi);axs[i,j].axis('off');axs[i,j].set_title(title+' (mm)',fontsize=8);fig.colorbar(im,ax=axs[i,j],shrink=.65)
  axs[i,3].imshow(good,cmap='gray');axs[i,3].axis('off');axs[i,3].set_title('Material/texture/CAD-qualified pixels\nN='+str(rec['reliable_N']),fontsize=8)
  im=axs[i,4].imshow(np.ma.masked_invalid(q['residual_mm']),cmap='coolwarm',vmin=-2,vmax=2);axs[i,4].axis('off');axs[i,4].set_title('HERO minus CAD (mm)',fontsize=8);fig.colorbar(im,ax=axs[i,4],shrink=.65)
  sec=rec['sectors'];ax=axs[i,5];ax.plot([x['sector']for x in sec],[x['median_mm']for x in sec],'o-');ax.axhline(0,c='black',lw=.6);ax.set_xlabel('Ring azimuth sector');ax.set_ylabel('median residual mm');ax.set_title('Bias is spatially nonuniform\nsector spread %.2f mm\nheld MAE %.3f -> %.3f mm'%(rec['sector_median_spread_mm'],rec['disjoint_Ring_before_MAE_mm'],rec['disjoint_Ring_after_MAE_mm']),fontsize=8)
 fig.suptitle('Fig6 | Native Ring HERO depth diagnosis | no whole-Polyp correction adopted\n22 native depth maps inspected; 0 pass frozen source-bias stability tests. Held MAE uses disjoint Ring sectors only.\nFinite Ring depth is not proof of correct depth; hypothetical Ring-only offset validation is not a corrected HERO prediction.');fig.tight_layout(rect=[0,0,1,.91]);finish(fig,'Fig6_Ring_HERO_Depth.png')

def main():
 export()
 for f in [fig1,fig2,fig3,fig4,fig5,fig6]:f();print('FIGURE_DONE',f.__name__,flush=True)
 save('provenance/DELIVERY_FIGURES.json',dict(source=asset(Path(__file__)),files=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],actual_data=True,GT=False,optimization=False))
if __name__=='__main__':main()
