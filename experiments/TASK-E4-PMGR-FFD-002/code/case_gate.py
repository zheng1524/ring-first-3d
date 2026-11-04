"""Same immutable local Mask derivative check for every physical case.

Added after discovering that the initial preflight only covered G01.
Historical G06 outputs remain negative evidence; this guard is not retroactive.
"""
from inputs import *
from shape import Body
from objective import Objective

def check_case(scene,row,p,fields,scope='PRETRAINING_CASE_GATE'):
    m=Body(row,p,fields);q=np.r_[p,np.zeros(12)];ob=Objective(scene,m);base=ob.evaluate(q,mask_only=True);rows=[]
    directions=[np.r_[np.array([.2,-.1,.3,.02,-.03,.01,.01,.02,-.02]),np.zeros(12)],np.r_[np.zeros(9),np.random.default_rng(217).normal(size=12)*.2]]
    for name,di in zip(['live9','FFD'],directions):
        for h in [.0001,.0003]:
            fd=(ob.evaluate(q+h*di,gradient=False,mask_only=True)['E']-ob.evaluate(q-h*di,gradient=False,mask_only=True)['E'])/(2*h);g=float(base['g']@di);rel=abs(fd-g)/max(abs(fd),abs(g),1e-4);rows.append(dict(case=scene,block=name,h=h,gradient=g,FD=fd,relative_difference=rel,passed=rel<.15,scope=scope))
    save('metrics/'+scene+'_'+scope+'.json',rows);return all(x['passed']for x in rows),rows

def main():
    rows=[]
    for scene in protocol()['scene_order']:
        p=np.load(R/'local_results'/scene/'C2/P0.npz')['q'][:9];fields=np.load(R/'inputs'/(scene+'_ffd_BASIS.npz'))['fields'];okay,r=check_case(scene,p0(scene,protocol()['scenes'][scene]['initial']),p,fields,'POST_HOC_QA_NOT_RETROACTIVE_GATE');rows+=r;print(scene,okay,flush=True)
    save('metrics/POST_HOC_CASE_MASK_GRADIENTS.json',rows)

if __name__=='__main__':main()
