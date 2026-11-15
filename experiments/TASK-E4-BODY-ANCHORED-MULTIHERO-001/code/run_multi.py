"""One shared Body, fixed native sources; atomic outer-round rollback."""
from body_multi import *
import argparse
from native_multi import raycast,corrected,peer_conflicts

def cumulative_bias(ss):return sum(s.w*CFG['hero_weight']*CFG['bias_prior_weight']*np.sum((s.theta/np.array(CFG['bias_prior_sigma_mm']))**2)for s in ss)
def snap(folder,label,c,ch,q,ss,extra):
 folder.mkdir(parents=True,exist_ok=True);V=ch.vertices(q).detach().cpu().numpy();np.savez_compressed(folder/(label+'.npz'),V=V,F=c.F,F_solid=c.F_solid,inferred_base_faces=c.inferred,boundary_vertex=c.boundary,parameters=q.detach().cpu().numpy(),source_ids=np.array([s.id for s in ss]),theta=np.array([s.theta for s in ss]));trimesh.Trimesh(V,c.F_solid,process=False).export(folder/(label+'_mm.ply'));save(str(folder.relative_to(R)/(label+'.json')),extra)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('group');ap.add_argument('arm',choices=['B0','B1','B2','B3']);args=ap.parse_args();g,arm=args.group,args.arm
 assert all(r['PASS']for r in load(R/'metrics/SYNTHETIC_TESTS.json'));assert load(R/'metrics/BASELINE_REPRODUCTION.json')['PASS'];guard_optimizer();torch.manual_seed(CFG['seed']);np.random.seed(CFG['seed']);folder=R/'runs'/g/arm;assert not(folder/'FINAL.npz').exists(),'Frozen final exists';c=Case(g);configure(c);ch=FreeVertices(c);ch.total_trust_D=CFG['body_total_trust_D'];q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);ss=[Source(s)for s in load(R/'config/SOURCES.json')if s['group']==g];weights_rec=source_weights(ss,c.center);save('metrics/'+g+'_SOURCE_WEIGHTS.json',weights_rec);ring=scene(c.ringV,c.ringF);gg=GeometryGuard(c,ch);obj=JointObjective(c,ch,ss);opt=torch.optim.Adam([q],lr=CFG['lr_mm']);q0=q.detach().clone();theta0=np.array([s.theta for s in ss]);start=time.time();hist=[];trials=[];biaslog=[];accept_total=0;peer_conflicts(ss,ring);initial=geometry_score(ss,c.V,c.F,ring);snap(folder,'INITIAL',c,ch,q,ss,initial);print('START',g,arm,'sources',len(ss),'fixed_N',initial['N'],flush=True)
 for rd in range(1,1 if arm=='B0'else CFG['rounds']+1):
  oldq=q.detach().clone();oldtheta=np.array([s.theta.copy()for s in ss]);oldopt=copy.deepcopy(opt.state_dict());oldsd=gg.lastsd.copy();oldrev=gg.lastreverse.copy();oldV=ch.vertices(q).detach().cpu().numpy();before=geometry_score(ss,oldV,c.F,ring);oldpen=cumulative_bias(ss);oldbind=obj.bind_geometry(oldV,ring);oldloss,oldparts=obj.compute(q,False);old_binding=obj.bind.copy();reason=[];roundaccept=0;body=scene(oldV,c.F)
  if arm in ['B1','B3']:
   for s in ss:
    cr=correspond(s,oldV,c.F,body,ring);t,rec=bias_proposal(s,cr);rec.update(group=g,arm=arm,round=rd);prev=s.theta.copy();native=s.z0+s.A@t
    if rec['status']=='PROPOSED':
     # Corrected points must stay in front of CAD and outside the Ring solid; no new penetration.
     oldX=s.points();newX=s.points(t);oldsdH=ring.compute_signed_distance(o3d.core.Tensor(oldX.astype(np.float32)),nsamples=3).numpy();newsdH=ring.compute_signed_distance(o3d.core.Tensor(newX.astype(np.float32)),nsamples=3).numpy();cad=s.o['cad_z'];valid0=s.z0+s.A@prev<cad-.05;valid1=native<cad-.05
     if (native<=0).any()or np.any(newsdH<np.minimum(oldsdH,0)-1e-5)or np.sum(valid1)<np.sum(valid0):rec.update(status='REJECTED_HERO_CAD_OR_VISIBILITY');t=prev
     else:
      s.theta=t;post=correspond(s,oldV,c.F,body,ring);same=cr['matched'];preerr=np.linalg.norm(cr['X'][same]-cr['Q'][same],axis=1).mean();posterr=post['distance'][same].mean();rec.update(actual_error_before_mm=preerr,actual_error_after_mm=posterr,matched_before=int(cr['matched'].sum()),matched_after=int(post['matched'].sum()))
      if posterr>preerr+1e-6 or post['matched'].sum()<cr['matched'].sum():s.theta=prev;rec.update(status='REJECTED_REASSOCIATED_GEOMETRY')
      else:rec.update(status='ACCEPTED')
    rec.update(final=s.theta.tolist(),max_cumulative_axial_mm=float(np.max(abs(s.A@s.theta))));biaslog.append(rec)
  bind=obj.bind_geometry(ch.vertices(q).detach().cpu().numpy(),ring)
  if arm in ['B2','B3']:
   for it in range(CFG['body_candidates_per_round']):
    loss,parts=obj.compute(q,True);grad=q.grad.detach().clone();qb=q.detach().clone();Vb=ch.vertices(q).detach().cpu().numpy();state=copy.deepcopy(opt.state_dict());opt.step();proposed=q.detach().clone();proposedstate=copy.deepcopy(opt.state_dict());dirs,coord=coherent_directions(ch,qb,[('ADAM',proposed-qb)],gg)
    with torch.no_grad():q.copy_(qb)
    opt.load_state_dict(state);done=False
    for method,d in dirs:
     move=float((ch.vertices(qb+d)-tensor(Vb,torch.float64)).norm(dim=1).max());d=d*min(1,ch.tau/max(move,1e-15))
     for ls in range(CFG['backtracks']):
      a=.5**ls;cand=qb+a*d;V=ch.vertices(cand).detach().cpu().numpy();why,geo,cache=gg.inspect(V,Vb);val=None
      if geo['max_step_mm']<1e-8:why.append('ZERO_GEOMETRIC_STEP')
      if not why:
       with torch.no_grad():val,_=obj.compute(cand,False)
       if not np.isfinite(val)or val>loss+1e-7:why.append('FULL_FIT_OBJECTIVE')
      trials.append(dict(group=g,arm=arm,round=rd,proposal=it,backtrack=ls,accepted=not why,reasons=why,before=loss,candidate=val,**geo));print('PROPOSAL',g,arm,rd,it,ls,why,'loss',val,flush=True)
      if why:
       if not(folder/('REJECTED_'+why[0]+'.npz')).exists():np.savez_compressed(folder/('REJECTED_'+why[0]+'.npz'),V=V,before_V=Vb,F=c.F,F_solid=c.F_solid,gradient=grad.cpu().numpy(),round=rd)
       continue
      with torch.no_grad():q.copy_(cand)
      opt.load_state_dict(proposedstate)
      # Smoothing changes the Adam direction: stale momentum must not be retained.
      opt.state[q].clear();gg.lastsd,gg.lastreverse=cache;roundaccept+=1;done=True;np.savez_compressed(folder/('MECHANISM_R%02d_P%02d.npz'%(rd,it)),before_V=Vb,after_V=V,F=c.F,gradient=grad.cpu().numpy(),delta=V-Vb);break
     if done:break
    if not done:
     with torch.no_grad():q.copy_(qb)
     opt.load_state_dict(state);assert state_equal(opt.state_dict(),state)
    if roundaccept>=CFG['body_accepted_per_round']:break
  peer_conflicts(ss,ring);V=ch.vertices(q).detach().cpu().numpy();after=geometry_score(ss,V,c.F,ring);candidatepen=cumulative_bias(ss);obj.bind=old_binding;candidate_loss,candidate_parts=obj.compute(q,False);check,geoinfo,_=gg.inspect(V,V) # full cumulative constraints retained, zero final incremental motion
  if check:reason+=check
  if candidate_loss+candidatepen>oldloss+oldpen+1e-7:reason.append('COMPLETE_FIXED_CORRESPONDENCE_OBJECTIVE')
  if after['hit']<before['hit']:reason.append('FIXED_NATIVE_HIT_COVERAGE_DROP')
  if after['matched']<before['matched']:reason.append('FIXED_NATIVE_MATCHED_COVERAGE_DROP')
  if after['score']+candidatepen>before['score']+oldpen+1e-7:reason.append('FIXED_DENOMINATOR_GEOMETRY_SCORE')
  # Evaluate objective change at the ORIGINAL fixed correspondences: refresh would change objective definition.
  # bias updates alter targets, so geometry acceptance above is independently mandatory.
  accepted=not reason
  if not accepted:
   np.savez_compressed(folder/('OUTER_REJECTED_%02d.npz'%rd),V=V,F=c.F,theta=np.array([s.theta for s in ss]))
   with torch.no_grad():q.copy_(oldq)
   for s,t in zip(ss,oldtheta):s.theta=t
   peer_conflicts(ss,ring);opt.load_state_dict(oldopt);gg.lastsd=oldsd;gg.lastreverse=oldrev;assert torch.equal(q,oldq)and state_equal(opt.state_dict(),oldopt)and np.array_equal(np.array([s.theta for s in ss]),oldtheta);roundaccept=0
  else:accept_total+=roundaccept
  V=ch.vertices(q).detach().cpu().numpy();final=geometry_score(ss,V,c.F,ring);rec=dict(group=g,arm=arm,round=rd,accepted=accepted,reasons=reason,body_updates=roundaccept,accepted_total=accept_total,before=before,candidate=after,after=final,candidate_loss=candidate_loss,candidate_parts=candidate_parts,initial_fixed_objective=oldloss,bias_prior_before=oldpen,bias_prior_candidate=candidatepen,max_Body_displacement_mm=float(np.linalg.norm(V-c.V,axis=1).max()),ring_min_mm=float(gg.lastsd.min()),geometry=geoinfo,correspondence_samples=bind,seconds=time.time()-start);hist.append(rec);snap(folder,'ROUND_%02d'%rd,c,ch,q,ss,rec);torch.save(dict(q=q.detach().cpu(),optimizer=opt.state_dict(),theta=np.array([s.theta for s in ss]),round=rd,torch_rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state(),numpy_rng=np.random.get_state(),config=CFG),folder/'LATEST.pt');save('metrics/'+g+'_'+arm+'_ROUNDS.json',hist);save('metrics/'+g+'_'+arm+'_TRIALS.json',trials);save('metrics/'+g+'_'+arm+'_BIAS.json',biaslog);print('ROUND_DONE',g,arm,rd,accepted,reason,'hit',before['hit'],final['hit'],'score',before['score'],final['score'],flush=True)
  if not accepted:break # exact state rollback with deterministic fixed proposal is a fixed point, not a reason to repeat identical deletion/optimization
 finalV=ch.vertices(q).detach().cpu().numpy();end=geometry_score(ss,finalV,c.F,ring);snap(folder,'FINAL',c,ch,q,ss,dict(group=g,arm=arm,seconds=time.time()-start,rounds=len(hist),accepted_body=accept_total,initial=initial,final=end,ring_min_mm=float(gg.lastsd.min()),GT_used=False));save('metrics/'+g+'_'+arm+'_BIAS.json',biaslog);save('metrics/'+g+'_'+arm+'_TRIALS.json',trials);print('FINISHED',g,arm,time.time()-start,flush=True)
if __name__=='__main__':
 import open3d as o3d
 main()
