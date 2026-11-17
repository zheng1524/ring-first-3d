"""All panels from frozen actual meshes, fixed observations and independent evaluation."""
from visual_base import *
from evaluate import distance
import matplotlib.colors as mcolors
OLD13=REPO/'experiments/TASK-E4-PYTORCH3D-RING-AWARE-001/runs/FREE_VERTEX_013'
SRCBODY=OLD13/'code/figures_body_alignment.py'
for node in ast.parse(SRCBODY.read_text()).body:
 if isinstance(node,ast.FunctionDef)and node.name in ['camera','render','show']:exec(compile(ast.Module(body=[node],type_ignores=[]),str(SRCBODY)+':direct_reuse','exec'),globals())
ANGLES=[(89.999,0),(-89.999,0),(0,0),(0,90),(0,180),(0,270)]
def z(n,t):return dict(np.load(R/'local_results/metric'/n/(t+'.npz')))
def review(n,held=False):
 c=next(c for c in load(R/'config/CASE_LOCK.json')if c['name']==n);return next(v['id']for v in c['views']if(v['role']!='FIT')==held)
def native_image(ax,n,cid,tags,heat=False):
 a=np.load(R/'inputs'/n/(cid+'.npz'));rg=np.load(R/'inputs'/n/'RING.npz');cad=cast(scene(rg['V'],rg['F']),a['K'],a['T'],360,640);ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan')
 for t,col in zip(tags,['#c39742','#a652af','#2879a6']):
  zz=z(n,t);depth=cast(scene(zz['V'],zz['F']),a['K'],a['T'],360,640);pred=np.isfinite(depth)&(depth<cad);edge(ax,pred,col)
  if heat:
   rgb=np.zeros((360,640,4));fn=(a['labels']==1)&~pred;fp=pred&(a['labels']==0);rgb[fn]=[.05,.3,1,.7];rgb[fp]=[1,.12,.03,.7];ax.imshow(rgb)
 ax.set_title(cid+' | '+','.join(tags),fontsize=7);ax.axis('off')
def bounds(n,tags):return np.r_[np.load(R/'inputs'/n/'RING.npz')['V'],*[z(n,t)['V']for t in tags]]
def meshgrid(n,tags,ax,angle=(20,-65)):
 b=bounds(n,tags)
 for a,t in zip(ax,tags):model_panel(a,n,z(n,t),b,angle);a.set_title(n+' '+t,fontsize=8)
def video_stability():
 n='G01';tags=['B_A_ONLY','B0_UNCORRECTED','C1_8'];fig,ax=plt.subplots(2,3,figsize=(16,10));meshgrid(n,tags,ax[0],(0,-65));per=load(R/'metrics/PER_VIEW_METRICS.json')
 for j,tag in enumerate(tags):
  rows=[r for r in per if r['case']==n and r['tag']==tag];groups=['004 FIT','004 HOLD','005 FIT','005 HOLD'];vals=[np.mean([r['IoU']for r in rows if r['video']==video and(r['role']=='FIT')==fit])for video,fit in [('004',True),('004',False),('005',True),('005',False)]];ax[1,j].bar(range(4),vals,color=['#2879a6','#74abc6','#e87a34','#edb484']);ax[1,j].set_xticks(range(4),groups,rotation=20);ax[1,j].set_ylim(0,1);ax[1,j].set_title(tag+' common fixed evaluation cameras');ax[1,j].set_ylabel('Native visible Mask IoU')
 fig.suptitle('Fig3 | G01 video addition: stability and systematic-bias controls\nSame frozen011 start, same budget; B1=C1_8 research candidate. Mesh and camera errors remain confounded. Black CAD, mm.');finish(fig,'Fig3_G01_Video_Stability.png')
def g02():
 fig,ax=plt.subplots(2,4,figsize=(20,9));per=load(R/'metrics/PER_VIEW_METRICS.json')
 for i,held in enumerate([False,True]):
  cid=review('G02',held);native_image(ax[i,0],'G02',cid,[]);native_image(ax[i,1],'G02',cid,['FINAL013']);native_image(ax[i,2],'G02',cid,['FINAL014'],True);ax[i,3].axis('off');txt=[]
  for tag in ['FINAL013','FINAL014']:
   r=next(v for v in per if v['case']=='G02'and v['view']==cid and v['tag']==tag);txt.append(f"{tag}\nIoU {r['IoU']:.3f}, P {r['Precision']:.3f}, R {r['Recall']:.3f}\nFN {r['FN']}, knownFP {r['FP']}\nBoundary {r['boundary_MAE_px']:.2f} px\nRing-front conflicts {r['Ring_front_conflict_N']}\nUpdate member: {r['used_for_this_model_update']}")
  ax[i,3].text(0,1,'\n\n'.join(txt),va='top',fontsize=10)
 fig.suptitle('Fig4 | G02 actual native FIT / protected HOLDOUT reprojection\nGreen observed Polyp, cyan observed Ring. Blue missing foreground, red extra known background. All-pixel and Ring-front diagnostics separately reported.');finish(fig,'Fig4_G02_Missing_Extra.png')
def g03():
 cfg=load(R/'config/FINAL_METHOD_FROZEN_BEFORE_HOLDOUT_GT.json')if(R/'config/FINAL_METHOD_FROZEN_BEFORE_HOLDOUT_GT.json').exists()else load(R/'provenance/FINAL_METHOD_FROZEN_BEFORE_HOLDOUT_GT.json');coarse=cfg['coarse'];e=cfg['E'];tags=['FINAL011','FINAL013',coarse,e,'FINAL014'];fig,ax=plt.subplots(3,5,figsize=(22,14));meshgrid('G03',tags,ax[0],(0,-65));meshgrid('G03',tags,ax[1],(25,-65))
 for j,tag in enumerate(tags):native_image(ax[2,j],'G03',review('G03'),[tag],True)
 fig.suptitle('Fig5 | G03 actual stalk-recovery sequence, same metric world/viewer\n011 start / historical013 / selected coarse / refined continuation / 014 final. No artificial stalk insertion, smoothing or trimming.');finish(fig,'Fig5_G03_Actual_Recovery_Process.png')
def refinement():
 n='G03';sig=np.load(R/'runtime/refinement'/n/'E2_adaptive_SIGNAL.npz');base=dict(V=sig['V'],F=sig['F'],F_solid=sig['F']);i1=dict(np.load(R/'arms/E1_global/inputs'/n/'INITIAL.npz'));i2=dict(np.load(R/'arms/E2_adaptive/inputs'/n/'INITIAL.npz'));final=z(n,'E2_adaptive');b=np.r_[base['V'],i1['V'],i2['V'],final['V'],np.load(R/'inputs'/n/'RING.npz')['V']];fig,ax=plt.subplots(2,3,figsize=(18,11));signal=sig['signal'][sig['F']].mean(1);fc=plt.get_cmap('viridis')(signal/max(1e-20,signal.max()))[:,:3];model_panel(ax[0,0],n,base,b,face_colors=fc);ax[0,0].set_title('Actual FIT contour-gradient signal',fontsize=9);stretch=sig['edge_stretch'];fc=plt.get_cmap('magma')(np.clip((stretch-1)/2,0,1))[:,:3];model_panel(ax[0,1],n,base,b,face_colors=fc);ax[0,1].set_title('Coarse edge stretch vs frozen011 (1 to3+)',fontsize=9);fc=np.tile([.4,.6,.9],(len(sig['F']),1));fc[sig['selected']]=[1,.15,.03];model_panel(ax[0,2],n,base,b,face_colors=fc);ax[0,2].set_title('Actually selected local subdivision faces',fontsize=9)
 for a,v,title in [(ax[1,0],i1,'E1 global subdivision, UNTRAINED'),(ax[1,1],i2,'E2 local subdivision, UNTRAINED'),(ax[1,2],final,'E2 after fixed continuation')]:model_panel(a,n,v,b);a.set_title(title+f"\nV={len(v['V'])}, F={len(v.get('F_solid',v['F']))}",fontsize=9)
 fig.suptitle('Fig6 | Real G03 subdivision controls, interpolation only before continued optimization\nBlack fixed CAD. Coarse gradient signal is a residual-driven localization proxy, not GT correspondence. All dimensions mm.');finish(fig,'Fig6_G03_Adaptive_Refinement.png')
def difficult_cases():
 fig,ax=plt.subplots(5,5,figsize=(21,17))
 for i,n in enumerate(['G07','G08','G09','G10','G11']):
  native_image(ax[i,0],n,review(n),[]);meshgrid(n,['FINAL011','FINAL013','FINAL014'],ax[i,1:4]);native_image(ax[i,4],n,review(n,True),['FINAL014'],True)
 fig.suptitle('Fig7 | All G07-G11: preserved inputs, actual initial/historical/final meshes and protected HOLDOUT\nSame per-case metric viewer. G10/G11: recipe-equivalent011 from013. Gray inferred base is not observed tissue; cameras remain conditional.');finish(fig,'Fig7_G07_G11_Detailed_Review.png')
def ablations():
 cases=load(R/'config/CASE_LOCK.json');native=load(R/'metrics/NATIVE_SUMMARY.json');gt=load(R/'metrics/BLENDER_ALIGNMENT_METRICS.json');cstage=['C0','C1_8','C2_16','C3_32','C4_ALL'];fig,axs=plt.subplots(6,4,figsize=(21,21),layout='constrained');ceiling=max(1.5,1.05*max(r['Chamfer_MAE_mm']for r in gt if r['label']in cstage))
 for i,c in enumerate(cases):
  a,b=axs[i//2,(i%2)*2:(i%2)*2+2];n=c['name'];rows=[next(r for r in native if r['case']==n and r['label']==t)for t in cstage];gr=[next(r for r in gt if r['case']==n and r['label']==t)for t in cstage]
  a.plot(range(5),[r['FIT_IoU']for r in rows],'o-',label='common FIT');a.plot(range(5),[r['HOLDOUT_IoU']for r in rows],'s--',label='HOLDOUT');a.set_ylim(0,1);a.set_title(n+' actual updateN='+','.join(str(r['training_views_N'])for r in rows),fontsize=8);a.legend(fontsize=7);a.set_ylabel('Native Mask IoU',fontsize=8)
  b.plot(range(5),[r['Chamfer_MAE_mm']for r in gr],'x:',c='red');b.set_ylim(0,ceiling);b.set_title(n+' independent GT, same 3D axis for every case',fontsize=8);b.set_ylabel('Best-rigid Chamfer (mm)',fontsize=8);delta=gr[-1]['Chamfer_MAE_mm']-gr[0]['Chamfer_MAE_mm'];b.text(.03,.93,f'all minus C0: {delta:+.6f} mm',transform=b.transAxes,va='top',fontsize=8)
  for aa in [a,b]:aa.set_xticks(range(5),['C0','8','16','32','all']);aa.grid(alpha=.15)
 for aa in axs[-1,2:]:aa.axis('off')
 fig.suptitle('Fig8 | View-count ablation: fixed native evaluation pool; all predictions frozen before independent GT\nTargets8/16/32/all per video, actual group totals shown. Separate 2D/3D axes; common absolute Chamfer scale avoids magnifying numerical changes.',fontsize=12);finish(fig,'Fig8_View_Count_2D_3D.png')
 base=load(R/'config/C_SELECTION.json')['method'];tags=[base,'D_D1_split','D_D2_bidir','D_D3_combo'];fig,ax=plt.subplots(2,2,figsize=(16,11));xx=np.arange(len(cases));width=.2
 for j,t in enumerate(tags):
  rr=[next(r for r in native if r['case']==c['name']and r['label']==t)for c in cases];bb=[next(r for r in native if r['case']==c['name']and r['label']==base)for c in cases];gg=[next(r for r in gt if r['case']==c['name']and r['label']==t)for c in cases];gb=[next(r for r in gt if r['case']==c['name']and r['label']==base)for c in cases]
  data=[[r['FIT_IoU']-b['FIT_IoU']for r,b in zip(rr,bb)],[r['FIT']['FP_per_mask']-b['FIT']['FP_per_mask']for r,b in zip(rr,bb)],[r['FIT']['boundary_MAE_px']-b['FIT']['boundary_MAE_px']for r,b in zip(rr,bb)],[r['Chamfer_MAE_mm']-b['Chamfer_MAE_mm']for r,b in zip(gg,gb)]]
  for a,dd in zip(ax.ravel(),data):a.bar(xx+(j-1.5)*width,dd,width,label=['D0 inherited013','D1 extraFP','D2 extraContour','D3 combination'][j]);a.axhline(0,c='black',lw=.6)
 for a,title in zip(ax.ravel(),['commonFIT IoU change (higher better)','Known FP/Mask change (lower better)','Boundary MAE change px (lower better)','Post-freeze GT Chamfer change mm (lower better)']):a.set_title(title);a.set_xticks(xx,[c['name']for c in cases],rotation=40);a.legend(fontsize=6)
 fig.suptitle('Fig9 | Fixed four-loss incremental ablation, same initialization/views/budget\n013 already contained separated FN/FP and bidirectional contour; no novelty claim for these inherited components. FIT-only method selection.');finish(fig,'Fig9_Contour_Loss_Ablation.png')
def alignment():
 rows=load(R/'metrics/BLENDER_ALIGNMENT_METRICS.json');cases=load(R/'config/CASE_LOCK.json');fig,ax=plt.subplots(11,4,figsize=(18,31))
 for i,c in enumerate(cases):
  n=c['name'];g=dict(np.load(R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz'));a=dict(np.load(R/'local_results/aligned'/n/'FINAL013.npz'));b=dict(np.load(R/'local_results/aligned'/n/'FINAL014.npz'));bound=np.r_[g['V'],a['V'],b['V']];row=next(r for r in rows if r['case']==n and r['label']=='FINAL014');show(ax[i,0],g['V'],g['F'],bound,(20,-65),n+' original Blender body',body_color='#8d9299');show(ax[i,1],a['V'],a['F'],bound,(20,-65),'013 best SE3',g);show(ax[i,2],b['V'],b['F'],bound,(20,-65),f"014 CD={row['Chamfer_MAE_mm']:.3f}mm, p95={row['Chamfer_p95_mm']:.3f}mm",g);err=distance(scene(g['V'],g['F']),b['V'][b['F']].mean(1));show(ax[i,3],b['V'],b['F'],bound,(20,-65),'014 surface distance, dark0 / yellow2+mm',errors=err)
  details,aa=plt.subplots(5,6,figsize=(22,18));before=z(n,'FINAL014');early=np.load(R/'local_results/aligned'/n/'FINAL011.npz');full=np.r_[bound,before['V'],early['V']]
  for j,ang in enumerate(ANGLES):
   show(aa[0,j],g['V'],g['F'],full,ang,'GT native author body',body_color='#8d9299');show(aa[1,j],before['V'],before['F'],full,ang,'014 BEFORE SE3',g)
   for k,t in enumerate(['FINAL011','FINAL013','FINAL014'],2):v=dict(np.load(R/'local_results/aligned'/n/(t+'.npz')));show(aa[k,j],v['V'],v['F'],full,ang,t+' bestSE3',g)
  details.suptitle(n+' actual pure-body six-direction comparison, fixed shared extent\nAfter Ring-based Metric Recovery and Best 6-DoF Rigid Alignment. Scale=1; not end-to-end pose accuracy.');finish(details,'details/'+n+'_Pure_Body_Six_Views.png')
 fig.suptitle('Fig10 | Eleven independent physical bodies: Ring scale locked, same best6DoF evaluator\nGT transparent gray, predictions purple. Ring/background excluded from alignment and these pure-body panels. No geometry postprocessing.');finish(fig,'Fig10_All_Groups_Best_Rigid_Alignment.png')
def export():
 index=[]
 for c in load(R/'config/CASE_LOCK.json'):
  n=c['name'];a=z(n,'FINAL014');rr=np.load(R/'inputs'/n/'RING.npz');folder=R/'review_models'/n;folder.mkdir(parents=True,exist_ok=True);np.savez_compressed(folder/'FINAL014_mm.npz',**a);trimesh.Trimesh(a['V'],a['F_solid'],process=False).export(folder/'FINAL014_mm.ply');sc=trimesh.Scene();body=trimesh.Trimesh(a['V']*.001,a['F_solid'],process=False);body.visual.face_colors=np.tile([137,83,175,255],(len(a['F_solid']),1));body.visual.face_colors[a['inferred_base_faces']]=[160,160,160,255];sc.add_geometry(body,node_name='actual014_body_inferred_base_gray');ring=trimesh.Trimesh(rr['V']*.001,rr['F'],process=False);ring.visual.face_colors=[8,8,8,255];sc.add_geometry(ring,node_name='fixed_CAD_Ring');(folder/'FINAL014_scene_m.glb').write_bytes(sc.export(file_type='glb'));index.extend(asset(p)for p in folder.iterdir())
 save('provenance/REVIEW_MODELS_INDEX.json',dict(files=index,NPZ_PLY_unit='mm',GLB_unit='m',presentation_conversion_only=.001,no_scientific_postprocessing=True))
def evidence_regions():
 cases=load(R/'config/CASE_LOCK.json');fig,ax=plt.subplots(11,2,figsize=(12,29))
 for i,c in enumerate(cases):
  n=c['name'];v=z(n,'FINAL014');ev=np.load(R/'local_results/native_eval'/n/'FINAL014_FACE_EVIDENCE.npz');colors=np.tile([.6,.6,.6],(len(v['F_solid']),1));mapping={tuple(sorted(f)):j for j,f in enumerate(v['F_solid'])}
  for j,f in enumerate(v['F']):
   index=mapping[tuple(sorted(f))]
   if ev['sampled_HERO_supported'][j]:colors[index]=[.1,.7,.25]
   elif ev['face_supported'][j]:colors[index]=[.15,.4,.85]
  b=bounds(n,['FINAL011','FINAL013','FINAL014'])
  for a,angle in zip(ax[i],[(20,-65),(0,40)]):model_panel(a,n,v,b,angle,face_colors=colors);a.set_title(n+' actual observation-evidence proxies',fontsize=8)
 fig.suptitle('Green sparse sameview HERO support; blue visible Mask-only; gray UNKNOWN/inferred\nNo sampled support is not counter-evidence. Black fixed CAD, same mm viewer; no GT used for these labels.');finish(fig,'details/Observed_vs_Unknown_Regions.png')
def main():
 assert(R/'provenance/INDEPENDENT_EVALUATION_COMPLETE.json').exists()
 for fn in [video_stability,g02,g03,refinement,difficult_cases,ablations,alignment,evidence_regions,export]:print('FIGURE',fn.__name__,flush=True);fn()
if __name__=='__main__':main()
