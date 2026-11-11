"""Actual frozen optimizer traces, same-capture photos, candidate cameras and honest missing depth."""
from qcommon import *
import textwrap
from visual_base import plt,edge
from visualize021 import layer,composite,free_camera,panel,body_layer,colors,temporal_frame
from geometry021 import group_data
from ring020 import CADCurves,ellipse_points
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def figureA():
 fig,axs=plt.subplots(2,3,figsize=(17,9));parts=[]
 for i,arm in enumerate(['B1','B2','B3']):
  a=load(Q/'results'/arm/'FINAL.json');calls=load(Q/'optimization'/arm/'CALLS.json');xx=np.arange(len(calls));ll=np.array([np.nan if c['loss']is None else c['loss']for c in calls]);axs[0,i].plot(xx,ll,'o-',ms=2,label='actual L-BFGS-B calls');axs[0,i].axhline(a['initial_loss'],ls='--',c='black',label='frozen021 endpoint');axs[0,i].set(title=a['method']+' from '+arm+'\n'+textwrap.fill(a['solver_message'],48),xlabel='actual function call',ylabel='unchanged021 FIT objective');axs[0,i].legend(fontsize=6);axs[0,i].grid(alpha=.2);parts.append(a)
 x=np.arange(3);axs[1,0].set_ylim(0,.037);axs[1,0].bar(x,[a['translation_change_mm']for a in parts]);axs[1,0].set_xticks(x,['A1','A2','A3']);axs[1,0].set_ylabel('actual pose translation change mm')
 for i,a in enumerate(parts):axs[1,0].text(i,a['translation_change_mm'],f"{a['translation_change_mm']:.3g}mm\n{a['rotation_change_deg']:.3g}deg",ha='center',fontsize=7)
 g=load(Q/'metrics/GRADIENT_COMPONENT_ISOLATION.json');g=[a for a in g if a['arm']=='B2'and a['parameter']=='pose'and a['h']==.01];x=np.arange(len(g));axs[1,1].bar(x-.2,[a['Ring_curves_AD']for a in g],.4,label='Ring AD');axs[1,1].bar(x+.2,[a['Ring_curves_FD']for a in g],.4,label='Ring centralFD');axs[1,1].set_xticks(x,[str(a['index'])for a in g]);axs[1,1].set(xlabel='original normalized pose coordinate',ylabel='directional derivative',title='Actual B2 Ring-gradient mismatch');axs[1,1].legend(fontsize=7)
 reg={a['method']:a for a in load(Q/'metrics/REGISTRATION_COMPARISON.json')};x=np.arange(3);before=[reg['A0_'+a]['HOLDOUT_IoU']for a in ['B1','B2','B3']];after=[reg['A'+str(i)]['HOLDOUT_IoU']for i in [1,2,3]];axs[1,2].bar(x-.2,before,.4,label='frozen021');axs[1,2].bar(x+.2,after,.4,label='mature solver');axs[1,2].set_xticks(x,['A1','A2','A3']);axs[1,2].set_ylim(0,1.06);axs[1,2].set(ylabel='heldout body IoU (not pose GT)',title='Independent evaluation after all candidates freeze');axs[1,2].legend(fontsize=7)
 for i,(a,b)in enumerate(zip(before,after)):axs[1,2].text(i,max(a,b)+.03,f'{a:.6f}\n→{b:.6f}',ha='center',fontsize=7)
 fig.suptitle('Figure A | Mature solver executed on exactly021 data/loss/priors/constraints; no photos in BA\nA2 movement and loss change are at numerical-noise scale. A1 partial decrease ends in line-search failure. No body/HERO/heldout in optimization.');fig.tight_layout(rect=[0,0,1,.93]);finishq(fig,'BA_CONVERGENCE.png');finishq(fig,'figures/Figure_A_Mature_Solver_Review.png');plt.close(fig)

def figureB():
 rows=load(Q/'metrics/PHOTO_REGISTRATION_COMPARISON.json');assets={a['id']:a for a in load(Q/'config/PHOTO_ASSETS.json')};cad=CADCurves(P/'inputs/G01/RING.npz');fig,axs=plt.subplots(3,4,figsize=(20,11))
 for i,r in enumerate(rows):
  cid=r['id'];a=assets[cid];d=np.load(a['cache']);rgb=d['RGB'];lab=d['labels'];ev=np.load(Q/'inputs'/cid/'RING_NATIVE_EVIDENCE.npz');report=load(Q/'inputs'/cid/'RING_FIT_NATIVE.json');C=np.array(load(Q/'results/photos'/cid/'FINAL.json')['C']);proj=np.load(Q/'inputs'/cid/'AUDIT_PROJECTION.npz')
  for ax in axs[i]:ax.imshow(rgb);ax.axis('off')
  edge(axs[i,0],lab==1,'lime');edge(axs[i,0],lab==2,'cyan');axs[i,0].set_title(cid+' INDEPENDENT_PHOTO\nraw20260805 SHA '+a['RGB']['sha256'][:12]+' | original nativeMask')
  for name,col in [('inner','cyan'),('outer','orange')]:
   p=(ev[name]+.5)/3-.5;axs[i,1].scatter(p[:,0],p[:,1],s=.6,c=col)
  if report.get('centerline'):
   for name,col in [('inner','cyan'),('outer','orange'),('centerline','magenta')]:
    q=ellipse_points(report[name],np.linspace(0,2*np.pi,512));q=(q+.5)/3-.5;axs[i,1].plot(q[:,0],q[:,1],ls='--',c=col,lw=.6)
  axs[i,1].set_title('Actual supported I/O points, nativeMask snap≤2.5px\nDXY full fitted curves dashed; Mid magenta is inferred fit')
  edge(axs[i,2],proj['ring_pred'],'black');edge(axs[i,2],lab==2,'cyan');axs[i,2].set_title('Actual fixedCAD black / observedRing cyan\nI/O MAE %.2f / %.2f px | conditional photo pose'%(r['Inner_MAE_px'],r['Outer_MAE_px']))
  edge(axs[i,3],lab==1,'lime');edge(axs[i,3],proj['body_pred_at_independent_photo_pose'],'#eb61e5');axs[i,3].set_title('Frozen018 body projection (evaluation only)\nIoU %.3f; photoHELD MAE %.2fpx, gate failed'%(r['frozen_independent_photo_pose_body_IoU'],r['PHOTO_HELD_error_px']['MAE']))
 fig.suptitle('Figure B | Three distinct still captures, original JPG SHA matches video-cohort source registry\nAll projections use independent photo PnP+Ring refinement, fixed assumed K490 at640×360. Video reference frames are not relabeled as photos. No photo depth inferred.');fig.tight_layout(rect=[0,0,1,.93]);finishq(fig,'figures/Figure_B_Independent_Photo_Ring_And_CAD.png');plt.close(fig)

def figureC():
 rv=np.load(P/'inputs/G01/RING.npz');b=np.load(P/'inputs/G01/BODY018.npz');views=load(P/'config/VIEWS.json');H=np.array(load(P/'results/B3.json')['T']);fig=plt.figure(figsize=(15,8));ax=fig.add_subplot(1,2,1,projection='3d');ax.add_collection3d(Poly3DCollection(rv['V'][rv['F']],facecolors='black',edgecolors='none'));ax.add_collection3d(Poly3DCollection(b['V'][b['F']],facecolors='#6f62a3',alpha=.5,edgecolors='none'));allp=[rv['V'],b['V']]
 for video,col in [('004','tab:blue'),('005','tab:orange')]:
  vv=sorted([v for v in views if v['video']==video],key=temporal_frame);Cs=[H@np.asarray(v['T'])if video=='005'else np.asarray(v['T'])for v in vv];ps=np.array([C[:3,3]for C in Cs]);allp.append(ps);ax.plot(*ps.T,'.-',ms=3,c=col,label=video+' frozen trajectory')
  for C in Cs[::max(1,len(Cs)//7)]:ax.quiver(*C[:3,3],*(C[:3,2]*2),color=col,linewidth=.6)
 for i,r in enumerate(load(Q/'metrics/PHOTO_REGISTRATION_COMPARISON.json')):
  C=np.array(load(Q/'results/photos'/r['id']/'FINAL.json')['C']);p=C[:3,3];allp.append(p[None]);ax.scatter(*p,c=['magenta','green','red'][i],marker='^',s=60,label=r['id']+' candidate');ax.quiver(*p,*(C[:3,2]*3),color=['magenta','green','red'][i]);ax.text(*p,r['id'],fontsize=6)
 Pts=np.r_[*allp];lo,hi=Pts.min(0),Pts.max(0);ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title='Actual004-world positions / camera-forward arrows\nPhoto candidates failed current heldout gate; not accepted strong geometry');ax.set_box_aspect(hi-lo);ax.view_init(25,-65);ax.legend(fontsize=6)
 ax=fig.add_subplot(1,2,2);rows=load(Q/'metrics/PHOTO_REGISTRATION_COMPARISON.json');y=np.arange(3);ax.barh(y,[r['minimum_direction_difference_deg']for r in rows]);ax.set_yticks(y,[r['id']for r in rows]);ax.set(xlabel='minimum angle to existing68 directions (deg)',title='Conditional direction estimates only\nAzimuth precision and new physical area not certified')
 for j,r in enumerate(rows):ax.text(r['minimum_direction_difference_deg'],j,' %.2f°'%r['minimum_direction_difference_deg'],va='center')
 fig.suptitle('Figure C | Independent still camera estimates and unchanged two-video scene\nTrue black CAD + frozen018 body. Only cameras are displayed; this task does not deform body or combine surfaces. Same metric coordinate, no scale/ICP.');fig.tight_layout(rect=[0,0,1,.91]);finishq(fig,'figures/Figure_C_Photo_Video_Camera_Geometry.png');plt.close(fig)

def figureD():
 H=np.array(load(P/'results/B3.json')['T']);conf,src=group_data('G01',H);rv=np.load(conf['ring']['path']);b=dict(np.load(conf['bodies']['B2']['path']));bounds=np.r_[rv['V'],b['V'],*[a['V'][np.unique(a['F'])]for a in src]];col=colors(len(src));layers=[layer(a['V'],a['F'],c,a['id'])for a,c in zip(src,col)]+[layer(rv['V'],rv['F'],'black','CAD')];fig,axs=plt.subplots(2,3,figsize=(17,10));view=free_camera(bounds,20,-65)
 panel(axs[0,0],composite(layers),view,bounds,'Existing21 native TRUSTED HERO sources\nActual unchanged open triangles and blackCAD')
 panel(axs[1,0],composite(layers+[body_layer(b,'B2')]),view,bounds,'Same sources + frozen018 body\nOverlap is not fusion or new photo-derived surface')
 for i,r in enumerate(load(Q/'metrics/PHOTO_REGISTRATION_COMPARISON.json')):
  pos=[(0,1),(0,2),(1,1)][i];ax=axs[pos];d=np.load(Q/'inputs'/r['id']/'PHOTO_RGB_MASK_K.npz');ax.imshow(d['RGB']);edge(ax,d['labels']==1,'lime');ax.axis('off');ax.set_title(r['id']+' new native HERO: MISSING\nTRUSTED area / compatibility / uncovered area: NOT_EVALUABLE\nCameraHeld MAE %.2fpx; official inference not run'%r['PHOTO_HELD_error_px']['MAE'],fontsize=8)
 ax=axs[1,2];ax.axis('off');ax.text(.02,.95,'Actual input status\n\n12/12 original photos and source-bound Masks found\n3/3 G01 numeric independent pose candidates\n0/3 pass new conservative photo-camera gate\n0 new official HERO runs\nNo photo-native TRUSTED faces to add\nNew visible area remains NOT_EVALUABLE\n\nExisting coverage stays unchanged.\nModel/loader/017 cleaning rules are indexed\nfor a later validated-camera run.',va='top',fontsize=10)
 fig.suptitle('Figure D | New geometry availability and missing evidence, preserved honestly\nNo video depth has been reprojected and renamed as native photo HERO. Original open geometry and uncertainty are retained; no body training.');fig.tight_layout(rect=[0,0,1,.92]);finishq(fig,'figures/Figure_D_Photo_Geometry_Readiness.png');plt.close(fig)

def figureE():
 rows=load(Q/'metrics/PHOTO_REGISTRATION_COMPARISON.json');fig,axs=plt.subplots(3,2,figsize=(15,11))
 for i,r in enumerate(rows):
  cid=r['id'];d=np.load(Q/'inputs'/cid/'PHOTO_RGB_MASK_K.npz');C=np.asarray(load(Q/'results/photos'/cid/'FINAL.json')['C']);m=[x for x in load(Q/'results/photos'/cid/'ALL_RGB_LANDMARK_MATCHES.json')if x['role']=='PHOTO_HELD'];ax=axs[i,0];ax.imshow(d['RGB']);edge(ax,d['labels']==1,'lime');ax.axis('off')
  for a in m:
   X=np.array(a['XYZ004_mm']);p=(X-C[:3,3])@C[:3,:3];q=p@d['K'].T;pred=q[:2]/q[2];uv=np.array(a['photo_uv']);ax.scatter(*uv,c='green',s=8);ax.scatter(*pred,c='red',s=8,marker='x');ax.annotate('',xy=pred,xytext=uv,arrowprops=dict(arrowstyle='->',color='yellow',lw=.7))
  ax.set_title(cid+' actualPHOTO_HELD (not in fit)\nobserved green / actual projected landmark red / residual yellow')
  mm=load(Q/'results/photos'/cid/'ALL_RGB_LANDMARK_MATCHES.json');counts={}
  for a in mm:
   for s in a['support_RGB_views']:counts[s['view']]=counts.get(s['view'],0)+1
  vid=max(counts,key=counts.get);v=next(v for v in load(P/'config/VIEWS.json')if v['id']==vid);a=np.load(v['cache']);ax=axs[i,1];ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');ax.axis('off')
  for x in mm:
   for s in x['support_RGB_views']:
    if s['view']==vid:ax.scatter(*s['uv'],s=8,c='lime')
  ax.set_title('Actual cached video RGB '+vid+'\nreal source feature observations, same640×360 frame')
 fig.suptitle('Supplement | Real photo-to-video RGB identity and independent heldout residuals\nNo spatial-nearest correspondence, no GT/mesh matching, no pose chosen from this heldout evaluation.');fig.tight_layout(rect=[0,0,1,.93]);finishq(fig,'figures/Photo_Heldout_RGB_Reprojection_Evidence.png');plt.close(fig)

def main():
 figureA();figureB();figureC();figureD();figureE();qsave('runtime/QUICK_FIGURES_COMPLETE.json',dict(epoch=time.time(),core_figures=4,source=asset(Path(__file__))));print('QUICK_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':main()
