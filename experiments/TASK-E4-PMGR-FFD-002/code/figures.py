"""Actual frozen-topology meshes and real project data; no smoothing/remeshing."""
from inputs import *
from visualization import pointcloud_audit_renderer as diag
from data import Data
from evaluate import stage_status
from shape import Body
from physical import blender_check
from matplotlib import cm,colors
import textwrap
plt=vis.configure()

def cp(scene,arm,stage):
    p=R/'local_results'/scene/arm/(stage+'.npz');return dict(np.load(p))if p.exists()else None
def render(scene,obj,bounds,basis,facecolors=None,n=420):
    eye,right,up=basis;u,v=np.meshgrid(np.linspace(*bounds[0],n),np.linspace(bounds[1][1],bounds[1][0],n));xy=np.c_[u.ravel(),v.ravel()];rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,(n*n,3))].astype(np.float32);cz=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();z=np.full(n*n,np.inf);out=np.ones((n*n,3))
    if obj is not None:
        h=mesh_scene(obj['V'],obj['F']).cast_rays(o3d.core.Tensor(rays));z=h['t_hit'].numpy();fi=h['primitive_ids'].numpy().astype(int);good=np.isfinite(z)&(z<=cz);normal=h['primitive_normals'].numpy();palette=np.tile([.16,.61,.73],(len(obj['F']),1))if facecolors is None else facecolors;out[good]=palette[fi[good]]*(.55+.45*abs(normal[good]@eye))[:,None]
    out[np.isfinite(cz)&(cz<z)]=.012
    return out.reshape(n,n,3)
def mesh(ax,scene,obj,bounds,basis,title,facecolors=None):
    if obj is None:ax.axis('off');ax.text(.5,.5,title+'\nNOT_RUN',ha='center',transform=ax.transAxes);return
    ax.imshow(render(scene,obj,bounds,basis,facecolors),extent=(*bounds[0],*bounds[1]),origin='upper');ax.set(xlim=bounds[0],ylim=bounds[1],title=title,xlabel='mm',ylabel='mm');ax.set_aspect('equal');ax.grid(alpha=.12)
def finish(fig,name,title,dpi=130):
    fig.suptitle('\n'.join(textwrap.fill(s,150)for s in title.splitlines()),fontsize=11);fig.tight_layout(rect=[0,0,1,.92]);fig.savefig(R/'figures'/name,dpi=dpi,facecolor='white');plt.close(fig);print('FIG',name,flush=True)
def overlay(ax,scene,obj,cid,title,unknown=True):
    d=Data(scene).views[cid];s=d['s'];im=cv2.resize(s['RGB'],(320,180),interpolation=cv2.INTER_AREA);ax.imshow(im);target=d['target_np'];ax.contour(target,[.5],colors='#48fa7d',linewidths=.9)
    if obj is not None:
        u,v=np.meshgrid(np.arange(320),np.arange(180));uv=np.c_[u.ravel(),v.ravel()];z=cast(mesh_scene(obj['V'],obj['F']),uv,d['K'],s['T'])[0];cad=d['cad'].ravel();pred=(np.isfinite(z)&(z>0)&(z<=cad)).reshape(180,320);ov=np.zeros((180,320,4));ov[pred&~target&d['known_np']]=[1,.1,.1,.5];ov[target&~pred&d['known_np']]=[.6,.2,1,.4];ax.imshow(ov);ax.contour(pred,[.5],colors='#12c8fa',linewidths=.9)
    if unknown:
        ov=np.zeros((180,320,4));ov[d['unknown']]=[.4,.4,.4,.55];ax.imshow(ov)
    vv,uu=np.nonzero(target|(s['labels'][1::2,1::2]==2));x0=max(0,uu.min()-16);x1=min(319,uu.max()+16);y0=max(0,vv.min()-16);y1=min(179,vv.max()+16);ax.set(xlim=(x0,x1),ylim=(y1,y0),title=title);ax.axis('off')

def main():
    ev=load(R/'metrics/EVALUATION.json');scene='G01_004';basis=vis.basis((-65,22));side=(np.array([1.,0,0]),np.array([0,1.,0]),np.array([0,0,1.]));stages=['P0','P1','P2','P3'];models=[cp(scene,'C2',s)for s in stages];bounds=diag.square_bounds([*[m['V']for m in models],ringmesh(scene).vertices],[basis,side]);fig,ax=plt.subplots(2,4,figsize=(20,10))
    for j,(name,obj)in enumerate(zip(stages,models)):
        met=load(R/'metrics'/(scene+'_C2_'+name+'.json'));subtitle=f"{name} | max {met['maximum_P0_move_mm']:.3f} / median {met['median_P0_move_mm']:.3f} mm"
        for i,b in enumerate([basis,side]):mesh(ax[i,j],scene,obj,bounds[i],b,subtitle+('\npartial: numerical trust limit'if j else'\nsafe frozen R1 initialization'))
    finish(fig,'Fig1_FFD_Actual_Evolution.png','G01 C2: actual P0 -> P1 -> P2 -> P3, fixed cameras and mm limits, black actual Ring CAD. All later stages made accepted updates but ended at the numerical trust limit; no claim of convergence. Top oblique / bottom world-X.')

    fig,ax=plt.subplots(2,6,figsize=(24,9))
    for i,cid in enumerate(['G01_004_growth_r06','G01_004_growth_r10']):
        overlay(ax[i,0],scene,None,cid,cid+' | real RGB / raw Mask',False);overlay(ax[i,1],scene,None,cid,'Fixed UNKNOWN (gray), same for both sides',True)
        for j,(name,obj)in enumerate(zip(stages,models)):overlay(ax[i,j+2],scene,obj,cid,'C2 '+name+' | cyan prediction')
    finish(fig,'Fig2_Real_Mask_Unknown_Projection.png','Real r06/r10 TRAINING views; display ROI only, unchanged pixel mapping. Green original Polyp Mask, cyan actual CAD-visible model, gray fixed UNKNOWN, red known outside, purple known missing. NO independent holdout.')

    obj=models[-1];en=dict(np.load(R/'local_results'/scene/'C2/P3_EVIDENCE.npz'));palette=np.tile([.94,.57,.17],(len(obj['F']),1));palette[en['face_observed_proxy']]=[.12,.67,.73];palette[en['face_multiview_proxy']]=[.10,.38,.67];signed=ringscene(scene).compute_signed_distance(o3d.core.Tensor(obj['V'].astype(np.float32))).numpy();gap=signed[obj['F']].min(1);norm=colors.Normalize(0,.5);heat=cm.viridis(norm(gap))[:,:3];fig,ax=plt.subplots(2,3,figsize=(17,11));P=np.concatenate([obs(c)['X']for c in protocol()['scenes'][scene]['P2']]);cols=np.concatenate([np.tile(cm.tab10(i)[:3],(512,1))for i,_ in enumerate(protocol()['scenes'][scene]['P2'])]);bb=diag.square_bounds([P,obj['V'],ringmesh(scene).vertices],[basis,side])
    for i,ba in enumerate([basis,side]):
        ax[i,0].imshow(render(scene,None,bb[i],ba),extent=(*bb[i][0],*bb[i][1]),origin='upper');eye,right,up=ba;rays=np.c_[P+1000*eye,np.broadcast_to(-eye,P.shape)].astype(np.float32);cz=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();keep=~np.isfinite(cz)|(cz>=999.998);vis.draw_rgb_points(ax[i,0],np.c_[P[keep]@right,P[keep]@up],cols[keep],P[keep]@eye,size=.65);ax[i,0].set(xlim=bb[i][0],ylim=bb[i][1],aspect='equal',xlabel='mm',ylabel='mm',title='Fixed reliable HERO XYZ pool: 7 x 512 real points')
        mesh(ax[i,1],scene,obj,bb[i],ba,'C2 actual Mesh: observed proxy / inferred',palette);mesh(ax[i,2],scene,obj,bb[i],ba,'C2 actual Mesh: nearest-CAD signed gap',heat);fig.colorbar(cm.ScalarMappable(norm=norm,cmap='viridis'),ax=ax[i,2],fraction=.035,label='vertex min gap proxy / mm (clipped .5)')
    finish(fig,'Fig3_HERO_Support_And_CAD_Clearance.png','HERO points are input evidence, not the predicted Mesh. Cyan=at least one source; dark blue=multiple partitions; orange=unsupported/inferred by the fixed .75mm visibility proxy. Black=CAD. Full-triangle final FCL gap 0.000103mm, Blender solid overlap 0; vertex heatmap alone is not collision certification.')

    fig,ax=plt.subplots(3,4,figsize=(20,14));finals=[cp(scene,'C0','P1_PARTIAL')]+[cp(scene,a,'P3')for a in ['C1','C2','C3']];bo=diag.square_bounds([*[c['V']for c in finals],ringmesh(scene).vertices],[basis])[0]
    for j,(a,c)in enumerate(zip(['C0 historical partial','C1 spectral','C2 progressive FFD','C3 full FFD from start'],finals)):mesh(ax[0,j],scene,c,bo,basis,a)
    curves={a:[next(x for x in ev['summary']if x.get('case')==scene and x.get('arm')==a and x.get('stage')==s)for s in stages]for a in ['C1','C2','C3']}
    for arm,co in zip(curves,['#a16cbb','#159cb0','#e88623']):
        ys=curves[arm];ax[1,0].plot(range(4),[x['mean_full_Mask_IoU']for x in ys],'o-',label=arm,c=co);dd=[next(x for x in ev['common_pairs']if x['source']=='ALL'and x['arm']==arm and x['stage']==s)['MAE']for s in stages];ax[1,1].plot(range(4),dd,'o-',label=arm,c=co);ax[1,2].plot(range(4),[x['native_hit_N']/x['native_fixed_N']for x in ys],'o-',label=arm,c=co)
    counts=load(R/'metrics/G01_004_RESULTS.json')['arms'];order=['C1','C2','C3'];aa=[next(x for x in counts if x['arm']==a)for a in order];ax[1,3].bar(order,[x['accepted_N']for x in aa],label='accepted',color='#199eaf');ax[1,3].bar(order,[x['rejected_N']for x in aa],bottom=[x['accepted_N']for x in aa],label='rejected',color='#da785a')
    for j,title in enumerate(['Full raw Mask mean IoU','Joint-common relative depth MAE / mm','Native first-surface hit / fixed3584','All actual update proposals']):
        ax[1,j].set_title(title);ax[1,j].grid(alpha=.2);ax[1,j].legend(fontsize=8)
        if j<3:ax[1,j].set_xticks(range(4),stages)
    sc='G06_004';p=load(R/'metrics/G06_004_SAFE_P0.json');row=p0(sc,'E1');m=Body(row,np.array(p['old_p']));old=dict(V=m.vertices(np.array(p['old_p'])),F=m.F);candidate=dict(np.load(R/'local_results/G06_004_P0_CANDIDATE.npz'));b6=diag.square_bounds([old['V'],candidate['V'],ringmesh(sc).vertices],[basis])[0];mesh(ax[2,0],sc,old,b6,basis,'G06 historical P0: independent physical group');mesh(ax[2,1],sc,candidate,b6,basis,'G06 safe candidate REJECTED (not a final output)');overlay(ax[2,2],sc,candidate,'G06_004_growth_r03','G06 r03 candidate projection / fixed UNKNOWN');ax[2,3].axis('off');ax[2,3].text(.01,.95,'G06 NOT_EXECUTABLE\nOne P0 solve only\nRing gap: 0.180657 mm\nVolume ratio: 1.23989\nKnown Mask mean IoU: -9.210 pp\nFrozen mean limit: -3 pp\nC1/C2/C3: NOT_RUN\nNo reinitialization / no retry',va='top',fontsize=11)
    finish(fig,'Fig4_Controls_And_Failure.png','G01 same source/scale: C0 is unmatched historical partial; C1-C3 share maximum budgets. Curves are training observation proxies, not GT. C3 improves projection most but has higher local curvature. G06 one safe-P0 candidate fails Mask preservation and is not promoted.')

    exported=[];detail=[]
    six=[basis,vis.basis((20,20)),vis.basis((110,15)),(np.eye(3)[0],np.eye(3)[1],np.eye(3)[2]),(np.eye(3)[1],np.eye(3)[0],np.eye(3)[2]),(np.eye(3)[2],np.eye(3)[0],np.eye(3)[1])]
    for arm in ['C1','C2','C3']:
        start=cp(scene,arm,'P0');end=cp(scene,arm,'P3');bbb=diag.square_bounds([start['V'],end['V'],ringmesh(scene).vertices],six);fig,axes=plt.subplots(2,6,figsize=(22,8))
        for i,c in enumerate([start,end]):
            for j,ba in enumerate(six):mesh(axes[i,j],scene,c,bbb[j],ba,arm+(' P0'if i==0 else' P3 endpoint')+' / '+['obliqueA','obliqueB','obliqueC','worldX','worldY','worldZ'][j])
        name='full/'+scene+'_'+arm+'_Six_Views.png';finish(fig,name,'Actual accepted endpoint meshes, same per-view mm window; read stage status for blocks and numerical limits. No mesh smoothing.',100);detail.append(asset(R/'figures'/name))
        for st in ['P0','P1','P2','P3','BEST','LAST_SAFE']:
            c=cp(scene,arm,st);folder=R/'local_results'/scene/arm;gl=trimesh.Scene();cad=ringmesh(scene).copy();cad.apply_scale(.001);cad.visual.vertex_colors=[4,4,4,255];gl.add_geometry(cad,node_name='KNOWN_BLACK_RING_CAD');meshbody=trimesh.Trimesh(c['V']*.001,c['F'],process=False);meshbody.visual.vertex_colors=[43,156,182,255];gl.add_geometry(meshbody,node_name=arm+'_'+st+'_FITTED_BODY_INFERRED_BACK');gl.export(folder/(st+'.glb'));exported.append(asset(folder/(st+'.glb')))
    # Additional real camera pairs from frozen protocol; display only, all training.
    for arm in ['C1','C2','C3']:
        fig,axes=plt.subplots(2,3,figsize=(14,8))
        for i,cid in enumerate([protocol()['scenes'][scene]['P1'][0],protocol()['scenes'][scene]['former_B']]):
            overlay(axes[i,0],scene,None,cid,cid+' real input',False);overlay(axes[i,1],scene,cp(scene,arm,'P0'),cid,'P0');overlay(axes[i,2],scene,cp(scene,arm,'P3'),cid,'P3 endpoint (training view)')
        name='full/'+scene+'_'+arm+'_Original_AB.png';finish(fig,name,'Original A/former-B camera geometry: B participates in training this round, never independent holdout.',110);detail.append(asset(R/'figures'/name))
    save('assets_index/VISUALIZATIONS.json',dict(core=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],detail=detail,GLB=exported,units='plots/PLY/NPZ mm; GLB metres',all_meshes_actual=True,renderer_source=asset(REPO/'visualization/real_p0_renderer.py')))

if __name__=='__main__':main()
