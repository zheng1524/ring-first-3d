"""Actual native triangles and fixed metric views; numeric proposals explicitly labelled."""
from evaluate_real import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
src=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/code/figures.py';node=next(n for n in ast.parse(src.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='actual_mesh_image');text=ast.get_source_segment(src.read_text(),node).replace('azim,color):','azim,color,face_colors=None):').replace('rgb[sel]=np.array(col)*shade[:,None]','rgb[sel]=np.array(col)*shade[:,None]\n        if idx==0 and face_colors is not None:rgb[sel]=np.asarray(face_colors)[fid[sel]]*shade[:,None]');exec(compile(text,str(src)+':source_facecolor_adapter','exec'),globals())
ANGLES=[(25,-65),(5,20),(0,110)]
def color(i):return matplotlib.colors.hsv_to_rgb([(i*.61803398875)%1,.65,.85])
def finish(fig,name):fig.savefig(R/'figures'/name,dpi=130,bbox_inches='tight');plt.close(fig)
def edge(ax,mask,c,lw=.7):
 for q in cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)[0]:ax.plot(q[:,0,0],q[:,0,1],c=c,lw=lw)
def combine(parts):
 V=[];F=[];C=[];off=0
 for v,f,c in parts:V.append(v);F.append(f+off);C.append(np.tile(c,(len(f),1)));off+=len(v)
 return np.concatenate(V),np.concatenate(F),np.concatenate(C)
def panel(ax,parts,ring,bounds,title,angle=ANGLES[0]):
 if not parts:ax.text(.1,.5,'NO NUMERIC CANDIDATE');ax.axis('off');return
 V,F,co=combine(parts);im,scale=actual_mesh_image(V,F,ring['V'],ring['F'],bounds,*angle,'#6677aa',co);ax.imshow(im);ax.plot([15,15+2*scale],[378,378],c='k',lw=2);ax.text(15,364,'2 mm (center-depth perspective)',fontsize=6);ax.set_title(title,fontsize=8);ax.axis('off')
def main():
 assert (R/'provenance/INDEPENDENT_EVALUATION_COMPLETED.json').exists();groups=['G03','G05','G01','G06'];data={};allrec=load(R/'config/REAL_SOURCES.json');legend=[]
 for g in groups:
  ss=[source(s)for s in allrec if s['group']==g];a1=np.load(R/'local_results/A1_LEGACY_REPLAY/runs'/g/'B1/FINAL.npz');tt=dict(zip(map(str,a1['source_ids']),a1['theta']));arms={a:[arm_source(s,a,tt)for s in ss]for a in ARMS};ring=dict(np.load(R/'inputs'/g/'RING.npz'));bodies={b:dict(np.load(R/'local_results'/g/(b+'.npz')))for b in ['Body-E','Body-U']};bounds=np.concatenate([ring['V']]+[a['V'][np.unique(a['m']['F'])]for aa in arms.values()for a in aa if a['available']]);data[g]=dict(ss=ss,arms=arms,ring=ring,bodies=bodies,bounds=bounds);legend.extend(dict(group=g,source=s['id'],color_rgb=color(i),original_faces=len(s['m']['F']))for i,s in enumerate(ss))
 fig,axs=plt.subplots(4,3,figsize=(16,14))
 for gi,g in enumerate(groups):
  d=data[g];s=next((x for x in d['ss']if x['rec']['origin']=='018'),d['ss'][0]);a=np.load(s['rec']['view_cache']);e=s['rec']['ellipse'];curve=ellipse_curve({k:np.array(e[k])for k in ['center','axes','U']});axs[gi,0].imshow(a['RGB']);edge(axs[gi,0],a['labels']==1,'lime');edge(axs[gi,0],a['labels']==2,'cyan');axs[gi,0].plot(*curve.T,c='yellow');outside=a['region_class']=='UNKNOWN';axs[gi,0].scatter(*a['uv'][outside][::30].T,s=1,c='gray');axs[gi,0].set_title(g+' '+s['id']+'\nFull Mask green / Ring cyan / generic core ellipse yellow',fontsize=8);axs[gi,0].axis('off')
  for j,b in enumerate(['Body-E','Body-U'],1):
   ax=axs[gi,j];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');m=d['bodies'][b];z=cast(scene(m['V'],m['F']),a['K'],np.array(s['rec']['C']),*a['labels'].shape);edge(ax,np.isfinite(z),'magenta');res=load(R/'local_results'/g/b/s['id']/'CANDIDATES_FROZEN.json');ch=res['chosen']
   if ch:
    region=np.load(R/'local_results'/g/b/s['id']/(ch['tag']+'_REGION.npz'));pu,_=project(region['Q'],np.array(ch['C']),a['K']);p=region['source_uv'];ii=np.arange(0,len(p),max(1,len(p)//15));ax.scatter(*p[ii].T,c='yellow',s=7);ax.quiver(p[ii,0],p[ii,1],pu[ii,0]-p[ii,0],pu[ii,1]-p[ii,1],color='red',angles='xy',scale_units='xy',scale=1,width=.002)
   ax.set_xlim(0,640);ax.set_ylim(360,0);ax.set_title(b+' original-pose Body magenta; actual final Q reprojection arrows\nOutside-core native geometry retained; no stalk-to-head anchors',fontsize=8);ax.axis('off')
 fig.suptitle('Figure 1 | Actual 2D regional correspondences. Arrows are measured reprojection residuals, not training gradients.');finish(fig,'Fig1_Region_Correspondences.png')
 fig,axs=plt.subplots(4,4,figsize=(16,15))
 for gi,g in enumerate(groups):
  d=data[g];ss=d['ss'];s=next((x for x in ss if x['rec']['origin']=='018'),ss[0]);idx=next(i for i,x in enumerate(ss)if x['id']==s['id']);bb=np.r_[d['bounds'],d['bodies']['Body-E']['V'],d['bodies']['Body-U']['V']]
  for j,b in enumerate(['Body-E','Body-U']):
   m=d['bodies'][b];panel(axs[gi,2*j],[(m['V'],m['F'],[.6,.5,.75]),(s['m']['V'],s['m']['F'],color(idx))],d['ring'],bb,g+' '+b+' frozen Body + native source')
   a=d['arms']['A2-'+b[-1]][idx];parts=[(m['V'],m['F'],[.6,.5,.75])]+([(a['V'],a['m']['F'],color(idx))]if a['available']else[]);panel(axs[gi,2*j+1],parts,d['ring'],bb,g+' '+b+' NUMERIC resection proposal\nIndependent qualification reported separately')
 fig.suptitle('Figure 2 | Fresh image-only ellipsoid vs frozen updated Body. Same bounds within each case; no Body update.');finish(fig,'Fig2_Body_E_U.png')
 fig,axs=plt.subplots(4,4,figsize=(16,15))
 for gi,g in enumerate(groups):
  d=data[g]
  for j,a in enumerate(ARMS):panel(axs[gi,j],[(s['V'],s['m']['F'],color(i))for i,s in enumerate(d['arms'][a])if s['available']],d['ring'],d['bounds'],g+' '+a+(' NUMERIC proposals'if a.startswith('A2')else''))
 fig.suptitle('Figure 3 | All native TRUSTED triangles. Same metric bounds, source colors, black actual CAD. No fusion/deletion.');finish(fig,'Fig3_HERO_All_Group_Comparison.png')
 for g,d in data.items():
  fig,axs=plt.subplots(3,4,figsize=(16,12))
  for ai,angle in enumerate(ANGLES):
   for j,a in enumerate(ARMS):panel(axs[ai,j],[(s['V'],s['m']['F'],color(i))for i,s in enumerate(d['arms'][a])if s['available']],d['ring'],d['bounds'],g+' '+a+' '+str(angle),angle)
  finish(fig,g+'_Three_Fixed_Directions.png')
  if g=='G03':
   near=np.concatenate([d['ring']['V']]+[s['V'][np.unique(s['m']['F'])]for s in d['arms']['A0']]);fig,axs=plt.subplots(3,4,figsize=(16,12))
   for ai,angle in enumerate(ANGLES):
    for j,a in enumerate(ARMS):panel(axs[ai,j],[(s['V'],s['m']['F'],color(i))for i,s in enumerate(d['arms'][a])if s['available']],d['ring'],near,g+' '+a+' ORIGINAL-REGION DETAIL',angle)
   fig.suptitle('G03 head/connection/elongated native-structure inspection | fixed ORIGINAL metric display range\nLarge misplaced proposals may leave this detail frame; complete all-proposal bounds are in G03_Three_Fixed_Directions.png. No face deletion.')
   finish(fig,'G03_Head_Stalk_Original_Region_Detail.png')
  # Full actual plane intersections, exactly same plane across all arms.
  y=float(np.median(d['bodies']['Body-U']['V'][:,1]));fig,axs=plt.subplots(1,4,figsize=(17,4))
  for j,arm in enumerate(ARMS):
   ax=axs[j]
   for i,s in enumerate(d['arms'][arm]):
    if not s['available']:continue
    seg=trimesh.intersections.mesh_plane(trimesh.Trimesh(s['V'],s['m']['F'],process=False),[0,1,0],[0,y,0])
    for line in seg:ax.plot(line[:,0],line[:,2],c=color(i),lw=.6)
   ax.set(title=g+' '+arm+' | Y=%.3f mm'%y,xlabel='world X mm',ylabel='world Z mm');ax.axis('equal');ax.grid(alpha=.2)
  finish(fig,g+'_Actual_Common_Sections.png')
 # Independent metrics + all controls; failed values retained.
 met=load(R/'metrics/COMPARISON.json');valid=load(R/'metrics/VALIDATION.json');controls=load(R/'metrics/CONTROL_RESULTS.json');fig,axs=plt.subplots(2,3,figsize=(17,9))
 for i,g in enumerate(groups):
  rr=[next(x for x in met if x['group']==g and x['arm']==a and x['comparison']=='independent_HERO_HOLDOUT')for a in ARMS];axs[0,0].plot(ARMS,[x['effective_error_mm']['MAE']for x in rr],'o-',label=g);axs[0,1].plot(ARMS,[x['support_N_fraction']for x in rr],'o-',label=g);axs[0,2].plot(ARMS,[x['fixed_10mm_penalty_mm']for x in rr],'o-',label=g)
 for j,b in enumerate(['Body-E','Body-U']):
  rr=[x for x in controls if x['Body']==b and 'final_point_error_mm'in x];axs[1,0].plot([x['control']for x in rr],[x['final_point_error_mm']['MAE']for x in rr],'o-',label=b);vv=[x for x in valid if x['Body']==b];axs[1,1].plot(groups,[sum(x['accepted_H']is not None for x in vv if x.get('group')==g)for g in groups],'o-',label=b)
  axs[1,2].plot(groups,[np.mean([x['derived_SIFT']['MAE']for x in vv if x.get('group')==g and x.get('derived_SIFT',{}).get('MAE')is not None])for g in groups],'o-',label=b)
 for ax,title in zip(axs.ravel(),['Independent raw-HERO HOLDOUT effective MAE mm','HOLDOUT support / fixed source-target N','HOLDOUT fixed-N miss penalty mm (10mm cap)','Synthetic known-point recovery MAE mm','Conditional source counts (group N=18/16/26/15)','Real held background Sampson MAE px']):ax.set_title(title,fontsize=9);ax.legend(fontsize=7);ax.grid(alpha=.2);ax.tick_params(axis='x',rotation=20)
 fig.suptitle('Figure 4 | Independent evidence, not Body self-consistency. Real absolute pose/geometry GT: NOT_EVALUABLE.');finish(fig,'Fig4_Independent_and_Control_Evaluation.png')
 # Controls actual surfaces; separate source identities C4 never averaged.
 ctr=load(R/'controls/SOURCES.json');fig,axs=plt.subplots(6,4,figsize=(16,22))
 for i,cid in enumerate(['C0_ZERO','C1_DEPTH','C2_POSE','C3_FAR','C4_LEFT','C4_RIGHT']):
  s=next(x for x in ctr if x['id']==cid);m=np.load(s['mesh']);truth=np.load(R/'controls/audit_only'/(cid+'_TRUE.npz'));rv=dict(np.load(s['ring_path']));baseV=truth['X'];pms=[(m['V'],m['F'],[.8,.3,.2]),(baseV,m['F'],[.6,.6,.6])];bb=np.r_[m['V'],baseV,rv['V']]
  results=[]
  for b in ['Body-E','Body-U']:
   r=load(R/'controls/results'/cid/b/'CANDIDATES_FROZEN.json');V=transform(m['V'],np.array(r['chosen']['H']));results.append(V);bb=np.r_[bb,V]
  for j,(v,title)in enumerate([(m['V'],'perturbed'),(baseV,'true control shape'),(results[0],'Body-E recovered'),(results[1],'Body-U recovered')]):panel(axs[i,j],[(v,m['F'],[.4,.5,.8])],rv,bb,cid+' '+title)
 finish(fig,'Control_Actual_Recovery.png')
 export=[]
 for g,d in data.items():
  sc=trimesh.Scene();sc.graph.update(frame_to='mm_to_m',matrix=np.diag([.001,.001,.001,1.]));layers=[]
  def add(name,V,F,c):
   mesh=trimesh.Trimesh(V,F,process=False);mesh.remove_unreferenced_vertices();mesh.visual.face_colors=np.tile(np.r_[np.array(c)*255,255].astype(np.uint8),(len(mesh.faces),1));sc.add_geometry(mesh,node_name=name,geom_name=name,parent_node_name='mm_to_m');layers.append(name)
  add('Ring_CAD',d['ring']['V'],d['ring']['F'],[.025]*3)
  for b,m in d['bodies'].items():add(b+'_FROZEN',m['V'],m['F'],[.5,.5,.7])
  for arm,ss in d['arms'].items():
   for i,s in enumerate(ss):
    if s['available']:add(arm+('_NUMERIC_NOT_CERTIFIED'if arm.startswith('A2')else'')+'__'+s['id'],s['V'],s['m']['F'],color(i))
   folder=R/'local_results'/g/arm;folder.mkdir(parents=True,exist_ok=True)
   for s in ss:
    if s['available']:np.savez_compressed(folder/(s['id']+'_DERIVED.npz'),V=s['V'],F=s['m']['F'],C=s['C'],native_pixel_id=s['m'].get('native_pixel_id',np.full(len(s['V']),-1,dtype=np.int64)),original_vertex_id=np.arange(len(s['V'])),original_mesh_uv=s['m']['uv'],original_mesh_K=s['m']['K'],original_face_id=s['m']['original_face_id'],native_vertex_identity_supplied=('native_pixel_id'in s['m']))
  path=R/'local_results'/g/(g+'_ALL_LAYERS.glb');sc.export(path);export.append(dict(group=g,asset=asset(path),layers=layers,root_scale=.001,meaning='overlaid separate meshes, NOT fused; numeric A2 may fail independent validation; select a single arm when viewing'))
 save('assets_index/GLB_INDEX.json',export);table('metrics/SOURCE_COLOR_LEGEND.csv',legend);save('provenance/VISUALIZATIONS_COMPLETED.json',dict(epoch=time.time(),real_geometry=True,all_original_faces=True));print('FIGURES_EXPORTED',flush=True)
if __name__=='__main__':main()
