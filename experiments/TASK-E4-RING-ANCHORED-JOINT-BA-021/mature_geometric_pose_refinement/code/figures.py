from refine import *
from visual_base import plt,edge
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from geometry021 import cpu_curve_distance
from ring020 import contours
COL={'P0':'black','S0':'#2a9d8f','A1':'#e9c46a','A2':'#4361ee','A3':'#e76f51'}
def finish(fig,name):fig.savefig(M/'figures'/name,dpi=135,bbox_inches='tight');plt.close(fig)
def main():
 vv=load(M/'config/VIEWS.json');rows=load(M/'metrics/ALL_VIDEO_METHOD_METRICS.json');rr=load(M/'metrics/FOUR_GROUP_POSE_COMPARISON.json');groups=load(P/'config/FOUR_GROUP_INPUTS.json');methods=['P0','S0','A1','A2','A3']
 fig,axs=plt.subplots(2,3,figsize=(16,9));syn=load(M/'metrics/CONICS_SYNTHETIC_MID_AUDIT.json');mid=load(M/'metrics/CONICS_MID_CONTINUOUS_CURVE_CHECK.json');axs[0,0].semilogy(np.arange(8),[r['best_known_circle_center_error_mm']for r in syn],'o-');axs[0,0].set(title='OfficialConics known-circle inverse self-check',xlabel='8 fixedCAD/camera configurations',ylabel='closest valid branch camera-center error mm')
 for d,col in [(35.,'tab:blue'),(50.,'tab:orange')]:
  a=[r for r in mid if r['depth_mm']==d];axs[0,1].plot([r['tilt_deg']for r in a],[r['true_circle_vs_Mid_continuous_px']['MAE']if r['Mid_valid']else np.nan for r in a],'o-',label=f'{d:g}mm')
 axs[0,1].set(title='ThickRing DXYMid vs true centerline',xlabel='inclination deg;70deg Mid failed',ylabel='continuous curve MAE pixel');axs[0,1].legend()
 jj=load(M/'metrics/FIXED_CORRESPONDENCE_JACOBIAN.json')
 for g in GROUPS:axs[0,2].loglog([.001,.0001,.00001],[max(r['relative']for r in jj if r['group']==g and r['h']==h)for h in [.001,.0001,.00001]],'o-',label=g)
 axs[0,2].axhline(.001,c='red',ls='--');axs[0,2].invert_xaxis();axs[0,2].set(title='Fixed actual3D-correspondence AD vs FD',xlabel='normalized step; all6DoF',ylabel='max relativeJ error');axs[0,2].legend(fontsize=7)
 for g in GROUPS:
  v=next(v for v in vv if v['group']==g and v['role']=='FIT');tr=load(M/'optimization'/g/'A2'/v['id']/'TRACE.json');axs[1,0].plot(np.arange(len(tr)+1),[tr[0]['before']]+[a['after']for a in tr],'o-',label=g)
 axs[1,0].set(title='Actual representativeA2 TRF accepted objectives',xlabel='outer correspondence update',ylabel='recomputed objective');axs[1,0].legend(fontsize=7)
 count=[]
 for arm in ['S0','A1','A2','A3']:count.append(sum(r['new_local_pose']for r in rows if r['role']=='FIT'and r['method']==arm))
 axs[1,1].bar(['S0','A1','A2','A3'],count,color=[COL[a]for a in ['S0','A1','A2','A3']]);axs[1,1].axhline(81,c='black',ls='--');axs[1,1].set(title='Independent numeric outputs /81 FIT targets',ylabel='not physical accuracy');
 for i,n in enumerate(count):axs[1,1].text(i,n+1,str(n)+'/81',ha='center')
 axs[1,2].axis('off');axs[1,2].text(.02,.97,'Local numeric gates and real optimization: completed\n81 FIT x4 methods =324 routes\n254 numeric poses;70 Conics-init failures\n17HOLDOUT cameras stay unchanged\n\nPOST-RUN COMPLETENESS AUDIT FAILED\nOur added primitive-neighborhood filter\nremoves valid CAD silhouette spans.\n\nPhoto extension: NOT RUN\nNo HERO inference / body training / GT fitting.',va='top',fontsize=11)
 fig.suptitle('Figure1 | Mature reuse, actual numeric validation and full four-group execution\nLocal Jacobians/descent passing does not certify the incomplete CAD contour model.');fig.tight_layout(rect=[0,0,1,.92]);finish(fig,'Figure1_Actual_Validation_and_Runs.png')
 fig,axs=plt.subplots(4,5,figsize=(21,12))
 for i,g in enumerate(GROUPS):
  v=next(v for v in vv if v['group']==g and v['role']=='FIT');d=np.load(v['cache'])
  for j,arm in enumerate(methods):
   ax=axs[i,j];ax.imshow(d['RGB']);edge(ax,d['labels']==1,'lime');edge(ax,d['labels']==2,'cyan');ax.axis('off');r=next(r for r in rows if r['id']==v['id']and r['method']==arm);f=M/'evaluation'/g/(arm+'.npz')
   if r.get('Ring_IoU')is not None and f.exists():edge(ax,np.load(f)['ring_pred'],'black');text=f"{g} {arm} | RingIoU {r['Ring_IoU']:.3f}\nheldSIFT {r['SIFT_HELD']['MAE']:.2f}px"if r['SIFT_HELD']['N']else f'{g} {arm} | no heldSIFT'
   else:text=g+' '+arm+' | NaN / invalidConics initialization';ax.text(.02,.04,'NO PREDICTION / NO FALLBACK',color='red',fontsize=8,transform=ax.transAxes)
   ax.set_title(text,fontsize=9)
 fig.suptitle('Figure2 | Same real FIT image and metric camera for every method; fixed firstFIT representative\nGreen observedPolyp / cyan observedRing / black fullCAD projection. No GT or body in pose fitting. Missing Conics outputs are retained.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Figure2_Four_Group_Real_RGB_P0_S0_A1_A2_A3.png')
 fig=plt.figure(figsize=(16,13))
 for i,g in enumerate(GROUPS):
  ax=fig.add_subplot(2,2,i+1,projection='3d');group=next(a for a in groups if a['group']==g);cad=RenderedCAD(group['ring']['path']);ax.add_collection3d(Poly3DCollection(cad.V[cad.F],facecolors='black',edgecolors='none'));pts=[cad.V]
  vs=[v for v in vv if v['group']==g and v['role']=='FIT']
  for arm in methods:
   cs=[]
   for v in vs:
    r=load(M/'results'/g/arm/v['id']/'FINAL.json')
    if r.get('pose')is not None:cs.append(np.array(r['pose']))
   if not cs:continue
   cs=np.array(cs);ps=cs[:,:3,3];pts.append(ps);ax.scatter(*ps.T,c=COL[arm],s=13 if arm=='P0' else 9,label=f'{arm} {len(cs)}/{len(vs)}')
   for C in cs[::max(1,len(cs)//4)]:ax.quiver(*C[:3,3],*(C[:3,2]*1.5),color=COL[arm],linewidth=.5)
  p=np.r_[*pts];lo,hi=p.min(0),p.max(0);ax.set(xlim=(lo[0]-1,hi[0]+1),ylim=(lo[1]-1,hi[1]+1),zlim=(lo[2]-1,hi[2]+1),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title=g+' actual fixedRing + FIT camera estimates\nNo scale/ICP; eachgroup separate world');ax.set_box_aspect(hi-lo+2);ax.view_init(20,-65);ax.legend(fontsize=7)
 fig.suptitle('Figure3 | True metric camera positions and forward axes, original and refined\nAll physical motion bounds unchanged1.2mm/10deg. These are numeric candidates, not certified poses.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Figure3_Four_Group_Metric_Cameras.png')
 fig=plt.figure(figsize=(19,16));coverage=load(M/'metrics/RENDER_COVERAGE_CAUSAL_AUDIT.json');gap=load(M/'metrics/RENDER_COVERAGE_GAP_LOCATIONS.json')
 for i,g in enumerate(GROUPS):
  v=next(v for v in vv if v['group']==g and v['role']=='FIT');C=canon_np(np.array(v['T']));K=np.array(v['K']);d=np.load(v['cache']);cad=RenderedCAD(v['ring_path']);ss=cad.segments(C,K);cont=contours(np.isfinite(cast(cad.cad,K,C,360,640)));ax=fig.add_subplot(4,3,3*i+1);ax.imshow(d['RGB'])
  for key in ['inner','outer']:
   ax.scatter(*cont[key].T,s=1,c='white');u=projection(cad.V[ss[key]].reshape(-1,3),C,K)[0].reshape(-1,2,2)
   for line in u:ax.plot(*line.T,c='deepskyblue',lw=1)
  bad=next(r for r in gap if r['group']==g and r['key']=='outer');ax.scatter(*bad['rendered_boundary_pixel'],s=130,edgecolors='red',facecolors='none');ax.axis('off');ax.set_title(g+' white: rendered silhouette; blue: acceptedCAD\nRed: actual uncovered boundary pixel')
  ax=fig.add_subplot(4,3,3*i+2,projection='3d');ax.add_collection3d(Poly3DCollection(cad.V[cad.F],facecolors='black',edgecolors='none'))
  for key in ['inner','outer']:
   for X in cad.V[ss[key]]:ax.plot(*X.T,c='deepskyblue',lw=.8)
  X=np.array(bad['CAD_XYZ_mm']);ax.plot(*X.T,c='red',lw=4);ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title='Red: excluded nearestCAD candidate\n2D coverage evidence; visibility notGT');ax.set_box_aspect(np.ptp(cad.V,axis=0));ax.view_init(35,-65)
  ax=fig.add_subplot(4,3,3*i+3);x=np.arange(2)
  for off,variant,col in [(-.2,'ACTUAL_ACCEPTED','red'),(.2,'DIAGNOSTIC_RENDER_BAND_WITHOUT_PRIMITIVE_GATE','tab:blue')]:
   vals=[next(r for r in coverage if r['group']==g and r['key']==key and r['variant']==variant)['distance_px']['p95']for key in ['inner','outer']];ax.bar(x+off,vals,.4,label='actual model'if off<0 else'only diagnosis: no primitive gate',color=col)
  ax.set_xticks(x,['Inner','Outer']);ax.set_ylabel('render-to-CAD-curve p95 pixel');ax.set_title('Primitive ownership gate causes large gaps');ax.legend(fontsize=6)
 fig.suptitle('Figure4 | Independent renderer self-consistency FAILURE after real video comparison\nActual model p95 gaps4–10px; same rendering band without added primitive gate <0.91px. Diagnostic only: no sixth optimization arm or hidden replacement.');fig.tight_layout(rect=[0,0,1,.95]);finish(fig,'Figure4_Real_CAD_Completeness_Failure.png');save('runtime/FIGURES_COMPLETE.json',dict(epoch=time.time(),core_figures=4,photo_figures='NOT_RUN_VIDEO_COMPLETENESS_GATE'));print('FOUR_CORE_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':main()
