"""Actual extracted surfaces and real RGB. No geometry postprocessing."""
from field import *
from data import Data
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.collections import LineCollection
plt.rcParams.update({'font.size':9,'axes.titlesize':10})
def stage(name):return dict(np.load(R/'local_results'/name/'FIELD.npz'))
def draw_mesh(ax,V,F,color,cad,bounds,angle=(25,-65),face_colors=None,title=''):
    m=trimesh.Trimesh(V,F,process=False);light=np.array([.3,-.4,.85]);sh=.55+.45*np.maximum(0,m.face_normals@light);base=np.asarray(matplotlib.colors.to_rgb(color));colors=base[None,:]*sh[:,None]if face_colors is None else np.asarray(face_colors)[:,:3]*sh[:,None]
    body=Poly3DCollection(V[F],facecolors=colors,edgecolors='none',linewidth=0,rasterized=True);ax.add_collection3d(body)
    ring=Poly3DCollection(cad.vertices[cad.faces],facecolors=(.035,.035,.035),edgecolors='none',linewidth=0,rasterized=True);ax.add_collection3d(ring)
    lo,hi=bounds;ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]),xlabel='X (mm)',ylabel='Y (mm)',zlabel='Z (mm)',title=title);ax.set_box_aspect(hi-lo);ax.view_init(*angle);ax.tick_params(labelsize=7,pad=0);ax.grid(False)
def polyline(ax,mask,color,label=None,known=None):
    cs,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
    segments=[]
    for co in cs:
        co=co[:,0,:].astype(float)
        for a,b in zip(co,np.roll(co,-1,axis=0)):
            if known is None or (known[int(a[1]),int(a[0])]and known[int(b[1]),int(b[0])]):segments.append([a,b])
    ax.add_collection(LineCollection(segments,colors=color,linewidths=1.15,label=label))
def savefig(fig,name):fig.savefig(R/'figures'/name,dpi=165,facecolor='white',bbox_inches='tight');plt.close(fig)
def main():
    data=Data();middle=load(R/'metrics/MIDDLE.json')['stage'];names=['INITIAL',middle,'FINAL'];S=[stage(n)for n in names];cad=ringmesh('G01_004');p=np.vstack([cad.vertices,S[0]['V']]);lo=p.min(0)-.7;hi=p.max(0)+.7;center=(lo+hi)/2;half=max(hi-lo)/2;bounds=(center-half,center+half)
    figs,axs=plt.subplots(2,3,figsize=(14,9),subplot_kw={'projection':'3d'})
    for row,angle in enumerate([(25,-65),(8,40)]):
        for k,(name,q)in enumerate(zip(names,S)):
            meta=load(R/'metrics'/(name+'.json'));draw_mesh(axs[row,k],q['V'],q['F'],['#8395ac','#4ba895','#3486c7'][k],cad,bounds,angle,title='%s | V=%.1f mm3\nCAD gap %.4f mm'%(name,meta['volume_mm3'],meta['Ring']['distance_mm']))
    figs.suptitle('G01_004 | Actual SDF zero meshes; identical world scale and cameras\nBlack = unchanged Ring CAD; raw facets, no mesh smoothing; camera eligibility conditional',fontsize=12);figs.subplots_adjust(top=.87,wspace=.12,hspace=.42);savefig(figs,'Fig1_Actual_SDF_Evolution.png')
    # Full original RGB coordinates; crop display only, identical across the row.
    fig,axs=plt.subplots(7,3,figsize=(13,19));full=load(R/'metrics/FULL_ORIGINAL_MASK_METRICS.json')
    for row,cid in enumerate(data.ids):
        s=source(cid);ym,xm=np.nonzero(s['labels']>0);xmin=max(0,xm.min()-25);xmax=min(639,xm.max()+25);ymin=max(0,ym.min()-25);ymax=min(359,ym.max()+25)
        for k,name in enumerate(names):
            ax=axs[row,k];q=np.load(R/'local_results'/name/(cid+'_FULL_PROJECTION.npz'));ax.imshow(s['RGB']);polyline(ax,s['labels']==1,'#25df54',known=q['known']);polyline(ax,q['pred'],'#ff35bf',known=q['known']);polyline(ax,s['labels']==2,'#ffe000');unknown=q['pred']&~q['known'];ax.set(xlim=(xmin,xmax),ylim=(ymax,ymin));ax.set_aspect('equal');ax.tick_params(labelsize=6);m=next(x for x in full if x['source']==cid and x['stage']==name);ax.set_title('%s | %s\nfull Mask IoU %.3f'%(cid.removeprefix('G01_004_'),name,m['full_original_IoU']));
            if k==0:ax.set_ylabel('FIT'if cid in data.fit else'UPDATE HOLDOUT',fontweight='bold')
    fig.suptitle('Actual RGB and frozen full Polyp Mask (green), SDF silhouette (magenta), Ring Mask (yellow)\nSymmetric CAD/Ring UNKNOWN omitted from contour forces; holdout had historical P0 initialization exposure',fontsize=11,y=1.005);fig.tight_layout();savefig(fig,'Fig2_Real_Multiview_Contours.png')
    # Surface evidence / expansion and shrink / a physical field section.
    fig=plt.figure(figsize=(15,9));final=S[-1];init=S[0];rt=mesh_scene(final['V'],final['F']);motion=-signed(rt,init['V']);cm=plt.get_cmap('coolwarm');fc=cm(np.clip((motion[init['F']].mean(1)+.4)/.8,0,1));ax=fig.add_subplot(231,projection='3d');draw_mesh(ax,init['V'],init['F'],'gray',cad,bounds,face_colors=fc,title='Measured motion on INITIAL zero mesh\nred = expansion; blue = contraction (mm)');fig.colorbar(plt.cm.ScalarMappable(norm=plt.Normalize(-.4,.4),cmap=cm),ax=ax,shrink=.55,label='Signed surface motion (mm)')
    ev=np.load(R/'local_results/FINAL/OBSERVATION_EVIDENCE.npz');fc=np.tile([.73,.73,.73],(len(final['F']),1));fc[ev['observed_face']]=[.3,.65,.9];fc[ev['multiview_face']]=[.2,.72,.43];ax=fig.add_subplot(232,projection='3d');draw_mesh(ax,final['V'],final['F'],'gray',cad,bounds,face_colors=fc,title='FINAL evidence proxy (no trimming)\ngreen: multi-partition; blue: single; gray: inferred/unresolved')
    ax=fig.add_subplot(233);g=Field(final['origin'],final['shape'],float(final['h']));ix=int(np.argmin(abs(np.arange(g.shape[0])*g.h+g.origin[0])));x=g.origin[0]+ix*g.h;y=g.origin[1]+np.arange(g.shape[1])*g.h;z=g.origin[2]+np.arange(g.shape[2])*g.h;arr=final['phi'].reshape(g.shape)[ix];ax.imshow(arr.T,origin='lower',extent=[y.min(),y.max(),z.min(),z.max()],vmin=-2,vmax=2,cmap='RdBu_r',aspect='equal');ax.contour(y,z,init['phi'].reshape(g.shape)[ix].T,levels=[0],colors=['#65ec4b'],linewidths=1.5);ax.contour(y,z,arr.T,levels=[0],colors=['#ff28c1'],linewidths=1.5);Y,Z=np.meshgrid(y,z,indexing='ij');CP=np.c_[np.full(Y.size,x),Y.ravel(),Z.ravel()];cads=signed(ringscene('G01_004'),CP).reshape(Y.shape);ax.contourf(y,z,cads.T,levels=[-100,0],colors=['black']);H=np.vstack([obs(c)['X']for c in data.fit]);sel=abs(H[:,0]-x)<.2;ax.scatter(H[sel,1],H[sel,2],s=2,c='gold');ax.set(title='Metric SDF cut X=%.2f mm\ngreen initial; magenta final; gold real HERO'%x,xlabel='Y (mm)',ylabel='Z (mm)')
    # Contour responsibility and normal displacement proposal on real RGB.
    import csv
    rr=list(csv.DictReader((R/'metrics/iter_01_CORRESPONDENCES.csv').open()));cid=data.fit[0];ss=source(cid);ax=fig.add_subplot(234);ax.imshow(ss['RGB']);polyline(ax,ss['labels']==1,'lime');rr=[r for r in rr if r['source']==cid][::8]
    for r in rr:
        uv=np.asarray(json.loads(r['uv']))*2+.5;tv=np.asarray(json.loads(r['target_uv']))*2+.5;ax.annotate('',xy=tv,xytext=uv,arrowprops={'color':'#ee3377'if float(r['normal_velocity_mm'])>0 else'#2299ff','arrowstyle':'->','lw':.7})
    ax.set(title='ref08 real silhouette proposals, iter 1\nred expands; blue contracts; arrows are proposals');ax.set_axis_off()
    ax=fig.add_subplot(235,projection='3d');sel=rr[::2];ax.scatter(init['V'][::4,0],init['V'][::4,1],init['V'][::4,2],s=.1,c='.7');
    for r in sel:
        P=np.array(json.loads(r['P']));n=np.array(json.loads(r['normal']));vel=float(r['normal_velocity_mm']);d=n*np.clip(vel,-.5,.5);ax.quiver(*P,*d,color='#ee3377'if vel>0 else'#2299ff',arrow_length_ratio=.25,linewidth=.7)
    ax.set(xlim=(bounds[0][0],bounds[1][0]),ylim=(bounds[0][1],bounds[1][1]),zlim=(bounds[0][2],bounds[1][2]),title='Same source / face-linked 3D proposals\narrows capped at 0.5 mm for display',xlabel='X (mm)',ylabel='Y (mm)',zlabel='Z (mm)');ax.view_init(25,-65);ax.set_box_aspect([1,1,1]);ax=fig.add_subplot(236);hist=load(R/'metrics/EVOLUTION_HISTORY.json');steps=[0]+[int(h['stage'].split('_')[-1])for h in hist[1:]];ax.plot(steps,[h['geometry']['volume_ratio']for h in hist],'-o',ms=3,label='actual volume / initial');ax.axhline(1,c='.5',ls='--');ax.set(xlabel='Accepted iteration',ylabel='Volume ratio',title='No global inflation or global shrink substitute');ax.legend()
    fig.suptitle('Geometry evidence and scalar-field mechanism | G01_004 | Actual project data; no GT',fontsize=12);fig.tight_layout();savefig(fig,'Fig3_SDF_Motion_And_Evidence.png')
    fig,axs=plt.subplots(2,3,figsize=(15,8));hist=load(R/'metrics/EVOLUTION_HISTORY.json');steps=[0]+[int(h['stage'].split('_')[-1])for h in hist[1:]]
    for ids,label,color in [(data.fit,'FIT','#1f77b4'),(data.validation,'UPDATE HOLDOUT','#e88613')]:
        met=[[r for r in h['per_source']if r['source']in ids]for h in hist];axs[0,0].plot(steps,[np.mean([r['fixed_Mask_loss']for r in aa])for aa in met],'-o',ms=3,label=label,c=color);axs[0,1].plot(steps,[np.mean([r['IoU']for r in aa])for aa in met],'-o',ms=3,label=label,c=color);axs[0,2].plot(steps,[sum(r['hit_N']for r in aa)/(512*len(ids))for aa in met],'-o',ms=3,label=label,c=color);axs[1,0].plot(steps,[np.mean([r['HERO_distance_mm']['MAE']for r in aa])for aa in met],'-o',ms=3,label=label,c=color)
    axs[0,0].set(title='Fixed-pixel Mask loss',ylabel='Loss');axs[0,1].set(title='Fixed known-region Mask IoU',ylabel='IoU');axs[0,2].set(title='Fixed native HERO ray coverage',ylabel='Hit / fixed observations');axs[1,0].set(title='All fixed HERO point-to-mesh proxy',ylabel='Mean absolute distance (mm)');axs[1,1].plot(steps,[h['Ring']['distance_mm']for h in hist],'-o',ms=3,c='black');axs[1,1].set(title='Actual triangle-to-CAD clearance',ylabel='Gap (mm)');axs[1,2].plot(steps,[h['initial_surface_drift_mm']['p95']for h in hist],'-o',ms=3,label='p95 drift');axs[1,2].plot(steps,[h['initial_surface_drift_mm']['maximum']for h in hist],'-o',ms=3,label='max drift');axs[1,2].set(title='True surface change from initial',ylabel='Symmetric distance (mm)')
    for ax in axs.ravel():
        ax.set_xlabel('Accepted iteration');ax.grid(alpha=.25)
        if ax.get_legend_handles_labels()[0]:ax.legend(fontsize=7)
    done=load(R/'metrics/RUN_FINISHED.json');fig.suptitle('%d accepted updates | %s\nHoldout is evaluation only; HERO is an uncertain observation proxy, never GT'%(done['accepted_N'],done['stop']),fontsize=12);fig.tight_layout();savefig(fig,'Fig4_Fixed_Denominator_Trends.png');print('FOUR_CORE_FIGURES',flush=True)
if __name__=='__main__':main()
