from g5_common import *
import inspect
sys.path.insert(0,str(DXY/'src'))
from dxy_mid._engine.ring_holes import run as holes
from dxy_mid._engine.components import FrameInput
from dxy_mid._engine.v81_components import existing_ring_check
from dxy_mid.selection import evaluate as quality
source=SYN/'scripts/adapter.py'
ns=dict(np=np,cv2=cv2,hashlib=hashlib,holes=holes,FrameInput=FrameInput,existing_ring_check=existing_ring_check,quality=quality);extract(source,['edges','adapt'],ns)
def main():
 verify('inputs');freeze('observations_protocol',[Path(__file__),R/'scripts/g5_common.py',source]+[Path(inspect.getsourcefile(f)) for f in [holes,existing_ring_check,quality]])
 rec=[]
 for a in ledger():
  im=image(a);lab=labels(a);ob,s=ns['adapt'](im,lab,a['id']);out={}
  for key,v in [('q',np.r_[ob['ring_train'],ob['ring_heldout']]),('p',ob['visible_region']),('b',ob['background_region'])]:
   # Image-space deterministic disjoint subsets; no ellipse samples as observations.
   order=np.lexsort((v[:,0],v[:,1]));v=v[order];v=v[np.linspace(0,len(v)-1,min(len(v),640 if key!='q' else 256),dtype=int)] if len(v) else v
   test=np.arange(len(v))%5==0;out[key+'_train']=v[~test];out[key+'_held']=v[test]
  np.savez_compressed(R/f"observations/{a['id']}.npz",**ob,**out);rec.append(s);print('DXY_ADAPTER',a['id'],s['DXY_valid'],'visible',s['raw_visible_ring_pixels'],'self candidates',s['background_facing_contour_candidates'],flush=True)
 save('metrics/ring_observations.json',rec);freeze('observations',list((R/'observations').glob('*.npz'))+[R/'metrics/ring_observations.json'])
if __name__=='__main__':main()
