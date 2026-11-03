"""CPU contracts plus one non-updating full GPU-chain check after native-ray guard."""
from official_adapter import *
import argparse
def main(gpu_check=False):
    p=protocol();checks=[];g=p['geometry'];s=g['mm_per_model_unit'];C=np.array(g['C_mm'])
    for a in load(R/'provenance/ORIGINAL_ASSETS.json')['files']:assert sha(a['path'])==a['sha256']
    for a in load(R/'provenance/INPUT_FREEZE.json')['files']:assert sha(a['path'])==a['sha256']
    for cid in SOURCES:
        f=frozen(cid);n=native(cid);a=original_anchor_geometry(cid);j=np.flatnonzero(f['eligible_HERO'].ravel());native_ids=f['native_pixel_ID'].ravel()[j];uv=np.c_[native_ids%640,native_ids//640];originalX=unproject(n['depth'].flat[native_ids].astype(float),n['T'],uv,n['Kn']);err=np.linalg.norm(a['X'][j]*s+C-originalX,axis=1)
        assert err.max()<1e-10;nv=f['normal_valid'].ravel();normal=f['normal_camera'].reshape(-1,3);normal_error=float(abs(np.linalg.norm(normal[nv],axis=1)-1).max());assert normal_error<1e-5
        eligible=a['eligible'][j];tt=np.linalg.norm(a['X'][j]-(n['T'][:3,3]-C)/s,axis=1);assert ((tt[eligible]>=a['near'][j][eligible])&(tt[eligible]<=a['far'][j][eligible])).all()
        dt=.5/s;free=eligible&(tt-dt>a['near'][j])&(tt-dt<a['far'][j]);points=a['X'][j]-a['direction'][j]*dt;assert ((points[free]>=-1-1e-8)&(points[free]<=1+1e-8)).all()
        back=(originalX-C)/s*s+C;assert np.linalg.norm(back-originalX,axis=1).max()<1e-10
        checks.append(dict(source=cid,crop_HERO_N=len(j),native_anchor_eligible_N=int(eligible.sum()),native_anchor_excluded_by_CAD_or_mask_or_ROI_N=int((~eligible).sum()),weak_free_space_eligible_N=int(free.sum()),exact_native_XYZ_inverse_max_mm=float(err.max()),normal_unit_error_max=normal_error,native_mask_and_CAD_checked=True,source_qualification='INSUFFICIENT_EVIDENCE',GT=False))
    table('metrics/NATIVE_ANCHOR_AND_COORDINATE_VALIDATION.csv',checks)
    if gpu_check:
        torch.set_num_threads(2);torch.backends.cuda.matmul.allow_tf32=False;model=make_model();loss=ProjectLoss('M1');data,batch=packet(SOURCES[0],1001);before={k:v.detach().clone()for k,v in model.state_dict().items()};events=instrument(model);output,terms=forward_and_loss(model,loss,data,batch)
        assert all(torch.isfinite(x)for x in terms.values());terms['loss'].backward();assert all(v.grad is None or torch.isfinite(v.grad).all()for v in model.parameters());assert all(torch.equal(before[k],v)for k,v in model.state_dict().items());assert (output['z_vals']>=batch['near']-1e-5).all()and(output['z_vals']<=batch['far']+1e-5).all();assert (output['weights'].sum(1)<=1+1e-5).all()
        uv=data['uv'];rays,cam=rend_util.get_camera_params(uv,data['pose'],data['intrinsics']);nativeRays=vis.camera_rays(uv[0].cpu().numpy(),frozen(SOURCES[0])['K_crop'],frozen(SOURCES[0])['c2w_mm']);nativeUnit=nativeRays[:,3:]/np.linalg.norm(nativeRays[:,3:],axis=1)[:,None];direction_error=float(np.linalg.norm(rays[0].detach().cpu().numpy()-nativeUnit,axis=1).max());assert direction_error<1e-5
        save('metrics/POST_NATIVE_GUARD_GPU_VALIDATION.json',dict(status='PASS_BOUNDED_CHAIN_NOT_FULL_TRAINING',optimizer_steps=0,model_parameters_unchanged=True,full_official_chain_calls=events,losses={k:float(v.detach())for k,v in terms.items()},sampler_all_queries_in_visible_interval=True,direction_max_error=direction_error,GT=False))
    save('metrics/PREFLIGHT_VALIDATION.json',dict(status='PASS_INPUT_AND_BOUNDED_COMPUTATIONAL_CONTRACTS',sources=checks,official_training_run=False,model_scientific_accuracy='NOT_EVALUABLE',GT=False))
    print('PREFLIGHT_VALIDATED',len(checks),'sources; formal training NOT_RUN; GPU non-update check',gpu_check)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--gpu-check',action='store_true');a=parser.parse_args();main(a.gpu_check)
