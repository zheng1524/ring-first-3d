from p3d import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
COLORS=['#000000','#288be3','#f6a623','#858585','#b7b7b7']

def main():
    assert load(R/'metrics/PROJECTION_GATE.json')['passed'],'Projection gate must pass'
    rows=[]
    for name in ['virtual','real']:
        c=Case(name);ids=[c.fit[0],c.fit[-1]]
        fig,axes=plt.subplots(len(ids),6,figsize=(22,7),squeeze=False)
        for k,cid in enumerate(ids):
            d=c.views[cid];side=np.load(R/'inputs'/name/(cid+'_SIDES.npz'));samples=load(R/'metrics/sides'/(cid+'.json'))
            with torch.no_grad():
                fr=c.fragments(c.base,cid);L,alpha,w,visibility,p=c.aware(fr,cid,True);bl=c.baseline(fr,cid)
                z=c.hard(c.base,cameras=d['cam']).zbuf[0,...,0];present=z>0;cad=d['cad_finite'];front=present&cad&(z<d['cad_z']-.05/c.scale);behind=present&cad&(z>d['cad_z']+.05/c.scale)
            ax=axes[k];ax[0].imshow(d['rgb']);ax[0].contour(d['labels']==1,levels=[.5],colors=['lime'],linewidths=.6);ax[0].contour(d['labels']==2,levels=[.5],colors=['cyan'],linewidths=.6);ax[0].set_title(cid+'\n'+('Blender labels (not clinical RGB)'if name=='virtual'else'Frozen real RGB + original Mask'))
            ax[1].imshow(d['rgb']);masked=np.ma.masked_where(side['classes']==0,side['classes']);ax[1].imshow(masked,cmap=ListedColormap(COLORS),vmin=0,vmax=4,alpha=.75);ax[1].set_title('A blue / B orange / C gray / D lightgray')
            # Actual selected sections, not schematic arrows. Deterministic thinning by sample index.
            shown=[s for s in samples if 'sites'in s][::max(1,len(samples)//12)]
            ax[2].imshow(d['rgb'])
            for s in shown:
                ex=np.array(s['exits']);sites=np.array(s['sites']);color=COLORS['ABCD'.index(s['class_final'])+1]
                ax[2].plot(ex[:,0],ex[:,1],color=color,lw=1.4);ax[2].scatter(sites[:,:,0].ravel(),sites[:,:,1].ravel(),s=12,c=color,edgecolors='white',linewidths=.3)
            ax[2].set_title('Actual nearest exits + sample sites')
            ax[3].imshow(bl.cpu(),vmin=0,vmax=1,cmap='Greens');ax[3].contour(cad.cpu(),levels=[.5],colors=['black'],linewidths=.8);ax[3].set_title('Official body alpha + fixed CAD footprint')
            rel=np.zeros(c.size,np.int8);rel[behind.cpu().numpy()]=1;rel[front.cpu().numpy()]=2
            ax[4].imshow(rel,cmap=ListedColormap(['#eeeeee','#288be3','#e33737']),vmin=0,vmax=2);ax[4].set_title('CAD before body: blue / body before CAD: red')
            effective=np.zeros(c.size+(3,));effective[:]=.8;effective[d['target'].cpu().numpy()>0]=[.1,.8,.2];effective[(w.cpu().numpy()<.05)&(d['target'].cpu().numpy()==0)]=[.2,.5,1];effective[front.cpu().numpy()]=[1,.1,.1]
            pp=R/'local_results/occlusion_audit';pp.mkdir(parents=True,exist_ok=True);np.savez_compressed(pp/(cid+'.npz'),effective_RGB=effective,actual_weight=w.cpu().numpy(),aware_alpha=alpha.cpu().numpy(),baseline_alpha=bl.cpu().numpy(),front=front.cpu().numpy(),behind=behind.cpu().numpy())
            ax[5].imshow(effective);ax[5].set_title('Effective loss: green positive / blue relaxed\nred front conflict / gray known background')
            for a in ax:a.set_axis_off()
            rows.append(dict(case=name,view=cid,baseline_L2=float(((bl-d['target'])**2).mean()),aware_L2=float(L),CAD_behind_N=int(behind.sum()),CAD_front_N=int(front.sum()),positive_preserved_N=int((d['target']>0).sum()),relaxed_negative_N=int(((w<.05)&(d['target']==0)).sum()),large_visible_foreground_wrongly_masked_N=int(((w<1)&(d['target']>0)).sum()),shown_cross_sections=[s['sample_id']for s in shown]))
        fig.suptitle('PRE-OPTIMIZATION Ring evidence audit — fixed cameras / no geometric updates',fontsize=14);fig.tight_layout();fig.savefig(R/'figures'/('Occlusion_Audit_'+name+'.png'),dpi=160);plt.close(fig)
    table('metrics/OCCLUSION_AUDIT.csv',rows);save('metrics/OCCLUSION_AUDIT.json',dict(rows=rows,figures=[asset(R/'figures'/('Occlusion_Audit_'+s+'.png'))for s in['virtual','real']],optimization_started=False))
if __name__=='__main__':main()
