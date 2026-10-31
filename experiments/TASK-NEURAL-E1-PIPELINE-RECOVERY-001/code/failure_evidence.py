"""Per-scene failure/limitation evidence; actual images, no new predictions."""
from common import *
from figures import solid_view, STAMP, plt
import textwrap

def main():
    D=load(R/'provenance/INPUT_ELIGIBILITY.json');V={v['id']:v for v in D['views']};gn=legacy_geometry_namespace(D)
    rows=[];folder=R/'figures/local';folder.mkdir(exist_ok=True)
    reasons={
      'G01_004':'C0 LIMITED: raw sequential frame identity unverified; cross-video transform unregistered. Three real references have shared HERO ancestors and depth conflicts. SDF mask adapter invalid; no new model run.',
      'G01_005':'C0 LIMITED: strict full-pipeline holdout=0. SDF full-ray opacity saturates. Old M3 CAD offset ~22 mm and predicted pose residual retained. These are old failures, no new model run.',
      'G06_004':'Known source leakage: raw00351 was an input to historical HERO G06_004_ref04. It remains DIAGNOSTIC_ONLY. No strict blind test is created by re-labelling.',
      'G07_004':'UNQUALIFIED_CAMERA_STRESS: frozen camera is not certified for normal success. raw00293 was an input to historical HERO G07_004_ref04. CPU adapter conversion is not camera qualification.',
      'G08_005':'LIMITED_STRESS: no pre-frozen strictly independent holdout. raw00943/raw01080 remain diagnostic targets. Conditional geometry conversion is not scientific success.'}
    for sid in ['G01_004','G01_005','G06_004','G08_005','G07_004']:
        c=next(c for c in D['references']if c['scene_id']==sid);tt=[t for t in D['targets']if t['scene']==sid]
        t=next((t for t in tt if t['known_HERO_input_of']),tt[0]);v=V[t['target']]
        A=np.asarray(Image.open(c['RGB']).convert('RGB'));labels=np.asarray(Image.open(c['Mask']));over=A/255.
        over[labels==1]=.6*over[labels==1]+.4*np.array([1.,.1,.5]);over[labels==2]=.4*over[labels==2]+.6*np.array([0.,.8,.9])
        fig,ax=plt.subplots(1,3,figsize=(17,6));ax[0].imshow(over);ax[0].axis('off');ax[0].set_title(c['id']+' real source RGB/Mask',fontsize=10)
        ax[1].imshow(np.asarray(Image.open(v['RGB']).convert('RGB')));ax[1].axis('off');ax[1].set_title(t['target']+'\n'+t['holdout_tier'],fontsize=10)
        P,col,_,_=gn['points'](c['id']);rm=ring(c['ring']);solid_view(ax[2],P,col,rm,vis.limits([P],rm),title=sid+' existing source XYZ / mm\n'+c['condition'],size=.4)
        fig.suptitle(sid+' failure/limitation evidence — '+STAMP,fontsize=12)
        fig.text(.035,.035,'\n'.join(textwrap.wrap(reasons[sid],155))+'\nRGB SHA256: '+sha(v['RGB'])+' | HERO input of: '+str(t['known_HERO_input_of']),fontsize=9)
        fig.subplots_adjust(top=.84,bottom=.22,wspace=.2)
        p=folder/(sid+'_failure_evidence.png');fig.savefig(p,dpi=120);plt.close(fig)
        rows.append(dict(scene=sid,reason=reasons[sid],source=c['id'],target=t['target'],target_RGB=asset(v['RGB']),
            parent_HERO=t['known_HERO_input_of'],figure=str(p),figure_SHA256=sha(p),new_model_run_N=0,measurement_mm=np.nan))
    save('provenance/PER_SCENE_FAILURE_EVIDENCE.json',rows)
    print('PER_SCENE_EVIDENCE_COMPLETE',len(rows),flush=True)

if __name__=='__main__':main()
