"""Standalone transcription of official tutorial silhouette cells, unchanged objective/budget."""
from p3d import *
from pytorch3d.io import load_obj,save_obj
from pytorch3d.utils import ico_sphere
from pytorch3d.renderer import look_at_view_transform,FoVPerspectiveCameras

def main():
    guard_optimizer();torch.manual_seed(20261106);np.random.seed(20261106)
    out=R/'local_results/official';out.mkdir(parents=True,exist_ok=True)
    assert not(out/'FINAL.obj').exists(),'Do not overwrite finished official replication'
    V,f,_=load_obj(str(R/'runtime/cow.obj'),load_textures=False,device=device)
    center=V.mean(0);scale=(V-center).abs().max();targetmesh=Meshes(verts=[(V-center)/scale],faces=[f.verts_idx])
    elev=torch.linspace(0,360,20,device=device);azim=torch.linspace(-180,180,20,device=device)
    rot,t=look_at_view_transform(dist=2.7,elev=elev,azim=azim,device=device);cams=FoVPerspectiveCameras(device=device,R=rot,T=t)
    rr=renderer(128)
    with torch.no_grad():targets=[rr(targetmesh,cameras=cams[j])[0,...,3].detach()for j in range(20)]
    src=ico_sphere(4,device);offset=torch.zeros_like(src.verts_packed(),requires_grad=True);opt=torch.optim.SGD([offset],lr=1.,momentum=.9)
    def full_loss(m):
        with torch.no_grad():return float(torch.stack([((rr(m,cameras=cams[j])[0,...,3]-targets[j])**2).mean()for j in range(20)]).mean())
    init=full_loss(src);hist=[];t0=time.time()
    save_obj(str(out/'INITIAL.obj'),src.verts_packed(),src.faces_packed())
    init_images=[rr(src,cameras=cams[j])[0,...,3].detach().cpu().numpy()for j in [0,5,10,15]]
    firstgrad=None
    for i in range(2000):
        opt.zero_grad();m=src.offset_verts(offset);loss=regularizers(m);l=torch.zeros((),device=device)
        chosen=np.random.permutation(20).tolist()[:2]
        for j in chosen:l+=((rr(m,cameras=cams[j])[0,...,3]-targets[j])**2).mean()/2
        loss['silhouette']=l;total=l+loss['edge']+.01*loss['normal']+loss['laplacian'];total.backward()
        grad=float(offset.grad.norm());assert torch.isfinite(offset.grad).all()and torch.isfinite(total)
        if firstgrad is None:firstgrad=grad
        opt.step();hist.append(dict(step=i+1,total=float(total.detach()),gradient_norm=grad,**{k:float(v.detach())for k,v in loss.items()}))
        if(i+1)%100==0:print('official',i+1,'loss',hist[-1]['total'],'elapsed',time.time()-t0,flush=True)
        if(i+1)in[500,1000,2000]:
            m=src.offset_verts(offset.detach());save_obj(str(out/('STEP_%04d.obj'%(i+1))),m.verts_packed(),m.faces_packed())
    final=src.offset_verts(offset.detach());end=full_loss(final)
    save_obj(str(out/'FINAL.obj'),final.verts_packed(),final.faces_packed());vv,ff,_=load_obj(str(out/'FINAL.obj'),load_textures=False,device=device);reload=Meshes(verts=[vv],faces=[ff.verts_idx])
    with torch.no_grad():
        rerender_error=max(float((rr(reload,cameras=cams[j])-rr(final,cameras=cams[j])).abs().max())for j in range(20))
    images=dict(target=np.array([targets[j].cpu().numpy()for j in [0,5,10,15]]),initial=np.array(init_images),final=np.array([rr(final,cameras=cams[j])[0,...,3].detach().cpu().numpy()for j in[0,5,10,15]]))
    np.savez_compressed(out/'RENDER_COMPARISON.npz',**images)
    table('metrics/OFFICIAL_TRAINING.csv',hist)
    result=dict(official_commit=load(R/'config/FROZEN.json')['official_commit'],steps=2000,views=20,optimizer='SGD(lr=1,momentum=.9)',initial_full_silhouette_L2=init,final_full_silhouette_L2=end,first_full_vertex_gradient=firstgrad,actual_vertex_displacement=stats(offset.detach().norm(dim=1).cpu().numpy()),OBJ_reload_max_rgba_error=rerender_error,elapsed_seconds=time.time()-t0,passed=end<init and firstgrad>0 and rerender_error<.001,changes_from_notebook=['No texture/RGB stage (not requested)','Deterministic seed; headless logs/OBJ instead of notebook animation','Same SoftSilhouette target dataset rendered one view at a time to limit transient GPU memory'])
    save('metrics/OFFICIAL_REPRODUCTION.json',result);print(result,flush=True)
if __name__=='__main__':main()
