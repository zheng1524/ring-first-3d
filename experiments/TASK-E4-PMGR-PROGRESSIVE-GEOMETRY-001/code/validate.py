"""Pre-optimization coordinate, topology, renderer and differential contracts."""
from inputs import *
from mesh_basis import *
from camera_renderer import *
import time
def main():
    rows=[];pr=protocol();u,v=np.meshgrid(np.arange(640),np.arange(360));uv=np.c_[u.ravel(),v.ravel()]
    for scene,sc in pr['scenes'].items():
        renderer=Renderer(scene)
        for initial in pr['initials']:
            row=p0(scene,initial);b=dict(np.load(R/'inputs'/f'{scene}_{initial}_basis.npz'));V=b['V'];F=b['F'];tn=tensor(V)
            for cid in sc['A']+sc['B']:
                s=source(cid);o=obs(cid);r=renderer.render(tn,F,s['K'],s['T'],(640,360));hard=r['hard'].cpu().numpy();z=r['z'].cpu().numpy()
                rz=cast(mesh_scene(V,F),uv,s['K'],s['T'])[0];cad=cast(ringscene(scene),uv,s['K'],s['T'])[0];expect=(np.isfinite(rz)&(rz<cad)).reshape(360,640);common=hard&expect
                analytic=first_depth(np.array(row['p']),np.array(row['R0']),vis.camera_rays(uv,s['K'],s['T']));ah=(np.isfinite(analytic)&(analytic<cad)).reshape(360,640)
                dz=abs(z[common]-rz.reshape(360,640)[common]);da=abs(z[hard&ah]-analytic.reshape(360,640)[hard&ah]);iou=float((hard&ah).sum()/max(1,(hard|ah).sum()))
                rt=(o['uv']+.5)*np.array([640/640,360/352])-.5;back=(rt+.5)/np.array([1,360/352])-.5;err=float(abs(back-o['uv']).max())
                passed=bool(np.mean(hard==expect)>=pr['P0_gate']['hard_agreement_min']and np.quantile(dz,.95)<=.15 and np.quantile(da,.95)<=.3 and iou>=.97 and err<1e-8)
                rows.append(dict(scene=scene,initial=initial,source=cid,role='A'if cid in sc['A']else'B',GPU_vs_O3D_agreement=float(np.mean(hard==expect)),GPU_vs_O3D_depth_p95_mm=float(np.quantile(dz,.95)),GPU_vs_analytic_IoU=iou,GPU_vs_analytic_depth_p95_mm=float(np.quantile(da,.95)),native_archive_roundtrip_px=err,pass_gate=passed))
                print('P0_GATE',scene,initial,cid,passed,iou,float(np.quantile(dz,.95)),flush=True)
            assert float(b['raw_orth'])<1e-7 and float(b['tangent_overlap'])<1e-7
    # Asymmetric synthetic control: genuine normal deformation gradient through
    # antialiasing, and native first triangle depth separately in losses tests.
    s=trimesh.creation.icosphere(subdivisions=3);V=np.asarray(s.vertices)*[3,2,1]+[0,0,20];F=np.asarray(s.faces);T=np.eye(4);K=np.array([[200,0,159.5],[0,200,89.5],[0,0,1.]])
    ren=Renderer('G01_004');amp=torch.zeros(1,device='cuda',requires_grad=True);direction=tensor(np.exp(-((V[:,0]-1)**2+(V[:,1])**2)/3)[:,None]*np.array([0,0,-1]))
    pred=ren.render(tensor(V)+direction*amp,F,K,T,cad=False);target=ren.render(tensor(V)+direction*.2,F,K,T,cad=False)['alpha'].detach();loss=((pred['alpha']-target)**2).sum();loss.backward();grad=float(amp.grad)
    syn=dict(name='ASYMMETRIC_SYNTHETIC_BUMP_NO_CAMERA_OPTIMIZATION',loss=float(loss),gradient=grad,pass_gradient=bool(np.isfinite(grad)and abs(grad)>1e-6))
    table('metrics/P0_RENDERER_GATE.csv',rows);save('metrics/P0_RENDERER_GATE.json',rows);save('metrics/SYNTHETIC_CONTROLS.json',[syn]);save('metrics/ENVIRONMENT.json',dict(torch=torch.__version__,cuda=torch.version.cuda,GPU=torch.cuda.get_device_name(),renderer_commit='253ac4fcea7de5f396371124af597e6cc957bfae',peak_allocated_bytes=torch.cuda.max_memory_allocated(),P0_all_pass=all(x['pass_gate']for x in rows),synthetic=syn))
if __name__=='__main__':main()
