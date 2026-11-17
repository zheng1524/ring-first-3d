"""All five frozen Ip predictions against GT; no ranking or new registration."""
from visual_base import *

def main():
    ips=load(R/'config/PROTOCOL.json')['phase_B']['cases']
    tags=['Stalk-A','Stalk-B','Stalk-C']
    metrics=load(R/'metrics/BLENDER_GEOMETRIC_METRICS.json')
    fig=plt.figure(figsize=(15,18))
    for i,n in enumerate(ips):
        g=np.load(R/'evaluation_only'/n/'ORIGINAL_BLENDER_GT_MM.npz')
        mm=[np.load(R/'local_results/aligned'/n/(t+'.npz')) for t in tags]
        bounds=np.r_[g['V'],*[m['V'] for m in mm]]
        center=(bounds.min(0)+bounds.max(0))/2
        rad=float(np.ptp(bounds,axis=0).max())*.53
        for j,(tag,m) in enumerate(zip(tags,mm)):
            ax=fig.add_subplot(len(ips),3,3*i+j+1,projection='3d')
            ax.add_collection3d(Poly3DCollection(g['V'][g['F']],facecolors=(.5,.5,.5,.28),edgecolors='none'))
            ax.add_collection3d(Poly3DCollection(m['V'][m['F']],facecolors=(.32,.20,.68,.72),edgecolors='none'))
            ax.set(xlim=(center[0]-rad,center[0]+rad),ylim=(center[1]-rad,center[1]+rad),zlim=(center[2]-rad,center[2]+rad))
            ax.set_box_aspect((1,1,1));ax.view_init(15,-65);ax.tick_params(labelsize=6)
            q=next(x for x in metrics if x['case']==n and x['label']==tag)
            ax.set_title(n+' '+tag+' | CD %.4f mm'%q['Chamfer_MAE_mm'],fontsize=9)
    fig.suptitle('All5 Ip | gray independent Blender / purple frozen prediction\nAfter Ring-based Metric Recovery and Best 6-DoF Rigid Alignment\nOne stored SE(3) per prediction, scale1; same per-case bounds. Missing stalk remains visible.',fontsize=12)
    fig.subplots_adjust(top=.93,hspace=.20,wspace=.04)
    finish(fig,'details/All5_Ip_Best_Rigid_GT_Comparison.png',125)
    print('ALL_IP_GT_REVIEW_WRITTEN',flush=True)

if __name__=='__main__':main()
