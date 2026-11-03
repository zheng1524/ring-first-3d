"""Actual RGB and original HERO renders; diagnostic plots, no generated geometry."""
from common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
COLORS={'C1':'#377eb8','C2':'#e69500','C3':'#379d52'}
def finish(fig,name,title):
    fig.suptitle(title,fontsize=14);fig.tight_layout(rect=[0,.025,1,.94]);fig.savefig(R/'figures'/name,dpi=145,facecolor='white');plt.close(fig)
def display(pred):
    out=np.full((360,640,3),.82);v=pred['valid'];out[v]=pred['RGBA'][v,:3]/255.;out[np.isfinite(pred['known_CAD_z_mm'])&~v]=0
    return out
def main():
    rows=load(R/'metrics/A_REPROJECTION.json');poses=load(R/'metrics/A_POSES.json');spec=protocol()['pairs']
    fig,axes=plt.subplots(4,7,figsize=(28,14.5));heads=['Real target B','Ring-First A RGB','SIFT + RF-scale A RGB','RF / B overlay','SIFT / B overlay','RF RGB error','SIFT RGB error']
    for i,p in enumerate(spec):
        a,b=p['A'],p['B'];B=source(b)['RGB'];prefix=a+'__'+b+'_Cleaned_';preds=[dict(np.load(R/'local_results/A'/(prefix+x+'.npz')))for x in ['RF','SIFT']]
        common=preds[0]['valid']&preds[1]['valid']&(source(b)['labels']==1);ims=[B,display(preds[0]),display(preds[1])]
        for pred in preds:
            v=pred['valid'];im=B/255.;im[v]=.5*im[v]+.5*pred['RGBA'][v,:3]/255.;ims.append(im)
        for pred in preds:
            err=abs(pred['RGBA'][:,:,:3].astype(float)-B).mean(2);im=np.full((360,640),np.nan);im[common]=err[common];ims.append(im)
        results=[next(x for x in rows if x['A']==a and x['kind']=='Cleaned'and x['method']==m)for m in ['Ring-First','SIFT + RF-scale']]
        for j,im in enumerate(ims):
            ax=axes[i,j]
            if j>=5:ax.imshow(im,cmap='magma',vmin=0,vmax=64);ax.set_facecolor('#ccc')
            else:ax.imshow(im)
            title=heads[j]
            if j==0:title=a+' ->\n'+CC[b]['reference']
            elif j in [1,2]:q=results[j-1];title+=f"\ncoverage {q['coverage']:.1%}; common MAE {q['common_RGB']['MAE']:.2f}"
            elif j>=5:title+=' 0-64 /255\nshared Polyp pixels only'
            ax.set_title(title,fontsize=9);ax.axis('off')
    fig.text(.5,.01,'Cleaned HERO geometry fixed across pose arms; source A colors only. Black = actual CAD, gray = unsupported. Same image size, z-buffer, CAD tolerance and denominator. No camera GT.',ha='center',fontsize=11)
    finish(fig,'Fig1_RF_vs_SIFT_Real_Reprojection.png','Historical A -> B pose ablation | 4 fixed pairs / 3 independent physical polyps')
    sens=load(R/'metrics/B_SENSITIVITY.json');fig,ax=plt.subplots(2,4,figsize=(21,9))
    for i,scene in enumerate(['G01_004','G06_004']):
        order=protocol()['B_orders'][scene];target=order[1]
        for name,label,color in [(target+':tz_mm','target body tz','#d44444'),(target+':bias_mm','target HERO bias','#3274a1')]:
            rr=[x for x in sens if x['scene']==scene and x['parameter']==name];xx=[x['amplitude']for x in rr]
            for j,yy in enumerate([[x['delta_E']for x in rr],[x['dynamic']['depth_mm']['MAE']for x in rr],[100*x['dynamic']['dynamic_visible_fraction']for x in rr]]):ax[i,j].plot(xx,yy,'o-',label=label,color=color,ms=4)
        for name,label in [(target+':rx_rad','body rx'),(target+':ry_rad','body ry'),(target+':rz_rad','body rz')]:
            rr=[x for x in sens if x['scene']==scene and x['parameter']==name];ax[i,3].plot([x['amplitude']for x in rr],[x['delta_E']for x in rr],'o-',label=label,ms=4)
        titles=['Fixed-correspondence total delta E','Dynamic overlap axial MAE (mm)','Dynamic visible fraction (%)','Rotation-only delta E']
        for j in range(4):ax[i,j].set_title(scene+' | '+titles[j]);ax[i,j].set_xlabel('Perturbation (deg)'if j==3 else'Perturbation (mm)');ax[i,j].grid(alpha=.2);ax[i,j].legend(fontsize=8)
    finish(fig,'Fig2_Pose_Depth_Sensitivity.png','Single-parameter fixed-budget perturbations | visibility reported separately; no optimum adopted')
    results=load(R/'metrics/B_SVD_RESULTS.json');fig,ax=plt.subplots(1,3,figsize=(21,6.8))
    for j,n in enumerate([2,8]):
        for c in ['C1','C2','C3']:
            r=next(x for x in results if x['scene']=='G01_004'and x['views']==n and x['constraint']==c);s=np.array(r['singular_values']);ax[j].semilogy(np.arange(len(s)),s/s[0],'o-',ms=3,label=f"{c}: {r['primary_rank']}/{r['parameters']}, cond={r['condition_number']:.0f}",color=COLORS[c])
        ax[j].axhline(.001,c='gray',ls='--',label='rank threshold 1e-3');ax[j].set_title(f'G01: {n} views | normalized spectrum');ax[j].set_xlabel('Singular-value index');ax[j].set_ylabel('sigma / sigma_max');ax[j].legend(fontsize=8);ax[j].grid(alpha=.2)
    for c,off in [('C2',-.18),('C3',.18)]:
        r=next(x for x in results if x['scene']=='G01_004'and x['views']==2 and x['constraint']==c);v=r['weakest_direction'];labels=list(v);ax[2].bar(np.arange(len(v))+off,list(v.values()),.36,color=COLORS[c],label=c)
    weaklabels=[('bias A'if x.startswith('G01_004_ref08:')else'bias B')if ':bias_'in x else x.split(':')[1].replace('_mm','').replace('_rad','')for x in labels]
    ax[2].set_xticks(np.arange(len(labels)),weaklabels,rotation=35);ax[2].set_title('2-view weakest directions\nphysically scaled parameters; arbitrary SVD sign');ax[2].legend();ax[2].grid(axis='y',alpha=.2)
    fig.text(.5,.015,'C1 = epipolar + HERO-backed reprojection + silhouette proxy; C2 adds HERO depth; C3 adds Ring. Proxy rank is not physical error separation.',ha='center',fontsize=10)
    finish(fig,'Fig3_Singular_Spectra_Weak_Directions.png','Jacobian analysis | translation 0.1 mm, rotation 0.1 deg, depth bias 0.1 mm')
    sup=load(R/'metrics/SUPPLEMENTARY_WITHOUT_SILHOUETTE.json');fig,ax=plt.subplots(2,3,figsize=(20,10))
    for i,scene in enumerate(['G01_004','G06_004']):
        counts=protocol()['B_counts'][scene]
        for c in ['C1','C2','C3']:
            rr=[next(x for x in results if x['scene']==scene and x['views']==n and x['constraint']==c)for n in counts]
            ax[i,0].plot(counts,[x['rank_fraction']for x in rr],'o-',label=c,color=COLORS[c]);ax[i,1].plot(counts,[x['condition_number']for x in rr],'o-',label=c,color=COLORS[c]);ax[i,2].plot(counts,[x['top_couplings'][0]['absolute_column_cosine']for x in rr],'o-',label=c,color=COLORS[c])
        # Additive ablation: mark image-only absence of depth observability explicitly.
        rr=[next(x for x in sup if x['scene']==scene and x['views']==n and x['mode']=='IMAGE_ONLY')for n in counts];ax[i,0].plot(counts,[x['rank_fraction']for x in rr],'s--',c='#777',label='image only (no silhouette)')
        titles=['Effective rank / parameter count','Balanced normalized condition number','Maximum pose / bias column cosine']
        for j in range(3):ax[i,j].set_title(scene+' | '+titles[j]);ax[i,j].set_xticks(counts,[f"{n} views\np={6*(n-1)+n}"for n in counts]);ax[i,j].grid(alpha=.2);ax[i,j].legend(fontsize=8)
        ax[i,0].set_ylim(.45,1.04);ax[i,1].set_yscale('log');ax[i,2].set_ylim(.5,1.01)
    finish(fig,'Fig4_View_Count_Identifiability.png','Nested frozen view sets | G06 has only 5 available HERO sources; no threshold relaxation')
    print('FOUR_ACTUAL_DATA_FIGURES_DONE',flush=True)
if __name__=='__main__':main()
