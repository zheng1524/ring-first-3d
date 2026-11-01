"""Post-stop read-only diagnosis: actual Adam step vs independent gradient formula."""
from common import *
from gpu_model_adapter import initialized_model,load_checkpoint
from fixed_renderer import render,terms,data_loss,eikonal,raw

def main():
    freeze('BEFORE_POSTSTOP_DIAGNOSIS.json',dict(additional_optimizer_steps=0,no_restart=True))
    check_gpu();model,_=initialized_model('cuda:0');initial={k:v.detach().cpu().clone() for k,v in model.state_dict().items()};names=list(model.named_parameters())
    gradients={k:None for k in ['rgb','depth','mask','anchor']};points=[];identities=[]
    for ref in REFS:
        b=packet(ref,'extra');p=render(model,b,load(R/'config/SELECTED_SAMPLING.json')['cells'],REFS.index(ref));t=terms(model,b,p)
        for key,value in t.items():
            _,vec,_=gradient(value,model);gradients[key]=vec/3 if gradients[key] is None else gradients[key]+vec/3
        obs=b['depth_weight']>0;tt=b['target_Z'][obs]/b['cosine'][obs]
        for pix,P in zip(b['source_pixel'][obs],b['origin'][obs]+b['direction'][obs]*tt[:,None]):points.append(P);identities.append(dict(source=ref,pixel=int(pix),kind='qualified_train_HERO'))
        valid=obs&p['render_hit']
        for pix,P in zip(b['source_pixel'][valid],b['origin'][valid]+b['direction'][valid]*p['front_t_mm'][valid,None]):points.append(P);identities.append(dict(source=ref,pixel=int(pix),kind='initial_real_front_zero'))
        del p,t
    e=eikonal(model);_,eg,_=gradient(e,model);base=gradients['rgb']+.1*gradients['depth']+.1*gradients['mask']+.1*eg
    states={a:torch.load(R/f'checkpoints/{a}/STOP_UNSAFE_step001.pt',map_location='cpu',weights_only=True) for a in ['A','B']}
    deltas={a:torch.cat([(states[a][name]-initial[name]).reshape(-1) for name,p in names]).to('cuda:0') for a in ['A','B']}
    summary=[];paramrows=[]
    for a in ['A','B']:
        g=base+(0 if a=='A'else .01)*gradients['anchor'];cursor=0;maxerror=0.
        for name,p in names:
            n=p.numel();gg=g[cursor:cursor+n].reshape(p.shape);lr=1e-5 if name.startswith('density.') else 1e-4
            expected=p.detach()-lr*gg/(gg.abs()+1e-8);actual=states[a][name].to(p.device);err=float(abs(expected-actual).max());maxerror=max(maxerror,err)
            dv=(actual-p.detach()).double();paramrows.append(dict(arm=a,name=name,parameter_N=n,delta_L2=float(dv.norm()),max_abs_update=float(abs(dv).max()),
                independent_Adam_first_step_max_abs_error=err,lr=lr))
            cursor+=n
        co=float(torch.dot(base.double(),g.double())/(base.double().norm()*g.double().norm()))
        summary.append(dict(arm=a,optimizer_updates_already_done=1,additional_updates=0,independent_first_Adam_formula_max_abs_error=maxerror,
            first_step_matches_registered_joint_gradient=maxerror<2e-7,actual_full_update_norm=float(deltas[a].double().norm()),
            initial_full_gradient_norm=float(g.double().norm()),cosine_to_A_initial_gradient=co,
            weighted_anchor_gradient_norm=float((.01*gradients['anchor']).double().norm()),base_gradient_norm=float(base.double().norm())))
    pts=np.asarray(points);f0=raw(model,pts)[0];rows=[]
    for i,x in enumerate(identities):
        _,jac,_=gradient(f0[i],model)
        rows.append(dict(**x,initial_SDF_mm=float(f0[i].detach()),**{a+'_first_order_dSDF_mm':float(torch.dot(jac.double(),deltas[a].double())) for a in ['A','B']}))
    del model,f0,jac,gradients,base,eg,e,deltas;gc.collect();torch.cuda.empty_cache()
    for a in ['A','B']:
        model=load_checkpoint(f'checkpoints/{a}/STOP_UNSAFE_step001.pt')
        with torch.no_grad():f=raw(model,pts)[0].cpu().numpy()
        for r,value in zip(rows,f):r[a+'_actual_SDF_mm']=float(value);r[a+'_actual_dSDF_mm']=float(value-r['initial_SDF_mm'])
        del model;gc.collect();torch.cuda.empty_cache()
    table('metrics/ACTUAL_PARAMETER_UPDATES.csv',paramrows);table('metrics/SDF_POINT_RESPONSES.csv',rows)
    save('metrics/FIRST_STEP_DIAGNOSIS.json',dict(rows=summary,point_N=len(rows),all_step_formulas_match=all(r['first_step_matches_registered_joint_gradient'] for r in summary),
        no_optimizer_created_in_diagnosis=True,additional_optimizer_step_N=0,interpretation='actual raw SDF changes and first-order responses; no step-size or loss search'))
    print('POSTSTOP_FIRST_STEP_DIAGNOSIS_COMPLETE',summary,flush=True)
if __name__=='__main__':main()
