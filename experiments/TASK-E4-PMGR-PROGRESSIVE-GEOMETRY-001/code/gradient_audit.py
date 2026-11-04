"""Actual active-space robust source gradients at saved geometry; no updates."""
from losses import *
def main():
    rows=[];matrices=[]
    for file in sorted((R/'metrics/runs').glob('*.json')):
        if file.name.endswith('__progress.json'):continue
        x=load(file);p=Problem(x['scene'],x['initial'])
        for st in x['stages'][1:]:
            cp=np.load(R/'local_results'/x['key']/(st['stage']+'.npz'));a=tensor(cp['a']).requires_grad_(True);loss,views,_=p.objective(a);mask=np.zeros(128);mask[st['active']]=1;grad=[]
            for vi in views:grad.append(torch.autograd.grad(vi['loss'],a,retain_graph=True)[0].detach().cpu().numpy()*mask)
            G=np.array(grad);norm=np.linalg.norm(G,axis=1);cos=G@G.T/np.maximum(norm[:,None]*norm[None,:],1e-15)
            matrices.append(dict(case_id=x['key'],stage=st['stage'],sources=p.ids,source_weights=p.weights,active=st['active'],active_parameter_gradients=G,cosine=cos))
            for i,cid in enumerate(p.ids):
                field=p.b['phi']@(-G[i]);mx=abs(field).max();diagnostic=field*(p.tau/max(mx,1e-15));rows.append(dict(case_id=x['key'],stage=st['stage'],source=cid,active_N=len(st['active']),gradient_L2=float(norm[i]),finite=bool(np.isfinite(G[i]).all()),cosine_with_sources=cos[i],diagnostic_steepest_normal_displacement_max_mm=float(abs(diagnostic).max()),source_weight=float(p.weights[i]),not_an_optimizer_update=True))
    save('metrics/ACTIVE_SOURCE_GRADIENTS.json',matrices);table('metrics/PER_VIEW_ACTIVE_GRADIENTS.csv',rows);save('metrics/ACTIVE_GRADIENT_VALIDATION.json',dict(stage_N=len(matrices),source_stage_N=len(rows),all_finite=all(r['finite']for r in rows),optimizer_updates=0,description='full fixed A observations; actual robust loss; masked to actual activated parameter space; source-specific steepest direction is diagnostic only'))
    print('ACTIVE_SOURCE_GRADIENT_AUDIT',len(matrices),'STAGES',all(r['finite']for r in rows))
if __name__=='__main__':main()
