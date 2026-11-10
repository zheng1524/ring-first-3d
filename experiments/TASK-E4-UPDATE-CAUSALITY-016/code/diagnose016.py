"""Read-only causal measurements and explicitly noncommitted shadow proposals."""
from tape import *
import argparse

TASK=Path(__file__).resolve().parents[1]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('case');args=ap.parse_args();guard_optimizer();n=args.case;c=Case(n);ch=FreeVertices(c);ch.total_trust_D=1.;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch);obj.attempt=40;gg=GeometryGuard(c,ch)
 G,per,corr,rec=instrument(c,ch,obj,q);info,rows=observability(c,c.V,corr,obj);far,targets=associations(obj,c.V);oldmask=np.zeros(ch.N,bool)
 for _,d in local_normalized(ch,q,sum(G.values())):oldmask|=d.norm(dim=1).cpu().numpy()>0
 seed=load(R/'inputs'/n/'STALK_SEED.json');patch=np.array(seed['s'])>0
 rec.update(case=n,far_associated_N=int(far.sum()),old_band_covers_far_N=int((far&oldmask).sum()),centerline_patch_covers_far_N=int((far&patch).sum()),far_rank_histogram={str(k):int((far&(info['rank']==k)).sum())for k in range(4)},vertex_rank_histogram={str(k):int((info['rank']==k).sum())for k in range(4)},GT_read=False,optimizer_steps=0,observability='Contour scalar-Jacobian diagonal 3x3 blocks; ignores inter-vertex coupling, not full Hessian or calibrated Fisher information')
 flat={cid+'__'+k:v for cid,dd in per.items()for k,v in dd.items()};np.savez_compressed(R/'metrics'/(n+'_CAUSAL_TAPE.npz'),V=c.V,F=c.F,F_solid=c.F_solid,far=far,old_candidate=oldmask,centerline_patch=patch,**info,**G_to_numpy(G),**flat);save('metrics/'+n+'_CORRESPONDENCES.json',rows);save('metrics/'+n+'_CAUSAL_SUMMARY.json',rec)
 image=sum(G[k]for k in NAMES[:4]);directions=[('FULL',-sum(G.values())),('IMAGE',-image)]+expanded_directions(ch,q,q.grad,obj)[0]+local_normalized(ch,q,q.grad)
 sd=gg.ring_distance(c.V);contact=sd<.02;pin=np.zeros(ch.N,bool);pin[np.unique(c.F_solid[contact])]=True;shadows=[]
 for label,d in directions[:6]:
  for mode in ['ORIGINAL','CONTACT_FACE_FIXED']:
   raw=d.detach().clone()
   if mode=='CONTACT_FACE_FIXED':raw[tensor(pin,torch.bool)]=0
   v=ch.vertices(raw).detach().cpu().numpy();move=np.linalg.norm(v-c.V,axis=1).max();raw*=ch.tau/max(move,1e-15)
   for alpha in [1.,.25,.0625]:
    step=alpha*raw;V=ch.vertices(step).detach().cpu().numpy();why,check,_=gg.inspect(V,c.V)
    with torch.no_grad():cost,parts=obj.compute(step,False)
    row=dict(case=n,direction=label,mode=mode,alpha=alpha,geometry_reasons=why,full_objective_change=cost-rec['parts']['total'],component_change={k:parts[k]-rec['parts'][k]for k in parts},**check);shadows.append(row)
    if alpha==1.:
     np.savez_compressed(R/'local_results'/(n+'_'+label+'_'+mode+'_SHADOW.npz'),V=V,before_V=c.V,F=c.F,F_solid=c.F_solid,delta=V-c.V,contact_faces=contact,pinned_vertices=pin)
 save('metrics/'+n+'_SHADOW_UPDATES.json',shadows);table('metrics/'+n+'_SHADOW_UPDATES.csv',shadows);print('DIAGNOSED',n,rec['far_associated_N'],rec['far_rank_histogram'],rec['additivity_relative_error'],flush=True)

def G_to_numpy(G):return {k:g.detach().cpu().numpy()for k,g in G.items()}
if __name__=='__main__':main()
