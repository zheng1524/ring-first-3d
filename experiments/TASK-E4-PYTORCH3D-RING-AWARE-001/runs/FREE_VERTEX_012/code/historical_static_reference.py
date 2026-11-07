from visual_common import *

def main():
 assert(R/'assets_index/PREDICTIONS_FROZEN_BEFORE_GT.json').exists();old=R.parent/'PROGRESSIVE_HERO_001';case=load(old/'inputs/real/CASE.json');assert case['identity']=='GP_Ip_12.0mm_closed_R10_single_refY/video004'and case['unit']=='mm';path=old/'local_results/real/D/FINAL.npz';z=np.load(path);rr=np.load(old/'inputs/real/RING.npz');currentRing=np.load(R/'inputs/G01/RING.npz');assert np.array_equal(rr['V'],currentRing['V'])and np.array_equal(rr['F'],currentRing['F']);new=model('G01','FINAL012');bound=np.r_[bounds('G01'),z['V']];fig,axs=plt.subplots(2,3,figsize=(15,10))
 for j,angle in enumerate([(65,-90),(0,-65),(30,-65)]):
  for i,(V,F,col,title)in enumerate([(z['V'],z['F'],'#da9a40','Historical progressive D: STATIC ONLY'),(new['V'],new['F_solid'],COL['FINAL012'],'012 FREE FINAL: actual current output')]):
   im,s=actual_mesh_image(V,F,rr['V'],rr['F'],bound,*angle,col);axs[i,j].imshow(im);axs[i,j].plot([20,20+2*s],[375,375],c='black',lw=1.4);axs[i,j].text(20,365,'2 mm',fontsize=6);axs[i,j].axis('off');axs[i,j].set_title(title+'\nviewer '+str(angle),fontsize=9)
 fig.suptitle('G01-video004 historical stalk-direction deformation: static visual reference only\nExact same world-mm Ring CAD; shared viewer and scale. Historical protocol/initialization differ, so this is not a scientific extra arm.\nHistorical geometry was first read after 012 prediction freeze; it never generated, selected or replaced any 012 vertex.',fontsize=11);fig.tight_layout(rect=[0,0,1,.9]);finish(fig,'full/G01_Historical_Static_Reference.png');save('assets_index/HISTORICAL_STATIC_REFERENCE.json',dict(asset=asset(path),identity=case['identity'],unit='mm',Ring_geometry_exact_match=True,read_only_after_prediction_freeze=True,not_optimization_input=True,not_output_fallback=True,not_in_quantitative_ranking=True))

if __name__=='__main__':main()
