"""Actual pre/post BA camera locations in the same metric world; display-only supplement."""
from plot_common import *
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def main():
 checkfreeze('provenance/ALL_CAMERAS_FROZEN_BEFORE_COVERAGE_HERO.json');fig=plt.figure(figsize=(14,12));rows=[]
 for i,g in enumerate(GROUPS):
  before={v['id']:v for v in load(N/'config'/(g+'_INITIAL_CAMERAS.json'))}
  if g=='G01':
   for cid in list(before):
    p=N/'registration/G01/NATIVE005_EXTENSION'/(cid+'_INITIAL.json')
    if p.exists():before[cid]=load(p)
  final={v['id']:v for v in load(camera_file(g))};r=load(N/'registration'/g/('JOINT_FULL6_NATIVE005_FINAL.json'if g=='G01'else'JOINT_FULL6_FINAL.json'));P0=np.array([before[c]['C'][:3][3]if False else np.array(before[c]['C'])[:3,3]for c in r['selected']]);P1=np.array([np.array(final[c]['C'])[:3,3]for c in r['selected']]);d=P1-P0;norm=np.linalg.norm(d,axis=1);ax=fig.add_subplot(2,2,i+1,projection='3d');conf=next(c for c in load(N/'config/FOUR_GROUP_INPUTS.json')if c['group']==g);ring=np.load(conf['ring']['path']);pc=Poly3DCollection(ring['V'][ring['F']],facecolor='black',edgecolor='none',alpha=1);ax.add_collection3d(pc);ax.scatter(*P0.T,c='#396ca8',s=17,label='frozen RF+RGB before');ax.scatter(*P1.T,c='#db7d25',s=17,label='joint full6 after');ax.quiver(*P0.T,*d.T,color='#b32235',arrow_length_ratio=.3,normalize=False,length=1.,linewidth=.8);allp=np.r_[P0,P1,ring['V']];lo=allp.min(0);hi=allp.max(0);center=(hi+lo)/2;radius=max(hi-lo)/2*1.08
  for dim in ['x','y','z']:getattr(ax,'set_'+dim+'lim')(center['xyz'.index(dim)]-radius,center['xyz'.index(dim)]+radius)
  ax.set_box_aspect((1,1,1));ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm');ax.set_title(f'{g} | actual {len(P0)} BA subset cameras\ncenter displacement mean={norm.mean():.4f}, max={norm.max():.4f} mm');ax.legend(fontsize=7)
  rows.append(dict(group=g,actual_cameras=len(P0),center_delta_mm=stats(norm),old=P0,new=P1,actual_vectors_mm=d,arrows_scale=1.,no_geometry_changed=True))
 fig.suptitle('Fig7b | Actual registration pre/post camera changes, black fixed CAD\nSame group metric coordinates and bounds; arrows are true candidate displacements (1x), not illustrative vectors.');fig.tight_layout(rect=[0,0,1,.94]);finish(fig,'Fig7b_Actual_Camera_Registration_Changes.png');save('metrics/ACTUAL_CAMERA_BEFORE_AFTER_VECTORS.json',rows);freeze('provenance/POSE_DELTA_VISUALIZATION_FROZEN.json',[Path(__file__),N/'figures/Fig7b_Actual_Camera_Registration_Changes.png',N/'metrics/ACTUAL_CAMERA_BEFORE_AFTER_VECTORS.json'],display_only=True,no_prediction_changed=True)
if __name__=='__main__':main()
