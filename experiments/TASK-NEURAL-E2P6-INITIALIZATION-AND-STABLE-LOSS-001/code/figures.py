"""Four evidence figures from frozen source images and actual untrained raw SDF traces."""
from common import *
from stable_losses import packet
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import ListedColormap

def rows(name):return list(csv.DictReader((R/name).open()))
def fmtref(ref):return ref.replace('G01_','')
def finish(fig,name,caption):
    fig.suptitle(caption,fontsize=13)
    fig.savefig(R/'figures'/name,dpi=140,bbox_inches='tight');plt.close(fig)

def main():
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    refs=[ref for rr in selected().values() for ref in rr];cal=load(R/'config/SHELL_CALIBRATION_FROZEN.json')
    fig,axs=plt.subplots(2,3,figsize=(15,9),layout='constrained');evidence=[]
    for row,(scene,rr) in enumerate(selected().items()):
        z=np.load(R/f'local_results/initialization/{scene}_zero_slice.npz');q=z['coordinate_mm'];lim=max(abs(z['before_B_SDF_mm']).max(),abs(z['after_SDF_mm']).max())
        for col,(key,title) in enumerate([('before_B_SDF_mm','Before: E2.5 physical B'),('after_SDF_mm','After: ONE shell-median rule')]):
            ax=axs[row,col];v=z[key];im=ax.imshow(v,origin='lower',extent=[q[0],q[-1],q[0],q[-1]],cmap='coolwarm',vmin=-lim,vmax=lim)
            if v.min()<0<v.max():ax.contour(q,q,v,levels=[0],colors='black',linewidths=1.5)
            else:ax.text(.03,.95,'No zero contour in this slice',transform=ax.transAxes,va='top',bbox=dict(facecolor='white',alpha=.8))
            ax.add_patch(Circle((0,0),cal[scene]['radius_mm'],fill=False,linestyle='--',color='green',label='frozen target shell'))
            ax.set(title=scene+' | '+title,xlabel='world x - ROI origin [mm]',ylabel='world z - ROI origin [mm]',aspect='equal')
            fig.colorbar(im,ax=ax,label='raw SDF [mm]',shrink=.7)
        ax=axs[row,2]
        for j,ref in enumerate(rr):
            b=packet(ref,'small');p=np.load(R/f'local_results/initialization/{ref}_small.npz');i=int(np.flatnonzero(p['observed'])[0])
            t=p['t_mm'][i];f=p['raw_sdf'][i];old=f+(cal[scene]['bias_network']-domains()[scene]['proposed_bias_network'])*domains()[scene]['mm_per_unit']
            x=t-b['start'][i];line=ax.plot(x,f,label=fmtref(ref),color='C'+str(j))[0];ax.plot(x,old,':',color=line.get_color(),alpha=.5)
            cross=np.flatnonzero((f[:-1]>0)&(f[1:]<=0));front=None
            if len(cross):
                k=int(cross[0]);front=t[k]+(t[k+1]-t[k])*f[k]/(f[k]-f[k+1]);ax.plot(front-b['start'][i],0,'o',color=line.get_color())
            evidence.append(dict(figure='Fig1',source=ref,split='small',selection='first fixed observed ray; no prediction selection',source_pixel=int(b['source_pixel'][i]),front_cross_mm=front))
        ax.axhline(0,color='black',lw=.8);ax.set(title='Real source rays: solid after / dotted before',xlabel='distance from certified prefix entry [mm]',ylabel='raw SDF [mm]');ax.legend()
    finish(fig,'Fig1_initialization_zero_and_front.png','UNTRAINED official MonoSDF | actual zero contours and sampled front intersections | GT unopened')

    stable=rows('STABLE_MASK_GRADIENT_TESTS.csv');fp=rows('metrics/FP32_FP64_CONSISTENCY.csv');anchor=rows('metrics/WEAK_HERO_ANCHOR_GRADIENTS.csv');math=rows('metrics/MATH_TARGET_EQUIVALENCE.csv')
    cases=['CALIBRATED_NORMAL','ALL_POSITIVE_FIELD','EMPTY_POSITIVE_RAYS','ALL_NEGATIVE_FIELD','RING_OCCLUDED_PREFIX'];labels=['normal','all positive','empty positive','all negative','Ring prefix']
    fig,axs=plt.subplots(2,2,figsize=(14,9),layout='constrained');x=np.arange(5)
    for j,(key,label) in enumerate([('old_geometry_gradient_norm','old BCE'),('stable_geometry_gradient_norm','stable BCE')]):
        vv=[]
        for case in cases:
            rs=[r for r in stable if r['case']==case and r['precision']=='FP64'];vv.append(np.median([float(r[key]) for r in rs if r[key]]))
        axs[0,0].bar(x+(j-.5)*.3,np.maximum(vv,1e-14),.3,label=label)
    axs[0,0].axhline(1e-10,color='red',ls='--',label='useful geometry threshold');axs[0,0].set(yscale='log',xticks=x,xticklabels=labels,ylabel='implicit-parameter gradient norm',title='Full neural autograd; zero bars shown at plotting floor 1e-14');axs[0,0].legend()
    for dtype,color in [('FP64','C0'),('FP32','C1')]:
        beta=[];geom=[]
        for field in ['POSITIVE','NEGATIVE']:
            aa=[r for r in anchor if r['field_control']==field and r['precision']==dtype];geom.append(np.median([float(r['geometry_gradient_norm']) for r in aa]))
            ss=[r for r in stable if r['case']=='ALL_'+field+'_FIELD' and r['precision']==dtype];beta.append(np.median([float(r['stable_beta_gradient_norm']) for r in ss]))
        axs[0,1].plot([0,1],geom,'o-',color=color,label=dtype+' weak HERO: geometry')
        axs[0,1].plot([0,1],beta,'x--',color=color,label=dtype+' stable Mask: beta')
    axs[0,1].set(yscale='log',xticks=[0,1],xticklabels=['all positive','all negative'],ylabel='parameter gradient norm',title='Beta-only gradient does not recover a surface');axs[0,1].legend(fontsize=8)
    a=np.array([float(r['FP64_loss']) for r in fp]);b=np.array([float(r['FP32_loss']) for r in fp]);axs[1,0].scatter(a,b,s=22);lims=[min(a.min(),b.min())*.8,max(a.max(),b.max())*1.2]
    axs[1,0].plot(lims,lims,'k--');axs[1,0].set(xscale='log',yscale='log',xlabel='stable loss FP64',ylabel='stable loss FP32',title='30/30 value and full-gradient precision checks pass')
    nanN=sum(r['old_loss_finite']=='False' for r in stable);maxerr=max(float(r['abs_error']) for r in math)
    texts=[f'Stable: {len(stable)}/{len(stable)} finite losses + full gradients',f'Old BCE: {nanN}/{len(stable)} nonfinite losses (all FP32)',f'80-digit reference: {len(math)}/{len(math)} equivalent target',f'Max absolute BCE difference: {maxerr:.3g}',
           'All-negative: 0/12 useful Mask geometry gradients','Weak HERO: 96/96 differential point directions toward f=0','No parameter updates; zero-crossing recovery NOT demonstrated']
    axs[1,1].axis('off');axs[1,1].text(.02,.96,'\n\n'.join(texts),va='top',fontsize=11)
    finish(fig,'Fig2_stable_mask_and_gradients.png','CONTROL EXPERIMENTS on real G01 rays and all 670,395 official parameters | no training')

    neural=rows('metrics/PER_REFERENCE_NEURAL_SUPERVISION.csv');fig,axs=plt.subplots(3,6,figsize=(19,10),layout='constrained')
    for j,ref in enumerate(refs):
        c,p,r=source(ref);b=packet(ref,'extra');pred=np.load(R/f'local_results/neural/{ref}_extra.npz');obs=pred['observed'];pix=b['source_pixel'];uv=np.c_[pix%640,pix//640]
        ax=axs[0,j];ax.imshow(Image.open(c['RGB']));ax.scatter(uv[obs&pred['render_hit'],0],uv[obs&pred['render_hit'],1],s=13,c='lime',label='front hit');ax.scatter(uv[obs&~pred['render_hit'],0],uv[obs&~pred['render_hit'],1],s=20,c='red',marker='x',label='miss');ax.set(title=fmtref(ref),xticks=[],yticks=[])
        rs=[next(r for r in neural if r['source']==ref and r['split']==sp) for sp in ['small','extra']]
        ax=axs[1,j];ax.bar([0,1],[float(r['hit_fraction']) for r in rs],color=['C0' if rs[0]['hit_gate']=='True' else 'crimson','C1']);ax.axhline(.5,color='red',ls='--');ax.set(ylim=(0,1.15),xticks=[0,1],xticklabels=['old small','disjoint extra'],ylabel='observed front-hit fraction' if j==0 else '')
        for k,rr in enumerate(rs):ax.text(k,float(rr['hit_fraction'])+.03,rr['front_hit_N']+'/'+rr['observed_HERO_N'],ha='center')
        ax=axs[2,j]
        for k,rr in enumerate(rs):ax.plot([0,1,2],[float(rr[t+'_geometry_gradient']) for t in ['Mask','RGB','Depth']],'o-',label=['small','extra'][k])
        ax.set(yscale='log',xticks=[0,1,2],xticklabels=['Mask','RGB','Depth'],ylabel='actual implicit gradient norm' if j==0 else '')
        if j==0:ax.legend()
    finish(fig,'Fig3_three_reference_neural_gate.png','REAL fixed source observations | green = front hit; red = miss | one shared UNTRAINED SDF per video; ref13 small FAIL retained')

    fig,axs=plt.subplots(2,4,figsize=(18,9),layout='constrained');regionnames=['P interior','P boundary','known negative','Ring','unknown'];cmap=ListedColormap(['#28be56','#f4bf35','#5079db','#777777','#f4f4f4']);visibility=[]
    for row,ref in enumerate([selected()['G01_004'][2],selected()['G01_005'][2]]):
        c,p,r=source(ref);b=packet(ref,'extra');pred=np.load(R/f'local_results/neural/{ref}_extra.npz');ax=axs[row,0];ax.imshow(Image.open(c['RGB']));ring=r['labels'].reshape(360,640)==2
        if ring.any():ax.contour(ring,levels=[.5],colors='black',linewidths=.7)
        ax.set(title=fmtref(ref)+' | actual RGB + Ring Mask',xticks=[],yticks=[])
        ax=axs[row,1];ax.imshow(r['sampling_class'].reshape(360,640),cmap=cmap,vmin=-.5,vmax=4.5);ax.set(title='Frozen five-class source semantics',xticks=[],yticks=[])
        visible=r['ROI_valid']&(r['mask_weight']>0);hero=(r['depth_weight']>0)&visible;z=np.zeros((230400,4));z[visible]=[.15,.45,1,.35];z[hero]=[0,1,.2,.65]
        ax=axs[row,2];ax.imshow(Image.open(c['RGB']));ax.imshow(z.reshape(360,640,4));ax.set(title='blue: finite Mask / green: qualified HERO',xticks=[],yticks=[])
        ax=axs[row,3];ids=np.flatnonzero((b['sampling_class']==3)&b['valid']&np.isfinite(b['Ring_t_mm']));assert len(ids)
        for k,i in enumerate(ids[:6]):
            ax.plot([b['start'][i],b['end'][i]],[k,k],color='C0',lw=4);ax.plot(b['Ring_t_mm'][i],k,'kx');visibility.append(dict(source=ref,pixel=int(b['source_pixel'][i]),prefix_start_mm=float(b['start'][i]),prefix_end_mm=float(b['end'][i]),Ring_t_mm=float(b['Ring_t_mm'][i]),end_before_Ring=True))
        ax.set(title='Actual Ring rays: finite prefix then CAD x',xlabel='ray t [mm]',ylabel='fixed sampled Ring ray index')
    handles=[plt.Line2D([],[],marker='s',ls='',color=cmap(i),label=n) for i,n in enumerate(regionnames)]
    fig.legend(handles=handles,loc='lower center',ncol=5,bbox_to_anchor=(.5,-.03))
    finish(fig,'Fig4_ring_visible_supervision.png','REAL source geometry | fixed CAD cuts integration before first Ring hit (0.05 mm margin) | no supervision behind CAD')
    save('provenance/FIGURE_EVIDENCE.json',dict(untrained=True,GT_opened=False,Fig1_ray_selection=evidence,Fig4_Ring_prefixes=visibility,
        figure_only_selection_does_not_change_any_gate=True,all_figures='real project source pixels / true official raw SDF; pathological controls explicitly labelled'))
    cards='\n'.join(f'<article><h2>{p.stem}</h2><img src="../figures/{p.name}"></article>' for p in sorted((R/'figures').glob('Fig*.png')))
    (R/'visualizations/index.html').write_text('<!doctype html><meta charset="utf-8"><title>E2.6 CPU evidence</title><style>body{font:16px sans-serif;background:#eee;margin:2em}img{width:100%;background:white}article{margin-bottom:3em}</style><h1>E2.6 CPU evidence — untrained / GPU NOT AUTHORIZED</h1><p>Frozen source rays. Failed coverage gates remain failed. No 3D reconstruction is claimed.</p>'+cards)
    print('FOUR_REAL_EVIDENCE_FIGURES_COMPLETE')

if __name__=='__main__':main()
