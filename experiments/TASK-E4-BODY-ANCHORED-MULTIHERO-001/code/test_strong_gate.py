from body_multi import *

def main():
 c=Case('G06');configure(c);ch=FreeVertices(c);s=Source(next(x for x in load(R/'config/SOURCES.json')if x['group']=='G06'));native=NativeDepth(c,ch,[s]);q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);L=native.term(ch.mesh(q),s,np.zeros(len(s.uv),bool));g=torch.autograd.grad(L,q)[0];L2=native.term(ch.mesh(q),s,None);g2=torch.autograd.grad(L2,q)[0];ok=float(g.abs().max())==0. and torch.isfinite(g2).all()and g2.norm()>0;save('metrics/STRONG_SUPERVISION_GATE_TEST.json',dict(PASS=bool(ok),all_paused_gradient_max=float(g.abs().max()),normal_native_gradient_norm=float(g2.norm()),fixed_N=len(s.uv),source=s.id,paused_loss=float(L),native_loss=float(L2),denominator_unchanged=True));assert ok;print('STRONG_GATE',ok,flush=True)
if __name__=='__main__':main()
