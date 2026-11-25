"""Frozen prediction evaluation on all 23 original views, no GT loading."""
import argparse,csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import binary_dilation
from ring_first_3d.mainline.paths import activate
activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
from projection_gate import stats
from ring_first_3d.synthetic.raster import ray_map
from pilot import TASK,inputs,sha

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();run=Path(args.run).resolve()
    if not (run/'PREDICTION_FROZEN.json').exists():raise ValueError('Prediction not frozen')
    final_sha=sha(run/'FINAL.npz');initial,views,ring,base,chart=inputs();final=dict(np.load(run/'FINAL.npz'));rows=[];maps={}
    for v in views:
        rz=ray_map(ring['V'],ring['F'],v['K'],v['C'],v['labels'].shape)['z'];known=~binary_dilation(v['labels']==2,iterations=3)
        for arm,b in [('INITIAL',initial),('PILOT',final)]:
            r=ray_map(b['V'],b['F'],v['K'],v['C'],v['labels'].shape);pred=r['valid']&(r['z']<rz-.05)
            rows.append(dict(id=v['id'],video=v['video'],role=v['role'],arm=arm,**stats(pred,v['labels']==1,known)));maps[v['id'],arm]=pred
    summary={role:{arm:{key:float(np.mean([r[key] for r in rows if r['role']==role and r['arm']==arm])) for key in ['IoU','Boundary_MAE_px','Boundary_Fscore_at2px']} for arm in ['INITIAL','PILOT']} for role in ['FIT','HOLDOUT']}
    summary.update(GT_status='NOT_EVALUATED_THIS_PILOT',GT_pose='unknown deployment pose',prediction_sha256=final_sha,independent_groups=1,views=23,scientific_status='LIMITED_UPDATE_EXECUTION_NOT_GENERAL_VALIDATION')
    out=TASK/'evidence'
    with (out/'PILOT_PER_VIEW.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    (out/'PILOT_EVALUATION.json').write_text(json.dumps(summary,indent=2)+'\n')
    chosen=[next(v for v in views if v['video']==video and v['role']==role) for video,role in [('004','FIT'),('005','FIT'),('004','HOLDOUT'),('005','HOLDOUT')]]
    fig,axes=plt.subplots(2,4,figsize=(16,8))
    for i,v in enumerate(chosen):
        for j,arm in enumerate(['INITIAL','PILOT']):
            ax=axes[j,i];ax.imshow(v['RGB']);ax.contour(v['labels']==1,levels=[.5],colors=['lime'],linewidths=.6);ax.contour(maps[v['id'],arm],levels=[.5],colors=['cyan'],linewidths=.6);r=next(r for r in rows if r['id']==v['id'] and r['arm']==arm);ax.set_title(f"{v['id']} {v['role']}\n{arm}: IoU {r['IoU']:.4f}; boundary {r['Boundary_MAE_px']:.2f}px");ax.axis('off')
    fig.suptitle('Actual RGB | green=observed Mask; cyan=predicted visible contour | geometry in mm; image in px | no GT');fig.tight_layout();fig.savefig(out/'PILOT_PROJECTIONS.png',dpi=135);plt.close(fig)
    fig=plt.figure(figsize=(12,5));P=np.r_[initial['V'],final['V'],ring['V']];center=(P.min(0)+P.max(0))/2;radius=np.ptp(P,axis=0).max()/2
    for i,(label,b) in enumerate([('Historical INITIAL',initial),('New 3-step PILOT',final)]):
        ax=fig.add_subplot(1,2,i+1,projection='3d');ax.plot_trisurf(*b['V'].T,triangles=b['F'],color='#4488bb',linewidth=.1,edgecolor='#336699',alpha=.85);ax.scatter(*ring['V'][::100].T,s=1,c='gray');ax.set(xlim=(center[0]-radius,center[0]+radius),ylim=(center[1]-radius,center[1]+radius),zlim=(center[2]-radius,center[2]+radius),xlabel='x mm',ylabel='y mm',zlabel='z mm',title=label);ax.set_box_aspect([1,1,1])
    fig.suptitle('Same physical scale and view | G01 | inferred whole body | no GT surface displayed');fig.tight_layout();fig.savefig(out/'PILOT_SURFACES.png',dpi=135);plt.close(fig)
    assert sha(run/'FINAL.npz')==final_sha
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
