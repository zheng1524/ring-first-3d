"""Reproducible direct-Blender pixel-grid cache; refuse existing optimized output."""
from common import *
from prepare016 import link
import shutil
def main():
 reg=load(R/'config/VIRTUAL_RUN_REGISTRY.json');assert not any(Path(x['final']).exists()for x in reg),'Virtual observations already frozen by optimization'
 files=[]
 for p in(R/'local_results/virtual_render320').glob('*.png'):
  a=np.asarray(Image.open(p).convert('RGB'));target=(a[:,:,0]>=128)&(a[:,:,0]>a[:,:,1]);out=R/'inputs/virtual_Ip'/(p.stem+'_RENDER_TARGET.npz');np.savez_compressed(out,target=target,source_pixels=a);files.append(asset(out))
  for x in reg:link(out,R/'arms'/x['tag']/'inputs/virtual_Ip'/out.name)
 assert len(files)==5
 for x in reg:x['script']='train_virtual_grid016.py';x['input_grid_repair']='direct Blender320; native Mask/cameras unchanged'
 save('config/VIRTUAL_RUN_REGISTRY.json',reg)
 for p in[R/'code/train_virtual_grid016.py',R/'code/virtual_grid_case016.py',R/'code/virtual_probe_grid016.py',R/'code/virtual_gate_grid016.py',R/'config/VIRTUAL_RUN_REGISTRY.json']:files.append(asset(p))
 save('provenance/VIRTUAL_GRID_INPUTS_AND_CODE_FROZEN.json',dict(epoch=time.time(),files=files,optimizer_steps=0,thresholds_unchanged=True))
 print('VIRTUAL_GRID_CACHE_FROZEN',flush=True)
if __name__=='__main__':main()
