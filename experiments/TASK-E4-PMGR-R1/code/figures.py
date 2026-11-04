"""Actual R1 triangles, original RGB, source XYZ; no fabricated unrun stages."""
from inputs import *
from observations import Observations
from geometry import Model
from visualization import pointcloud_audit_renderer as diag
import textwrap
plt=vis.configure()

def ortho(scene,V,F,bounds,basis,n=420):
    eye,right,up=basis
    u,v=np.meshgrid(np.linspace(*bounds[0],n),np.linspace(bounds[1][1],bounds[1][0],n))
    xy=np.c_[u.ravel(),v.ravel()]
    rays=np.c_[1000*eye+xy[:,0,None]*right+xy[:,1,None]*up,np.broadcast_to(-eye,(n*n,3))].astype(np.float32)
    cz=ringscene(scene).cast_rays(o3d.core.Tensor(rays))['t_hit'].numpy()
    image=np.ones((n*n,3));z=np.full(n*n,np.inf)
    if V is not None:
        h=mesh_scene(V,F).cast_rays(o3d.core.Tensor(rays));z=h['t_hit'].numpy()
        norm=h['primitive_normals'].numpy();keep=np.isfinite(z)&(z<=cz)
        image[keep]=np.array([.15,.62,.75])*(.55+.45*abs(norm[keep]@eye))[:,None]
    image[np.isfinite(cz)&(cz<z)]=.015
    return image.reshape(n,n,3)

def model(ax,scene,cp,bounds,basis,title):
    if cp is None:
        ax.text(.5,.5,title+'\nNOT_RUN / NaN',ha='center',va='center',transform=ax.transAxes,fontsize=12);ax.axis('off');return
    ax.imshow(ortho(scene,cp['V'],cp['F'],bounds,basis),extent=(*bounds[0],*bounds[1]),origin='upper')
    ax.set(xlim=bounds[0],ylim=bounds[1],xlabel='mm',ylabel='mm',title=title);ax.set_aspect('equal');ax.grid(alpha=.15)

def projection(ax,scene,cp,cid,title):
    s=source(cid);ax.imshow(s['RGB']);full=s['labels']==1;ax.contour(full,[.5],colors='#50ec74',linewidths=1)
    if (s['labels']==2).any():ax.contour(s['labels']==2,[.5],colors='black',linewidths=.6)
    if cp is not None:
        u,v=np.meshgrid(np.arange(640),np.arange(360));uv=np.c_[u.ravel(),v.ravel()]
        z=cast(mesh_scene(cp['V'],cp['F']),uv,s['K'],s['T'])[0];cz=cast(ringscene(scene),uv,s['K'],s['T'])[0]
        pred=(np.isfinite(z)&(z>0)&(z<=cz)).reshape(360,640)
        overlay=np.zeros((360,640,4));overlay[pred&~full&(s['labels']!=2)]=[1,.12,.12,.35];overlay[full&~pred]=[.5,.2,1,.28]
        ax.imshow(overlay)
        if pred.any():ax.contour(pred,[.5],colors='#17c7fc',linewidths=1)
    ax.set_title(title,fontsize=10);ax.axis('off')

def finish(fig,name,title):
    title='\n'.join(textwrap.fill(line,155)for line in title.splitlines())
    fig.suptitle(title,fontsize=11);fig.tight_layout(rect=[0,0,1,.91]);fig.savefig(R/'figures'/name,dpi=135,facecolor='white');plt.close(fig);print('FIGURE',name,flush=True)

def loadcp(path):return dict(np.load(path))if Path(path).exists()else None

def main():
    results=load(R/'metrics/CASE_RESULTS.json');scene=results[0]['scene'];sc=protocol()['scenes'][scene]
    pre=load(R/'metrics'/(scene+'_P0_FEASIBILITY_RECONSTRUCTED.json'));hist=loadcp(R/'local_results'/(scene+'_HISTORICAL_P0.npz'));cand=loadcp(R/'local_results'/(scene+'_P0_CANDIDATE.npz'))
    stages={s:loadcp(R/'local_results'/scene/(s+'.npz'))for s in ['P0','P1','P2','LAST_SAFE']}
    base=stages['P0'];cid=sc['P1'][0];basis=vis.basis((-65,22));cad=ringmesh(scene)
    bounds=diag.square_bounds([hist['V'],cand['V'],cad.vertices,*[c['V']for c in stages.values()if c is not None]],[basis])[0]
    fig,ax=plt.subplots(2,3,figsize=(17,10))
    model(ax[0,0],scene,hist,bounds,basis,'Historical P0 (penetrating)')
    model(ax[0,1],scene,cand,bounds,basis,'Single-solve conservative P0 candidate\n'+pre['status'])
    old=pre['old_collision'];new=pre['new_collision'];ax[0,2].axis('off')
    text=(f"{scene} / {sc['initial']}\nHistorical O3D signed vertex: {old['body_vertex_min_signed_mm']:.4f} mm\nCandidate FCL surface gap: {new['distance_mm']:.4f} mm\nAnalytic clearance bound: {pre['analytic_clearance_lower_bound_mm']:.4f} mm\nBlender solid overlap: {pre['new_Blender']['EXACT_intersection_volume_mm3']:.6g} mm³\nVolume / history: {pre['volume_ratio']:.3f}\nMean IoU change: {pre['mean_IoU_change']:+.4f}\nP0 verdict: {pre['status']}\n"+'\n'.join(pre['reasons']))
    ax[0,2].text(.01,.98,text,va='top',fontsize=10,wrap=True)
    projection(ax[1,0],scene,hist,cid,cid+' historical')
    projection(ax[1,1],scene,cand,cid,cid+' candidate')
    sg=ringscene(scene).compute_signed_distance(o3d.core.Tensor(hist['V'].astype(np.float32))).numpy();P=hist['V'];im=ax[1,2].scatter(P@basis[1],P@basis[2],c=sg,cmap='coolwarm',s=8,vmin=-.5,vmax=.5);ax[1,2].set(xlim=bounds[0],ylim=bounds[1],aspect='equal',xlabel='mm',ylabel='mm',title='Historical vertices / CAD signed distance (mm)');ax[1,2].grid(alpha=.15);fig.colorbar(im,ax=ax[1,2],fraction=.035,label='signed mm; negative=inside CAD')
    finish(fig,'Fig1_P0_Clearance.png','Actual triangle geometry + black Ring CAD. Green=original Polyp Mask; cyan=visible model; red=outside; purple=missed. All views are training, NOT held out.')

    updates=load(R/'metrics/ALL_UPDATE_PROPOSALS.json')if(R/'metrics/ALL_UPDATE_PROPOSALS.json').exists()else[]
    # Deterministic diagnostic: first rejected candidate, otherwise first update.
    selected=next((r for r in updates if not r['accepted']),updates[0]if updates else None)
    row=p0(scene,sc['initial']);m=Model(row)
    if selected:
        snap=loadcp(selected['snapshot']);before={'V':snap['before_V'],'F':snap['F']};proposed={'V':snap['proposed_V'],'F':snap['F']};after={'V':snap['accepted_V'],'F':snap['F']}
        mapping=load(Path(selected['snapshot']).with_name(Path(selected['snapshot']).stem+'_CORRESPONDENCE.json'))[cid]
        key=selected['stage']+f" iter{selected['iteration']} trial{selected['trial']}";verdict='ACCEPT'if selected['accepted']else'REJECT: '+', '.join(selected['reasons'])
    else:
        before=hist;proposed=cand;after=base
        mapping=Observations(scene,m).linearize(hist['q'],[cid],True)['mapping'][cid]
        key='P0 feasibility diagnostic ONLY; P1/P2 NOT_RUN';verdict=pre['status']+': '+', '.join(pre['reasons'])
    uv=np.asarray(mapping['uv']);target=np.asarray(mapping['target_uv']);P=np.asarray(mapping['P']);edges=np.asarray(mapping['edges'],int);t=np.asarray(mapping['fraction']);Q=proposed['V'][edges[:,0]]*(1-t[:,None])+proposed['V'][edges[:,1]]*t[:,None];pick=np.linspace(0,len(P)-1,min(35,len(P))).astype(int);faces=np.asarray(mapping['faces'],int)
    if updates:
        from postprocess import restore
        _,_,mm=restore(scene);uu=updates[-1];ss=loadcp(uu['snapshot']);dcid=sc['P2'][4];oo=Observations(scene,mm);mp=oo.linearize(ss['q_before'],None,True)['mapping'][dcid];ma=oo.linearize(ss['q_proposed'],None,True)['mapping'][dcid]
        dp={'V':ss['before_V'],'F':ss['F']};duv=mp['uv'];dt=mp['target_uv'];dP=mp['P'];de=mp['edges'];df=mp['fraction'];dQ=ss['proposed_V'][de[:,0]]*(1-df[:,None])+ss['proposed_V'][de[:,1]]*df[:,None];di=np.linspace(0,len(dP)-1,30).astype(int)
        fig,ax=plt.subplots(2,2,figsize=(15,11));projection(ax[0,0],scene,dp,dcid,dcid+' real residuals / final rejected proposal')
        ax[0,0].quiver(duv[di,0],duv[di,1],dt[di,0]-duv[di,0],dt[di,1]-duv[di,1],angles='xy',scale_units='xy',scale=1,color='#ffe400',width=.003)
        model(ax[0,1],scene,dp,bounds,basis,'Responsible actual triangles; actual motion, no magnification')
        for tri in dp['V'][dp['F'][np.unique(mp['faces'][di])]]:ax[0,1].plot(np.r_[tri@basis[1],tri[0]@basis[1]],np.r_[tri@basis[2],tri[0]@basis[2]],c='#a433ae',lw=.6)
        ax[0,1].quiver(dP[di]@basis[1],dP[di]@basis[2],(dQ-dP)[di]@basis[1],(dQ-dP)[di]@basis[2],angles='xy',scale_units='xy',scale=1,color='#ed3c18',width=.004)
        ax[1,0].imshow(source(dcid)['RGB']);ax[1,0].scatter(duv[:,0],duv[:,1],s=10,c='#10dbff',label='before samples');ax[1,0].scatter(ma['uv'][:,0],ma['uv'][:,1],s=5,c='#e53c21',label='candidate resampled');ax[1,0].set_title('True silhouette samples: 110 -> 112');ax[1,0].legend(fontsize=8);ax[1,0].axis('off')
        dr=next(x for x in load(R/'metrics/POSTHOC_DIAGNOSTICS.json')['per_view']if x['proposal']==10 and x['source']==dcid)
        vals=[dr['dynamic_delta_px'],dr['fixed_feature_delta_px'],dr['raster_contour_delta_px']];ax[1,1].bar(['dynamic edge samples','fixed features','full pixel contour'],vals,color=['#df6932','#188ea6','#6389ac']);ax[1,1].axhline(.5,c='red',ls='--',label='registered 0.5px protection');ax[1,1].axhline(0,c='gray');ax[1,1].set(ylabel='contour change / px; + means worse',title='POSTHOC diagnostics; formal rejection unchanged');ax[1,1].legend(fontsize=8);ax[1,1].tick_params(axis='x',labelsize=8)
        finish(fig,'Fig2_Contour_To_Geometry.png','Final rejected update: 0.0231 mm max movement. Yellow=2D error; magenta=responsible triangles; red=actual movement. Dynamic contour metric crosses threshold, fixed-feature and raster diagnostics do not. No additional fitting.')

    fig,ax=plt.subplots(2,3,figsize=(17,10))
    for j,(cp,title)in enumerate([(before,'Before'),(proposed,'Proposed'),(after,'Accepted state'if after is not None else'No accepted P0; P1 NOT_RUN')]):
        model(ax[0,j],scene,cp,bounds,basis,title)
        if cp is None:ax[1,j].axis('off');ax[1,j].text(.5,.5,'NOT_RUN / NaN',ha='center',transform=ax[1,j].transAxes)
        else:projection(ax[1,j],scene,cp,sc['P2'][5],sc['P2'][5]+' '+title)
    reason_short='rejected: contour regression at ref13/ref03/r04/r10/r14'if selected and not selected['accepted']else verdict
    finish(fig,'Fig3_Proposal_And_Decision.png',key+' | '+reason_short+' | max proposed move 0.570 mm, gap 0.0297 mm; CORE objective 3.0054 -> 2.8741.\nRejected candidates are diagnostic geometry, never substituted as final predictions. Bottom: growth_r10 training view.')

    partial=stages['P1']if stages['P1']is not None else stages['LAST_SAFE']
    sequence=[hist,base,partial,stages['P2']];names=['Historical P0','Conservative P0','P1'if stages['P1']is not None else'P1 partial / STOP','P2']
    fig,ax=plt.subplots(2,4,figsize=(21,10))
    for j,(cp,name)in enumerate(zip(sequence,names)):
        model(ax[0,j],scene,cp,bounds,basis,name)
        if cp is None:ax[1,j].axis('off');ax[1,j].text(.5,.5,name+' NOT_RUN / NaN',ha='center',transform=ax[1,j].transAxes);continue
        projection(ax[1,j],scene,cp,cid,cid+' / '+name)
        for c in sc['P1']:
            X=obs(c)['X'];_,right,up=basis;ax[0,j].scatter(X@right,X@up,s=.5,c='#dd9c3a',alpha=.22)
    finish(fig,'Fig4_Actual_Geometry_Evolution.png',scene+' | same observation angle and mm limits; actual meshes, sparse fixed HERO XYZ (ochre), black CAD. Never impute missing stages.')

    exported=[]
    for case in results:
        scene=case['scene'];paths=list((R/'local_results'/scene).glob('P*.npz'))+list((R/'local_results'/scene).glob('LAST_SAFE.npz'))
        paths=[p for p in paths if '__'not in p.stem]
        for p in paths:
            cp=loadcp(p);gl=trimesh.Scene();ca=ringmesh(scene).copy();ca.apply_scale(.001);ca.visual.vertex_colors=[4,4,4,255];gl.add_geometry(ca,node_name='KNOWN_RING_CAD');b=trimesh.Trimesh(cp['V']*.001,cp['F'],process=False);b.visual.vertex_colors=[40,155,185,255];gl.add_geometry(b,node_name=p.stem+'_FITTED_BODY_UNKNOWN_BACK_IS_INFERRED');gl.export(p.with_suffix('.glb'));exported.append(asset(p.with_suffix('.glb')))
        if paths:
            cp=loadcp(paths[-1]);six=[vis.basis((-65,22)),vis.basis((15,20)),vis.basis((110,15)),tuple(np.eye(3)[[0,1,2]]),tuple(np.eye(3)[[1,0,2]]),tuple(np.eye(3)[[2,0,1]])];bb=diag.square_bounds([cp['V'],ringmesh(scene).vertices],six);fig,ax=plt.subplots(2,3,figsize=(14,9))
            for a,ba,bo,name in zip(ax.ravel(),six,bb,['oblique A','oblique B','oblique C','world X','world Y','world Z']):model(a,scene,cp,bo,ba,p.stem+' / '+name)
            finish(fig,'full/'+scene+'_Six_Views.png',scene+' actual last available accepted mesh. Inferred back is not verified tissue.')
    save('assets_index/VISUALIZATIONS.json',dict(core=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],glb=exported,renderer=asset(REPO/'visualization/real_p0_renderer.py'),selection='first rejected P1/P2 proposal, otherwise first accepted; if none, P0 feasibility diagnostic only',unknown_stages='NOT_RUN/NaN'))

if __name__=='__main__':main()
