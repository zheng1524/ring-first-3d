"""Actual source RGB/XYZ and actual exported parametric triangles; no learned outputs."""
from run import *
from visualization import pointcloud_audit_renderer as diag
plt=vis.configure()
COLORS={'A1-0':'#9467bd','A1-1':'#2ca02c','A1-2':'#ed8a23','A1-3':'#168fc2'}
PRIMARY=load(R/'metrics/S2_PRIMARY.json')
def model(scene,arm):return next(m for m in PRIMARY if (m['scene'],m['arm'])==(scene,arm))
def native_layers(scene):
    raw=[];clean=[];rc=[];cc=[]
    for cid in protocol()['scenes'][scene]['A']:
        s=source(cid)
        for arr,colors,n in [(raw,rc,native(cid)),(clean,cc,cleaned(cid))]:
            v,u=np.nonzero(n['valid']);uv=np.c_[u,v];arr.append(unproject(n['depth'][v,u].astype(float),s['T'],uv,n['Kn']));colors.append(n['native_RGB'][v,u]/255.)
    return np.concatenate(raw),np.concatenate(rc),np.concatenate(clean),np.concatenate(cc)
def projection(ax,cid,m=None):
    s=source(cid);o=observation(cid);ax.imshow(s['RGB']);ax.contour(o['full_polyp'],[.5],colors='#aaaaff',linewidths=.6);ax.contour(o['head'],[.5],colors='#62ff6b',linewidths=.8)
    if m is not None:
        a=np.load(R/'local_results'/(key(m['scene'],m['arm'])+'__'+cid+'.npz'));pred=a['predicted_mask'];outside=pred&~o['head'];rgba=np.zeros((*outside.shape,4));rgba[outside]=[1,.05,.05,.35];ax.imshow(rgba);ax.contour(pred,[.5],colors=COLORS[m['arm']],linewidths=1.1)
        b=m['B_metrics'][0];ax.set_title(f"{m['arm']} ({m['parameter_N']}p)  IoU {b['head_IoU']:.3f}\nD-hit {b['depth_ray_hit_fraction']:.1%}; D-MAE {b['relative_depth_mm']['MAE']:.3f} mm",fontsize=9)
    ax.set_xlim(0,640);ax.set_ylim(360,0);ax.axis('off')
def mesh_frame(m,scene,bounds,basis,n=400):
    eye,right,up=basis;xx,yy=np.meshgrid(np.linspace(*bounds[0],n),np.linspace(bounds[1][1],bounds[1][0],n));xy=np.c_[xx.ravel(),yy.ravel()];rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,(n*n,3))].astype(np.float32)
    cad=ringscene(scene).cast_rays(o3d.core.Tensor(rays));cz=cad['t_hit'].numpy();out=np.ones((n*n,3))
    if m is not None:
        P,F=mesh(np.array(m['p']),np.array(m['R0']),m['family'],True);hits=mesh_scene(P,F).cast_rays(o3d.core.Tensor(rays));z=hits['t_hit'].numpy();norm=hits['primitive_normals'].numpy();valid=np.isfinite(z)&(z<=cz)
        color=np.array(__import__('matplotlib').colors.to_rgb(COLORS.get(m['arm'],'#168fc2')));shade=.55+.45*abs(norm@eye);out[valid]=color*shade[valid,None]
    out[np.isfinite(cz)&((z>cz)if m is not None else True)]=.025
    return out.reshape(n,n,3)
def draw_model(ax,m,scene,bounds,basis,title):
    ax.imshow(mesh_frame(m,scene,bounds,basis),extent=(*bounds[0],*bounds[1]),origin='upper');ax.set(xlim=bounds[0],ylim=bounds[1],title=title,xlabel='view horizontal / mm',ylabel='view vertical / mm');ax.set_aspect('equal');ax.grid(alpha=.15)
def draw_points(ax,P,rgb,scene,bounds,basis,title):
    eye,right,up=basis;q=np.c_[P@right,P@up];r=np.c_[P+1000*eye,np.broadcast_to(-eye,P.shape)];cz=ringscene(scene).cast_rays(o3d.core.Tensor(r.astype(np.float32)))['t_hit'].numpy();keep=~np.isfinite(cz)|(cz>=999.998)
    artist=vis.draw_rgb_points(ax,q[keep],rgb[keep],P[keep]@eye,size=.45);artist.set_zorder(3)
    ring=mesh_frame(None,scene,bounds,basis);alpha=(ring.mean(2)<.9).astype(float);ax.imshow(np.dstack([ring,alpha]),extent=(*bounds[0],*bounds[1]),origin='upper',zorder=1)
    ax.set(xlim=bounds[0],ylim=bounds[1],title=title,xlabel='view horizontal / mm',ylabel='view vertical / mm');ax.set_aspect('equal');ax.grid(alpha=.15)
def finish(fig,name,title):
    fig.suptitle(title,fontsize=13);fig.tight_layout(rect=[0,0,1,.95]);fig.savefig(R/'figures'/name,dpi=145,facecolor='white');plt.close(fig);print('FIGURE',name,flush=True)
def main():
    scenes=list(protocol()['scenes']);fig,ax=plt.subplots(4,6,figsize=(22,12))
    for i,scene in enumerate(scenes):
        sc=protocol()['scenes'][scene];cid=sc['B'][0];projection(ax[i,0],cid);ax[i,0].set_title(f"{scene} {sc['kind']} | B={cid.split(scene+'_')[-1]}\nRGB; {sc['tier']}",fontsize=8)
        s=source(cid);o=observation(cid);label=np.zeros((360,640,3));label[o['full_polyp']]=[.25,.25,.8];label[o['head']]=[.2,.85,.3];label[s['labels']==2]=.025;ax[i,1].imshow(label);ax[i,1].axis('off');ax[i,1].set_title(f"Fixed original Mask / head cue\nhead N={o['head'].sum():,}; B CONDITIONAL",fontsize=9)
        for j,arm in enumerate(['A1-0','A1-1','A1-2','A1-3']):projection(ax[i,j+2],cid,model(scene,arm))
    finish(fig,'Fig1_Frozen_B_Real_Projection.png','A-only fitting → frozen B. Green: head cue; blue: full Polyp; colored: prediction; red: outside cue. No real GT.')
    layers={s:native_layers(s)for s in scenes};bases=[vis.basis((-65,22)),vis.basis((0,0)),vis.basis((-65,75))];bounds={}
    fig,ax=plt.subplots(4,4,figsize=(18,17))
    for i,scene in enumerate(scenes):
        raw,rc,cl,cc=layers[scene];sets=[raw,cl,ringmesh(scene).vertices]+[mesh(np.array(model(scene,a)['p']),np.array(model(scene,a)['R0']),model(scene,a)['family'],True)[0]for a in ['A1-2','A1-3']];bounds[scene]=diag.square_bounds(sets,bases)
        b=bounds[scene][0];draw_points(ax[i,0],raw,rc,scene,b,bases[0],scene+' | Raw HERO (A only)');draw_points(ax[i,1],cl,cc,scene,b,bases[0],'Frozen cleaned HERO'if scene!='G07_004'else'G07: RAW, no qualified cleanup')
        for j,a in enumerate(['A1-2','A1-3']):draw_model(ax[i,j+2],model(scene,a),scene,b,bases[0],a+' '+model(scene,a)['family']+' | INFERRED')
    finish(fig,'Fig2_Metric_Body_HERO_Comparison.png','Actual XYZ vs inferred low-dimensional body; black actual Ring CAD; shared mm windows per scene. Original geometry unchanged.')
    fig,ax=plt.subplots(4,4,figsize=(17,17))
    for i,scene in enumerate(scenes):
        for v in range(2):
            for j,a in enumerate(['A1-2','A1-3']):
                m=model(scene,a);draw_model(ax[i,2*v+j],m,scene,bounds[scene][v+1],bases[v+1],f"{scene} {m['kind']} | {a} {m['family']}\n{'side'if v==0 else'top-oblique'}; "+('STRESS / Is NOT_EVALUABLE'if scene=='G07_004'else'CONDITIONAL'))
    finish(fig,'Fig3_Class_Families_Side_Top.png','Same input budget: ellipsoid vs bounded star / open cap / finite height graph. No true stalk or measured base inferred.')
    # Failure evidence is fixed model families / all starts, not cherry-picked primary output.
    fig,ax=plt.subplots(2,2,figsize=(15,11));jj=load(R/'metrics/S4_JACOBIANS.json')
    for scene in scenes:
        for arm in ['A1-2','A1-3']:
            j=next(j for j in jj if (j['scene'],j['arm'])==(scene,arm));s=np.array(j['singular_values']);ax[0,0].semilogy(np.arange(1,len(s)+1),s/s[0],label=f'{scene} {arm}'+(' [J unstable]'if j['status']=='NUMERICALLY_UNSTABLE_J'else''))
    ax[0,0].axhline(.001,color='black',ls='--');ax[0,0].set(title='Whitened observation J; no priors',xlabel='singular index',ylabel='s / s_max');ax[0,0].legend(fontsize=7)
    pp=load(R/'metrics/S4_PERTURBATIONS.json');names=['contour_plus_1px','D_weight_0.9','D_weight_1.1','last_A_removed','camera_right_tx_0.05mm_ry_0.1deg']
    for scene in scenes:
        for a in ['A1-2','A1-3']:ax[0,1].plot(range(5),[next(p['center_displacement_mm']for p in pp if(p['scene'],p['arm'],p['perturbation'])==(scene,a,n))for n in names],'-o',label=scene+' '+a)
    ax[0,1].set_xticks(range(5),['C+1px','D×.9','D×1.1','A minus last','camera copy'],rotation=12);ax[0,1].set(title='Fixed finite perturbations',ylabel='body center displacement / mm');ax[0,1].legend(fontsize=7)
    allr=load(R/'metrics/S2_ALL_STARTS.json')
    for scene in scenes:
        for a in ['A1-2','A1-3']:
            rr=[m for m in allr if(m['scene'],m['arm'])==(scene,a)];ax[1,0].plot([r['objective']for r in rr],[r['B_metrics'][0]['head_IoU']for r in rr],'o-',label=scene+' '+a)
    ax[1,0].set(title='All three starts: A loss vs conditional B IoU',xlabel='A objective (not comparable across scenes)',ylabel='B head IoU');ax[1,0].legend(fontsize=7)
    scene='G08_005';cid=protocol()['scenes'][scene]['B'][0];o=observation(cid);s=source(cid);ax[1,1].imshow(s['RGB']);ax[1,1].contour(o['head'],[.5],colors='#55ff55')
    for a in ['A1-2','A1-3']:
        npz=np.load(R/'local_results'/(key(scene,a)+'__'+cid+'.npz'));ax[1,1].contour(npz['predicted_mask'],[.5],colors=COLORS[a],linewidths=1.3)
    ax[1,1].axis('off');ax[1,1].set_title('G08 pressure case: better outline ≠ better D\nA1-2 D-MAE .413 mm; A1-3 .898 mm')
    finish(fig,'Fig4_Failure_Identifiability.png','All models/starts retained. Local rank and shape appearance do not prove physical truth or an independent validation gate.')
    # Detailed review artifacts: six real geometry views, GLB with separate nodes,
    # and a self-contained local HTML index (no network viewer/CDN).
    detail=R/'local_results/review';detail.mkdir(exist_ok=True);index=[]
    six=[vis.basis(a)for a in [(-65,22),(25,22),(115,22),(-155,22),(0,0),(-65,80)]]
    for scene in scenes:
        m=model(scene,'A1-3');raw,rc,cl,cc=layers[scene];P,F=mesh(np.array(m['p']),np.array(m['R0']),m['family'],True);bs=diag.square_bounds([raw,cl,P,ringmesh(scene).vertices],six);fig,ax=plt.subplots(2,3,figsize=(15,10))
        for k in range(6):draw_model(ax.flat[k],m,scene,bs[k],six[k],f'{scene} inferred {m["family"]} | diagnostic view {k+1}')
        fig.suptitle('Six display views; frozen scientific cameras unchanged; black actual CAD; mm');fig.tight_layout();path=detail/(scene+'_Six_Views.png');fig.savefig(path,dpi=130);plt.close(fig)
        tm=trimesh.Trimesh(P,F,process=False);tm.visual.vertex_colors=[30,145,195,255];cad=ringmesh(scene).copy();cad.visual.vertex_colors=[5,5,5,255]
        glb=trimesh.Scene();glb.add_geometry(tm,node_name='INFERRED_A1_BODY');glb.add_geometry(cad,node_name='KNOWN_RING_CAD');glb.add_geometry(trimesh.points.PointCloud(cl,colors=(cc*255).astype(np.uint8)),node_name='OBSERVED_FROZEN_CLEANED_HERO');gp=detail/(scene+'_Review.glb');gp.write_bytes(glb.export(file_type='glb'));index.append(dict(scene=scene,sixviews=asset(path),glb=asset(gp),model=key(scene,'A1-3'),tier=protocol()['scenes'][scene]['tier']))
    (detail/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>E4 A1 local review</title><h1>E4 inferred bodies, not ground truth</h1>'+''.join(f'<h2>{x["scene"]} — {x["tier"]}</h2><a href="{Path(x["glb"]["path"]).name}">Separate-node GLB</a><br><img width="1000" src="{Path(x["sixviews"]["path"]).name}">'for x in index))
    save('metrics/VISUALIZATION_INDEX.json',dict(core=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],detailed=index,source_renderer=asset(REPO/'visualization/real_p0_renderer.py'),basis_and_bounds_reused=asset(REPO/'visualization/pointcloud_audit_renderer.py'),geometry_display='actual source XYZ and exported parametric triangles; flat shading only, no smoothing',B_RGB_recoloring=False))
if __name__=='__main__':main()
