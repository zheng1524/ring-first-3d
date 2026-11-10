"""Same-graph original scalar grouping versus expanded component differentiation."""
from tape import *

def main():
 guard_optimizer();c=Case('G02');ch=FreeVertices(c);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch);obj.attempt=40;obj.depth.begin(ch.mesh(q));rows=[];exactG=torch.zeros_like(q);expandedG=exactG.clone()
 for cid in c.fit:
  t,m=view_terms(c,ch,obj,q,cid);exact=obj._last_exact_view_loss;g0=gradient(exact,q);g1=gradient(sum(t.values()),q);gs=sum(gradient(v,q)for v in t.values());exactG+=g0;expandedG+=gs
  # Two backward paths to the same scalar, exactly the same graph.
  q.grad=None;exact.backward(retain_graph=True);bg=q.grad.detach().clone();repeat=gradient(exact,q)
  rows.append(dict(view=cid,exact_vs_expanded_norm=float((g0-gs).norm()),exact_vs_expanded_relative=float((g0-gs).norm()/g0.norm().clamp_min(1e-30)),expanded_joint_vs_separate=float((g1-gs).norm()/g1.norm().clamp_min(1e-30)),exact_autograd_vs_backward=float((g0-bg).norm()/g0.norm().clamp_min(1e-30)),exact_repeat_error=float((g0-repeat).norm()/g0.norm().clamp_min(1e-30)),value_difference=float(exact.detach()-sum(t.values()).detach()),exact_norm=float(g0.norm())))
 reg=gradient(relative_total(obj.prior(ch.mesh(q))),q);exactG+=reg;expandedG+=reg;obj.compute(q,True);full=q.grad.detach().clone();out=dict(rows=rows,exact_grouped_sum_vs_original_compute=float((exactG-full).norm()/full.norm()),expanded_vs_exact_grouped=float((expandedG-exactG).norm()/exactG.norm()),original_gradient_norm=float(full.norm()),GT_read=False,optimizer_steps=0)
 save('metrics/G02_EXACT_GROUPING_ISOLATION.json',out);print(out,flush=True)
if __name__=='__main__':main()
