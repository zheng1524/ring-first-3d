"""True input evidence and exported ellipsoids; shared mm frames and black CAD."""
from fitting import *
from visualization import pointcloud_audit_renderer as diag
plt=vis.configure();COLORS={'E1':'#e58c22','E2':'#168dbd'}
def selected(scene,arm,variant='full'):
    return next(x for x in load(R/'metrics/PRIMARY_A_ONLY.json')if(x['scene'],x['arm'],x['variant'])==(scene,arm,variant))
def raw_layers(scene):
    raw=[];cl=[];rc=[];cc=[]
    for cid in protocol()['scenes'][scene]['A']:
        s=source(cid)
        for n,points,colors in [(native(cid),raw,rc),(cleaned(cid),cl,cc)]:
            v,u=np.nonzero(n['valid']);points.append(unproject(n['depth'][v,u].astype(float),s['T'],np.c_[u,v],n['Kn']));colors.append(n['native_RGB'][v,u]/255.)
    return np.concatenate(raw),np.concatenate(rc),np.concatenate(cl),np.concatenate(cc)
def frame(scene,m,bounds,basis,n=360):
    eye,right,up=basis;u,v=np.meshgrid(np.linspace(*bounds[0],n),np.linspace(bounds[1][1],bounds[1][0],n));xy=np.c_[u.ravel(),v.ravel()];rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,(n*n,3))].astype(np.float32);cad=ringscene(scene).cast_rays(o3d.core.Tensor(rays));cz=cad['t_hit'].numpy();image=np.ones((n*n,3));z=np.full(n*n,np.inf)
    if m is not None:
        P,F=mesh(np.array(m['p']),np.array(m['R0']));hit=mesh_scene(P,F).cast_rays(o3d.core.Tensor(rays));z=hit['t_hit'].numpy();N=hit['primitive_normals'].numpy();visible=np.isfinite(z)&(z<=cz);color=np.array(__import__('matplotlib').colors.to_rgb(COLORS[m['arm']]));shade=.55+.45*abs(N@eye);image[visible]=shade[visible,None]*color
    image[np.isfinite(cz)&(cz<z)]=.02
    return image.reshape(n,n,3)
def model_view(ax,scene,m,bounds,basis,title):
    ax.imshow(frame(scene,m,bounds,basis),extent=(*bounds[0],*bounds[1]),origin='upper');ax.set(xlim=bounds[0],ylim=bounds[1],xlabel='view horizontal / mm',ylabel='view vertical / mm',title=title);ax.set_aspect('equal');ax.grid(alpha=.12)
def point_view(ax,scene,P,rgb,bounds,basis,title):
    eye,right,up=basis;q=np.c_[P@right,P@up];rays=np.c_[P+1000*eye,np.broadcast_to(-eye,P.shape)].astype(np.float32);cad=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy();keep=~np.isfinite(cad)|(cad>=999.998);artist=vis.draw_rgb_points(ax,q[keep],rgb[keep],P[keep]@eye,size=.45);artist.set_zorder(3);ring=frame(scene,None,bounds,basis);alpha=(ring.mean(2)<.9).astype(float);ax.imshow(np.dstack([ring,alpha]),extent=(*bounds[0],*bounds[1]),origin='upper',zorder=1);ax.set(xlim=bounds[0],ylim=bounds[1],xlabel='view horizontal / mm',ylabel='view vertical / mm',title=title);ax.set_aspect('equal');ax.grid(alpha=.12)
def finish(fig,name,title):
    fig.suptitle(title,fontsize=13);fig.tight_layout(rect=[0,0,1,.95]);fig.subplots_adjust(hspace=.35);fig.savefig(R/'figures'/name,dpi=145,facecolor='white');plt.close(fig);print('FIGURE',name,flush=True)
def projection(ax,scene,arm,cid):
    s=source(cid);o=obs(cid);a=np.load(R/'local_results'/(scene+'__'+arm+'__full__'+cid+'.npz'));pred=a['predicted_mask'];known=s['labels']!=2;outside=pred&~o['full_polyp']&known;miss=o['full_polyp']&~pred;ax.imshow(s['RGB']);rgba=np.zeros((360,640,4));rgba[outside]=[1,.05,.05,.35];rgba[miss]=[.4,.3,1,.25];ax.imshow(rgba);ax.contour(o['full_polyp'],[.5],colors='#64ff77',linewidths=.8);ax.contour(pred,[.5],colors=COLORS[arm],linewidths=1.2);b=selected(scene,arm)['B'][0];ax.set_title(f"{arm} | IoU {b['full_mask_IoU']:.3f}; hit {b['depth_hit_N']}/32\nrelative-D MAE {b['relative_depth_mm']['MAE']:.3f} mm",fontsize=10);ax.axis('off')
def main():
    scenes=list(protocol()['scenes']);dxy={x['source']:x for x in load(R/'provenance/DXY_GENERATED.json')};fig,ax=plt.subplots(4,4,figsize=(18,12))
    for i,scene in enumerate(scenes):
        cid=protocol()['scenes'][scene]['A'][0];s=source(cid);o=obs(cid);d=dxy[cid];ax[i,0].imshow(s['RGB']);ax[i,0].set_title(f"{scene} {protocol()['scenes'][scene]['kind']}\n{cid}; {GATE[cid]['qualification']}",fontsize=8);ax[i,0].axis('off');ax[i,1].imshow(s['RGB']);ax[i,1].contour(o['full_polyp'],[.5],colors='#64ff77');ax[i,1].contour(s['labels']==2,[.5],colors='#f055ee');ax[i,1].contour(o['ellipse_target'],[.5],colors=COLORS['E1']);ax[i,1].set_title('Full Mask green / official DXY orange\nRing magenta; identical source coordinates',fontsize=9);ax[i,1].axis('off')
        for j,(arm,target)in enumerate([('E1',o['ellipse_target']),('E2',o['full_polyp'])]):
            image=np.zeros((360,640,3));image[target]=__import__('matplotlib').colors.to_rgb(COLORS[arm]);image[s['labels']==2]=.4;ax[i,j+2].imshow(image);ax[i,j+2].contour(o['full_polyp'],[.5],colors='#64ff77',linewidths=.8);ax[i,j+2].set_title(f"{arm} fitting target; Ring gray=unknown\nB evaluation: FULL original Mask (both arms)",fontsize=9);ax[i,j+2].axis('off')
    finish(fig,'Fig1_Two_Inputs.png','One upstream DXY version for every frame; no class-specific E4 processing. E2 includes every original Polyp pixel.')
    fig,ax=plt.subplots(4,4,figsize=(18,12))
    for i,scene in enumerate(scenes):
        cid=protocol()['scenes'][scene]['B'][0];s=source(cid);o=obs(cid);ax[i,0].imshow(s['RGB']);ax[i,0].axis('off');ax[i,0].set_title(scene+' B '+cid.split(scene+'_')[-1]+'\n'+protocol()['scenes'][scene]['tier'].replace('_AND_HEAD_CUE',''),fontsize=8);lab=np.zeros((360,640,3));lab[o['full_polyp']]=[.2,.85,.3];lab[s['labels']==2]=.4;ax[i,1].imshow(lab);ax[i,1].axis('off');ax[i,1].set_title(f"FULL original Polyp N={o['full_polyp'].sum():,}\nRing unknown; no head mask",fontsize=9)
        for j,arm in enumerate(['E1','E2']):projection(ax[i,j+2],scene,arm,cid)
    finish(fig,'Fig2_Frozen_B_Comparison.png','A-only selected models on the same real B: green observed Mask, red outside, purple missed. B remains CONDITIONAL; no real GT.')
    basis=vis.basis((-65,22));six=[vis.basis(a)for a in [(-65,22),(25,22),(115,22),(-155,22),(0,0),(-65,80)]];layers={s:raw_layers(s)for s in scenes};bounds={};fig,ax=plt.subplots(4,4,figsize=(18,17))
    for i,scene in enumerate(scenes):
        raw,rc,cl,cc=layers[scene];models=[selected(scene,a)for a in ['E1','E2']];P=[mesh(np.array(m['p']),np.array(m['R0']))[0]for m in models];bounds[scene]=diag.square_bounds([raw,cl,ringmesh(scene).vertices,*P],[basis])[0];b=bounds[scene];point_view(ax[i,0],scene,raw,rc,b,basis,scene+' | Raw HERO');point_view(ax[i,1],scene,cl,cc,b,basis,'Frozen cleaned HERO'if scene!='G07_004'else'G07 Raw stress (no qualified cleanup)')
        for j,m in enumerate(models):model_view(ax[i,j+2],scene,m,b,basis,m['arm']+' | same 9p ellipsoid | INFERRED')
    finish(fig,'Fig3_Metric_3D_Comparison.png','Real source XYZ and inferred ellipsoids, black actual Ring CAD. Same mm window per scene; no smoothing, clipping or filled HERO holes.')
    st=load(R/'metrics/MULTISTART_STABILITY.json');ch=load(R/'metrics/VARIANT_STABILITY.json');pairs=load(R/'metrics/PAIRED_COMPARISON.json');fig,ax=plt.subplots(2,2,figsize=(15,11));x=np.arange(4)
    for j,arm in enumerate(['E1','E2']):
        ax[0,0].bar(x+(j-.5)*.32,[next(y['center_pairwise_mm']['maximum']for y in st if(y['scene'],y['arm'])==(s,arm))for s in scenes],.32,label=arm,color=COLORS[arm]);ax[0,1].plot(x,[next(y['center_mm']for y in ch if(y['scene'],y['arm'],y['variant'])==(s,arm,'drop_last_A'))for s in scenes],'-o',label=arm+' drop last A',color=COLORS[arm]);ax[0,1].plot(x,[next(y['center_mm']for y in ch if(y['scene'],y['arm'],y['variant'])==(s,arm,'camera_copy'))for s in scenes],'--x',label=arm+' camera copy',color=COLORS[arm])
    for a in ax[0]:a.set_xticks(x,scenes);a.legend(fontsize=8);a.set_ylabel('center displacement / mm');a.grid(alpha=.15)
    ax[0,0].set_title('Three fixed starts: maximum center spread');ax[0,1].set_title('Same initialization/R0; fixed view and camera perturbations')
    for change in ch:
        m=selected(change['scene'],change['arm'],change['variant'])
        if not m['optimizer_success']:ax[0,1].annotate('NC',(scenes.index(change['scene']),change['center_mm']),xytext=(4,5),textcoords='offset points',color='#b00020',fontsize=9)
    for s in scenes:
        ms=[selected(s,a)for a in ['E1','E2']];ax[1,0].plot([m['B'][0]['full_mask_IoU']for m in ms],[m['B'][0]['relative_depth_mm']['MAE']for m in ms],'-',color='#999',lw=.7)
        for m in ms:b=m['B'][0];ax[1,0].scatter(b['full_mask_IoU'],b['relative_depth_mm']['MAE'],color=COLORS[m['arm']]);ax[1,0].annotate(s+' '+m['arm'],(b['full_mask_IoU'],b['relative_depth_mm']['MAE']),fontsize=7)
    ax[1,0].set(title='Full Mask IoU vs relative HERO depth residual',xlabel='B IoU (higher)',ylabel='D residual MAE / mm (lower)');ax[1,0].grid(alpha=.15)
    worst=max(pairs,key=lambda y:y['delta_relative_depth_MAE_mm']);scene=worst['scene'];cid=protocol()['scenes'][scene]['B'][0];s=source(cid);o=obs(cid);ax[1,1].imshow(s['RGB']);ax[1,1].contour(o['full_polyp'],[.5],colors='#64ff77')
    for arm in ['E1','E2']:
        a=np.load(R/'local_results'/(scene+'__'+arm+'__full__'+cid+'.npz'));ax[1,1].contour(a['predicted_mask'],[.5],colors=COLORS[arm],linewidths=1.2)
    ax[1,1].set_title(scene+' | largest E2-minus-E1 depth error\nFailure display rule only; no B model selection');ax[1,1].axis('off');finish(fig,'Fig4_Stability_And_Failure.png','All starts retained; smooth/closed is not ground truth. Orange E1, blue E2. NC = nonconverged diagnostic.')
    detail=R/'local_results/review';detail.mkdir(exist_ok=True);index=[]
    for scene in scenes:
        models=[selected(scene,a)for a in ['E1','E2']];raw,rc,cl,cc=layers[scene];P=[mesh(np.array(m['p']),np.array(m['R0']))[0]for m in models];bs=diag.square_bounds([raw,cl,*P,ringmesh(scene).vertices],six);fig,ax=plt.subplots(2,6,figsize=(24,9));glb=trimesh.Scene();glb.metadata.update(scientific_coordinates='Ring_world_mm',export_units='m',uniform_mm_to_m=.001);cad=ringmesh(scene).copy();cad.apply_scale(.001);cad.visual.vertex_colors=[5,5,5,255];glb.add_geometry(cad,node_name='KNOWN_RING_CAD');glb.add_geometry(trimesh.points.PointCloud(cl/1000,colors=(cc*255).astype(np.uint8)),node_name='OBSERVED_FROZEN_HERO')
        for i,m in enumerate(models):
            for j in range(6):model_view(ax[i,j],scene,m,bs[j],six[j],m['arm']+' diagnostic view '+str(j+1))
            verts,faces=mesh(np.array(m['p']),np.array(m['R0']));tm=trimesh.Trimesh(verts/1000,faces,process=False);tm.visual.vertex_colors=np.r_[np.array(__import__('matplotlib').colors.to_rgb(COLORS[m['arm']]))*255,255].astype(np.uint8);glb.add_geometry(tm,node_name='INFERRED_'+m['arm']+'_ELLIPSOID')
        fig.suptitle(scene+' | same mm and six diagnostic cameras; separate E1/E2 rows; original scientific cameras unchanged');fig.tight_layout();png=detail/(scene+'_Six_Views.png');fig.savefig(png,dpi=125);plt.close(fig);gp=detail/(scene+'_Review.glb');gp.write_bytes(glb.export(file_type='glb'))
        starts=[x for x in load(R/'metrics/ALL_FITS.json')if x['scene']==scene and x['variant']=='full'];allP=[mesh(np.array(m['p']),np.array(m['R0']))[0]for m in starts];bb=diag.square_bounds([raw,cl,*allP,ringmesh(scene).vertices],[basis])[0];fig,ax=plt.subplots(2,3,figsize=(14,9))
        for i,arm in enumerate(['E1','E2']):
            for j in range(3):
                m=next(x for x in starts if x['arm']==arm and x['start']==j);model_view(ax[i,j],scene,m,bb,basis,f"{arm} start{j} | A-cost {m['objective']:.3f}\nB-IoU {m['B'][0]['full_mask_IoU']:.3f}; no B selection")
        fig.suptitle(scene+' | all three initializations, identical display camera and mm extent');fig.tight_layout();mp=detail/(scene+'_All_Starts.png');fig.savefig(mp,dpi=130);plt.close(fig);index.append(dict(scene=scene,sixviews=asset(png),GLB=asset(gp),all_starts=asset(mp)))
    (detail/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>E4 E1/E2</title><h1>Actual XYZ vs inferred ellipsoids, mm; no real GT</h1>'+''.join(f'<h2>{x["scene"]}</h2><a href="{Path(x["GLB"]["path"]).name}">GLB separate nodes</a><br><img width="1300" src="{Path(x["sixviews"]["path"]).name}"><br><img width="1000" src="{Path(x["all_starts"]["path"]).name}">'for x in index))
    save('metrics/VISUALIZATION_INDEX.json',dict(core=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],detailed=index,source_renderer=asset(REPO/'visualization/real_p0_renderer.py'),bounds_and_basis=asset(REPO/'visualization/pointcloud_audit_renderer.py'),B_RGB_recoloring=False,geometry_postprocessing=False))
if __name__=='__main__':main()
