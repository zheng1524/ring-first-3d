"""CPU-only interrupted-run preview. No optimization, GT or final-arm selection."""
from visual_base import *

def main():
    dest=R/'figures/progress_20261109';dest.mkdir(parents=True,exist_ok=True)
    reps=load(R/'config/REPRESENTATIVE_VIEWS.json');cases=load(R/'config/CASE_LOCK.json');models=[]
    for c in cases:
        n=c['name'];folder=R/'arms/S8/local_results'/n;final=folder/'FINAL.npz'
        if final.exists():
            p=final;status=load(R/'arms/S8/metrics'/(n+'_RUN.json'))['status']
        else:
            saved=list(folder.glob('ACCEPTED_*.npz'))+list(folder.glob('ATTEMPT_*.npz'))
            if not saved:continue
            # Chronologically latest complete checkpoint, never by shape or loss.
            p=max(saved,key=lambda x:int(np.load(x)['attempt']));status='INTERRUPTED_CHECKPOINT_NOT_FINAL'
        a=dict(np.load(p));models.append((n,a,p,status))
    fig,ax=plt.subplots(len(models),3,figsize=(13,3.0*len(models)),squeeze=False)
    fig2,bx=plt.subplots(len(models),3,figsize=(15,3.0*len(models)),squeeze=False);rows=[]
    for i,(n,a,path,status)in enumerate(models):
        init=dict(np.load(R/'inputs'/n/'INITIAL.npz'));s0=dict(np.load(R/'arms/S0/local_results'/n/'FINAL.npz'));ring=np.load(R/'inputs'/n/'RING.npz');bounds=np.concatenate([init['V'],s0['V'],a['V'],ring['V']]);label=f"S8 accepted={int(a['accepted'])}, attempt={int(a['attempt'])}"
        if status=='INTERRUPTED_CHECKPOINT_NOT_FINAL':label+=' NOT FINAL'
        for j,(title,m)in enumerate([('Frozen INITIAL',init),('S0 cached original013 control',s0),(label,a)]):
            model_panel(ax[i,j],n,m,bounds);ax[i,j].set_title(n+' '+title,fontsize=8)
        cid=reps[n]['HOLDOUT']or reps[n]['FIT'];im=np.load(R/'inputs'/n/(cid+'.npz'));cad=np.load(R/'runtime/cad_depth'/(cid+'.npz'))['z'];lab=im['labels'];measures={}
        for j,(title,m)in enumerate([('Observed RGB / Mask',None),('S0',s0),(label,a)]):
            q=bx[i,j];q.imshow(im['RGB']);edge(q,lab==1,'lime');edge(q,lab==2,'cyan')
            if m is not None:
                z=cast(scene(m['V'],m['F']),im['K'],im['T'],*lab.shape);pred=np.isfinite(z)&(z<cad);known=lab!=2;target=lab==1;tp=int((pred&target).sum());fn=int((~pred&target).sum());fp=int((pred&known&~target).sum());iou=tp/max(1,tp+fn+fp);edge(q,pred,'gold');rgba=np.zeros((*lab.shape,4));rgba[(lab==1)&~pred]=[.1,.25,1,.5];rgba[(lab==0)&pred]=[1,.1,.04,.5];q.imshow(rgba);title+=f' IoU={iou:.3f}';measures['S0'if j==1 else'S8_checkpoint']=dict(IoU=iou,TP=tp,FN=fn,FP=fp,Mask_N=int(target.sum()))
            q.set_title(n+' '+cid+'\n'+title,fontsize=8);q.axis('off')
        rows.append(dict(case=n,status=status,source=asset(path),accepted=int(a['accepted']),attempt=int(a['attempt']),fixed_representative_view=cid,metric_definition='Single fixed original013 HOLDOUT view; observed Ring excluded from negative pixels; NOT full pooled/final evaluation',metrics=measures))
    fig.suptitle('INTERRUPTED RUN PREVIEW | Frozen INITIAL / S0 / available S8\nActual meshes, same per-case millimeter extent, black CAD; gray inferred cap. No S16/S32 results yet.',fontsize=12)
    fig2.suptitle('INTERRUPTED RUN PREVIEW | Fixed original013 Mesh-update HOLDOUT views\nGreen observed Polyp, cyan Ring, gold predicted boundary; blue missing, red extra known background. No GT read.',fontsize=12)
    fig.subplots_adjust(top=.96,bottom=.01,left=.02,right=.98,hspace=.22,wspace=.08)
    fig2.subplots_adjust(top=.96,bottom=.01,left=.02,right=.98,hspace=.25,wspace=.08)
    finish(fig,'progress_20261109/Available_Mesh_Comparison.png',110);finish(fig2,'progress_20261109/Available_Holdout_Contours.png',110)
    save('metrics/INTERRUPTED_PREVIEW.json',dict(epoch=time.time(),GT_accessed=False,optimization_executed=False,complete_S8_groups=7,incomplete_S8_case='G08',S16_S32_not_run=True,rows=rows))
    table('metrics/INTERRUPTED_PREVIEW.csv',[dict(case=q['case'],status=q['status'],accepted=q['accepted'],attempt=q['attempt'],view=q['fixed_representative_view'],S0_IoU=q['metrics']['S0']['IoU'],S8_available_IoU=q['metrics']['S8_checkpoint']['IoU'])for q in rows])
    print('CPU_PREVIEW_READY',len(rows),dest,flush=True)

if __name__=='__main__':main()
