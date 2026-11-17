"""Per-case native preview as soon as three paired predictions exist, CPU only."""
from visual_base import *
import argparse
def main():
    ap=argparse.ArgumentParser();ap.add_argument('case');n=ap.parse_args().case;tags=['Init-A','Init-B','Init-C'];models=[dict(np.load(R/'initializations'/n/(t+'.npz')))for t in tags]+[dict(np.load(R/'arms'/t/'local_results'/n/'FINAL.npz'))for t in tags];ring=np.load(R/'inputs'/n/'RING.npz');bounds=np.concatenate([m['V']for m in models]+[ring['V']]);fig,ax=plt.subplots(4,3,figsize=(15,16));held=load(R/'config/VIEW_SELECTION.json')[n]['HOLDOUT'];cid=held[0];a=np.load(R/'inputs'/n/(cid+'.npz'));cad=cast(scene(ring['V'],ring['F']),a['K'],a['T'],*a['labels'].shape)
    for j,t in enumerate(tags):
        model_panel(ax[0,j],n,models[j],bounds);ax[0,j].set_title(n+' '+t+' INITIAL');model_panel(ax[1,j],n,models[j+3],bounds);ax[1,j].set_title(t+' FINAL');model_panel(ax[2,j],n,models[j+3],bounds,angle=(0,0));ax[2,j].set_title(t+' FINAL world side');p=cast(scene(models[j+3]['V'],models[j+3]['F']),a['K'],a['T'],*a['labels'].shape);m=np.isfinite(p)&(p<cad);ax[3,j].imshow(a['RGB']);edge(ax[3,j],a['labels']==1,'lime');edge(ax[3,j],a['labels']==2,'cyan');edge(ax[3,j],m,'gold');ax[3,j].set_title(t+' fixed HOLDOUT '+cid,fontsize=8);ax[3,j].axis('off')
    fig.suptitle(n+' | Same mm coordinates / black fixed CAD / gray inferred cap\nPhase A: same downstream losses, optimizer and budget. HOLDOUT not used for selection. GT not opened.');fig.subplots_adjust(top=.94);finish(fig,'phase_A/'+n+'_Initialization_And_Update.png',120);print('PREVIEW_READY',n,flush=True)
if __name__=='__main__':main()
