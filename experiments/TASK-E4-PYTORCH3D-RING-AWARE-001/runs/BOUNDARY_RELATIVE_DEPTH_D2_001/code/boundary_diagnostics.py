from common import *
from evaluate import pointcast
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 assert load(R/'assets_index/PREDICTIONS_FROZEN.json')['all_expected_finals'];rows=[];cfg=load(R/'config/PROTOCOL.json')
 for name in cfg['cases']:
  rr=np.load(R/'inputs'/name/'RING.npz');rs=scene(rr['V'],rr['F'])
  for arm in cfg['arms']:
   m=np.load(R/'local_results'/name/arm/'FINAL.npz');rt=scene(m['V'],m['F'])
   for v in getcase(name)['views']:
    cid=v['id'];o=np.load(R/'depth_observations'/(cid+'.npz'));ray=np.c_[o['uv'],np.ones(len(o['uv']))]@np.linalg.inv(o['K']).T;X=(ray*o['z'][:,None])@o['T'][:3,:3].T+o['T'][:3,3];_,_,z=pointcast(rt,X,o['K'],o['T']);_,_,cz=pointcast(rs,X,o['K'],o['T']);hit=np.isfinite(z)&(z>0)&(z<cz-.05);dist=np.minimum(o['distance_background_px'],o['distance_ring_px']);kind=o['distance_background_px']<=o['distance_ring_px'];err=z-o['z'];r=abs(err)/.5;cost=np.where(hit,np.minimum(np.where(r<1,.5*r*r,r-.5),9.5),9.5)
    for edge in['Background','Ring']:
     for lo,hi in[(0,4),(4,8),(8,float('inf'))]:
      ix=(kind if edge=='Background'else~kind)&(dist>lo)&(dist<=hi);good=ix&hit
      rows.append(dict(case=name,arm=arm,source=cid,role=v['role'],nearest_boundary=edge,distance_interval_px=str((lo,hi)),fixed_N=int(ix.sum()),hit_N=int(good.sum()),unhit_N=int((ix&~hit).sum()),weight_mean=float(o['boundary_weight'][ix].mean())if ix.any()else None,conditional_depth_error_mm=stats(err[good]),fixed_denominator_cost=float(cost[ix].mean())if ix.any()else None,same_ID_set_across_arms=True))
 table('metrics/BOUNDARY_STRATIFIED_DEPTH.csv',rows)
 fig,axs=plt.subplots(6,2,figsize=(14,21));COL={'B':'#2b7bba','E1':'#e79920','E2':'#24925c','E3':'#9b57b4'};prev=R.parent/'PROGRESSIVE_HERO_001'
 for i,c in enumerate(cfg['cases']):
  for a in cfg['arms']:
   p=prev/'metrics'/('virtual_B_TRAINING.csv'if c=='virtual_IIa'else'real_B_TRAINING.csv')if a=='B'and c in cfg['reuse_B']else R/'metrics'/(c+'_'+a+'_TRAINING.csv');h=list(csv.DictReader(p.open()));x=[int(v['step'])for v in h];axs[i,0].plot(x,[float(v['total'])for v in h],c=COL[a],label=a);axs[i,1].plot(x,[float(v['gradient_norm'])for v in h],c=COL[a],label=a)
  for j,label in enumerate(['total loss (objectives differ)','actual total parameter gradient norm']):axs[i,j].set(title=c+' | '+label,xlabel='optimizer step');axs[i,j].set_yscale('log');axs[i,j].grid(alpha=.2);axs[i,j].legend(fontsize=8)
 fig.suptitle('All 300 updates, no selected checkpoint | B/E1/E2/E3 same local geometry schedule\nTotal loss values have different definitions and must not be used to rank model accuracy.');fig.tight_layout(rect=[0,0,1,.96]);fig.savefig(R/'figures/full/Loss_And_Gradient_Curves.png',dpi=110);plt.close(fig)
if __name__=='__main__':main()
