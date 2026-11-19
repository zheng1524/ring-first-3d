"""A1 nine-parameter TRF solver with exact 2D blocks, no HERO/depth block."""
from common import *
class Problem:
    def __init__(self,name,arm,only_ids=None):
        self.scene=name;self.arm=arm;self.variant='full';sc=load(R/'config/BODY_FIT_VIEWS.json')[name];self.group=sc['group'];self.ids=sc['FIT'] if only_ids is None else only_ids
        self.R0=np.array(sc['R0']);self.base=np.r_[0.,0.,-2.,0.,0.,0.,np.log([5.,5.,3.])]
        self.lo=np.r_[np.full(3,-10.),np.full(3,-.8),np.log(np.full(3,.25))];self.hi=np.r_[np.full(3,10.),np.full(3,.8),np.log(np.full(3,15.))]
        dxy={x['source']:x for x in load(R/'provenance/DXY_GENERATED.json')};self.targets=[];self.cameras=[];self.calls=0;self.invalid_calls=0;self.trace=[]
        ss={s['source_id']:s for s in load(R/'config/SOURCE_BINDING.json')};meta={s['id']:load(s['source']) for s in load(OLD/'config/SOURCES.json')}
        if arm=='E1' and any(not dxy[c]['available'] for c in self.ids):raise ValueError('NOT_EVALUABLE_DXY_NO_SELECTED_GEOMETRY')
        y,x=np.mgrid[:360,:640];alluv=np.c_[x.ravel(),y.ravel()];gx,gy=np.meshgrid(np.arange(160)*4+1.5,np.arange(90)*4+1.5);grid=np.c_[gx.ravel(),gy.ravel()]
        for cid in self.ids:
            s=source(cid);target=s['labels']==1
            if arm=='E1':
                d=dxy[cid];coords=(alluv-np.array(d['center_px']))@np.linalg.inv(np.array(d['basis_px'])).T;target=((coords*coords).sum(1)<=1).reshape(360,640)
            cad=cast(ringscene(self.group),grid,s['K'],s['T'])[0]
            self.targets.append(target_data(target,s['labels'],cad,s['T'],s['K']));self.cameras.append(dict(K=s['K'],T=s['T']))
        rgbsets=[]
        for c in self.ids:
            m=meta[c];q=set(m.get('source_SHA',[]));q.update(v['sha256'] for v in m.get('parent_RGB',[]) if v.get('sha256'));q.add(ss[c]['RGB_content_SHA']);rgbsets.append(q)
        w=[]
        for i,c in enumerate(self.ids):
            corr=sum(len(rgbsets[i]&rgbsets[j])/max(1,len(rgbsets[i]|rgbsets[j])) for j in range(len(self.ids)) if i!=j)
            quality=1. if ss[c]['pool_formal'] else .25;w.append(quality/(1+corr))
        self.weights=np.array(w)/sum(w);self.N=sum(128+len(t['boundary'])+14400 for t in self.targets)+9
    def data_residual(self,p):
        rr=[]
        for target,s,w in zip(self.targets,self.cameras,self.weights):
            rr.extend([x*np.sqrt(w) for x in two_d_parts(p,self.R0,target,s['K'],s['T'],ringscene(self.group))])
        return np.concatenate(rr)
    def residual(self,p):
        self.calls+=1
        try:
            data=self.data_residual(p);prior=np.r_[(p[:3]-self.base[:3])/10,p[3:6]/.8,(p[6:9]-self.base[6:9])/1.2]*np.sqrt(.05);r=np.r_[data,prior]
            if not np.isfinite(r).all():raise ValueError('nonfinite residual')
        except (ValueError,np.linalg.LinAlgError):self.invalid_calls+=1;r=np.full(self.N,1000.)
        self.trace.append(dict(call=self.calls,p=p.copy(),objective=float(r@r/2)))
        return r

# Compile the original method unchanged. No rewrite of solver options/initialization.
solver_ns=dict(globals());reuse(A1/'fitting.py',['solve'],solver_ns,cls='Problem');Problem.solve=solver_ns['solve']

def qualified(problem,r):
    why=[];p=np.array(r['p']);c,Q,a=decode(p,problem.R0)
    if not r['optimizer_success']:why.append('OPTIMIZER_NOT_CONVERGED')
    if not np.isfinite(p).all() or not np.isfinite(r['objective']):why.append('NONFINITE_RESULT')
    if (p<problem.lo-1e-9).any() or (p>problem.hi+1e-9).any():why.append('PARAMETER_OUTSIDE_BOUNDS')
    for s in problem.cameras:
        try:
            ellipse_projection(p,problem.R0,s['K'],s['T'])
            cc=(c-s['T'][:3,3])@s['T'][:3,:3];extent=np.sqrt(np.sum((s['T'][:3,2]@Q*a)**2))
            if cc[2]-extent<=0:why.append('BODY_BEHIND_CAMERA')
        except (ValueError,np.linalg.LinAlgError):why.append('INVALID_PROJECTED_CONIC')
    return not why,sorted(set(why))

def main(name,arm):
    guard('fit');path=f'local_results/{name}/{arm}'
    if (R/path/'SELECTION.json').exists():return
    sc=load(R/'config/BODY_FIT_VIEWS.json')[name]
    if not sc['FIT'] or arm=='E1' and not sc['E1_available']:
        save(path+'/SELECTION.json',dict(pool=name,arm=arm,available=False,p=None,status='NOT_EVALUABLE_DXY_NO_SELECTED_GEOMETRY' if sc['FIT'] else sc['status'],missing_required=sc['E1_missing_required']))
        return
    problem=Problem(name,arm);fits=[]
    for start in range(3):
        problem.trace=[];r=problem.solve(start);ok,why=qualified(problem,r);r.update(eligible=ok,ineligible_reasons=why)
        save(path+f'/START_{start}.json',r)
        trace=problem.trace;np.savez_compressed(R/path/f'TRACE_{start}.npz',p=np.array([x['p'] for x in trace]),objective=np.array([x['objective'] for x in trace]))
        save(path+f'/TRACE_{start}.json',dict(calls=len(trace),evaluations=trace))
        fits.append(r);print(name,arm,start,r['optimizer_success'],r['nfev'],r['objective'],why,flush=True)
    eligible=[x for x in fits if x['eligible']]
    if eligible:
        win=min(eligible,key=lambda x:(x['objective'],x['start']));out=dict(win,pool=name,available=True,status='NUMERICAL_CONVERGED_NOT_ACCURACY_CERTIFICATE',selection='lowest FIT objective among eligible normal-success results only')
        V,F=mesh(np.array(win['p']),np.array(win['R0']));np.savez_compressed(R/path/('Body-E-DXY.npz' if arm=='E1' else 'Body-E-FULLMASK.npz'),V=V,F=F,p=win['p'],R0=win['R0']);trimesh.Trimesh(V,F,process=False).export(R/path/'Body_mm.ply')
    else:out=dict(pool=name,arm=arm,available=False,p=None,status='NO_ELIGIBLE_CONVERGED_START',failed_starts=[x['ineligible_reasons'] for x in fits])
    save(path+'/SELECTION.json',out)
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
