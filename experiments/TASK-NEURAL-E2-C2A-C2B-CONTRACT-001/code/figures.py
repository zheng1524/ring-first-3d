"""E2 core review figures. Analytic controls and existing observations only."""
from context import *
from matplotlib.collections import PolyCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
plt=vis.configure()
STAMP='CPU CONTRACT / ANALYTIC CONTROL — NO NEW MODEL OUTPUT'
COLORS=np.array([[.1,.75,.35],[.25,.5,.95],[0,0,0],[.95,.62,.15],[.76,.77,.79]])
RA_COLORS=np.array([[.1,.75,.35],[.86,.2,.75],[.25,.5,.95],[0,0,0],[.76,.77,.79]])

def finish(fig,name):
    fig.text(.5,.007,STAMP+' | GPU NOT GRANTED | cameras frozen',ha='center',color='firebrick',fontsize=10)
    fig.savefig(R/'figures'/name,dpi=130,facecolor='white');plt.close(fig)

def depth(ax,z,title):
    ax.imshow(np.full(z.shape+(3,),.77));im=ax.imshow(np.ma.masked_where(z<=0,z),vmin=10,vmax=65,cmap='viridis');ax.set_title(title,fontsize=8);ax.axis('off');return im

def main():
    syn=np.load(R/'local_results/C2A_synthetic.npz');curve=list(csv.DictReader((R/'metrics/C2A_OPACITY_CONTINUITY.csv').open()))
    fig=plt.figure(figsize=(19,12));gs=fig.add_gridspec(2,3,hspace=.30,wspace=.25)
    ax=fig.add_subplot(gs[0,0],projection='3d');rm=ring('R10');ax.plot_trisurf(*rm.vertices.T,triangles=rm.faces,color='black',linewidth=0,shade=False,alpha=1)
    a,b=np.meshgrid(np.linspace(0,2*np.pi,48),np.linspace(0,np.pi,24));ax.plot_surface(1+4.5*np.cos(a)*np.sin(b),4.5*np.sin(a)*np.sin(b),5+4.5*np.cos(b),color='seagreen',alpha=.35,linewidth=0)
    ax.add_collection3d(Poly3DCollection(syn['plane_vertices'][syn['plane_faces']],facecolors=['#ddab61']*4,alpha=.2,edgecolor='brown',linewidth=.4))
    ax.set(xlim=(-10,10),ylim=(-10,10),zlim=(-5,20),xlabel='X mm',ylabel='Y mm',zlabel='Z mm',title='Synthetic Sphere + frozen physical Ring + known BG')
    ax=fig.add_subplot(gs[0,1]);ax.imshow(RA_COLORS[syn['sampling_class_id']]);ax.axis('off');ax.set_title('RA five sampling classes\ngreen interior / magenta boundary / blue non-Polyp / black Ring / grey unknown',fontsize=9)
    ax=fig.add_subplot(gs[0,2]);im=ax.imshow(syn['opacity'],vmin=0,vmax=1,cmap='magma');ax.axis('off');ax.set_title('Finite visible Polyp opacity\nonly ROI prefix before first occluder',fontsize=10);fig.colorbar(im,ax=ax,fraction=.04)
    ax=fig.add_subplot(gs[1,0]);ax.plot([float(x['background_t_mm'])for x in curve],[float(x['opacity'])for x in curve],label='finite ROI Polyp opacity');ax.axhline(1,c='firebrick',ls='--',label='old forced terminal opacity');ax.set(xlabel='BG first-hit t / mm',ylabel='Polyp opacity',title='Continuous response to moving occluder');ax.legend(fontsize=8)
    ax=fig.add_subplot(gs[1,1]);im=ax.imshow(syn['cutoff'],cmap='viridis');ax.axis('off');ax.set_title('Actual visible integration end t / mm\nCAD/BG first-hit, no terminal tail',fontsize=10);fig.colorbar(im,ax=ax,fraction=.04)
    ax=fig.add_subplot(gs[1,2]);ax.axis('off');s=load(R/'metrics/C2A_SYNTHETIC_GATE.json');text=f"Synthetic tests: {s['check_N']} PASS\n\nUNCLAMPED Polyp SDF inside finite ROI\nOfficial Laplace density math reused on CPU\nNo 1e10 terminal cell\nRing/BG = hard visibility stop\nOccluded rays supervise visible prefix only\nUNKNOWN weight = 0\nEmpty field opacity = 0\nAnalytic geometry gradients checked\nNo model or parameter update"
    ax.text(0,.95,text,va='top',fontsize=12)
    fig.suptitle('C2a | finite opacity, geometric ray order and continuous occlusion response',fontsize=15);finish(fig,'Fig1_C2a_finite_opacity.png')

    D=registry();C={c['id']:c for c in D['references']};fig,axs=plt.subplots(2,3,figsize=(20,10))
    for i,(scene,refs)in enumerate(selected().items()):
        for j,ref in enumerate(refs):
            z=np.load(R/f'local_results/rays/{ref}.npz');cl=z['sampling_class'].reshape(360,640);ax=axs[i,j];ax.imshow(RA_COLORS[cl]);bad=z['HERO_visibility_conflict'].reshape(360,640)
            ax.contour(bad,levels=[.5],colors=['red'],linewidths=.4);ax.axis('off')
            pos=int((z['labels']==1).sum());fg=int((z['ray_class']==0).sum());ax.set_title(ref+f'\npositive Mask kept {fg}/{pos}; rejected HERO only {int(bad.sum())}',fontsize=10)
            inset=ax.inset_axes([.015,.64,.28,.33]);inset.imshow(np.asarray(Image.open(C[ref]['RGB']).convert('RGB')));inset.axis('off')
    fig.suptitle('C2a RA sampling semantics | six frozen source cameras\nGreen=Polyp interior; magenta=boundary band; blue=non-Polyp visible prefix; black=Ring; grey=UNKNOWN\nRed outlines: HERO visibility conflict. Positive Mask is preserved; only the conflicting depth is rejected.',fontsize=12)
    fig.subplots_adjust(top=.80,bottom=.08,hspace=.30);finish(fig,'Fig2_actual_ray_semantics.png')

    data=load(R/'provenance/C2B_DATA_MANIFEST.json');loss=list(csv.DictReader((R/'metrics/C2B_PER_VIEW_LOSS_RESPONSE.csv').open()))
    gn=legacy_geometry_namespace(D);solid=extract(E1/'code/figures.py',['solid_view'],dict(globals()))['solid_view']
    fig,axs=plt.subplots(2,3,figsize=(22,12))
    for i,x in enumerate(data):
        P=[];col=[]
        for ref in x['references']:
            p,c,_,_=gn['points'](ref);P.append(p);col.append(c)
        points=np.concatenate(P);colors=np.concatenate(col);rm=ring('R10');solid(axs[i,0],points,colors,rm,vis.limits([points],rm),title=x['scene']+' | actual source point evidence / mm',size=.25)
        ax=axs[i,1];ax.axis('off')
        for j,ref in enumerate(x['references']):
            y=.85-.26*j;ax.text(.02,y,ref+'\nsource weight 1/3',fontsize=9,bbox=dict(fc='#e5edfa',ec='#617fb1'));ax.annotate('',(.60,.48),(.45,y),arrowprops=dict(arrowstyle='->',color='#617fb1'))
        ax.text(.60,.48,'ONE shared\nPolyp SDF',fontsize=12,ha='center',bbox=dict(fc='#d6f0de',ec='green'))
        ax.text(.02,.02,'HERO correlated components: '+str(x['correlation_component_N'])+'\nThree distinct RGB views; shared HERO error ancestry',fontsize=10)
        ax.set_title(x['scene']+' — independent local coordinate system')
        ax=axs[i,2];rr=[r for r in loss if r['scene']==x['scene']];gr=[np.linalg.norm(json.loads(r['analytic_geometry_gradient']))for r in rr]
        ax.bar(range(3),gr,color=['#4187bb','#55aa88','#cf9955']);ax.set_xticks(range(3),[r['source'].replace(x['scene']+'_','')for r in rr]);ax.set(ylabel='analytic geometry gradient norm',title='Each real reference reaches the SAME analytic SDF probe\nCPU contract only; no learned prediction')
    fig.suptitle('C2b | separate G01_004 and G01_005 three-reference streams\nNo cross-video fusion; HERO correlation normalization applied after per-view pixel normalization',fontsize=14)
    fig.subplots_adjust(top=.86,bottom=.09,hspace=.4,wspace=.35);finish(fig,'Fig3_C2b_shared_source_loss.png')

    fig=plt.figure(figsize=(21,13));gs=fig.add_gridspec(3,4,height_ratios=[1,1,.9],hspace=.35,wspace=.25)
    for i,(scene,refs)in enumerate(selected().items()):
        counts=[]
        for j,ref in enumerate(refs):
            clean=np.load(R/f'local_results/map_inputs/{ref}_Cleaned.npz');counts.append(int(clean['validity'].sum()))
            z=np.load(R/f'local_results/map_inputs/{ref}_M3_HERO_CAD.npz');cad=z['CAD_condition_mask'];ax=fig.add_subplot(gs[i,j]);im=depth(ax,z['depth_z_m']*1000,ref+f'\nRA M3 HERO+CAD; black outlines={int(cad.sum())} CAD pixels');ax.contour(cad,levels=[.5],colors=['black'],linewidths=.45);fig.colorbar(im,ax=ax,shrink=.6,fraction=.04)
        ax=fig.add_subplot(gs[i,3]);ax.bar(range(3),counts,color='steelblue');ax.set_xticks(range(3),['ref A','ref B','ref C']);ax.set(ylabel='valid Polyp depth pixels',title=scene+' sparse conditions\n0 = unknown, no hole filling')
    ax=fig.add_subplot(gs[2,0]);ax.axis('off');ax.text(0,1,'RA M0 RGB + frozen K/pose\nM1 + native HERO\nM2 + Cleaned projected depth\nM3 + visible Ring CAD depth\nM4 switch F1/F2/F3 (exclusive)\n\n14 primary profile configs\n+ 2 Raw diagnostic profiles\nOfficial forward count = 0',va='top',fontsize=11)
    ax=fig.add_subplot(gs[2,1]);ax.axis('off');ax.text(0,1,'30 source-view derived depth conditions\n10 E1 projections reused\n20 additional source-view projections\n\nRaw/Cleaned/F1/F2/F3 have parents\nSame RGB prior versions ≠ new views\nNo extra valid/confidence field\nSource K/c2w remain frozen',va='top',fontsize=11)
    ax=fig.add_subplot(gs[2,2]);ax.axis('off');ax.text(0,1,'Future evaluation identities\n004: fixed diagnostic target only\n005: 00860 / 00611 recon-only\nStrict blind holdout = 0\n\nRA M1 full-native vs Polyp-only loss\nrequires matched-information registration\nRA M3 CAD residual is self-consistency\nAbsolute GT error: NOT_EVALUABLE',va='top',fontsize=11)
    ax=fig.add_subplot(gs[2,3]);ax.axis('off');ax.text(0,1,'Formal GPU science: NOT READY\nGPU: NOT GRANTED\n\nOfficial raw-SDF/loss graph pending\nPhysical beta + initialization need gate\nNo certified real BG triangle occluder\nHERO conflicts and correlation retained\nBudgets/stop rules need registration',va='top',fontsize=11,color='firebrick')
    fig.suptitle('C2b | Map official legal input contracts, aligned to RA section7.2\nCAD-conditioned Ring accuracy is not independent Polyp accuracy; each RGB gets one legal depth hypothesis',fontsize=13,y=.98)
    finish(fig,'Fig4_Map_M0_M4_inputs.png')
    html='<!doctype html><meta charset="utf-8"><title>E2 C2a+C2b</title><style>body{max-width:1450px;margin:auto;padding:24px;font:17px sans-serif;background:#f3f5f7}article{background:white;padding:16px;margin:24px 0}img{width:100%}.state{color:#a52621}a{color:#145b99}</style><h1>E2 C2a+C2b CPU 工程合同</h1><p class="state">GPU NOT GRANTED · 正式模型前向0 · 权重更新0 · 未生成新模型重建</p><p><a href="../TECHNICAL_REPORT.md">技术报告</a> · <a href="../FAILURE_LEDGER.md">失败与限制</a> · <a href="../REPRODUCE.md">复现</a></p>'
    for p in sorted((R/'figures').glob('Fig*.png')):html+=f'<article><h2>{p.name}</h2><img src="../figures/{p.name}"></article>'
    (R/'visualizations/index.html').write_text(html)
    save('provenance/FIGURE_MANIFEST.json',dict(figures=[asset(p)for p in sorted((R/'figures').glob('Fig*.png'))],renderer=asset(REPO/'visualization/real_p0_renderer.py'),stamp=STAMP,synthetic_scene_not_real_reconstruction=True))
    print('E2_FIGURES_COMPLETE',flush=True)

if __name__=='__main__':main()
