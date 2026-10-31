"""Four core evidence figures from real source data and actual untrained CPU runs."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

def readrows(name):return list(csv.DictReader((R/'metrics'/name).open()))
def stamp(fig,text='CPU DIAGNOSTIC ONLY | GPU NOT AUTHORIZED | NO TRAINING / NO RECONSTRUCTION CLAIM'):
    fig.text(.5,.012,text,ha='center',fontsize=10,color='firebrick')
def savefig(fig,name):fig.savefig(R/'figures'/name,dpi=135);plt.close(fig)

def depth_fig():
    fig,axes=plt.subplots(2,6,figsize=(21,8));flows=readrows('PAIRWISE_QUALIFICATION_FLOW.csv')
    cmap=ListedColormap(['#2f9965','#aaa','#608ab8','#111','#a0546c','#e0a340'])
    for row,(scene,refs) in enumerate(selected().items()):
        A,B=refs[:2];ca,pa,ra=source(A);cb,pb,rb=source(B);z=np.load(R/'local_results/depth_pairs'/(A+'__'+B+'.npz'))
        rgb=np.asarray(Image.open(ca['RGB']).convert('RGB'));axes[row,0].imshow(rgb);axes[row,0].contour((pa['labels']==1).astype(float),[.5],colors=['lime'],linewidths=.5)
        axes[row,0].set_title(A+'\nactual source RGB + Polyp Mask',fontsize=9)
        for col,img,title in [(1,np.where(pa['depth_mm']>0,pa['depth_mm'],np.nan),'A native axial Z (mm)'),
            (2,z['A_projected_Z_in_B_mm'],'A unproject/world/project into B (mm)'),
            (3,np.where(pb['depth_mm']>0,pb['depth_mm'],np.nan),B+' native axial Z (mm)')]:
            artist=axes[row,col].imshow(img,vmin=15,vmax=65,cmap='viridis');axes[row,col].set_title(title,fontsize=9)
            fig.colorbar(artist,ax=axes[row,col],fraction=.045,pad=.02).ax.tick_params(labelsize=6)
        sub=axes[row,3].inset_axes([.65,.03,.33,.33]);sub.imshow(np.asarray(Image.open(cb['RGB']).convert('RGB')));sub.axis('off')
        artist=axes[row,4].imshow(z['residual_A_mm'],vmin=-2,vmax=2,cmap='coolwarm');fig.colorbar(artist,ax=axes[row,4],fraction=.045,pad=.02).ax.tick_params(labelsize=6)
        axes[row,4].set_title('signed e(A→B), at A pixels (mm)\nALL loose candidates retained',fontsize=9)
        view=np.ma.masked_where(z['condition']==255,z['condition']);axes[row,5].imshow(view,cmap=cmap,vmin=-.5,vmax=5.5,interpolation='nearest')
        f=next(x for x in flows if x['A']==A and x['B']==B)
        axes[row,5].set_title('conditional'+f['conditional_candidate_N']+' / loose'+f['loose_candidate_N']+'\nOrange: uncertified correspondence',fontsize=9)
        for ax in axes[row]:ax.axis('off')
    fig.suptitle('P1 | True source-world-target depth comparison; B is another INPUT reference, not an evaluation target',fontsize=13)
    fig.text(.03,.075,'Qualification colors: green conditional; grey outside; blue identity/native-depth invalid; black known Ring occlusion; purple A self-occlusion; orange uncertified\nConditional cycle/normal selection can favor agreement. Both loose and conditional statistics/coverage are reported; neither certifies physical identity.',fontsize=10)
    stamp(fig);fig.tight_layout(rect=(0,.14,1,.94));savefig(fig,'Fig1_depth_conflicts.png')

def ring_fig():
    fig,axes=plt.subplots(6,4,figsize=(14,16));rows=readrows('RING_DEPTH_RESIDUALS.csv')
    for row,ref in enumerate([x for rr in selected().values() for x in rr]):
        z=np.load(R/f'local_results/ring/{ref}.npz');mask=z['source_Ring_Mask'];yy,xx=np.where(mask)
        box=(slice(max(0,yy.min()-15),min(360,yy.max()+16)),slice(max(0,xx.min()-15),min(640,xx.max()+16)))
        axes[row,0].imshow(mask[box],cmap='gray',vmin=0,vmax=1);axes[row,0].set_title(ref+'\nsource Ring identity Mask',fontsize=8)
        cad=np.where(z['reliable_Ring'],z['CAD_Z_mm'],np.nan)
        for col,img,title in [(1,cad,'qualified fixed CAD Z (mm)'),(2,z['native_Ring_Z_mm'],'native HERO Ring Z (mm)')]:
            artist=axes[row,col].imshow(img[box],cmap='viridis',vmin=15,vmax=65);axes[row,col].set_title(title,fontsize=8)
            fig.colorbar(artist,ax=axes[row,col],fraction=.04,pad=.02).ax.tick_params(labelsize=5)
        residual=z['residual_mm'][z['reliable_Ring']];r=next(x for x in rows if x['source']==ref and x['tier']=='RING_INTERIOR_INCIDENCE')
        if len(residual):
            axes[row,3].hist(residual,bins=np.linspace(-3,3,61),color='#487fa8');axes[row,3].axvline(float(r['median_signed']),c='firebrick')
            axes[row,3].set_title('N='+str(len(residual))+' / Mask'+r['Ring_Mask_N']+'; med'+f"{float(r['median_signed']):.3f}"+'mm\np95abs'+f"{float(r['p95_abs']):.3f}"+'mm; outside±3='+str(int((abs(residual)>3).sum())),fontsize=8)
        else:axes[row,3].text(.5,.5,'NOT EVALUABLE: no native Ring depth',ha='center')
        for ax in axes[row,:3]:ax.axis('off')
        axes[row,3].set_xlim(-3,3);axes[row,3].tick_params(labelsize=7)
    fig.suptitle('P1-B | Ring HERO−CAD residuals under FROZEN cameras\nNO residual-based agreement filter; no Polyp depth substitution; crop from source Mask only',fontsize=12)
    stamp(fig);fig.tight_layout(rect=(0,.035,1,.96));savefig(fig,'Fig2_ring_depth_residuals.png')

def neural_fig():
    fig,axes=plt.subplots(2,3,figsize=(17,9));init=readrows('NEURAL_INITIALIZATION_AND_HITS.csv');sel=readrows('DEGENERACY_SELECTION_COUNTEREXAMPLE.csv');deg=readrows('DEGENERACY_TESTS.csv')
    for row,(scene,refs) in enumerate(selected().items()):
        for candidate,color in [('A_LEGACY_INIT_CONTROL','#3579b8'),('B_SOURCE_ROI_PHYSICAL','#dd8c38')]:
            rec=[x for x in init if x['scene']==scene and x['candidate']==candidate]
            z=np.load(R/f'local_results/neural/{scene}_{candidate}_{refs[0]}.npz')
            axes[row,0].plot(z['trace_t_mm'],z['trace_raw_SDF_mm'],c=color,label=candidate[0]+': beta'+f"{float(rec[0]['beta_mm']):.3g}"+'mm')
            opacity_values=[];hit=[];observed=[]
            for ref in refs:
                p=np.load(R/f'local_results/neural/{scene}_{candidate}_{ref}.npz');opacity_values.extend(p['opacity']);hit.extend(p['render_hit']);observed.extend(p['observed'])
            axes[row,1].scatter(np.arange(len(opacity_values)),opacity_values,s=10,c=color,label=candidate[0]+': observed hits'+str(sum(x and y for x,y in zip(hit,observed)))+'/18')
        axes[row,0].axhline(0,c='black',ls='--',lw=.8);axes[row,0].set(xlabel='finite source ray t (mm)',ylabel='raw SDF (mm)',title=scene+' | one preselected actual ray')
        axes[row,0].legend(fontsize=8);axes[row,1].set(xlabel='16 fixed rays ×3 references',ylabel='finite Polyp opacity',ylim=(-.05,1.05),title='Actual untrained network; misses remain NaN depth')
        axes[row,1].legend(fontsize=8)
    usable=[x for x in sel if x['scene']=='G01_004' and x['current_joint_total']]
    axes[0,2].plot([float(x['hit_coverage']) for x in usable],[float(x['Depth_loss']) for x in usable],'o-',label='hit-conditional depth loss')
    axes[0,2].plot([float(x['hit_coverage']) for x in usable],[float(x['current_joint_total']) for x in usable],'s-',label='joint objective')
    axes[0,2].invert_xaxis();axes[0,2].set(xlabel='fixed observed hit coverage (decreasing →)',ylabel='objective value',title='Selection counterexample: error falls with coverage')
    axes[0,2].legend(fontsize=8)
    dd=[x for x in deg if x['scene']=='G01_005' and float(x['diagnostic_offset_mm'])>=0]
    axes[1,2].plot([float(x['diagnostic_offset_mm']) for x in dd],[float(x['current_Mask_dLoss_dOffset']) for x in dd],'o-',label='current clamped BCE')
    axes[1,2].plot([float(x['diagnostic_offset_mm']) for x in dd],[float(x['stable_Mask_dLoss_dOffset']) for x in dd],'s-',label='stable log-optical candidate')
    axes[1,2].set(xlabel='diagnostic raw SDF offset (mm); weights unchanged',ylabel='d Mask loss / d offset',title='Actual005 empty field: old gradient0; candidate≈3.553')
    axes[1,2].legend(fontsize=8)
    fig.suptitle('UNTRAINED OFFICIAL NETWORK / CPU TEST | FIXED_SAMPLER_DIAGNOSTIC_ONLY',fontsize=14)
    fig.text(.04,.065,'Four unique scene/candidate networks,670395 parameters each; two exact seeded replays after diagnostic dtype fix. No optimizer step.\n004/A passes three-reference wiring;004/B misses ref13;005/A and005/B miss all qualified depth rays. No third initialization was searched.',fontsize=10)
    stamp(fig);fig.tight_layout(rect=(0,.12,1,.94));savefig(fig,'Fig3_official_sdf_cpu.png')

def three_ref_fig():
    fig=plt.figure(figsize=(17,12));outer=fig.add_gridspec(2,3,left=.045,right=.985,bottom=.15,top=.87,wspace=.22,hspace=.28);init=readrows('NEURAL_INITIALIZATION_AND_HITS.csv');grad=readrows('NEURAL_PER_REFERENCE_GRADIENTS.csv')
    for row,(scene,refs) in enumerate(selected().items()):
        for col,ref in enumerate(refs):
            inner=outer[row,col].subgridspec(2,1,height_ratios=[3,1.7],hspace=.18);ax=fig.add_subplot(inner[0]);bar=fig.add_subplot(inner[1]);c,p,r=source(ref);rgb=np.asarray(Image.open(c['RGB']).convert('RGB')).copy()
            black=(p['labels']==2)&np.isfinite(r['ring_first_t_mm'].reshape(360,640));rgb[black]=[10,10,10];ax.imshow(rgb)
            ax.contour((p['labels']==1).astype(float),[.5],colors=['lime'],linewidths=.6)
            conflict=np.zeros(230400,bool)
            for B in refs:
                if B==ref:continue
                z=np.load(R/'local_results/depth_pairs'/(ref+'__'+B+'.npz'));conflict[z['source_pixel'][abs(z['residual'])>z['threshold_mm']]]=True
            if conflict.any():ax.contour(conflict.reshape(360,640).astype(float),[.5],colors=['red'],linewidths=.4)
            ix=load(R/f'provenance/{ref}_CPU_PIXEL_SELECTION.json')['pixel'];ax.scatter(np.array(ix)%640,np.array(ix)//640,s=5,c='cyan')
            a=next(x for x in init if x['source']==ref and x['candidate']=='A_LEGACY_INIT_CONTROL');b=next(x for x in init if x['source']==ref and x['candidate']=='B_SOURCE_ROI_PHYSICAL')
            ax.set_title(ref+' |16 rays, native depth6\nA hits'+a['observed_hit_N']+'/6; B hits'+b['observed_hit_N']+'/6; positive Mask'+a['positive_Mask_N'],fontsize=10);ax.axis('off')
            for j,candidate in enumerate(['A_LEGACY_INIT_CONTROL','B_SOURCE_ROI_PHYSICAL']):
                for k,term in enumerate(['rgb','mask','depth']):
                    rr=next(x for x in grad if x['source']==ref and x['candidate']==candidate and x['loss']==term)
                    value=float(rr['gradient_norm']) if rr['gradient_norm'] else None;x=k+(j-.5)*.28
                    if value is None:bar.text(x,1e-4,'NaN',rotation=90,fontsize=7,ha='center')
                    elif value==0:bar.text(x,1e-4,'0',fontsize=8,ha='center')
                    else:bar.bar(x,value,.26,color=['#3579b8','#dd8c38'][j],label='A'if j==0 else'B')
            bar.set(xticks=np.arange(3),xticklabels=['RGB','Mask','Depth'],xlim=(-.5,2.5),yscale='log',ylim=(5e-5,2e3),ylabel='true parameter gradient norm');bar.tick_params(labelsize=7)
    fig.suptitle('Three REAL references per video → SAME official neural parameters\nGreen: source Polyp Mask; red: source-depth conflict; cyan: frozen CPU rays; black: observed fixed CAD hit',fontsize=13)
    fig.text(.035,.06,'Blue A=legacy init; orange B=source-ROI physical candidate. NaN means no valid front-hit loss, not gradient0. Eikonal is ONE shared-field regularizer per model.\nShared HERO dependence remains one component per video; images are inputs, not new reconstruction outputs. Full per-source counts/losses/cosines in CSV.',fontsize=10)
    stamp(fig);savefig(fig,'Fig4_three_reference_gradients.png')

def main():
    depth_fig();ring_fig();neural_fig();three_ref_fig()
    paths=sorted((R/'figures').glob('Fig*.png'));save('provenance/FIGURE_MANIFEST.json',dict(figures=[asset(p) for p in paths],
        label='UNTRAINED OFFICIAL NETWORK / CPU TEST',GT=False,all_RGB_are_qualified_source_inputs=True,GPU='NOT_AUTHORIZED'))
    (R/'visualizations/index.html').write_text('<!doctype html><meta charset="utf-8"><title>E2.5 CPU evidence</title><style>body{font:16px sans-serif;max-width:1500px;margin:2em auto}img{width:100%}</style><h1>E2.5 — UNTRAINED OFFICIAL NETWORK / CPU TEST</h1><p>GPU NOT AUTHORIZED; no optimizer update; neural three-reference gate failed in005.</p>'+''.join('<h2>'+p.name+'</h2><img src="../figures/'+p.name+'">' for p in paths))
    print('FOUR_CORE_FIGURES_COMPLETE')

if __name__=='__main__':main()
