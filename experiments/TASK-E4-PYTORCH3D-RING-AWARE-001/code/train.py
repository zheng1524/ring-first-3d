from p3d import *
from pytorch3d.io import save_obj,load_obj
import argparse

def main():
    ap=argparse.ArgumentParser();ap.add_argument('case',choices=['virtual','real']);ap.add_argument('arm',choices=['Baseline','RingAware']);args=ap.parse_args()
    guard_optimizer()
    for fn in ['OFFICIAL_GATE','PROJECTION_GATE','GRADIENT_GATE']:assert load(R/'metrics'/(fn+'.json'))['passed'],fn
    assert (R/'metrics/OCCLUSION_AUDIT.json').exists()
    freeze=load(R/'assets_index/PREOPT_FREEZE.json')
    for a in freeze['files']:assert sha(a['path'])==a['sha256'],a['path']
    c=Case(args.case);cfg=load(R/'config/FROZEN.json');np.random.seed(cfg['seed']);torch.manual_seed(cfg['seed'])
    out=R/'local_results'/args.case/args.arm;out.mkdir(parents=True,exist_ok=True);assert not(out/'FINAL.npz').exists()
    offset=torch.zeros_like(c.base.verts_packed(),requires_grad=True);opt=torch.optim.SGD([offset],lr=1.,momentum=.9);hist=[];times=[];t0=time.time()
    def snapshot(step):
        m=c.base.offset_verts(offset.detach());V,F=c.mm(m);np.savez_compressed(out/('STEP_%04d.npz'%step),V=V,F=F,offset=offset.detach().cpu().numpy(),center=c.center,scale=c.scale)
        trimesh.Trimesh(V,F,process=False).export(out/('STEP_%04d_mm.ply'%step))
        torch.save(dict(step=step,offset=offset.detach().cpu(),optimizer=opt.state_dict(),numpy_state=np.random.get_state(),torch_state=torch.get_rng_state(),cuda_state=torch.cuda.get_rng_state(),config=cfg),out/('STEP_%04d.pt'%step))
    snapshot(0)
    for i in range(cfg['project_steps']):
        tick=time.time();opt.zero_grad();m=c.base.offset_verts(offset);prior=regularizers(m);chosen=np.random.permutation(len(c.fit))[:2];l=sum(c.loss(m,c.fit[j],args.arm)for j in chosen)/len(chosen)
        total=l+prior['edge']+.01*prior['normal']+prior['laplacian'];total.backward()
        if not torch.isfinite(total)or not torch.isfinite(offset.grad).all():
            save('metrics/'+args.case+'_'+args.arm+'_INTERRUPTED.json',dict(step=i,reason='NaN/Inf actual numerical failure'));raise FloatingPointError('NaN/Inf')
        grad=float(offset.grad.norm());opt.step();torch.cuda.synchronize();times.append(time.time()-tick)
        hist.append(dict(case=args.case,arm=args.arm,step=i+1,views=[c.fit[j]for j in chosen],silhouette=float(l.detach()),total=float(total.detach()),full_vertex_gradient_norm=grad,max_displacement_mm=float(offset.detach().norm(dim=1).max())*c.scale,elapsed_seconds=time.time()-t0,seconds_per_step=times[-1],**{k:float(v.detach())for k,v in prior.items()}))
        if(i+1)in cfg['project_checkpoints']:snapshot(i+1)
        if(i+1)%25==0:print(args.case,args.arm,i+1,'L',hist[-1]['total'],'elapsed',time.time()-t0,flush=True);table('metrics/'+args.case+'_'+args.arm+'_TRAINING.csv',hist)
    m=c.base.offset_verts(offset.detach());V,F=c.mm(m);np.savez_compressed(out/'FINAL.npz',V=V,F=F);trimesh.Trimesh(V,F,process=False).export(out/'FINAL_mm.ply')
    save_obj(str(out/'FINAL_normalized.obj'),m.verts_packed(),m.faces_packed(),decimal_places=16)
    v,f,_=load_obj(str(out/'FINAL_normalized.obj'),device=device,load_textures=False);reload=Meshes(verts=[v],faces=[f.verts_idx])
    with torch.no_grad():err=max(float((c.renderer(m,cameras=d['cam'])-c.renderer(reload,cameras=d['cam'])).abs().max())for d in c.views.values())
    save('metrics/'+args.case+'_'+args.arm+'_RUN.json',dict(case=args.case,arm=args.arm,completed_steps=cfg['project_steps'],elapsed_seconds=time.time()-t0,mean_seconds_per_step=float(np.mean(times)),peak_GPU_bytes=torch.cuda.max_memory_allocated(),OBJ_reload_max_alpha_error=err,initial_vertex_count=len(c.V),final_vertex_count=len(V),GT_read=False,optimizer='official SGD(lr=1,momentum=.9)',mesh_postprocessing=False,displacement_mm=stats(np.linalg.norm(V-c.V,axis=1))))
    print('Completed',args.case,args.arm,flush=True)
if __name__=='__main__':main()
