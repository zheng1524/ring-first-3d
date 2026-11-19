"""Actual meshes, measured correspondences, gradient proposals and real displacements."""
from visual_base import *
from matplotlib.lines import Line2D
OLD15=REPO/'experiments/TASK-E4-MULTIVIEW-INIT-STALK-015'

def model(path):return dict(np.load(path))
def axes_mesh(ax,n,z,bounds,angle=(20,-65),color=(.6,.6,.6,.5)):
 f=z.get('F_solid',z['F']);ax.add_collection3d(Poly3DCollection(z['V'][f],facecolors=color,edgecolors='none'));rg=np.load(R/'inputs'/n/'RING.npz');ax.add_collection3d(Poly3DCollection(rg['V'][rg['F']],facecolors='black',edgecolors='none'));c=(bounds.min(0)+bounds.max(0))/2;d=np.ptp(bounds,axis=0).max()*.52
 ax.set(xlim=(c[0]-d,c[0]+d),ylim=(c[1]-d,c[1]+d),zlim=(c[2]-d,c[2]+d));ax.set_box_aspect((1,1,1));ax.view_init(*angle);ax.tick_params(labelsize=6)

def main():
 assert(R/'metrics/NATIVE_AND_GEOMETRY.json').exists();cases=load(R/'config/CASE_LOCK.json');audit={x['case']:x for x in load(R/'metrics/VIEW_SAMPLING_AUDIT.json')};inv=load(R/'metrics/VIEW_SELECTION_AND_WEIGHTS.json');sel=load(R/'config/VIEW_SELECTION_016.json');reg=load(R/'config/RUN_REGISTRY.json');native=load(R/'metrics/NATIVE_AND_GEOMETRY.json')
 fig,ax=plt.subplots(11,4,figsize=(18,30))
 for i,c in enumerate(cases):
  n=c['name'];rr=[x for x in inv if x['case']==n];D=np.array([x['direction']for x in rr]);mean=D.mean(0);mean/=np.linalg.norm(mean);u=np.cross(mean,[0,0,1.]);u/=max(1e-15,np.linalg.norm(u));v=np.cross(mean,u);xx=np.degrees(np.arctan2(D@u,D@mean));yy=np.degrees(np.arctan2(D@v,D@mean))
  for j,key in enumerate(['old','balanced']):
   a=ax[i,j];a.scatter(xx,yy,s=7,c='lightgray');ids=np.array([x['selected_'+key]for x in rr]);weight=np.array([x['weight_'+key]for x in rr]);a.scatter(xx[ids],yy[ids],s=30+200*weight[ids],c=[x['direction_block']for x in np.array(rr,dtype=object)[ids]],cmap='tab10',edgecolors='black',linewidths=.3);cov=audit[n][key];a.set_title(n+' '+key+' N%d; span %.1fdeg'%(cov['N'],cov['max_span_deg']),fontsize=8);a.set_aspect('equal',adjustable='datalim');a.tick_params(labelsize=6);a.grid(alpha=.2)
  paths=[next(x['final']for x in reg if x['case']==n and x['tag']==t)for t in ['S0_015','S1_BALANCED']];mm=[model(p)for p in paths];rg=np.load(R/'inputs'/n/'RING.npz');bounds=np.r_[mm[0]['V'],mm[1]['V'],rg['V']]
  for j,z in enumerate(mm):model_panel(ax[i,j+2],n,z,bounds);ax[i,j+2].set_title(['015 original selection','016 quota-balanced'][j],fontsize=8)
 fig.suptitle('All11 | single-video direction coverage and actual S0/S1 meshes\nGray available cameras; colored selected direction blocks; size=optimization weight. Same per-case native mm and black CAD. Angular tangent-plane coordinates, not time.',fontsize=11);fig.subplots_adjust(top=.955,hspace=.35,wspace=.18);finish(fig,'Fig1_All11_Direction_Balance_And_Meshes.png',105)
 fig=plt.figure(figsize=(20,10))
 for i,n in enumerate(['G03','G01']):
  root=R/'arms/DIAGNOSTIC';t=np.load(root/'metrics'/(n+'_CAUSAL_TAPE.npz'));corr=load(root/'metrics'/(n+'_CORRESPONDENCES.json'));cid=sel[n]['OLD'][0];a=np.load(R/'inputs'/n/(cid+'.npz'));cc=[x for x in corr if x['view']==cid];cc=sorted(cc,key=lambda x:-x['residual_px'])[:16];z=dict(V=t['V'],F=t['F'],F_solid=t['F_solid']);rg=np.load(R/'inputs'/n/'RING.npz');bounds=np.r_[t['V'],rg['V']]
  ax=fig.add_subplot(2,4,i*4+1);ax.imshow(a['RGB']);edge(ax,a['labels']==1,'lime');edge(ax,a['labels']==2,'cyan')
  for x in cc:
   p=np.array(x['predicted_uv']);target=np.array(x['target_uv']);ax.annotate('',xy=target,xytext=p,arrowprops=dict(arrowstyle='->',color='orange',lw=.8))
  ax.axis('off');ax.set_title(n+' real FIT: actual nearest-contour residuals',fontsize=9)
  ax=fig.add_subplot(2,4,i*4+2,projection='3d');direction=a['T'][:3,3]-t['V'].mean(0);elev=float(np.degrees(np.arcsin(direction[2]/np.linalg.norm(direction))));azim=float(np.degrees(np.arctan2(direction[1],direction[0])));axes_mesh(ax,n,z,bounds,angle=(elev,azim));pp=np.array([x['world_point_mm']for x in cc]);ax.scatter(*pp.T,color='red',s=14,depthshade=False);ax.set_title('Actual 3D contour points / original IDs\nViewed along source-camera direction',fontsize=8)
  actual=np.load(root/'metrics'/(n+'_OLD_B_FIRST_ACTUAL_TAPE.npz'));ax=fig.add_subplot(2,4,i*4+3,projection='3d',computed_zorder=False);image=sum(actual[k]for k in ['silhouette','missing','extra','contour']);depth=actual['absolute']+actual['relative'];prior=actual['prior'];full=image+depth+prior;scale=.2/max(1e-30,np.linalg.norm(full,axis=1).max());center=t['V'][np.linalg.norm(full,axis=1).argmax()];near=np.linalg.norm(t['V']-center,axis=1)<1.5;faces=t['F_solid'][near[t['F_solid']].any(1)];ax.add_collection3d(Poly3DCollection(t['V'][faces],facecolors=(.7,.7,.7,.12),edgecolors=(.5,.5,.5,.25),linewidths=.3,zorder=0));ix=np.flatnonzero(near);ix=ix[np.argsort(np.linalg.norm(full[ix],axis=1))[-12:]];ax.set_box_aspect((1,1,1));ax.view_init(20,-65);ax.tick_params(labelsize=6)
  for g,col in [(image,'green'),(depth,'blue'),(prior,'orange')]:
   d=-scale*g[ix];ax.quiver(*t['V'][ix].T,*d.T,color=col,linewidth=1.2,arrow_length_ratio=.3,zorder=20)
  ax.set(xlim=(center[0]-1,center[0]+1),ylim=(center[1]-1,center[1]+1),zlim=(center[2]-1,center[2]+1));ax.set_title('Actual attempt1 gradients; local diagnostic crop\ngreen=image / blue=depth / orange=prior\nOriginal local triangles; overlay, not optimizer motion',fontsize=8)
  p=OLD15/'arms/Stalk-B/local_results'/n/'FINAL.npz';zz=model(p);bb=np.r_[bounds,zz['V']];ax=fig.add_subplot(2,4,i*4+4,projection='3d');axes_mesh(ax,n,zz,bb,color=(.4,.25,.7,.7));d=zz['V']-t['V'];ix=np.argsort(np.linalg.norm(d,axis=1))[-16:];ax.quiver(*t['V'][ix].T,*d[ix].T,color='magenta',linewidth=.6,arrow_length_ratio=.15);ax.set_title('Actual accumulated 015-B displacement\nmax %.4f mm'%np.linalg.norm(d,axis=1).max(),fontsize=9)
 fig.suptitle('Residual → original face/vertex → measured loss gradient → actual geometry\nAll arrays retain source IDs. Gradient proposal and momentum optimizer displacement are separate quantities.',fontsize=12);fig.subplots_adjust(top=.90,hspace=.15,wspace=.08);finish(fig,'Fig2_Residual_Gradient_Displacement_Causality.png',135)
 fig=plt.figure(figsize=(19,10))
 for i,n in enumerate(['G03','G01']):
  z=np.load(R/'local_results'/(n+'_RING_WITNESSES.npz'));bounds=np.r_[z['V0'],z['V1'],z['Vfixed'],z['ringV']];trials=load(R/'arms/DIAGNOSTIC/metrics'/(n+'_SHADOW_UPDATES.json'))
  for j,key in enumerate(['V0','V1','Vfixed']):
   ax=fig.add_subplot(2,4,i*4+j+1,projection='3d');m=dict(V=z[key],F=z['F']);axes_mesh(ax,n,m,bounds);p=z['witness_before'];d=z['witness_after']-p
   if j==1:ax.scatter(*z['witness_after'].T,color='red',s=8,depthshade=False);ax.quiver(*p.T,*d.T,color='red',linewidth=.7,arrow_length_ratio=.25)
   text=['Current body','Full-gradient candidate','Contact faces fixed'][j]
   if j:
    q=next(x for x in trials if x['direction']=='FULL'and x['mode']==('ORIGINAL'if j==1 else'CONTACT_FACE_FIXED')and x['alpha']==1.);text+='\n'+(','.join(q['geometry_reasons'])or'Guard passed')+'\nDelta L %.6f'%q['full_objective_change']
   ax.set_title(n+' '+text,fontsize=8)
  a=load(R/'metrics'/(n+'_RING_WITNESS_ATTRIBUTION.json'))[0];val=a['predicted_component_normal_motion_mm'];ax=fig.add_subplot(2,4,i*4+4);keys=list(val);ax.barh(keys,[val[k]for k in keys],color=['red'if val[k]<0 else'green'for k in keys]);ax.axvline(0,color='black',lw=.7);ax.set_xlabel('mm along CAD outward normal');ax.tick_params(labelsize=7);ax.set_title('Worst witness: component-induced normal motion\nNegative pushes toward Ring; same full-step scale',fontsize=8)
 fig.suptitle('Fixed-budget noncommitted shadow test | actual CAD and original triangles\nFreezing a contact-face coordinate subspace can retain a feasible descent direction. The complete original GeometryGuard remains active.',fontsize=12);fig.subplots_adjust(top=.87,bottom=.08,wspace=.25,hspace=.42);finish(fig,'Fig3_Ring_Contact_Rejected_And_Feasible_Directions.png',135)
 fig,ax=plt.subplots(6,3,figsize=(15,24))
 for i,n in enumerate(['G03','G01']):
  paths=[OLD15/'arms/Init-A/local_results'/n/'FINAL.npz',OLD15/'arms/Stalk-B/local_results'/n/'FINAL.npz',R/'arms/MECH_COHERENT/local_results'/n/'FINAL.npz'];mm=[model(p)for p in paths];rg=np.load(R/'inputs'/n/'RING.npz');bounds=np.r_[*[m['V']for m in mm],rg['V']]
  for k,angle in enumerate([(20,-65),(0,90)]):
   for j,m in enumerate(mm):model_panel(ax[2*i+k,j],n,m,bounds,angle=angle);ax[2*i+k,j].set_title(n+' '+['Same shared start','015 Stalk-B','016 contact+Sobolev'][j]+' / '+str(angle),fontsize=9)
 n='virtual_Ip';vr=load(R/'config/VIRTUAL_RUN_REGISTRY.json');mm=[model(x['final'])for x in vr];rg=np.load(R/'inputs'/n/'RING.npz');bounds=np.r_[*[m['V']for m in mm],rg['V']]
 for j,m in enumerate(mm):model_panel(ax[4,j],n,m,bounds);ax[4,j].set_title(vr[j]['tag']+' / virtual fixed control',fontsize=9)
 gp=load(R/'metrics/VIRTUAL_NATIVE_PROJECTION_GATE.json')['GT_source']['path'];gt=model(gp);p0=model(R/'inputs/virtual_Ip/INITIAL.npz');last=[gt,p0,mm[2]];gb=np.r_[bounds,gt['V']]
 for j,m in enumerate(last):model_panel(ax[5,j],n,m,gb,angle=(0,90));ax[5,j].set_title(['Virtual GT (surface-only; self intersections)','Same independent P0','V3 coherent after5 accepted updates'][j],fontsize=8)
 fig.suptitle('Same Mesh / cameras / loss / budget in the real mechanism pair\nActual surfaces, no smoothing, trimming or reconstruction substitution. Black CAD, native mm. Virtual controls use one versus three known cameras.',fontsize=12);fig.subplots_adjust(top=.94,hspace=.17,wspace=.03);finish(fig,'Fig4_Actual_Geometry_Update_Strategy_Comparison.png',120)
 print('FOUR_CAUSAL_FIGURES_COMPLETE',flush=True)
if __name__=='__main__':main()
