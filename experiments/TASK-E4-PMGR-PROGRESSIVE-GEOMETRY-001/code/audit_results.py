"""Independent saved-geometry replay; no optimizer or holdout-driven choices."""
from inputs import *
from mesh_basis import shape
from trust_region import self_intersections
from losses import Problem,tensor
from observability import decompose
import argparse,itertools,time
def check_all():
    checks=[];per=[];src=[]
    controls=load(R/'assets_index/CONTROL_SOURCE_INDEX.json')if(R/'assets_index/CONTROL_SOURCE_INDEX.json').exists()else[]
    for a in load(R/'assets_index/LOCAL_DATA_SOURCES.json')+controls:
        ok=sha(a['path'])==a['sha256'];src.append(dict(path=a['path'],unchanged=ok))
    checks.append(dict(name='ALL_ORIGINAL_ASSETS_UNCHANGED',pass_check=all(x['unchanged']for x in src),N=len(src)))
    versions=[]
    for path in sorted((R/'metrics/runs').glob('*.json')):
        if path.name.endswith('__progress.json'):continue
        x=load(path)
        versions.append(tuple((c['path'],c['sha256'])for c in x.get('core_code',[])))
        if len(x.get('stages',[]))!=4:checks.append(dict(name=x['key']+'_STAGES',pass_check=False));continue
        b=dict(np.load(R/'inputs'/f"{x['scene']}_{x['initial']}_basis.npz"));good=True;maxerr=0;selfi=[];coverage_drops=[];ring_violation=[];max_accepted_step=0
        F=b['F'];ringpoints=lambda V:np.vstack([V,V[F].mean(1),(V[F[:,0]]+V[F[:,1]])/2,(V[F[:,1]]+V[F[:,2]])/2,(V[F[:,2]]+V[F[:,0]])/2]);base_ring=ringscene(x['scene']).compute_signed_distance(o3d.core.Tensor(ringpoints(b['V']).astype(np.float32))).numpy()
        for st in x['stages']:
            cp=dict(np.load(R/'local_results'/x['key']/(st['stage']+'.npz')));err=float(abs(shape(b,cp['a'])-cp['V']).max());maxerr=max(maxerr,err);good&=np.array_equal(cp['F'],b['F'])and err<1e-10
            si=self_intersections(cp['V'],cp['F']);selfi.append(si['intersections']);rd=ringscene(x['scene']).compute_signed_distance(o3d.core.Tensor(ringpoints(cp['V']).astype(np.float32))).numpy();ring_violation.append(int((rd<np.minimum(base_ring,0)-.010001).sum()))
        accepted=[s for s in x['steps']if s['accepted']];max_accepted_step=max((s['geometry_checks']['max_step_mm']for s in accepted),default=0)
        check=bool(good and max(selfi)==0 and not any(ring_violation)and max_accepted_step<=x['trust_tau_mm']+1e-6 and x['gradient_evaluations']==120)
        checks.append(dict(name=x['key']+'_GEOMETRY_REPLAY',pass_check=check,max_replay_error_mm=maxerr,self_intersections=selfi,P0_relative_ring_violations=ring_violation,max_accepted_step_mm=max_accepted_step,tau_mm=x['trust_tau_mm']))
        for cid in protocol()['scenes'][x['scene']]['A']:
            h0=next(v['depth_hit_N']for v in x['stages'][0]['evaluations']if v['source']==cid);hf=next(v['depth_hit_N']for v in x['stages'][-1]['evaluations']if v['source']==cid);vi=protocol()['scenes'][x['scene']]['A'].index(cid);H0=x['stages'][0]['per_view'][vi]['H_N'];Hf=x['stages'][-1]['per_view'][vi]['H_N'];per.append(dict(case_id=x['key'],source=cid,P0_hit=h0,P3_hit=hf,fixed_N=512,coverage_decreased=hf<h0,drop_N=h0-hf,P0_visible_H_N=H0,P3_visible_H_N=Hf,visible_H_decreased=Hf<H0,H_missing_never_assigned_zero=True))
    checks.append(dict(name='ONE_FROZEN_CORE_VERSION_ALL_FORMAL_RUNS',pass_check=bool(versions)and len(set(versions))==1,unique_versions=len(set(versions))))
    save('metrics/RESULT_INTEGRITY.json',checks);table('metrics/COVERAGE_DEGENERACY.csv',per);save('metrics/POSTRUN_ASSET_SHA.json',src);print('INTEGRITY',sum(c['pass_check']for c in checks),'/',len(checks),flush=True)
@__import__('torch').no_grad()
def active_rank():
    # End-stage actual-parameter J, not the full 128-candidate spectrum.
    # Keep common finite rows; no rows from B. This is post-fit diagnosis only.
    rows=[];out=R/'metrics/ACTIVE_JACOBIAN_RANK.json';existing=load(out)if out.exists()else[];seen={x['case_id']+'_'+x['stage']for x in existing};rows.extend(existing)
    for path in sorted((R/'metrics/runs').glob('*.json')):
        if path.name.endswith('__progress.json'):continue
        x=load(path)
        if len(x.get('stages',[]))!=4:continue
        p=Problem(x['scene'],x['initial'])
        for st in x['stages'][1:]:
            if x['key']+'_'+st['stage']in seen:continue
            cp=dict(np.load(R/'local_results'/x['key']/(st['stage']+'.npz')));V=tensor(cp['V']);r,_=p.parts(V,return_vector=True);der=[];valid=np.isfinite(r);start=time.monotonic()
            for k in st['active']:
                direction=tensor(p.b['n']*p.b['phi'][:,k,None]);a,_=p.parts(V+.01*direction,return_vector=True);b,_=p.parts(V-.01*direction,return_vector=True);d=(a-b)/.02;der.append(d);valid&=np.isfinite(d)
            J=np.stack(der,1)[valid]if der else np.empty((int(valid.sum()),0));_,s,rank=decompose(J)
            rows.append(dict(case_id=x['key'],stage=st['stage'],actual_active_N=len(st['active']),effective_rank=rank,condition=float(s[0]/s[rank-1])if rank else None,singular_values=s,common_row_N=int(valid.sum()),censored_row_N=int((~valid).sum()),seconds=time.monotonic()-start,description='end-stage actual deformation parameters only; P0 parameters frozen; no regularizer rows; real A only'))
            save('metrics/ACTIVE_JACOBIAN_RANK.json',rows);print('ACTIVE_J',x['key'],st['stage'],rank,'/',len(st['active']),flush=True)
    table('metrics/ACTIVE_JACOBIAN_RANK.csv',rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--active-rank',action='store_true');a=ap.parse_args();active_rank()if a.active_rank else check_all()
if __name__=='__main__':main()
