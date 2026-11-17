"""Actual image overlays and six orthographic metric mesh views, no model tuning."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def line(ax,mask,color,label):
    q=contour(mask)
    if len(q):ax.scatter(q[:,0],q[:,1],s=.35,c=color,label=label,rasterized=True)

def overlay(ax,cid,models,title):
    s=source(cid);ax.imshow(s['RGB']);line(ax,s['labels']==1,'#00ff86','raw mask annotation; Ring contact unknown')
    d=next(x for x in load(R/'provenance/DXY_GENERATED.json') if x['source']==cid)
    if d['available']:
        th=np.linspace(0,2*np.pi,200);q=np.array(d['center_px'])+np.c_[np.cos(th),np.sin(th)]@np.array(d['basis_px']).T;ax.plot(q[:,0],q[:,1],color='#ffce45',lw=1.2,label='official DXY geometry')
    for arm,color in [('E1','#ff50c7'),('E2','#48c8ff')]:
        if arm in models:
            p=models[arm]/(cid+'_PROJECTION.npz')
            if p.exists():line(ax,np.load(p)['predicted_mask'] & (s['labels']!=2),color,'Body '+arm)
    ring=s['labels']==2
    ax.imshow(np.dstack([np.full(ring.shape,.7),np.full(ring.shape,.7),np.full(ring.shape,.7),ring*.22]))
    ax.set_xlim(0,639);ax.set_ylim(359,0);ax.set_title(title,fontsize=7);ax.axis('off')

def mesh_panel(ax,layers,ring,az,el,limit):
    for V,F,color,label,alpha in layers:
        collection=Poly3DCollection(V[F],facecolors=color,edgecolors='none',alpha=alpha,rasterized=True)
        ax.add_collection3d(collection)
    ax.add_collection3d(Poly3DCollection(ring['V'][ring['F']],facecolors='#9da2a8',edgecolors='none',alpha=.55,rasterized=True))
    mid=(limit[0]+limit[1])/2;r=max(limit[1]-limit[0])/2
    ax.set(xlim=(mid[0]-r,mid[0]+r),ylim=(mid[1]-r,mid[1]+r),zlim=(mid[2]-r,mid[2]+r),xlabel='x / mm',ylabel='y / mm',zlabel='z / mm')
    ax.set_box_aspect([1,1,1]);ax.view_init(el,az);ax.tick_params(labelsize=5);ax.set_proj_type('ortho')
    if abs(el)==90:ax.set_zticks([]);ax.set_zlabel('')
    elif az in [0,180]:ax.set_xticks([]);ax.set_xlabel('')
    else:ax.set_yticks([]);ax.set_ylabel('')

def main():
    assert (R/'provenance/EVALUATION_COMPLETED.json').exists()
    guard('evaluation');plan=load(R/'config/BODY_FIT_VIEWS.json');index=[]
    figdir=R/'figures/overlays';figdir.mkdir(exist_ok=True)
    for name,sc in plan.items():
        models={arm:R/'local_results'/name/arm for arm in ['E1','E2'] if load(R/'local_results'/name/arm/'SELECTION.json')['available']}
        n=len(sc['raw_sources']);cols=3;fig,axes=plt.subplots(int(np.ceil(n/cols)),cols,figsize=(15,3*int(np.ceil(n/cols))),squeeze=False)
        for ax,cid in zip(axes.ravel(),sc['raw_sources']):
            role='FIT' if cid in sc['FIT'] else 'HOLDOUT' if cid in sc['HOLDOUT'] else 'EXCLUDED DIAGNOSTIC'
            overlay(ax,cid,models,role+' | '+cid)
            sf,sa=plt.subplots(figsize=(10,6));overlay(sa,cid,models,role+' | '+cid);sa.legend(loc='upper right',fontsize=7);sf.savefig(figdir/(cid+'.png'),dpi=120,bbox_inches='tight');plt.close(sf)
        for ax in axes.ravel()[n:]:ax.axis('off')
        axes.ravel()[0].legend(loc='upper right',fontsize=6)
        fig.suptitle(name+' | green=original mask, yellow=official DXY, pink=E1, cyan=E2 | Ring gray=unknown\nAll body contours are model projections; hidden ellipsoid is inferred; no GT',fontsize=10)
        fig.tight_layout();fig.savefig(R/'figures'/(name+'_ALL_VIEW_OVERLAYS.png'),dpi=135,bbox_inches='tight');plt.close(fig)
        index.append(dict(pool=name,kind='every source actual projection',path='figures/'+name+'_ALL_VIEW_OVERLAYS.png'))
        if not models:continue
        layers=[]
        for arm,color in [('E1','#d336a6'),('E2','#1b9eeb')]:
            if arm not in models:continue
            m=load(models[arm]/'SELECTION.json');V,F=mesh(np.array(m['p']),np.array(m['R0']),high=False);layers.append((V,F,color,arm,.42))
        if sc['video']=='004':
            up=ASSETS/'TASK-E4-BODY-GUIDED-HERO-RELOCALIZATION-001/local_results'/sc['group']/'Body-U.npz'
            if up.exists():
                u=np.load(up);layers.append((u['V'],u['F'],'#ffa740','Body-U historical comparator',.15))
        ring=np.load(ASSETS/'TASK-E4-BODY-ANCHORED-MULTIHERO-001/inputs'/sc['group']/'RING.npz');allV=np.r_[ring['V'],*[a[0] for a in layers]];limit=[allV.min(0)-1,allV.max(0)+1]
        fig=plt.figure(figsize=(15,9))
        for k,(az,el) in enumerate([(0,0),(180,0),(90,0),(-90,0),(0,90),(0,-90)]):
            ax=fig.add_subplot(2,3,k+1,projection='3d');mesh_panel(ax,layers,ring,az,el,limit);ax.set_title(f'az={az}, elev={el}',fontsize=9)
        fig.suptitle(name+' | pink=Body-E-DXY, blue=Body-E-FULLMASK, orange=historical Body-U, gray=Ring CAD\nMetric mm; entire ellipsoid backside is prior-inferred, not observed; no GT',fontsize=11)
        fig.tight_layout();fig.savefig(R/'figures'/(name+'_SIX_DIRECTION_BODIES.png'),dpi=125,bbox_inches='tight');plt.close(fig)
        index.append(dict(pool=name,kind='six metric directions',path='figures/'+name+'_SIX_DIRECTION_BODIES.png'))
        # All three starts, including optimizer failures, at an identical scale.
        fig=plt.figure(figsize=(13,8));startlayers=[]
        for arm,color in [('E1','#d336a6'),('E2','#1b9eeb')]:
            for start in range(3):
                fp=R/'local_results'/name/arm/f'START_{start}.json'
                if fp.exists():
                    m=load(fp);V,F=mesh(np.array(m['p']),np.array(m['R0']),high=False);startlayers.append((arm,start,m,(V,F,color,arm,.5)))
        pts=np.r_[ring['V'],*[q[3][0] for q in startlayers]];lim=[pts.min(0)-1,pts.max(0)+1]
        for arm,start,m,layer in startlayers:
            ax=fig.add_subplot(2,3,(0 if arm=='E1' else 3)+start+1,projection='3d');mesh_panel(ax,[layer],ring,35,25,lim)
            ax.set_title(arm+f' start {start} | '+('eligible' if m['eligible'] else 'FAILED retained'),color='black' if m['eligible'] else 'red',fontsize=9)
        fig.suptitle(name+' | all starts at same metric scale; Ring gray; complete ellipsoid is a model inference',fontsize=11);fig.tight_layout();fig.savefig(R/'figures'/(name+'_MULTISTART_SHAPES.png'),dpi=120,bbox_inches='tight');plt.close(fig)
        index.append(dict(pool=name,kind='all starts including failures',path='figures/'+name+'_MULTISTART_SHAPES.png'))
        print('VISUALIZED',name,flush=True)
    save('assets_index/FIGURES.json',index)
if __name__=='__main__':main()
