"""Bounded last backend control: coarse bins versus official naive rasterizer."""
from tape import *
import hashlib
def main():
 guard_optimizer();c=Case('G02');ch=FreeVertices(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch);obj.attempt=40;obj.depth.begin(ch.mesh(q));records=[]
 for mode in ['DEFAULT_COARSE','NAIVE_BIN0']:
  c.renderer.rasterizer.raster_settings.bin_size=None if mode=='DEFAULT_COARSE'else 0
  for cid in c.fit:
   first=None
   for rep in range(4):
    m=ch.mesh(q);fr=c.fragments(m,cid);base,alpha,w,*_=c.aware(fr,cid,True);g=gradient(base,q);arrays={k:getattr(fr,k).detach().cpu().numpy()for k in ['pix_to_face','zbuf','bary_coords','dists']};v=m.verts_packed().detach().cpu().numpy();state=dict(arrays=arrays,g=g,v=v)
    if first is None:first=state
    changes={k:dict(changed_N=int((a!=first['arrays'][k]).sum()),max_abs=float(abs(a.astype(float)-first['arrays'][k].astype(float)).max()))for k,a in arrays.items()};records.append(dict(mode=mode,view=cid,repeat=rep,normalized_input_vertices_exact_equal=bool(np.array_equal(v,first['v'])),fragment_changes=changes,silhouette_gradient_repeat_relative=float((g-first['g']).norm()/first['g'].norm().clamp_min(1e-30))))
 out=dict(rows=records,summary={mode:max(x['silhouette_gradient_repeat_relative']for x in records if x['mode']==mode)for mode in ['DEFAULT_COARSE','NAIVE_BIN0']},CUBLAS_WORKSPACE_CONFIG=os.environ.get('CUBLAS_WORKSPACE_CONFIG'),allow_tf32=torch.backends.cuda.matmul.allow_tf32,optimizer_steps=0,training_backend_not_changed=True);save('metrics/G02_BINNING_CONTROL.json',out);print('BINNING_CONTROL',out['summary'],flush=True)
if __name__=='__main__':main()
