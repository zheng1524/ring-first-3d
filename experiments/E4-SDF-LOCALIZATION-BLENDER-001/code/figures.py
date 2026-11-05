from model import *
from renderer import Renderer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.collections import LineCollection
plt.rcParams.update({'font.size':9,'axes.titlesize':10})
def lines(ax,mask,col,known=None):
    cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE);seg=[]
    for co in cs:
        co=co[:,0]
        for a,b in zip(co,np.roll(co,-1,axis=0)):
            if known is None or known[a[1],a[0]]and known[b[1],b[0]]:seg.append([a,b])
    ax.add_collection(LineCollection(seg,colors=col,linewidths=1.2))
def draw(ax,V,F,title,cad,color='#72b0c9',values=None,vmin=-.4,vmax=.4,cmap='coolwarm',facecolors=None,alpha=1.):
    m=trimesh.Trimesh(V,F,process=False);shade=.65+.35*np.maximum(0,m.face_normals@np.array([.3,-.5,.8]));col=np.tile(matplotlib.colors.to_rgb(color),(len(F),1))
    if values is not None:col=plt.get_cmap(cmap)(np.clip((np.asarray(values)[F].mean(1)-vmin)/(vmax-vmin),0,1))[:,:3]
    if facecolors is not None:col=facecolors
    ax.add_collection3d(Poly3DCollection(V[F],facecolors=col*shade[:,None],edgecolors='none',linewidth=0,rasterized=True,alpha=alpha));ax.add_collection3d(Poly3DCollection(cad['V'][cad['F']],facecolors=(.03,.03,.03),edgecolors='none',rasterized=True));ax.set(xlim=(-6.6,6.6),ylim=(-6.6,6.6),zlim=(-.5,2.2),xlabel='X (mm)',ylabel='Y (mm)',zlabel='Z (mm)',title=title);ax.set_box_aspect([13.2,13.2,2.7]);ax.view_init(32,-70);ax.grid(False);ax.tick_params(labelsize=7,pad=0)
def image_colors(rgb):
    c=np.ones_like(rgb)*235;body=(rgb[:,:,0]>128)&(rgb[:,:,0]>rgb[:,:,1]);ring=rgb[:,:,1]>128;c[body]=[228,167,176];c[ring]=[15,15,15];return c
def savefig(fig,name):fig.savefig(R/'figures'/name,dpi=170,bbox_inches='tight',facecolor='white');plt.close(fig)
def main():
    renderer=Renderer();gt=np.load(R/'audit_only/TARGET_GT.npz');base=np.load(R/'inputs/BASE_SOURCE_MESH.npz');final=np.load(R/'local_results/FINAL/MODEL.npz');cad=dict(np.load(R/'inputs/RING_CAD.npz'));audit=load(R/'metrics/GEOMETRY_EVALUATION.json');hist=load(R/'metrics/FIT_HISTORY.json');gate=load(R/'metrics/PROJECTION_GATE.json')
    fig,axs=plt.subplots(5,3,figsize=(13,13))
    for row,c in enumerate(renderer.views):
        d=renderer.data[c['id']];q=np.load(R/'audit_only'/('TARGET__'+c['id']+'_PROJECTION_GATE.npz'));bg=image_colors(d['target_rgb']);m=next(x for x in gate['rows']if x['state']=='TARGET'and x['view']==c['id']);pred=renderer.project(scene(final['V'],final['F']),c['id'])[0]
        for ax in axs[row]:ax.imshow(bg);ys,xs=np.nonzero(q['Blender']|q['Ring_Blender']);ax.set(xlim=(max(0,xs.min()-10),min(639,xs.max()+10)),ylim=(min(359,ys.max()+10),max(0,ys.min()-10)));ax.set_aspect('equal');ax.tick_params(labelsize=6)
        axs[row,0].set_title(c['id'].split('_')[-1]+' | '+c['role']+'\nBlender target label render')
        lines(axs[row,1],q['Blender'],'#26bd43');lines(axs[row,1],q['pred'],'#b425f5');axs[row,1].set_title('GT Mesh reprojection gate\nIoU %.5f'%m['body_IoU']);lines(axs[row,2],q['Blender'],'#26bd43');lines(axs[row,2],pred,'#0078d6');axs[row,2].set_title('Frozen final prediction vs target\ngreen target / blue prediction')
    fig.suptitle('CONTROL EXPERIMENT | One static Blender scene, known metric cameras and black Ring CAD\nLabel colors changed for display only; no real RGB or anatomy certification',fontsize=12);fig.tight_layout(rect=[0,0,1,.95]);savefig(fig,'Fig1_Camera_Gate_And_Contours.png')
    rows=list(csv.DictReader((R/'metrics/CORRESPONDENCE_GT_AUDIT.csv').open()));fig=plt.figure(figsize=(15,9))
    for k,cid in enumerate(protocol()['fit_views']):
        ax=fig.add_subplot(2,3,k+1);d=renderer.data[cid];ax.imshow(image_colors(d['target_rgb']));lines(ax,d['target'],'#d12fff');rr=[r for r in rows if r['view']==cid];rank=sorted(rr,key=lambda r:float(r['seed_weight']),reverse=True);tail=rank[15:];rr=rank[:15]+tail[::max(1,len(tail)//10)][:10]
        for r in rr:
            uv=np.array(json.loads(r['uv']));tv=np.array(json.loads(r['target_uv']));co='#25a148'if r['inside_GT_support']=='True'else'#e67e00';ax.scatter(*uv,s=7,c=co);ax.annotate('',xy=tv,xytext=uv,arrowprops=dict(arrowstyle='->',color=co,lw=.8))
        ys,xs=np.nonzero(d['target']);ax.set(xlim=(xs.min()-15,xs.max()+15),ylim=(ys.max()+15,ys.min()-15),title=cid.split('_')[-1]+' | top 15 + 10 spread samples (no GT selection)\ngreen: GT support / orange: elsewhere');ax.set_aspect('equal')
        ax3=fig.add_subplot(2,3,k+4,projection='3d');colors=np.tile([.7,.7,.7],(len(base['F']),1));mask=gt['changed'][base['F']].sum(1)>=2;colors[mask]=[.95,.3,.3];draw(ax3,base['V'],base['F'],'Actual 3D points / translucent BASE for visibility',cad,facecolors=colors,alpha=.3)
        P=np.array([json.loads(r['P'])for r in rr]);good=np.array([r['inside_GT_support']=='True'for r in rr]);ax3.scatter(P[:,0],P[:,1],P[:,2],s=10,c=np.where(good,'#25a148','#e67e00'),depthshade=False);q=load(R/'metrics/MASK_ONLY_INITIALIZATION.json')['q'];ax3.scatter(*q[:3],c='black',marker='x',s=45);ax3.scatter(*gt['true_center_mm'],c='yellow',edgecolor='black',marker='*',s=75)
    fig.suptitle('2D nearest-contour arrows and actual 3D source points | red = GT edited support\nBlack X = Mask-only seed; yellow star = hidden GT center (revealed only after prediction freeze)',fontsize=12);fig.subplots_adjust(hspace=.28,wspace=.15,top=.88);savefig(fig,'Fig2_2D_3D_Correspondence_Audit.png')
    sur=np.load(R/'audit_only/FINAL_SURFACE_AUDIT.npz');fig=plt.figure(figsize=(15,10));ax=fig.add_subplot(231,projection='3d');draw(ax,gt['V'],gt['F'],'GT single local bulge (audit only)',cad,color='#dc919d');ax=fig.add_subplot(232,projection='3d');draw(ax,final['V'],final['F'],'Recovered official-DMTet zero mesh\nraw facets; no display smoothing',cad,color='#419ac4');colors=np.tile([.74,.74,.74],(len(base['F']),1));g=sur['GT_changed'][base['F']].sum(1)>=2;p=sur['actual_changed'][base['F']].sum(1)>=2;colors[g]=[.9,.2,.25];colors[p]=[.18,.45,.95];colors[g&p]=[.65,.2,.75];ax=fig.add_subplot(233,projection='3d');draw(ax,base['V'],base['F'],'Regions on common BASE surface\nred GT / blue recovered / purple overlap',cad,facecolors=colors)
    for k,(values,title,vmin,vmax)in enumerate([(sur['GT_displacement_mm'],'GT signed nearest-surface change (mm)',-.4,.4),(sur['actual_displacement_mm'],'Actual net signed surface change (mm)',-.4,.4),(sur['error_mm'],'Actual minus GT, same distance operator (mm)',-.35,.35)]):
        ax=fig.add_subplot(2,3,k+4,projection='3d');draw(ax,base['V'],base['F'],title,cad,values=values,vmin=vmin,vmax=vmax);fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(vmin,vmax),cmap='coolwarm'),ax=ax,shrink=.48,pad=.12,label='Signed motion (mm)')
    fig.suptitle('True meshes, GT vs actual update region, and physical displacement | Same metric camera and scale\nBottom maps use the common BASE mesh for correspondence; they are not replacement reconstruction meshes',fontsize=12);fig.subplots_adjust(top=.88,hspace=.35,wspace=.1);savefig(fig,'Fig3_GT_vs_Actual_Region_And_Motion.png')
    stages=audit['stages'];xx=np.arange(len(stages));labels=[s['stage']for s in stages];fig,axs=plt.subplots(2,3,figsize=(15,8));axs[0,0].plot(xx,[s['fit_IoU']for s in stages],'-o',label='FIT');axs[0,0].plot(xx,[s['holdout_IoU']for s in stages],'-o',label='HOLDOUT');axs[0,0].set(title='Full visible Mask IoU',ylabel='IoU');axs[0,1].plot(xx,[h['objective']if h['objective']is not None else np.nan for h in hist],'-o');axs[0,1].set(title='Mask-only optimization loss',ylabel='Frozen objective');axs[0,2].plot(xx,[s['parameter_center_error_mm']for s in stages],'-o',label='correction center');axs[0,2].plot(xx,[s['actual_update_centroid_error_mm']for s in stages],'-o',label='actual motion centroid');axs[0,2].axhline(.5,c='r',ls='--',label='frozen 0.5 mm');axs[0,2].set(title='3D localization error (audit only)',ylabel='mm')
    axs[1,0].plot(xx,[s['predicted_positive_peak_mm']for s in stages],'-o',label='actual positive peak');axs[1,0].axhline(stages[-1]['GT_peak_mm'],c='black',ls='--',label='GT peak');axs[1,0].set(title='Actual expansion, not raw SDF coefficient',ylabel='mm');axs[1,1].plot(xx,[s['wrong_region_displacement_mm']['p95']for s in stages],'-o',label='outside GT support p95');axs[1,1].axhline(.05,c='r',ls='--',label='frozen 0.05 mm');axs[1,1].set(title='Wrong-region motion (audit only)',ylabel='mm');axs[1,2].plot(xx,[s['quality']['normal_angle_deg']['p95']for s in stages],'-o',label='adjacent-normal p95');axs[1,2].axhline(stages[0]['quality']['normal_angle_deg']['p95']+5,c='r',ls='--',label='initial +5 deg');axs[1,2].set(title='Raw mesh roughness',ylabel='degrees')
    for ax in axs.ravel():
        ax.grid(alpha=.2);ax.set_xticks(xx,labels,rotation=25,ha='right',fontsize=7)
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=7)
    fig.suptitle('One fixed feasibility run; GT metrics computed after prediction freeze\nA higher Mask IoU does not certify correct 3D update location',fontsize=12);fig.tight_layout(rect=[0,0,1,.93]);savefig(fig,'Fig4_Roundwise_Mask_Localization_Roughness.png');print('FOUR_CORE_FIGURES_DONE',flush=True)
if __name__=='__main__':main()
