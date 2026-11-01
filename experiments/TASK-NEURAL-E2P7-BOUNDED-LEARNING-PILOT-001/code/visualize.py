"""Actual initial/rejected-step1 evidence; unavailable scheduled steps stay blank."""
from common import *
from visualization.same_camera_scene import SameCameraScene
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

def rows(name):return list(csv.DictReader((R/'metrics'/name).open()))
def surf(key):return np.load(R/f'local_results/surfaces/{key}.npz')
def dense(key,ref):return np.load(R/f'local_results/dense/{key}_{ref}.npz')
def finish(fig,name,title):
    fig.suptitle(title,fontsize=13);fig.savefig(R/'figures'/name,dpi=120,bbox_inches='tight');plt.close(fig)

@lru_cache(None)
def cad(ref):
    c,p,r=source(ref);m=trimesh.load(c['Ring_CAD']['path'],process=False);return SameCameraScene(m,r['K'],r['c2w_mm'],(640,360),VENDOR)

def model_image(key,ref):
    p=dense(key,ref);shape=tuple(p['shape']);image=np.full((*shape,3),.9);hit=p['render_hit'].reshape(shape);image[hit]=p['RGB'].reshape(*shape,3)[hit]
    ring=cad(ref).ring_image()[::4,::4];_,_,r=source(ref);ringt=r['ring_first_t_mm'][p['source_pixel']].reshape(shape);front=p['front_t_mm'].reshape(shape)
    opaque=(ring[:,:,3]>0)&(~hit|(ringt<=front));image[opaque]=ring[opaque,:3];return image

def main():
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,5,figsize=(17,7),layout='constrained');radius=domain()['ROI_radius_mm']
    for row,arm in enumerate(['A','B']):
        for col,(key,title) in enumerate([('Initial','Initial / step0'),(arm+'_STOP1','Actual step1 / STOPPED'),(None,'Step25 / NOT RUN'),(None,'Step50 / NOT RUN'),(None,'Step100 / NOT RUN')]):
            ax=axs[row,col]
            if key is None:ax.axis('off');ax.text(.5,.5,title+'\nHard coverage stop at step1',ha='center',va='center',color='crimson');continue
            p=surf(key);q=p['coordinate_mm'];f=p['SDF_mm'][:,len(q)//2,:].T;im=ax.imshow(f,origin='lower',extent=[q[0],q[-1],q[0],q[-1]],cmap='coolwarm',vmin=-2,vmax=6)
            if f.min()<0<f.max():ax.contour(q,q,f,levels=[0],colors='black',linewidths=1.5)
            ax.add_patch(Circle((0,0),radius,fill=False,ls='--',color='green'));ax.set(title=arm+' | '+title,xlabel='x - ROI origin [mm]',ylabel='z - ROI origin [mm]',aspect='equal')
            fig.colorbar(im,ax=ax,shrink=.6,label='actual raw SDF [mm]')
    finish(fig,'Fig1_SDF_learning.png','G01_005 | actual official neural zero sets | both arms STOPPED after1 update; safe final=step0 | no synthetic surfaces')

    fig,axs=plt.subplots(3,8,figsize=(22,9),layout='constrained')
    for row,ref in enumerate(REFS):
        c,p,r=source(ref);rgb=np.asarray(Image.open(c['RGB']));truth=r['labels'].reshape(360,640)==1
        axs[row,0].imshow(rgb);axs[row,0].set_title(ref.replace('G01_005_','')+' RGB');axs[row,1].imshow(truth,cmap='gray');axs[row,1].set_title('source Polyp Mask')
        for k,arm in enumerate(['A','B']):
            pred=dense(arm+'_STOP1',ref);shape=tuple(pred['shape']);opacity=pred['opacity'].reshape(shape);dep=pred['depth_mm'].reshape(shape)
            im=axs[row,2+k].imshow(opacity,vmin=0,vmax=1,cmap='viridis');axs[row,2+k].set_title(arm+' step1 opacity');fig.colorbar(im,ax=axs[row,2+k],shrink=.55)
            im=axs[row,4+k].imshow(np.ma.masked_invalid(dep),cmap='magma');axs[row,4+k].set_title(arm+' depth [mm]; NaN=miss');fig.colorbar(im,ax=axs[row,4+k],shrink=.55)
            ax=axs[row,6+k];ax.imshow(rgb);ax.contour(truth,levels=[.5],colors='red',linewidths=.6);ax.contour(np.arange(shape[1])*4,np.arange(shape[0])*4,opacity,levels=[.5],colors='lime',linewidths=.8);ax.set_title(arm+' source red / predicted green')
        for ax in axs[row]:ax.set(xticks=[],yticks=[])
    finish(fig,'Fig2_three_reference_fit.png','Three fixed real references | one shared SDF per arm | REJECTED step1 outputs; source masks are observations, not GT3D')

    fig=plt.figure(figsize=(17,12),layout='constrained');axes=fig.subplots(3,4,subplot_kw={'projection':None})
    stats={r['model']:r for r in load(R/'metrics/SURFACE_DIAGNOSTICS.json')};colors=np.array([[.65,.65,.65],[.15,.65,.35],[.95,.5,.1]])
    for row,key in enumerate(['Initial','A_STOP1','B_STOP1']):
        p=surf(key);V=p['vertices'];F=p['faces'];cls=p['vertex_class'];fc=p['face_class'];axold=axes[row,0];pos=axold.get_subplotspec();axold.remove();ax=fig.add_subplot(pos,projection='3d');axes[row,0]=ax
        shown=fc>0;coll=Poly3DCollection(V[F[shown]],facecolors=colors[fc[shown]],edgecolor='none',alpha=1);ax.add_collection3d(coll)
        ringmesh=cad(REFS[0]).mesh;ax.add_collection3d(Poly3DCollection(np.asarray(ringmesh.vertices)[np.asarray(ringmesh.faces)],facecolors='#141414',edgecolor='none',alpha=1))
        # Unknown points are diagnostics, never a filled/closed posterior mesh.
        un=V[cls==0][::5];ax.scatter(*un.T,s=.5,c='.6',alpha=.12)
        ax.set(xlim=(-8,8),ylim=(-8,8),zlim=(-10,5),xlabel='world X [mm]',ylabel='world Y [mm]',zlabel='world Z [mm]',title=key+' | open visible subset');ax.set_box_aspect((16,16,15));ax.view_init(elev=22,azim=-55)
        for col,ref in enumerate(REFS,1):
            ax=axes[row,col];visible=p['visible_by_source'][col-1];use=visible
            # The same fixed camera projector and opaque CAD apply to all classes.
            cad(ref).draw(ax,V[use],colors[cls[use]],np.empty((0,3)),np.empty((0,3)),point_size=2.1)
            ax.set_title(key+' / '+ref.replace('G01_005_',''))
        s=stats[key];axes[row,1].text(.02,.03,f"supported {s['supported_vertex_N']} / conflict {s['conflict_vertex_N']} / unknown {s['unknown_vertex_N']} vertices",transform=axes[row,1].transAxes,fontsize=8)
    fig.legend(handles=[Line2D([],[],marker='s',ls='',color=colors[i],label=lab) for i,lab in enumerate(['unknown prior points','HERO-consistent supported','HERO conflict'])]+[Line2D([],[],color='black',lw=4,label='fixed solid Ring CAD')],loc='lower center',ncol=4,bbox_to_anchor=(.5,-.02))
    finish(fig,'Fig3_visible_surface.png','Actual neural zero-set diagnostics | initial and REJECTED trained step1 | no backside filling; no watertight enforcement; all cameras frozen')

    fig,axs=plt.subplots(6,3,figsize=(16,20),layout='constrained')
    for j,ref in enumerate(REFS):
        c,_,_=source(ref);axs[0,j].imshow(Image.open(c['RGB']));axs[0,j].set_title(ref+' actual RGB')
        for row,arm in [(1,'A'),(2,'B')]:axs[row,j].imshow(model_image(arm+'_STOP1',ref));axs[row,j].set_title(arm+' neural RGB step1; grey=no Polyp hit')
    for row,(A,B) in enumerate([(REFS[0],REFS[1]),(REFS[1],REFS[2])],3):
        for j,arm in enumerate(['A','B']):
            p=np.load(R/f'local_results/warps/{arm}_STOP1_{A}_to_{B}.npz');axs[row,j].imshow(np.where(np.isfinite(p['RGB']),p['RGB'],.9));axs[row,j].set_title(arm+' source-only warp '+A[-8:]+' -> '+B[-8:])
        im=axs[row,2].imshow(np.ma.masked_invalid(p['RGB_error']),vmin=0,vmax=.3,cmap='inferno');axs[row,2].set_title('B source-warp RGB error; missing=unknown');fig.colorbar(im,ax=axs[row,2],shrink=.6)
    hist=rows('COVERAGE_HISTORY.csv');curves=rows('TRAINING_CURVES.csv')
    for col,split in enumerate(['extra','small']):
        ax=axs[5,col]
        for arm,ls in [('A','-'),('B','--')]:
            for j,ref in enumerate(REFS):
                rr=[r for r in hist if r['arm']==arm and r['source']==ref and r['split']==split];ax.plot([int(r['step']) for r in rr],[float(r['coverage']) for r in rr],marker='o',ls=ls,color='C'+str(j),label=arm+' '+ref[-8:])
        ax.axhline(.5,c='red',ls=':');ax.set(ylim=(0,1.05),xticks=[0,1],xlabel='actual optimizer step; stopped at1',ylabel='fixed observed front-hit fraction',title=split+' coverage');ax.legend(fontsize=7,ncol=2)
    ax=axs[5,2]
    for arm,ls in [('A','-'),('B','--')]:
        rr=[r for r in curves if r['arm']==arm];base=rr[0]
        for j,k in enumerate(['rgb_loss','depth_loss','mask_loss','Eikonal_loss','anchor_loss']):ax.plot([int(r['step'])for r in rr],[float(r[k])/float(base[k])for r in rr],ls=ls,color='C'+str(j),marker='o',label=arm+' '+k)
    ax.set(yscale='log',xticks=[0,1],xlabel='actual optimizer step',ylabel='loss / own initial loss',title='Per-term changes; no100-step curve');ax.legend(fontsize=7,ncol=2)
    for ax in axs[:5].ravel():ax.set(xticks=[],yticks=[])
    finish(fig,'Fig4_multiview_validation.png','G01_005 shared-model failure evidence | RGB warps use SOURCE colors only, never target retexturing | same-image diagnostics, not independent view test')
    (R/'figures/index.html').write_text('<!doctype html><meta charset="utf-8"><title>E2.7 stopped pilot</title><style>body{font:16px sans-serif;margin:2em;background:#eee}img{width:100%;background:white}</style><h1>E2.7 — both arms STOPPED at step1</h1><p>Last safe model is step0. Step25/50/100 were not run. These are failure diagnostics, not successful reconstructions.</p>'+''.join(f'<h2>{p.stem}</h2><img src="{p.name}">'for p in sorted((R/'figures').glob('Fig*.png'))))
    save('provenance/FIGURE_EVIDENCE.json',dict(model_labels=['Initial','A_STOP1','B_STOP1'],scheduled_25_50_100='NOT_RUN',
        actual_neural_fields=True,analytic_spheres_used=False,shared_source_cameras=True,GT_opened=False,backside_filled=False,
        Ring=asset(source(REFS[0])[0]['Ring_CAD']['path']),all_warps='source A RGB only; target B RGB used for residual only',view_test_independence=False))
    print('FOUR_ACTUAL_FAILURE_FIGURES_COMPLETE')
if __name__=='__main__':main()
