"""Actual meshes and actual HERO XYZ; fixed display selection E2/seed0."""
from inputs import *
from mesh_basis import shape
from losses import Problem
from visualization import pointcloud_audit_renderer as diag
import matplotlib
plt=vis.configure()
def runs():return [load(p)for p in sorted((R/'metrics/runs').glob('*.json'))if not p.name.endswith('__progress.json')]
def row_for(allrows,scene,initial='E2',seed=0,arm='PMGR'):return next(x for x in allrows if(x['scene'],x['initial'],x['seed'],x['arm'])==(scene,initial,seed,arm))
def geometry(row,stage):
    return dict(np.load(R/'local_results'/row['key']/(stage+'.npz')))
def ortho(scene,V,F,bounds,basis,face_observed=None,n=320):
    eye,right,up=basis;u,v=np.meshgrid(np.linspace(*bounds[0],n),np.linspace(bounds[1][1],bounds[1][0],n));xy=np.c_[u.ravel(),v.ravel()];rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,(n*n,3))].astype(np.float32)
    ch=ringscene(scene).cast_rays(o3d.core.Tensor(rays));cz=ch['t_hit'].numpy();image=np.ones((n*n,3));z=np.full(n*n,np.inf)
    if V is not None:
        h=mesh_scene(V,F).cast_rays(o3d.core.Tensor(rays));z=h['t_hit'].numpy();norm=h['primitive_normals'].numpy();ids=h['primitive_ids'].numpy().astype(int);keep=np.isfinite(z)&(z<=cz);colors=np.tile([.93,.58,.17],(len(z),1))
        if face_observed is not None:colors[keep&face_observed[np.clip(ids,0,len(F)-1)]]=[.12,.64,.74]
        shade=.55+.45*abs(norm@eye);image[keep]=colors[keep]*shade[keep,None]
    image[np.isfinite(cz)&(cz<z)]=.02
    return image.reshape(n,n,3)
def model(ax,scene,V,F,bounds,basis,title,face_observed=None):
    ax.imshow(ortho(scene,V,F,bounds,basis,face_observed),extent=(*bounds[0],*bounds[1]),origin='upper');ax.set(xlim=bounds[0],ylim=bounds[1],xlabel='mm',ylabel='mm',title=title);ax.set_aspect('equal');ax.grid(alpha=.12)
def layers(scene):
    P=[];C=[];raw=[];rawC=[]
    palette=np.array([[.90,.16,.20],[.20,.65,.15],[.24,.30,.95]])
    for i,cid in enumerate(protocol()['scenes'][scene]['A']):
        for obj,ps,cs in [(cleaned(cid),P,C),(native(cid),raw,rawC)]:
            v,u=np.nonzero(obj['valid']);X=unproject(obj['depth'][v,u].astype(float),obj['T'],np.c_[u,v],obj['Kn']);ps.append(X);cs.append(np.tile(palette[i%3],(len(X),1)))
    return np.concatenate(P),np.concatenate(C),np.concatenate(raw),np.concatenate(rawC)
def points(ax,scene,P,C,bounds,basis,alpha=1):
    eye,right,up=basis;rays=np.c_[P+1000*eye,np.broadcast_to(-eye,P.shape)].astype(np.float32);cad=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();keep=~np.isfinite(cad)|(cad>=999.998);artist=vis.draw_rgb_points(ax,np.c_[P[keep]@right,P[keep]@up],C[keep],P[keep]@eye,size=.16);artist.set_alpha(alpha);artist.set_zorder(3)
def finish(fig,name,title,dpi=135):
    fig.suptitle(title,fontsize=12);fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(R/'figures'/name,dpi=dpi,facecolor='white');plt.close(fig);print('FIGURE',name,flush=True)
def core(allrows):
    scenes=list(protocol()['scenes']);basis=vis.basis((-65,22));bounds={};models={};observed={};Ls={}
    for scene in scenes:
        row=row_for(allrows,scene);models[scene]=[geometry(row,s)for s in ['P0','P1','P2','P3']];Ls[scene]=layers(scene);p=Problem(scene,'E2');from scipy.spatial import cKDTree
        trees=[]
        for cid in p.ids:
            n=cleaned(cid);v,u=np.nonzero(n['valid']);trees.append(cKDTree(unproject(n['depth'][v,u].astype(float),n['T'],np.c_[u,v],n['Kn'])))
        observed[scene]=[]
        for cp in models[scene]:
            visible=p.visibility(cp['V']);support=np.any([visible[k]&(tree.query(cp['V'])[0]<=.5)for k,tree in enumerate(trees)],axis=0);observed[scene].append(support[p.F].sum(1)>=2)
        bounds[scene]=diag.square_bounds([*(x['V']for x in models[scene]),ringmesh(scene).vertices],[basis])[0]
    fig,ax=plt.subplots(4,4,figsize=(17,14))
    for i,scene in enumerate(scenes):
        row=row_for(allrows,scene)
        for j,cp in enumerate(models[scene]):model(ax[i,j],scene,cp['V'],cp['F'],bounds[scene],basis,f"{scene} {row['stages'][j]['stage']} | active {row['stages'][j]['active_N']}\nmax from P0 {row['stages'][j]['max_P0_displacement_mm']:.3f} mm",observed[scene][j])
    finish(fig,'Fig1_Progressive_Geometry.png','PMGR E2 / seed0 fixed display; actual P0-P3 mesh, same mm bounds. Cyan=visible and <=0.5mm to SAME-source frozen HERO proxy; orange=inferred. Black=CAD.')
    fig,ax=plt.subplots(4,4,figsize=(18,11))
    for i,scene in enumerate(scenes):
        row=row_for(allrows,scene);cid=protocol()['scenes'][scene]['B'][0];s=source(cid);full=s['labels']==1
        for j,stage in enumerate(['P0','P1','P2','P3']):
            pr=np.load(R/'local_results'/row['key']/(stage+'__'+cid+'.npz'))['pred'];over=np.zeros((360,640,4));over[pr&~full&(s['labels']!=2)]=[1,.1,.1,.4];over[full&~pr]=[.4,.25,1,.3];ax[i,j].imshow(s['RGB']);ax[i,j].imshow(over);ax[i,j].contour(full,[.5],colors='#63fa77',linewidths=.7);ax[i,j].contour(pr,[.5],colors='#1bbbe5',linewidths=.8);ev=next(x for x in row['stages'][j]['evaluations']if x['source']==cid);ax[i,j].set_title(f"{scene} B {stage} | IoU {ev['IoU']:.3f}\nhit {ev['depth_hit_N']}/512; relD {ev['relative_depth_error_mm']['MAE']:.3f} mm",fontsize=9);ax[i,j].axis('off')
    finish(fig,'Fig2_Heldout_B_Reprojection.png','Same real heldout B and FULL original Mask: green observed, cyan prediction, red outside, purple missed. CONDITIONAL B; never optimized.')
    fig,ax=plt.subplots(4,4,figsize=(17,14))
    for i,scene in enumerate(scenes):
        P,C,raw,rawC=Ls[scene];bb=diag.square_bounds([P,*(x['V']for x in models[scene]),ringmesh(scene).vertices],[basis])[0]
        for j,cp in enumerate(models[scene]):
            model(ax[i,j],scene,cp['V'],cp['F'],bb,basis,scene+f' P{j} + source-coloured real HERO XYZ',observed[scene][j]);points(ax[i,j],scene,P,C,bb,basis,.45)
    finish(fig,'Fig3_HERO_XYZ_Relation.png','Frozen cleaned HERO actual XYZ over actual optimization meshes. Red/green/blue = A source IDs in protocol order. No synthetic points or pasted faces.')
    fig,ax=plt.subplots(4,4,figsize=(18,12));colors={'PMGR':'#139db2','C1_DIRECT_HIGH_DOF':'#e08224','C2_FREQ_ONLY_PROGRESSIVE':'#a24aaa'}
    for i,scene in enumerate(scenes):
        # All arms AND stages use the very same native depth-pair intersection
        # for this plot. Per-model hit-conditional means are not comparable.
        common_depth={};common_counts=[];cid=protocol()['scenes'][scene]['B'][0];ob=obs(cid)
        for initial in ['E1','E2']:
            for seed in [0,1]:
                arr={arm:[dict(np.load(R/'local_results'/row_for(allrows,scene,initial,seed,arm)['key']/(stage+'__'+cid+'.npz')))for stage in ['P0','P1','P2','P3']]for arm in colors}
                common=np.logical_and.reduce([a['pair_hit']for values in arr.values()for a in values]);pp=ob['pairs'][common];common_counts.append(int(common.sum()))
                for arm,values in arr.items():common_depth[(initial,seed,arm)]=[float(abs(a['z'][pp[:,0]]-a['z'][pp[:,1]]-ob['delta'][common]).mean())if len(pp)else np.nan for a in values]
        for arm,col in colors.items():
            rs=[x for x in allrows if x['scene']==scene and x['arm']==arm and x.get('stages')];curves=np.array([[next(v for v in st['evaluations']if v['role']=='B')['IoU']for st in x['stages']]for x in rs]);mean=curves.mean(0);ax[i,0].plot(range(4),mean,'o-',c=col,label=arm.split('_')[0]);ax[i,0].fill_between(range(4),curves.min(0),curves.max(0),alpha=.1,color=col)
            dd=np.array([common_depth[(x['initial'],x['seed'],arm)]for x in rs]);ax[i,1].plot(range(4),dd.mean(0),'o-',c=col)
            ax[i,2].plot(range(4),np.mean([[st['active_N']for st in x['stages']]for x in rs],0),'o-',c=col)
        pm=row_for(allrows,scene);ax[i,3].plot([s['step']for s in pm['steps']],[s['accepted_full_loss']for s in pm['steps']],c=colors['PMGR']);rej=[s['step']for s in pm['steps']if not s['accepted']];ax[i,3].scatter(rej,[pm['steps'][k-1]['accepted_full_loss']for k in rej],s=9,c='red');ax[i,0].set_ylabel(scene+'\nB Mask IoU');ax[i,1].set_ylabel(f'joint-common relD / mm\nN={min(common_counts)}–{max(common_counts)}/256');ax[i,2].set_ylabel('active normal modes');ax[i,3].set_ylabel('full-A objective / rejected red')
        for a in ax[i,:3]:a.set_xticks(range(4),['P0','P1','P2','P3']);a.grid(alpha=.2)
    ax[0,0].legend(fontsize=7);finish(fig,'Fig4_Ablation_Conflict.png','All E1/E2 and both seeds retained: lines mean, bands min/max (not confidence intervals); rows are independent scenes. G07/G08 pressure cases.')
def detailed(allrows):
    index=[]
    for row in allrows:
        if len(row.get('stages',[]))<4:continue
        scene=row['scene'];folder=R/'local_results'/row['key'];s=source(protocol()['scenes'][scene]['A'][0]);b=source(protocol()['scenes'][scene]['B'][0]);basisA=(-s['T'][:3,2],s['T'][:3,0],-s['T'][:3,1]);basisB=(-b['T'][:3,2],b['T'][:3,0],-b['T'][:3,1]);six=[basisA,basisB,vis.basis((-65,22)),(np.array([1.,0,0]),np.array([0,1.,0]),np.array([0,0,1.])),(np.array([0,1.,0]),np.array([1.,0,0]),np.array([0,0,1.])),(np.array([0,0,1.]),np.array([1.,0,0]),np.array([0,1.,0]))]
        cps=[geometry(row,s)for s in ['P0','P1','P2','P3']];bs=diag.square_bounds([*(c['V']for c in cps),ringmesh(scene).vertices],six);fig,ax=plt.subplots(2,6,figsize=(23,8))
        for i,cp in enumerate([cps[0],cps[-1]]):
            for j,ba in enumerate(six):model(ax[i,j],scene,cp['V'],cp['F'],bs[j],ba,('P0'if i==0 else'P3')+' '+['near A','near B','oblique','world X','world Y','world Z'][j])
        png=R/'figures/full'/(row['key']+'_Six_Views.png');fig.suptitle(row['key']+' | real mesh, same mm; unknown back is initialized/inferred');fig.tight_layout();fig.savefig(png,dpi=90);plt.close(fig)
        for stage,cp in zip(['P0','P1','P2','P3'],cps):
            gl=trimesh.Scene();cad=ringmesh(scene).copy();cad.apply_scale(.001);cad.visual.vertex_colors=[5,5,5,255];gl.add_geometry(cad,node_name='KNOWN_CAD');m=trimesh.Trimesh(cp['V']/1000,cp['F'],process=False);m.visual.vertex_colors=[45,155,185,255];gl.add_geometry(m,node_name='OPTIMIZED_BODY_NOT_PHYSICAL_GT');gl.export(folder/(stage+'.glb'))
        index.append(dict(key=row['key'],six_view=asset(png),stages=[asset(folder/(s+'.glb'))for s in ['P0','P1','P2','P3']]))
    save('assets_index/GLB.json',index)
    reviews=[]
    for scene in protocol()['scenes']:
        row=row_for(allrows,scene);P,C,raw,rawC=layers(scene);gl=trimesh.Scene();cad=ringmesh(scene).copy();cad.apply_scale(.001);cad.visual.vertex_colors=[5,5,5,255];gl.add_geometry(cad,node_name='KNOWN_BLACK_RING_CAD')
        gl.add_geometry(trimesh.points.PointCloud(raw/1000,colors=np.c_[rawC*255,np.full(len(raw),255)].astype(np.uint8)),node_name='RAW_HERO_REAL_XYZ')
        gl.add_geometry(trimesh.points.PointCloud(P/1000,colors=np.c_[C*255,np.full(len(P),255)].astype(np.uint8)),node_name='FROZEN_CLEANED_HERO_REAL_XYZ')
        for stage in ['P0','P1','P2','P3']:
            cp=geometry(row,stage);m=trimesh.Trimesh(cp['V']/1000,cp['F'],process=False);m.visual.vertex_colors=[45,155,185,255];gl.add_geometry(m,node_name=stage+'_OPTIMIZED_BODY_WITH_INFERRED_BACK')
        dest=R/'local_results'/(scene+'_Layered_Review.glb');gl.export(dest);reviews.append(asset(dest))
    save('assets_index/LAYERED_HERO_REVIEW.json',reviews)
    (R/'local_results/REVIEW_INDEX.html').write_text('<!doctype html><meta charset="utf-8"><title>PMGR review</title><h1>Actual XYZ and inferred bodies, fixed metric coordinates</h1><p>Toggle GLB nodes to compare. GLB uses metres; all scientific arrays and plots use millimetres. No GT. Unknown back is inferred.</p>'+''.join('<h2>'+Path(x['path']).stem+'</h2><a href="'+Path(x['path']).name+'">Layered GLB</a>'for x in reviews)+'<p>All seed/initial/arm six-view PNGs: ../figures/full/</p>')
def diagnostics(allrows):
    fig,ax=plt.subplots(4,3,figsize=(15,12))
    for i,scene in enumerate(protocol()['scenes']):
        row=row_for(allrows,scene)
        for st in row['spectra']:ax[i,0].semilogy(st['singular_values'],label=st['stage'])
        ax[i,0].set_title(scene+' full candidate + P0 J');ax[i,0].legend(fontsize=7);cs=np.array(row['spectra'][-1]['cosine']);im=ax[i,1].imshow(cs,vmin=-1,vmax=1,cmap='coolwarm');ax[i,1].set_title('P3 source residual-gradient cosine');labels=[cid.split(scene+'_')[-1]for cid in protocol()['scenes'][scene]['A']];ax[i,1].set_xticks(range(len(labels)),labels,rotation=20,fontsize=7);ax[i,1].set_yticks(range(len(labels)),labels,fontsize=7)
        mo=[m for m in row['mode_rows']if m['stage']=='P3'];ax[i,2].bar(range(128),[m['independent_ratio']for m in mo],color=['#1c9caf'if m['actual_active']else'#c56e35'for m in mo]);ax[i,2].axhline(.05,c='k',ls='--');ax[i,2].set_title('Mode independent information / released cyan')
    fig.tight_layout();fig.savefig(R/'figures/full/J_Spectrum_And_Conflict.png',dpi=120);plt.close(fig)
def mode_maps():
    from matplotlib import cm,colors
    basis=vis.basis((-65,22));fig,ax=plt.subplots(4,5,figsize=(21,14));eye,right,up=basis
    for i,scene in enumerate(protocol()['scenes']):
        p=Problem(scene,'E2');V=p.b['V'];F=p.F;visibles=p.visible;blocks={GATE[c]['block']for c in p.ids};support=sum(np.any(visibles[[GATE[c]['block']==b for c in p.ids]],axis=0)for b in blocks);bounds=diag.square_bounds([V,ringmesh(scene).vertices],[basis])[0];n=300;u,v=np.meshgrid(np.linspace(*bounds[0],n),np.linspace(bounds[1][1],bounds[1][0],n));xy=np.c_[u.ravel(),v.ravel()];rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,(n*n,3))].astype(np.float32);hit=mesh_scene(V,F).cast_rays(o3d.core.Tensor(rays));z=hit['t_hit'].numpy();fid=hit['primitive_ids'].numpy().astype(int);cz=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();good=np.isfinite(z)&(z<=cz);shade=.6+.4*abs(hit['primitive_normals'].numpy()@eye)
        for j,k in enumerate([None,0,12,44,127]):
            values=support[F].mean(1)if k is None else p.b['phi'][F,k].mean(1);norm=colors.Normalize(0,max(1,len(blocks)))if k is None else colors.Normalize(-1,1);cmap=cm.get_cmap('viridis'if k is None else'coolwarm');image=np.ones((n*n,3));image[good]=cmap(norm(values[np.clip(fid[good],0,len(F)-1)]))[:,:3]*shade[good,None];image[np.isfinite(cz)&(cz<z)]=.02;ax[i,j].imshow(image.reshape(n,n,3),extent=(*bounds[0],*bounds[1]),origin='upper');ax[i,j].set(xlabel='mm',ylabel='mm',title=scene+(' visible A partitions'if k is None else f' normalized normal mode {k+1}'));ax[i,j].set_aspect('equal');fig.colorbar(cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax[i,j],fraction=.04,pad=.02)
    fig.suptitle('Actual P0 mesh coloured by visibility or frozen basis field; NO geometric deformation in this diagnostic. Spectral fields are dimensionless, coefficients are mm.');fig.tight_layout();fig.savefig(R/'figures/full/Mode_Spatial_Support.png',dpi=115);plt.close(fig)
def main():
    rs=runs();core(rs);diagnostics(rs);mode_maps();detailed(rs);save('assets_index/VISUALIZATIONS.json',dict(core=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],detailed=[asset(p)for p in sorted((R/'figures/full').glob('*.png'))],display_selection='predeclared E2 seed0 for geometry panels; all seeds/initials in ablation',renderer_source=asset(REPO/'visualization/real_p0_renderer.py')))
if __name__=='__main__':main()
