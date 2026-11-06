from stable import *
def main():
 tests=[]
 def value(x):return (x*x).sum()+torch.where(x[1]>0,x.sum()*0+.1,x.sum()*0)
 x=torch.tensor([1.,0.],device=device,dtype=torch.float64,requires_grad=True);L=value(x);g=torch.autograd.grad(L,x)[0];bad=torch.tensor([-1.,1.],device=device,dtype=torch.float64)*.02;reject=[float(value(x+.5**k*bad))>float(L)for k in range(8)];good=-.02*g;gain=float(value(x+good)-L);tests.append(dict(test='hard_active_set_same_direction_all_backtracks_fail',passed=all(reject)));tests.append(dict(test='steepest_restart_decreases_same_piecewise_objective',passed=gain<0,change=gain))
 q=torch.tensor([1.],device=device,dtype=torch.float64,requires_grad=True);opt=torch.optim.Adam([q],lr=.02);(q*q).sum().backward();opt.step();opt.zero_grad();state=copy.deepcopy(opt.state_dict());base=q.detach().clone();(q*q).sum().backward();opt.step()
 with torch.no_grad():q.copy_(base)
 opt.load_state_dict(state);tests.append(dict(test='failed_proposal_exact_restore_before_restart',passed=state_equal(opt.state_dict(),state)and torch.equal(q,base)));opt.state[q].clear();opt.zero_grad();(q*q).sum().backward();opt.step();tests.append(dict(test='accepted_restart_moments_reinitialize_at_step1',passed=int(opt.state[q]['step'])==1));save('metrics/RESTART_CONTRACT.json',dict(passed=all(x['passed']for x in tests),tests=tests,real_model_optimizer_steps=0,synthetic_optimizer_updates=3));assert all(x['passed']for x in tests);print('RESTART_CONTRACT_PASS')
if __name__=='__main__':main()
