from common import *
from evaluate import pointcast,distance,area_samples
import ast
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import open3d as o3d
SRC=R.parents[1]/'code/figures.py'
for n in ast.parse(SRC.read_text()).body:
 if isinstance(n,ast.FunctionDef)and n.name in['actual_mesh_image','edge']:exec(compile(ast.get_source_segment(SRC.read_text(),n),str(SRC)+':reuse','exec'),globals())
COL={'P0':'#9a9a9a','B':'#2b7bba','E1':'#e79920','E2':'#24925c','E3':'#9b57b4'}
def output(fig,name,dpi=120):
 p=R/'figures'/name;p.parent.mkdir(exist_ok=True,parents=True);fig.savefig(p,dpi=dpi,bbox_inches='tight');plt.close(fig)
def path(case,arm,step=300):return R/'inputs'/case/'INITIAL.npz'if arm=='P0'else R/'local_results'/case/arm/('STEP_%04d.npz'%step)
def data(case,arm,step=300):return dict(np.load(path(case,arm,step)))
def gt(case):return dict(np.load(OLD/'audit_only/NATIVE_CAD_GT.npz'if case=='virtual_IIa'else R/'audit_only'/case/'GT.npz'))
def project(P,K,T):
 q=(P-T[:3,3])@T[:3,:3]@K.T;return q[:,:2]/q[:,2:]
def rawview(ax,c,a,s=300,angle=(25,-65)):
 o=data(c,a,s);p0=data(c,'P0');cad=np.load(R/'inputs'/c/'RING.npz');im,px=actual_mesh_image(o['V'],o['F'],cad['V'],cad['F'],p0['V'],*angle,COL[a]);ax.imshow(im);ax.plot([20,20+2*px],[375,375],c='black',lw=2);ax.text(20,365,'2mm at viewer-center',fontsize=6);ax.axis('off')
def field3d(ax,V,vectors,color,title,gain):
 norms=np.linalg.norm(vectors,axis=1);maximum=float(norms.max());gain=.5/max(maximum,1e-15);valid=np.flatnonzero(norms>1e-12);ids=valid[np.argsort(norms[valid])[-40:]]if len(valid)else valid
 ax.scatter(V[::max(1,len(V)//1200),0],V[::max(1,len(V)//1200),1],V[::max(1,len(V)//1200),2],s=.3,c='#aaaaaa',alpha=.35)
 if len(ids):ax.quiver(*V[ids].T,*(vectors[ids]*gain).T,color=color,length=1,normalize=False,linewidth=.7)
 ax.set_title(title+f'\nmax raw {maximum:.3g}mm; display gain {gain:.1f}',fontsize=8);ax.set(xlabel='X mm',ylabel='Y mm',zlabel='Z mm');ax.view_init(25,-65);ax.set_box_aspect(np.maximum(np.ptp(V,axis=0),.1))
def main():
 assert load(R/'assets_index/PREDICTIONS_FROZEN.json')['all_expected_finals'];cfg=load(R/'config/PROTOCOL.json');ends=load(R/'metrics/ENDPOINTS.json');summary=load(R/'metrics/SUMMARY.json');shapes=load(R/'metrics/SHAPE.json');sections=load(R/'metrics/SECTIONS.json');fig,axs=plt.subplots(6,5,figsize=(17,19))
 for i,c in enumerate(cfg['cases']):
  for j,a in enumerate(['P0','B','E1','E2','E3']):
   ax=axs[i,j];rawview(ax,c,a);rec=next(x for x in ends if x['case']==c and x['arm']==a);ax.set_title(c+' | '+a+'\nRing '+str(rec['Ring_collision'])+' / self '+str(rec['self_FCL_N'])+('+'if rec['self_FCL_N']>=256 else'')+' | hold IoU %.3f'%rec['holdout_IoU'],fontsize=8)
   if c.startswith('virtual'):
    g=gt(c);p0=data(c,'P0');rr=np.load(R/'inputs'/c/'RING.npz');gi,_=actual_mesh_image(g['V'],g['F'],rr['V'],rr['F'],p0['V'],25,-65,'#d47878');ins=ax.inset_axes([.67,.66,.32,.32]);ins.imshow(gi);ins.axis('off');ins.set_title('Blender GT',fontsize=5)
 fig.suptitle('D2 | six frozen cases | P0 / B / E1 uniform absolute / E2 boundary weighted / E3 plus relative\nActual unmodified Meshes at fixed step300; black Ring CAD; same viewer and mm scale within each case. GT inset: posterior only.\nVirtual depths = IDEAL_GT_DEPTH_UPPER_BOUND; real cameras retain original qualifications. Self256+ = checked lower bound.',fontsize=11);fig.tight_layout(rect=[0,0,1,.95]);output(fig,'FigA_Six_Case_Final_Comparison.png')
 # Full requested evolution, independent complete figure for every case, no chosen best checkpoint.
 for c in cfg['cases']:
  fig,axs=plt.subplots(4,5,figsize=(16,12))
  for i,a in enumerate(cfg['arms']):
   for j,step in enumerate([0,50,100,200,300]):
    rawview(axs[i,j],c,'P0'if step==0 else a,step);axs[i,j].set_title(f'{a} | step{step}',fontsize=9)
  fig.suptitle(c+' | actual Mesh evolution, same viewer / black CAD / no repairs\n0 / 50 / 100 / 200 / 300; virtual GT and depth metrics are independent of this display');fig.tight_layout(rect=[0,0,1,.94]);output(fig,'full/FigA_'+c+'_Evolution.png')
 # True gradient and momentum update, fixed predeclared steps 50 and 300.
 mechanism=[]
 fig=plt.figure(figsize=(19,12))
 for i,c in enumerate(['virtual_IIa','real_Ip','real_Is']):
  me=np.load(R/'local_results'/c/'E3/MECHANISM_0050.npz');cid=str(me['views'][0]);d=np.load(R/'inputs'/c/(cid+'.npz'));V=me['before_V'];F=me['F'];p0=data(c,'P0');scale=float(abs(p0['V']-p0['V'].mean(0)).max());rr=np.load(R/'inputs'/c/'RING.npz');cz=cast(scene(rr['V'],rr['F']),d['K'],d['T'],360,640);z=cast(scene(V,F),d['K'],d['T'],360,640);pred=np.isfinite(z)&(z<cz);target=d['labels']==1
  ax=fig.add_subplot(3,5,i*5+1);ax.imshow(d['RGB']);edge(ax,target,'lime');edge(ax,pred,'magenta');ax.set_title(c+' | E3 pre-step50\nRGB/labels, target green/pred purple',fontsize=8);ax.axis('off')
  ax=fig.add_subplot(3,5,i*5+2);error=np.zeros((360,640,3));error[target&~pred]=[.1,.65,.1];error[pred&~target]=[.9,.1,.1];ax.imshow(error);ax.set_title('Actual missing green / outside red\nfull original Mask denominator',fontsize=8);ax.axis('off')
  sil=-me['silhouette_gradient_per_mm']*scale**2;actual=me['actual_displacement_mm'];norm=np.linalg.norm(sil,axis=1);ids=np.argsort(norm)[-40:];uv=project(V,d['K'],d['T']);delta=project(V+sil*20,d['K'],d['T'])-uv;ax=fig.add_subplot(3,5,i*5+3);ax.imshow(d['RGB']);edge(ax,pred,'magenta');ax.quiver(uv[ids,0],uv[ids,1],delta[ids,0],delta[ids,1],color='yellow',angles='xy',scale_units='xy',scale=1);ax.set(xlim=(0,640),ylim=(360,0));ax.set_title('Computed silhouette-only -gradient\nno-momentum SGD displacement, x20',fontsize=8);ax.axis('off')
  ax=fig.add_subplot(3,5,i*5+4,projection='3d');field3d(ax,V,sil,'orange','Same 3D silhouette gradient locations',20)
  ax=fig.add_subplot(3,5,i*5+5,projection='3d');field3d(ax,V,actual,'#6849a4','Actual SGD displacement incl momentum',20)
  for step in[1,50,100,200,300]:
   mm=np.load(R/'local_results'/c/'E3'/('MECHANISM_%04d.npz'%step));g=mm['silhouette_gradient_per_mm'];ab=mm['absolute_gradient_per_mm'];rel=mm['relative_gradient_per_mm'];a=g.reshape(-1);b=ab.reshape(-1);cos=float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)))if np.linalg.norm(a)*np.linalg.norm(b)>0 else None;den=np.linalg.norm(g,axis=1)*np.linalg.norm(ab,axis=1);active=den>1e-18;cs=np.sum(g*ab,axis=1)[active]/den[active];mechanism.append(dict(case=c,step=step,silhouette_absolute_global_cosine=cos,vertex_joint_nonzero_N=int(active.sum()),vertex_supportive_N=int((cs>0).sum()),vertex_conflict_N=int((cs<0).sum()),silhouette_gradient_norm=float(np.linalg.norm(g)),absolute_gradient_norm=float(np.linalg.norm(ab)),relative_gradient_norm=float(np.linalg.norm(rel)),actual_displacement_max_mm=float(np.linalg.norm(mm['actual_displacement_mm'],axis=1).max()),no_momentum_term_sum_displacement_mm_norm=float(np.linalg.norm(-(g+ab+rel+mm['prior_gradient_per_mm'])*scale**2)),actual_momentum_displacement_mm_norm=float(np.linalg.norm(mm['actual_displacement_mm']))))
 fig.suptitle('Fig B | error -> actual computed gradient -> executed update; E3 fixed pre-step50\n3D arrows use original Mesh vertex IDs. 2D arrows x20; 3D arrows normalized to max 0.5mm for display with gain stated. Raw mm vectors saved.\nSilhouette gradient is joint sampled FIT views at this step; displayed RGB is one fixed FIT view.',fontsize=11);fig.tight_layout(rect=[0,0,1,.92]);output(fig,'FigB_Contour_Gradient_Actual_Update.png');table('metrics/MECHANISM_DIAGNOSTICS.csv',mechanism)
 fig=plt.figure(figsize=(24,13))
 for i,c in enumerate(['virtual_IIa','real_Ip','real_Is']):
  me=np.load(R/'local_results'/c/'E3/MECHANISM_0050.npz');cid=str(me['views'][0]);d=np.load(R/'inputs'/c/(cid+'.npz'));ob=np.load(R/'depth_observations'/(cid+'.npz'));V=me['before_V'];F=me['F'];p0=data(c,'P0');scale=float(abs(p0['V']-p0['V'].mean(0)).max());ray=np.c_[ob['uv'],np.ones(len(ob['uv']))]@np.linalg.inv(ob['K']).T;X=(ray*ob['z'][:,None])@ob['T'][:3,:3].T+ob['T'][:3,3];_,_,zz=pointcast(scene(V,F),X,ob['K'],ob['T']);uv=ob['RGB_uv'];cad=np.load(R/'inputs'/c/'RING.npz');_,_,cz=pointcast(scene(cad['V'],cad['F']),X,ob['K'],ob['T']);hit=np.isfinite(zz)&(zz>0)&(zz<cz-.05);pair=ob['pairs'];good=hit[pair[:,0]]&hit[pair[:,1]];pairerr=(zz[pair[:,0]]-zz[pair[:,1]])-(ob['z'][pair[:,0]]-ob['z'][pair[:,1]])
  for j in range(5):
   ax=fig.add_subplot(3,8,i*8+j+1);ax.imshow(d['RGB']);ax.axis('off')
   if j==0:q=ax.scatter(uv[:,0],uv[:,1],c=ob['z'],s=6,cmap='viridis');title=c+'\n'+('IDEAL GT depth'if c.startswith('virtual')else'HERO axial depth')+' mm'
   elif j==1:q=ax.scatter(uv[hit,0],uv[hit,1],c=zz[hit],s=6,cmap='viridis');title='Current first Mesh depth mm'
   elif j==2:q=ax.scatter(uv[hit,0],uv[hit,1],c=(zz-ob['z'])[hit],s=7,cmap='coolwarm',vmin=-2,vmax=2);title='Mesh - observed mm\ncolor clipped +/-2'
   elif j==3:q=ax.scatter(uv[:,0],uv[:,1],c=ob['boundary_weight'],s=7,cmap='viridis',vmin=0,vmax=1);title='E2 fixed boundary weight\nsame candidate IDs / Mask intact'
   else:
    ids=np.flatnonzero(good)[::max(1,int(good.sum())//24)];q=None
    for k in ids:
     p=uv[pair[k]];ax.plot(p[:,0],p[:,1],c=plt.cm.coolwarm(np.clip(pairerr[k]/4+.5,0,1)),lw=.8)
    title='E3 actual fixed same-view pairs\nrelative residual clipped +/-2mm'
   ax.set_title(title,fontsize=8)
   if q is not None:fig.colorbar(q,ax=ax,fraction=.035,pad=.01)
  for j,key,label,col in[(5,'absolute_gradient_per_mm','Absolute depth only','orange'),(6,'relative_gradient_per_mm','Relative depth only','green'),(7,'actual_displacement_mm','Executed total + momentum','#6849a4')]:
   ax=fig.add_subplot(3,8,i*8+j+1,projection='3d');vec=me[key]if j==7 else-me[key]*scale**2;field3d(ax,V,vec,col,label,20)
 fig.suptitle('Fig C | fixed E3 pre-step50 depth mechanism, native rays and raw gradient arrays\nSparse observations only, no fabricated dense interpolation. Gradients include frozen .01 loss weights. Final column is actual mixed SGD+momentum update.\nVirtual = ideal-depth upper bound, never called HERO. Point pairs and weights were frozen before any optimization.',fontsize=11);fig.tight_layout(rect=[0,0,1,.93]);output(fig,'FigC_Depth_Weights_Pairs_Gradients.png')
 fig,axs=plt.subplots(3,5,figsize=(21,12))
 for i,c in enumerate(['virtual_Ip','virtual_Is','virtual_IIa']):
  g=gt(c);gp=area_samples(g['V'],g['F']);grt=scene(g['V'],g['F']);mgt=trimesh.Trimesh(g['V'],g['F'],process=False)
  for j,a in enumerate(['B','E1','E2','E3']):
   m=data(c,a);err=distance(scene(m['V'],m['F']),gp);ax=axs[i,j];sc=ax.scatter(gp[:,0],gp[:,2],c=err,cmap='magma',s=1,vmin=0,vmax=2);ax.set_aspect('equal',adjustable='box');ax.set(xlabel='GT X mm',ylabel='GT Z mm');ss=next(x for x in shapes if(x['case'],x['arm'],x['step'],x['region'])==(c,a,300,'top'));rec=next(x for x in ends if x['case']==c and x['arm']==a);ax.set_title(c+' | '+a+'\nGT->Mesh error; height %.2f/GT %.2f mm\nChamfer %.3f mm, solid valid %s'%(ss['maximum_height_mm'],ss['GT_maximum_height_mm'],rec['Chamfer_MAE_mm'],rec['solid_geometry_valid']),fontsize=8)
  ax=axs[i,4]
  for a in['B','E1','E2','E3']:
   ss=[x for x in sections if x['case']==c and x['arm']==a];ax.plot([x['prediction_raw_proxy_area_mm2']for x in ss],[x['z_mm']for x in ss],c=COL[a],label=a)
  ss=[x for x in sections if x['case']==c and x['arm']=='B'];ax.plot([x['GT_section_area_mm2']for x in ss],[x['z_mm']for x in ss],'--',c='black',label='GT');ax.set(xlabel='raw section area proxy mm2',ylabel='Z mm',title='Same world-height section curves\nself-intersection: area proxy only');ax.legend(fontsize=7);ax.grid(alpha=.2)
 fig.subplots_adjust(right=.93);cb=fig.add_axes([.945,.25,.008,.45]);fig.colorbar(sc,cax=cb,label='GT surface distance to Mesh, mm; clipped at 2');
 fig.suptitle('Fig D | independent native Blender GT shape audit after all predictions frozen\nSame 6000 GT samples, surface distance in mm; height uses original Blender base Z=0, never P0 volume as truth.\nNative Ip/Is and all virtual predictions self-intersect: volume NOT_EVALUABLE; closed-loop section curves are diagnostic area proxies, no fixes.',fontsize=11);fig.tight_layout(rect=[0,0,.92,.91]);output(fig,'FigD_Virtual_GT_Surface_And_Height.png')
 # Detailed scalar stage curves and virtual old C/D references, explicitly historical unequal conditions.
 fig,axs=plt.subplots(2,3,figsize=(16,8))
 for i,c in enumerate(cfg['cases']):
  ax=axs.ravel()[i]
  for a in cfg['arms']:
   rr=[x for x in summary if x['case']==c and x['arm']in['P0',a]];ax.plot([x['step']for x in rr],[x['Chamfer_MAE_mm']if c.startswith('virtual')else x['holdout_depth_MAE_mm']for x in rr],'-o',c=COL[a],label=a)
  ax.set(title=c,xlabel='step',ylabel='GT Chamfer mm'if c.startswith('virtual')else'conditional heldout HERO MAE mm');ax.legend();ax.grid(alpha=.2)
 fig.tight_layout();output(fig,'full/Stage_3D_And_Depth_Curves.png')
 save('assets_index/VISUALIZATION_SOURCE.json',dict(reused_helpers=asset(SRC),raw_Mesh=True,postprocess=False,view=(25,-65),same_scale_rule='existing helper P0+Ring fixed viewer',gradient_snapshots='MECHANISM_0050 and 1/100/200/300 metrics; arrays from actual training autograd',arrow_gain='2D x20; 3D .5mm/max actual vector norm, per-panel gain annotated',momentum_distinguished=True))
 print('FOUR_CORE_FIGURE_CLASSES_DONE')
if __name__=='__main__':main()
