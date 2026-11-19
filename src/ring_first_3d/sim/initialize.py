"""Independent E1/E2 nine-parameter Body using original T05–T09 math."""
import json
import numpy as np
from scipy.spatial import cKDTree
from ..adapters.dxy import measure_pixels
from ..synthetic.io import fetch,save_json,outputs
from ..synthetic.raster import scene
from ..contracts.identities import sha256
from ..policy.contracts import require
from .geometry import ellipse_proxy,cast
from .legacy import namespace


def ellipse_target(shape,fit):
    y,x=np.mgrid[:shape[0],:shape[1]];uv=np.c_[x.ravel(),y.ravel()]
    q=(uv-np.asarray(fit['center_px']))@np.linalg.inv(np.asarray(fit['basis_px'])).T
    return((q*q).sum(1)<=1).reshape(shape)


def run(task,attempt):
    root=attempt.parents[1];sc=task['sim'];ns=namespace(task);frames=json.loads(fetch(root,'G0_simulate','public/frame_index.json').read_text())
    ring=np.load(fetch(root,'G0_simulate','public/canonical_ring.npz'));rs=scene(ring['V'],ring['F'])
    fits=[];data={}
    for row in frames:
        cid=row['id'];a=dict(np.load(fetch(root,'G0_simulate','public/initialization/'+cid+'.npz')));data[cid]=a
        for domain,RGB,labels in [('synthetic',a['RGB'],a['labels']),('real_source',a['real_RGB'],a['real_labels'])]:
            official=measure_pixels(RGB,labels,inner_diameter_mm=10.,source_id='SIM_REV1:'+domain+':'+row['source_id'],dxy_root=task['inputs']['dxy_root'])
            proxy=ellipse_proxy(labels==1)
            fits.append(dict(id=cid,video=row['video'],role=row['role'],domain=domain,formal=official,proxy=proxy,
                mapping_fit='FORMAL_DXY_CANDIDATE'if official['available']else'MASK_ELLIPSE_PROXY',
                center_px=official['center_px']if official['available']else proxy['center_px']if proxy else None,
                basis_px=official['basis_px']if official['available']else proxy['basis_px']if proxy else None))
    save_json(attempt/'IMAGE_FITS.json',fits);save_json(attempt/'REUSE_RECEIPTS.json',ns['reuse_receipts'])
    by={r['id']:r for r in fits if r['domain']=='synthetic'};ids=[]
    for v in ['004','005']:
        options=sorted(r['id']for r in frames if r['video']==v and r['role']=='FIT')
        ids.extend([options[i]for i in np.linspace(0,len(options)-1,sc['initialization_views_per_video'],dtype=int)])
    class Problem:
        solve=ns['solve']
        def __init__(self,arm):
            self.scene='G01_LIKE_SHARED';self.arm=arm;self.variant='SIM_ADAPTER_2D_ONLY';self.ids=ids;self.R0=np.eye(3)
            self.base=np.asarray(sc['model_base']);self.lo=np.r_[np.full(3,-10.),np.full(3,-.8),np.log(np.full(3,.25))];self.hi=np.r_[np.full(3,10.),np.full(3,.8),np.log(np.full(3,15.))]
            self.calls=0;self.invalid_calls=0;self.targets=[];self.cameras=[];self.weights=np.full(len(ids),1/len(ids))
            gx,gy=np.meshgrid(np.arange(160)*4+1.5,np.arange(90)*4+1.5);grid=np.c_[gx.ravel(),gy.ravel()]
            for cid in ids:
                a=data[cid];K,C=a['K'],a['C'];fit=by[cid]['formal']if arm=='E1'else by[cid]['proxy']
                target=a['labels']==1 if arm=='E2'else ellipse_target(a['labels'].shape,fit)
                cad=cast(rs,grid,K,C)[0]
                self.targets.append(ns['target_data'](target,a['labels'],cad,C,K));self.cameras.append(dict(K=K,T=C))
            self.N=sum(128+len(t['boundary'])+14400 for t in self.targets)+9
        def residual(self,p):
            self.calls+=1
            try:
                rr=[]
                for t,c,w in zip(self.targets,self.cameras,self.weights):rr.extend([x*np.sqrt(w)for x in ns['two_d_parts'](p,self.R0,t,c['K'],c['T'],rs)])
                prior=np.r_[(p[:3]-self.base[:3])/10,p[3:6]/.8,(p[6:9]-self.base[6:9])/1.2]*np.sqrt(.05)
                r=np.r_[np.concatenate(rr),prior]
                if not np.isfinite(r).all():raise ValueError('Nonfinite 2D residual')
                return r
            except(ValueError,np.linalg.LinAlgError):self.invalid_calls+=1;return np.full(self.N,1000.)
    results=[];selections={}
    for arm in ['E1','E2','E1_PROXY']:
        missing=[cid for cid in ids if not by[cid]['formal']['available']]if arm=='E1'else[]
        if missing:
            selections[arm]=dict(available=False,status='NOT_EVALUABLE_DXY_NO_SELECTED_GEOMETRY',missing_required=missing);continue
        problem=Problem(arm);starts=[]
        for start in range(sc['initialization_starts']):
            fit=problem.solve(start);p=np.asarray(fit['p']);eligible=np.isfinite(p).all()and np.isfinite(fit['objective'])and(fit['objective']<1000.)
            fit.update(arm=arm,finite_bounded_diagnostic=bool(eligible),eligible_converged=bool(eligible and fit['optimizer_success']))
            starts.append(fit);results.append(fit)
            print('BODY_FIT',arm,start,fit['optimizer_success'],fit['nfev'],fit['objective'],flush=True)
        eligible=[r for r in starts if r['eligible_converged']]
        # A finite, bounded diagnostic baseline is explicitly retained when a
        # mature optimizer reaches its iteration cap. It is not certified as
        # converged; this scientific negative must not abort other methods.
        candidates=eligible or[r for r in starts if r['finite_bounded_diagnostic']]
        if candidates:
            best=min(candidates,key=lambda r:(r['objective'],r['start']));selections[arm]=dict(available=True,status='CONVERGED_NUMERIC_NOT_ACCURACY_CERTIFICATE'if eligible else'FINITE_DIAGNOSTIC_NONCONVERGED',selected_start=best['start'],p=best['p'],R0=best['R0'],objective=best['objective'],starts=starts)
            V,F=ns['mesh'](np.asarray(best['p']),np.asarray(best['R0']),True)
            np.savez_compressed(attempt/(arm+'_body.npz'),V=V,F=F,p=best['p'],R0=best['R0'])
        else:selections[arm]=dict(available=False,status='NO_FINITE_BOUNDED_START',starts=starts)
    chosen=next((arm for arm in sc['initialization_order']if selections[arm]['available']),None)
    require(chosen is not None,'BODY_INITIALIZATION','All independent initialization arms failed')
    body=np.load(attempt/(chosen+'_body.npz'));np.savez_compressed(attempt/'FROZEN_BODY.npz',**dict(body))
    freeze=dict(selected_arm=chosen,selection='Predeclared E1/E2/explicit proxy priority; only FIT objective, no GT',fit_ids=ids,
        body_sha256=sha256(attempt/'FROZEN_BODY.npz'),GT_read_by_predictor=False,body_frozen=True,history_prediction_fallback=0,
        selections=selections,multi_start_stability={arm:dict(available=s['available'],parameter_std=np.std([r['p']for r in s.get('starts',[])],axis=0)if s.get('starts')else None)for arm,s in selections.items()})
    save_json(attempt/'BODY_FREEZE.json',freeze)
    return outputs(attempt,dict(status='PASS',role='predictor',selected_arm=chosen,fit_views=len(ids),formal_numeric_frames=sum(r['formal']['available']for r in fits if r['domain']=='synthetic'),synthetic_frames=len(frames),GT_read_by_predictor=False,body_frozen=True))
