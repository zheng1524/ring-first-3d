"""Only bounded 128/256 sampling and six-packet CPU/GPU FP32 parity; zero steps."""
from common import *
from gpu_model_adapter import initialized_model,save_initial
from fixed_renderer import render,terms,data_loss,eikonal,array_pred

def difference(a,b):
    valid=np.isfinite(a)&np.isfinite(b)
    return float(np.max(abs(a[valid]-b[valid]))) if valid.any() else None
def cosine(a,b):
    a=a.double().cpu();b=b.double().cpu();na=float(a.norm());nb=float(b.norm())
    return float(torch.dot(a,b)/(na*nb)),abs(nb-na)/max(na,1e-30)

def measure(model,b,cells):
    p=render(model,b,cells,REFS.index(b['source']));t=terms(model,b,p);loss=data_loss(t,.01);metrics={};grads={}
    for key,value in list(t.items())+[('joint_B_data',loss)]:
        g,_,v=gradient(value,model);metrics[key]=dict(loss=float(value.detach()),**g);grads[key]=v.cpu()
    result=dict(pred=array_pred(p),terms=metrics,grads=grads,delta_beta=p['delta_beta'].cpu().numpy(),beta_mm=float(model.density.get_beta().detach())*domain()['mm_per_unit'])
    del p,t,loss;gc.collect();return result

def main():
    freeze('BEFORE_PREFLIGHT.json',dict(optimizer_step_N=0,authorized_GPU_diagnostics=True))
    cpu=save_initial();initial=load(R/'provenance/INITIAL_MODEL.json');hardware=check_gpu();gpu,meta=initialized_model('cuda:0')
    assert meta['FP32_SHA256']==initial['FP32_SHA256'];hash_before=parameter_hash(gpu);torch.cuda.reset_peak_memory_stats()
    sample_rows=[];cache={};protocol=cfg()['sampler_compare']
    for split in ['extra','small']:
        for ref in REFS:
            b=packet(ref,split);p128=measure(gpu,b,128);p256=measure(gpu,b,256);row=dict(source=ref,split=split,
                Mask128=p128['terms']['mask']['loss'],Mask256=p256['terms']['mask']['loss'],
                Mask_relative_difference=abs(p128['terms']['mask']['loss']-p256['terms']['mask']['loss'])/max(abs(p128['terms']['mask']['loss']),1e-12),
                depth_max_abs_mm=difference(p128['pred']['depth_mm'],p256['pred']['depth_mm']),front_max_abs_mm=difference(p128['pred']['front_t_mm'],p256['pred']['front_t_mm']),
                opacity_max_abs=difference(p128['pred']['opacity'],p256['pred']['opacity']),RGB_max_abs=difference(p128['pred']['RGB'],p256['pred']['RGB']),
                hit_set_equal=bool(np.array_equal(p128['pred']['render_hit'],p256['pred']['render_hit'])),hit_N128=int((p128['pred']['render_hit']&(b['depth_weight']>0)).sum()),hit_N256=int((p256['pred']['render_hit']&(b['depth_weight']>0)).sum()),beta128_mm=p128['beta_mm'],beta256_mm=p256['beta_mm'])
            for term in ['mask','joint_B_data']:
                co,rel=cosine(p128['grads'][term],p256['grads'][term]);row[term+'_implicit_cosine']=co;row[term+'_implicit_norm_relative']=rel
            for cells,p in [(128,p128),(256,p256)]:
                for quantile in [0,.5,.95,1.]:row[f'delta_beta_{cells}_q{quantile}']=float(np.quantile(p['delta_beta'],quantile))
                for term in ['rgb','depth','mask','anchor']:row[f'{term}_{cells}']=p['terms'][term]['loss']
            row['converged128']=row['Mask_relative_difference']<=protocol['mask_relative_max'] and row['depth_max_abs_mm'] is not None and row['depth_max_abs_mm']<=protocol['depth_max_abs_mm'] and row['opacity_max_abs']<=protocol['opacity_max_abs'] and row['RGB_max_abs']<=protocol['RGB_max_abs'] and row['hit_set_equal'] and all(row[k+'_implicit_cosine']>=protocol['implicit_cosine_min'] and row[k+'_implicit_norm_relative']<=protocol['implicit_norm_relative_max'] for k in ['mask','joint_B_data'])
            sample_rows.append(row);cache[(ref,split,128)]=p128;cache[(ref,split,256)]=p256
            print('SAMPLER_COMPARE',ref,split,'128converged',row['converged128'],'hits',row['hit_N128'],row['hit_N256'],flush=True)
    cells=128 if all(r['converged128'] for r in sample_rows) else 256
    table('metrics/SAMPLING_COMPARISON.csv',sample_rows);save('config/SELECTED_SAMPLING.json',dict(cells=cells,status='CONVERGED_128' if cells==128 else 'SELECTED256_NOT_FULLY_CONVERGED',search_N=1,additional_density_search=False))
    parity=[];tol=cfg()['parity']
    for split in ['extra','small']:
        for ref in REFS:
            b=packet(ref,split);cp=measure(cpu,b,cells);gp=cache[(ref,split,cells)]
            for term in ['rgb','depth','mask','anchor','joint_B_data']:
                co,rel=cosine(cp['grads'][term],gp['grads'][term]);a=cp['terms'][term]['loss'];z=gp['terms'][term]['loss'];finite=cp['terms'][term]['finite']and gp['terms'][term]['finite']and np.isfinite([a,z]).all()
                passed=finite and abs(a-z)<=tol['loss_atol']+tol['loss_rtol']*abs(a) and co>=tol['implicit_cosine_min']and rel<=tol['implicit_norm_relative_max']
                parity.append(dict(source=ref,split=split,term=term,CPU_loss=a,GPU_loss=z,abs_loss_difference=abs(a-z),implicit_gradient_cosine=co,implicit_norm_relative=rel,all_gradients_finite=finite,pass_=passed))
            d=difference(cp['pred']['depth_mm'],gp['pred']['depth_mm']);ft=difference(cp['pred']['front_t_mm'],gp['pred']['front_t_mm']);op=difference(cp['pred']['opacity'],gp['pred']['opacity']);rgb=difference(cp['pred']['RGB'],gp['pred']['RGB']);equal=bool(np.array_equal(cp['pred']['render_hit'],gp['pred']['render_hit']))
            parity.append(dict(source=ref,split=split,term='prediction',depth_max_abs_mm=d,front_max_abs_mm=ft,opacity_max_abs=op,RGB_max_abs=rgb,hit_set_equal=equal,
                pass_=equal and d is not None and d<=tol['depth_max_abs_mm']and ft is not None and ft<=tol['front_cross_max_abs_mm']and op<=tol['opacity_max_abs']and rgb<=tol['RGB_max_abs']))
            print('GPU_PARITY',ref,split,'pass',all(r['pass_'] for r in parity if r['source']==ref and r['split']==split),flush=True)
    ce=eikonal(cpu);ge=eikonal(gpu);cm,_,cg=gradient(ce,cpu);gm,_,gg=gradient(ge,gpu);co,rel=cosine(cg,gg)
    parity.append(dict(source='SHARED_EXTRA18_ONLY',split='extra',term='eikonal',CPU_loss=float(ce.detach()),GPU_loss=float(ge.detach()),implicit_gradient_cosine=co,implicit_norm_relative=rel,
        pass_=cm['finite']and gm['finite']and abs(float(ce.detach())-float(ge.detach()))<=tol['loss_atol']+tol['loss_rtol']*abs(float(ce.detach()))and co>=tol['implicit_cosine_min']and rel<=tol['implicit_norm_relative_max']))
    assert parameter_hash(gpu)==hash_before;peak=memory_guard();table('metrics/GPU_PARITY_DETAILS.csv',parity)
    initial128=[cache[(ref,'extra',128)]['pred']['render_hit'] for ref in REFS];baseline_ok=all(int((h&(packet(ref,'extra')['depth_weight']>0)).sum())==n for ref,h,n in zip(REFS,initial128,[27,29,31]))
    passed=all(r['pass_'] for r in parity)and baseline_ok
    save('metrics/GPU_PARITY.json',dict(status='PASS_ALLOW_BOUNDED_TRAINING' if passed else 'PREFLIGHT_BLOCKED',pass_=passed,rows=parity,
        selected_cells=cells,sampling_fully_converged=(cells==128),same_canonical_initialization=True,initial128_E26_counts_match=baseline_ok,
        GPU=hardware,peak_allocated_bytes=peak,parameters_unchanged=parameter_hash(gpu)==hash_before,optimizer_step_N=0,TF32=False,AMP=False))
    print('PREFLIGHT_COMPLETE',passed,'selected',cells,'peakMiB',peak/2**20,flush=True)
    if not passed:raise SystemExit(2)
if __name__=='__main__':main()
