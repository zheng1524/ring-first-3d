"""Frozen-output evaluation and figures through the existing real renderers."""
from audit import *
from functools import lru_cache
import trimesh
from visualization.same_camera_scene import SameCameraScene
plt=vis.configure()
sys.path.insert(0,str(OLD/'surface_fusion_v3/vendor'))
import open3d as o3d
D=load(R/'provenance/INPUT_ELIGIBILITY.json');CC={c['id']:c for c in D['references']};VV={v['id']:v for v in D['views']}
ANGLES=[(-65,22),(0,0),(90,0),(180,0),(-90,0),(0,90)]
FIG_SOURCES={}
@lru_cache(None)
def points(cid):
 c=CC[cid];z=np.load(c['source_points']);P=z['XYZ_mm']if'XYZ_mm'in z else z['points_mm'];uv=next((z[k]for k in ['source_uv','pixel_uv','uv']if k in z),None)
 if uv is None:uv=np.c_[z['source_u'],z['source_v']]
 m=trimesh.load(c['mesh'],process=False);rgb=np.asarray(Image.open(c['RGB']).convert('RGB'));return P,rgb[uv[:,1],uv[:,0]]/255.,np.asarray(m.faces),uv
@lru_cache(None)
def ring(kind):return trimesh.load(OLD/'surface_fusion_v2/inputs/R10_ring.obj'if kind=='R10'else OLD.parent/'assets/ring_R5.obj',process=False)
def combine(sid,kind,only_ids=None):
 refs=[c for c in D['references']if c['scene_id']==sid and (only_ids is None or c['id']in only_ids)];P=[];C=[];F=[];offset=0
 for c in refs:
  p,col,faces,_=points(c['id']);keep=np.ones(len(p),bool)
  if kind in ['Cleaned_F1','AllAvailable_Cleaned_F1']:keep=~np.load(c['cleaned_flags']['path'])['clean_removed']
  if kind=='F2':keep=np.load(PART/f'local_results/pointcloud_blocks/{sid}/ViewPartition_Cleaned_F2/{c["id"]}.npz')['accepted']
  faces=faces[keep[faces].all(1)];ids=np.flatnonzero(keep);mapper=np.full(len(p),-1,int);mapper[ids]=np.arange(len(ids))+offset;P.append(p[ids]);C.append(col[ids]);F.append(mapper[faces]);offset+=len(ids)
 return dict(P=np.concatenate(P),C=np.concatenate(C),F=np.concatenate(F),input_refs=[c['id']for c in refs],method=kind)
def f3(sid):
 z=np.load(GROW/f'local_results/glb/{sid}_Joint_sources.npz');P=z['XYZ_derived_mm'];C=z['RGB'];lookup={(ref,int(i)):j for j,(ref,i)in enumerate(zip(z['source_reference'],z['original_point_id']))};ff=[]
 for block in load(GROW/f'local_results/scenes/{sid}_Final.json')['blocks']:
  ref=block['reference'];f=points(ref)[2][block['face_ids']];ff +=[[lookup[(ref,int(i))]for i in face]for face in f]
 return dict(P=P,C=C,F=np.asarray(ff,int),input_refs=sorted(set(z['source_reference'])),method='F3_Joint')
def methods(sid):
 hist=[c['id']for c in D['references'][:14]if c['scene_id']==sid]
 out={name:combine(sid,name,hist)for name in ['Raw_F1','Cleaned_F1','F2']};out['AllAvailable_Cleaned_F1']=combine(sid,'AllAvailable_Cleaned_F1');out['F3_Joint']=f3(sid)
 if sid=='G01_005':
  pair=load(R/'config/sdf_minimal.json')['input_ids'];out['Raw_F1_matching_inputs']=combine(sid,'Raw_F1',pair);out['Cleaned_F1_matching_inputs']=combine(sid,'Cleaned_F1',pair)
  for mode in ['M0','M1','M2','M3']:
   p=R/f'local_results/map/{mode}/surface.npz'
   if p.exists():
    z=np.load(p);out['Map_'+mode]=dict(P=z['XYZ_mm'],C=z['RGB'],F=z['faces'],input_refs=pair,method='Map_'+mode)
  z=np.load(R/'local_results/sdf_scene/surface.npz');support=z['face_observed_support'];F=z['faces'][support];ids=np.unique(F);mapper=np.full(len(z['XYZ_mm']),-1,int);mapper[ids]=np.arange(len(ids));out['SDF_supported']=dict(P=z['XYZ_mm'][ids],C=z['RGB'][ids],F=mapper[F],input_refs=pair,method='SDF_supported')
 return out
@lru_cache(None)
def cad_scene(kind):
 m=ring(kind);rt=o3d.t.geometry.RaycastingScene(nthreads=2);rt.add_triangles(o3d.core.Tensor(np.asarray(m.vertices,np.float32)),o3d.core.Tensor(np.asarray(m.faces,np.uint32)));return rt
# Exact existing triangle renderer and target evaluation. No target RGB argument
# to prediction; all per-target outputs are frozen before target images open.
ns=extract(Path('/home/liu/ring_first_3d_view_eval/experiments/TASK-VIEW-OBSERVABILITY-GT-EVAL-001/code/reprojection.py'),['render','evaluate','neutral'],dict(np=np,o3d=o3d,vis=vis,cad_scene=cad_scene))
render_triangle=ns['render'];evaluate=ns['evaluate'];neutral=ns['neutral']

def figure_save(fig,name,sources):
 fig.savefig(R/'figures'/name,dpi=125,facecolor='white');plt.close(fig);FIG_SOURCES[name]=sources

def input_figure():
 fig=plt.figure(figsize=(17,14));gs=fig.add_gridspec(5,4,width_ratios=[1.5,1.5,1.3,1.2],hspace=.27,wspace=.13)
 for row,sid in enumerate(['G01_004','G01_005','G06_004','G08_005','G07_004']):
  c=next(c for c in D['references']if c['scene_id']==sid);im=np.asarray(Image.open(c['RGB']).convert('RGB'));mask=np.asarray(Image.open(c['Mask']));overlay=im/255.;overlay[mask==1]=.6*overlay[mask==1]+.4*np.array([1,.1,.5]);overlay[mask==2]=.4*overlay[mask==2]+.6*np.array([0,.9,.9]);
  ax=fig.add_subplot(gs[row,0]);ax.imshow(im);ax.set_title(sid+' | real input',fontsize=10);ax.axis('off');ax=fig.add_subplot(gs[row,1]);ax.imshow(overlay);ax.set_title('Polyp=magenta; Ring=cyan',fontsize=9);ax.axis('off')
  ax=fig.add_subplot(gs[row,2],projection='3d');vv=[v for v in D['views']if v.get('source_id')==c['group']+'_video'+c['video'] and v.get('c2w')is not None];centers=np.array([v['c2w']for v in vv])[:,:3,3];cad=ring(c['ring']);ax.plot(*centers.T,color='royalblue',lw=1);ax.scatter(*centers.T,s=12,color='royalblue');ax.scatter(*np.asarray(cad.vertices).T,s=.2,color='black');ax.set(xlabel='x mm',ylabel='y mm',zlabel='z mm',title='Frozen camera centers / fixed CAD');ax.set_box_aspect([1,1,1]);ax.tick_params(labelsize=6)
  ax=fig.add_subplot(gs[row,3]);ax.axis('off');n=sum(x['scene_id']==sid for x in D['references']);text=sid+'\n'+c['morphology']+'/'+c['ring']+'\n'+c['condition']+'\n'+str(n)+' HERO refs; dependency recovered\nNative/display/XYZ units checked\nGT: DENY; poses conditional'
  ax.text(0,.95,text,va='top',fontsize=9,wrap=True)
 fig.suptitle('Phase E | REAL INPUT AUDIT | 4 physical groups / 5 single-video scenes\nHistorical data only; no cross-video coordinate certification',fontsize=15,y=.995)
 figure_save(fig,'Fig1_four_group_inputs_cameras.png',[c['RGB']for c in D['references'][:9]])

def sixview_figure(mm):
 fig,axs=plt.subplots(6,6,figsize=(19,17));rr=ring('R10');allP=[mm[s]['Raw_F1']['P']for s in mm]
 mapname=next((n for n in ['Map_M3','Map_M2','Map_M1','Map_M0']if n in mm['G01_005']),None)
 rows=[('G01_004','F2'),('G01_004','F3_Joint'),('G01_004',None),('G01_005','F2'),('G01_005',mapname),('G01_005','SDF_PRIOR_DIAGNOSTIC')]
 prior=np.load(R/'local_results/sdf_scene/surface.npz')
 allP.append(prior['XYZ_mm'])
 if mapname:allP.append(mm['G01_005'][mapname]['P'])
 bounds=[vis.limits(allP,rr,a)for a in ANGLES]
 for i,(sid,name)in enumerate(rows):
  for j,a in enumerate(ANGLES):
   ax=axs[i,j]
   if name is None:ax.axis('off');ax.text(.5,.5,'NOT_RUN\nSDF / MapAnything\nvideo004',ha='center',va='center',fontsize=11,color='firebrick');continue
   if name=='SDF_PRIOR_DIAGNOSTIC':p=prior['XYZ_mm'];c=np.full((len(p),3),.55)
   else:z=mm[sid][name];p=z['P'];c=z['C']
   label='SDF prior / FAILED'if name=='SDF_PRIOR_DIAGNOSTIC'else name
   vis.view(ax,p,c,rr,bounds[j],angle=a,title=f'{sid} | {label}\nview {j+1}; mm',size=.8)
   ax.title.set_fontsize(8)
   ax.tick_params(labelsize=6)
  if i in [0,3]:fig.text(.01,.945 if i==0 else .495,'SINGLE-VIDEO RECONSTRUCTION — video'+sid[-3:],fontsize=11,fontweight='bold')
 fig.suptitle('Real XYZ six-view comparison | fixed mm bounds and source RGB\nSDF grey = unsupported zero-level set; observed-supported faces = 0 (FAILED geometry gate)',fontsize=14,y=.995)
 fig.text(.5,.007,'CROSS-VIDEO CANDIDATE — NOT FUSED | no cross-video optimization or fusion | Raw/Cleaned/F3 full six-view gallery retained locally',ha='center',fontsize=10)
 fig.subplots_adjust(top=.915,bottom=.045,hspace=.65,wspace=.22)
 figure_save(fig,'Fig2_G01_six_views_and_method_status.png',['historical source XYZ/UV and Final scene face IDs','map outputs if present','SDF frozen zero-level set (prior/unknown only)'])
 # Full local strips, all historical/new methods with actual outputs.
 for sid,ms in mm.items():
  for name,z in ms.items():
   if not len(z['P']):continue
   fig,axs=plt.subplots(1,6,figsize=(20,4))
   for j,a in enumerate(ANGLES):vis.view(axs[j],z['P'],z['C'],rr,vis.limits(allP+[z['P']],rr,a),angle=a,title=f'{sid} {name} / mm',size=.8)
   folder=R/'figures/local';folder.mkdir(exist_ok=True);fig.savefig(folder/(sid+'_'+name+'_six_views.png'),dpi=110);plt.close(fig)
 save('provenance/SIX_VIEW_PARAMETERS.json',dict(angles=ANGLES,bounds=bounds,point_size=.8,renderer=str(REPO/'visualization/real_p0_renderer.py'),renderer_SHA256=sha(REPO/'visualization/real_p0_renderer.py'),cross_video_fused=False))

def eval_and_fig(mm):
 targets=[t for t in D['targets']if t['scene']in mm];predictions={};freeze=[]
 folder=R/'local_results/reprojection';folder.mkdir(parents=True,exist_ok=True)
 for t in targets:
  v=VV[t['target']];K=np.array(v['K']);pose=np.array(v['c2w'])
  for name,z in mm[t['scene']].items():
   if not len(z['F']):continue
   p=render_triangle(z['P'],z['F'],z['C'],K,pose,np.eye(4),'R10');predictions[(t['target'],name)]=p
   dest=folder/(t['target']+'_'+name+'.npz');np.savez_compressed(dest,**p);freeze.append(dict(path=str(dest),sha256=sha(dest),method=name,target=t['target'],source_input_refs=z['input_refs']))
 save('provenance/ALL_PREDICTIONS_BEFORE_TARGET_RGB.json',dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=freeze,GT_used=False,target_RGB_and_Mask_read=False,render_implementation='exact AST existing reprojection.py:render',CAD_tolerance_mm=.05,protocol='actual triangles; point-center legacy statistics are not interchanged'))
 rows=[];commonrows=[];comparisons=[]
 for t in targets:
  v=VV[t['target']];B=np.asarray(Image.open(v['RGB']).convert('RGB'));labels=np.asarray(Image.open(v['Mask']));polyp=labels==1;frame_preds={}
  for name,z in mm[t['scene']].items():
   p=predictions.get((t['target'],name))
   if p is None:
    rows.append(dict(scene=t['scene'],target=t['target'],method=name,status='NOT_EVALUABLE_NO_OBSERVED_SUPPORT',target_Polyp_pixels=int(polyp.sum()),common_pixels=0,target_coverage=0.,RGB_MAE_0_255=None));continue
   met,mae,valid=evaluate(p,B,labels);union=(p['valid']|polyp).sum();met['silhouette_IoU']=float(valid.sum()/union)if union else None
   edge=lambda a:a&~cv2.erode(a.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
   ep,eb=edge(p['valid']),edge(polyp);dp=cv2.dilate(ep.astype(np.uint8),np.ones((5,5),np.uint8))>0;db=cv2.dilate(eb.astype(np.uint8),np.ones((5,5),np.uint8))>0;pr=(ep&db).sum()/max(1,ep.sum());re=(eb&dp).sum()/max(1,eb.sum());met['boundary_F1_2px']=float(2*pr*re/(pr+re))if pr+re else 0.
   rows.append(dict(scene=t['scene'],target=t['target'],method=name,status='FINITE_RENDER_CONDITIONAL_NOT_GT',holdout_tier=t['holdout_tier'],**met));frame_preds[name]=p
  for name in frame_preds:
   if name=='F3_Joint':continue
   a=frame_preds['F3_Joint'];b=frame_preds[name];valid=a['valid']&b['valid']&polyp
   commonrows.append(dict(scene=t['scene'],target=t['target'],baseline='F3_Joint',candidate=name,common_pixels=int(valid.sum()),target_Polyp_pixels=int(polyp.sum()),baseline_MAE=float(abs(a['RGBA'][...,:3].astype(float)-B).mean(-1)[valid].mean())if valid.any()else None,candidate_MAE=float(abs(b['RGBA'][...,:3].astype(float)-B).mean(-1)[valid].mean())if valid.any()else None,holdout_tier=t['holdout_tier']))
  # Include every G01 target in local A->B figures; core uses frozen first 005.
  selected=next((x for x in ['Map_M3','Map_M2','Map_M1','Map_M0']if x in frame_preds),'F3_Joint');p=frame_preds[selected];mae=abs(p['RGBA'][...,:3].astype(float)-B).mean(-1);overlay=B/255.;valid=p['valid'];overlay[valid]=.5*overlay[valid]+.5*p['RGBA'][valid,:3]/255.;unknown=np.full(B.shape,.83);unknown[polyp&~valid]=[1,.2,.1];unknown[valid&polyp]=[.15,.8,.4];cad_occ=np.isfinite(p['known_CAD_z_mm'])&np.isfinite(p['z_mm'])&(p['z_mm']>p['known_CAD_z_mm']+.05);unknown[cad_occ]=[.1,.1,.1]
  images=[B,neutral(p['RGBA']),overlay,np.where((valid&polyp)[...,None],np.clip(mae/80,0,1)[...,None]*np.array([1.,.2,.1]),.83),unknown];titles=['Real target B',selected+' | A geometry/source RGB','50% overlay','RGB difference / common support','Green=supported; red=unknown; black=CAD occlusion']
  fig,axs=plt.subplots(2,5,figsize=(18,5),gridspec_kw={'height_ratios':[3,1]})
  for ax,im,title in zip(axs[0],images,titles):ax.imshow(im);ax.set_title(title,fontsize=9);ax.axis('off');ax.set_anchor('N')
  for ax in axs[1]:ax.axis('off')
  axs[1,0].text(0,1,t['target']+'\n'+t['holdout_tier']+'\nfull B Polyp denominator: '+str(int(polyp.sum())),va='top',fontsize=10)
  axs[1,1].text(0,1,'SDF: FAILED OBSERVED-SUPPORT GATE\n0 supported faces / frozen criterion\nPrior-only surface excluded from metrics',va='top',fontsize=10,color='firebrick')
  axs[1,3].text(0,1,'Map: '+selected+'\nif selected F3: Map NOT_RUN/FAILED\nNo B RGB/Mask used to fit geometry',va='top',fontsize=10)
  fig.suptitle('REAL A→B | '+t['scene']+' | conditional diagnostic; unknown tissue occlusion remains unresolved',fontsize=14);fig.tight_layout(rect=[0,0,1,.94]);path=R/'figures/local';path.mkdir(exist_ok=True);fig.savefig(path/(t['target']+'_A_to_B.png'),dpi=125)
  if t['target']=='G01_video005_v005_00860':figure_save(fig,'Fig3_G01_real_A_to_B.png',[v['RGB'],v['Mask'],'frozen source-only predictions'])
  else:plt.close(fig)
 table('metrics/G01_REAL_TARGET_COMPARISON.csv',rows);table('metrics/G01_IDENTICAL_COMMON_PIXELS.csv',commonrows)
 return rows,commonrows

def failure_figure(mm):
 fig=plt.figure(figsize=(17,11));gs=fig.add_gridspec(2,3,hspace=.32,wspace=.3);prior=np.load(R/'local_results/sdf_scene/surface.npz');rr=ring('R10');bounds=vis.limits([prior['XYZ_mm']],rr,(-65,22));ax=fig.add_subplot(gs[0,0]);vis.view(ax,prior['XYZ_mm'],np.full((len(prior['XYZ_mm']),3),.6),rr,bounds,title='SDF zero-level set / mm\nALL prior-or-unknown; supported faces=0')
 ax=fig.add_subplot(gs[0,1]);loss=load(R/'metrics/SDF_LOSS_TRACE.json');ax.plot([x['step']for x in loss],[x['depth']for x in loss],label='absolute-Z loss');ax.plot([x['step']for x in loss],[x['silhouette']for x in loss],label='silhouette loss');ax.set(xlabel='optimizer step / one frozen run',ylabel='loss',title='400 steps; no budget extension');ax.legend(fontsize=8)
 ax=fig.add_subplot(gs[0,2]);ax.axis('off');env=load(R/'provenance/ENVIRONMENT_CHECK.json');s=load(R/'provenance/SDF_RUN_RESULT.json');ax.text(0,1,'CUDA tensor: PASS\nCleanup: 58 invalid download artifacts\n6.05 GiB released; valid weights retained\nSDF: 400 steps / '+str(round(s['optimization_seconds'],2))+' s\nObserved-support area: 0 mm²\nSDF boundary-domain adaptation FAILED\nMap status: see official run ledger\nGT: DENY; no cross-video optimization',va='top',fontsize=11)
 cadrows=[]
 for j,name in enumerate(['F3_Joint','Map_M3','Map_M0']):
  ax=fig.add_subplot(gs[1,j]);z=mm['G01_005'].get(name)
  if z is None:ax.axis('off');ax.text(.5,.5,name+'\nNOT_RUN / FAILED',ha='center',va='center',fontsize=13);continue
  signed=cad_scene('R10').compute_signed_distance(o3d.core.Tensor(z['P'].astype(np.float32)),nthreads=2,nsamples=3).numpy();inside=signed<-.02;C=z['C'].copy();C[inside]=[1,.05,.05];bb=vis.limits([mm['G01_005']['Raw_F1']['P'],z['P']],rr,(-65,22));vis.view(ax,z['P'],C,rr,bb,title=name+' | FULL RANGE / mm\nCAD inside '+str(int(inside.sum()))+'/'+str(len(inside))+'; see axis scales',size=.8);cadrows.append(dict(scene='G01_005',method=name,point_N=len(inside),CAD_inside_N=int(inside.sum()),maximum_inside_mm=float(max(0,-signed.min())),tolerance_mm=.02,GT_used=False))
 fig.suptitle('Observed support / prior-only distinction and real failure evidence\nSource-supported is conditional on camera + HERO, never a true-surface certificate',fontsize=14)
 figure_save(fig,'Fig4_support_CAD_failure_evidence.png',['SDF frozen field + training trace','actual model/baseline XYZ + fixed CAD signed distance'])
 table('metrics/NEW_OUTPUT_CAD_AUDIT.csv',cadrows)

def main():
 assert (R/'provenance/MAP_RUN_RESULT.json').exists(),'do not read targets until bounded model branch ends'
 input_figure();mm={sid:methods(sid)for sid in ['G01_004','G01_005']};sixview_figure(mm);eval_and_fig(mm);failure_figure(mm);save('provenance/FIGURE_SOURCES.json',FIG_SOURCES)
 # Index all local outputs, including original meshes/GLBs without copying them.
 rows=[]
 for p in sorted((R/'figures').rglob('*.png')):rows.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,kind='core'if p.parent==R/'figures'else'LOCAL_ONLY'))
 for p in sorted((GROW/'local_results/glb').glob('G01*.glb')):rows.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,kind='HISTORICAL_LOCAL_ONLY_NOT_NEW_OUTPUT'))
 table('provenance/GALLERY_AND_GLB_INDEX.csv',rows)
 print('EVIDENCE_COMPLETE',len(rows),'indexed artifacts',flush=True)
if __name__=='__main__':main()
