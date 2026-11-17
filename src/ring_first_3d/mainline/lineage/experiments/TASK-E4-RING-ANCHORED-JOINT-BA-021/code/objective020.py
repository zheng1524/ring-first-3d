from ring020 import *

def hub(x):return torch.where(x.abs()<1,.5*x*x,x.abs()-.5)
def skew(t):
 x,y,z=t;o=x*0;return torch.stack([torch.stack([o,-z,y]),torch.stack([z,o,-x]),torch.stack([-y,x,o])])

class SymmetricFeatures:
 def __init__(self,scope,held=False):
  self.v={v['id']:v for v in load(R/'config/VIEWS.json')};self.directions=[]
  names=[scope,('REVERSE'if scope=='CROSS'else'NEGATIVE_REVERSE')]
  if held:names=[s+'_HOLDOUT'for s in names]
  for direction,name in enumerate(names):
   p=R/'features'/(name+'_PNP.json');obs=[]
   for x in load(p):
    if not x['success']:continue
    v=self.v[x['target']];obs.append(dict(view=x['target'],T=tensor(v['T'],torch.float64),K=tensor(v['K'],torch.float64),X=tensor(x['landmark_X'],torch.float64),uv=tensor(x['uv'],torch.float64),landmark=np.asarray(x['landmark_indices'],int)))
   self.directions.append(obs)
  self.epi=[]
  for x in load(R/'features'/((scope+'_HOLDOUT_EPI.json')if held else(scope+'_EPI_2D_ONLY.json'))):
   a,b=self.v[x['a']],self.v[x['b']];self.epi.append(dict(target=x['b'],Ta=tensor(a['T'],torch.float64),Tb=tensor(b['T'],torch.float64),ia=tensor(np.linalg.inv(a['K']),torch.float64),ib=tensor(np.linalg.inv(b['K']),torch.float64),p=tensor(np.c_[x['p'],np.ones(len(x['p']))],torch.float64),q=tensor(np.c_[x['q'],np.ones(len(x['q']))],torch.float64)))
 def evaluate(self,H,mode='symmetric',details=False):
  losses=[];report={}
  for direction,obs in enumerate(self.directions):
   tracks={};errs=[]
   for a in obs:
    if direction==0:C=H@a['T'];X=a['X']
    else:C=a['T'];X=a['X']@H[:3,:3].T+H[:3,3]
    P=(X-C[:3,3])@C[:3,:3];proj=P@a['K'].T;uv=proj[:,:2]/proj[:,2:].clamp_min(1e-6);dist=(uv-a['uv']).square().sum(1).add(1e-12).sqrt();l=torch.where(P[:,2]>0,hub(dist/3),torch.full_like(dist,100.))
    for k,z in zip(a['landmark'],l):tracks.setdefault(int(k),[]).append(z)
    if details:errs.extend(dist.detach().cpu().numpy())
   value=torch.stack([torch.stack(x).mean()for x in tracks.values()]).mean()if tracks else H.sum()*0
   losses.append(value);report['forward'if direction==0 else'reverse']=dict(N=sum(len(a['X'])for a in obs),tracks=len(tracks),frames=len(obs),loss=float(value.detach()),error_px=stats(errs)if details else None)
  F=losses[0]if mode=='single'else .5*(losses[0]+losses[1]);E={};ee=[]
  for a in self.epi:
   C=H@a['Tb'];rot=C[:3,:3].T@a['Ta'][:3,:3];t=C[:3,:3].T@(a['Ta'][:3,3]-C[:3,3]);M=a['ib'].T@skew(t)@rot@a['ia'];fp=a['p']@M.T;fq=a['q']@M;err=(a['q']*fp).sum(1)/(fp[:,:2].square().sum(1)+fq[:,:2].square().sum(1)).clamp_min(1e-20).sqrt();E.setdefault(a['target'],[]).append(hub(err/3).mean())
   if details:ee.extend(err.detach().cpu().numpy())
  epi=torch.stack([torch.stack(x).mean()for x in E.values()]).mean()if E else H.sum()*0;report['epipolar']=dict(frames=len(E),N=sum(len(a['p'])for a in self.epi),loss=float(epi.detach()),error_px=stats(ee)if details else None)
  return F,epi,report

class Objective:
 def __init__(self,ids,scope,arm,body=None):
  self.proto=load(R/'config/PROTOCOL.json');self.ids=ids;self.scope=scope;self.arm=arm;self.ring=RingRenderer(ids);self.feature=SymmetricFeatures(scope);self.scale=tensor(self.proto['pose_scale'],torch.float64);blocks={x:self.ring.data[x]['meta']['direction_block019']for x in ids};n=len(set(blocks.values()));self.w={x:1/n/sum(y==blocks[x]for y in blocks.values())for x in ids};self.rw=dict(self.proto['ring_weights']);self.body=body
  if arm=='R3_MASK_ONLY':self.rw={k:float(k=='M')for k in self.rw}
  elif arm=='R3_INNER_OUTER':self.rw=dict(M=.25,I=.375,C=0.,O=.375)
 def transform(self,q,seed):return exp_se3(q*self.scale)@seed
 def evaluate(self,q,seed,gradient=False,component_gradient=False):
  if gradient:q.grad=None
  totals={k:0. for k in ['M','I','C','O','F','E','prior','body']};gr={k:np.zeros(6)for k in totals};per=[]
  for cid in self.ids:
   H=self.transform(q,seed);ls,aux,_=self.ring.losses(H,cid);l=sum(self.rw[k]*ls[k]for k in ls)*self.w[cid]
   if component_gradient:
    for k,v in ls.items():gr[k]+=self.w[cid]*torch.autograd.grad(v,q,retain_graph=True)[0].detach().cpu().numpy()
   for k,v in ls.items():totals[k]+=self.w[cid]*float(v.detach())
   if self.body is not None:
    b=self.body.polyp(H,cid,False);l=l+self.w[cid]*b;totals['body']+=self.w[cid]*float(b.detach())
    if component_gradient:gr['body']+=self.w[cid]*torch.autograd.grad(b,q,retain_graph=True)[0].detach().cpu().numpy()
   if gradient:l.backward()
   per.append(dict(view=cid,weight=self.w[cid],ring={k:float(v.detach())for k,v in ls.items()},evidence=aux))
  H=self.transform(q,seed);F,E,aux=self.feature.evaluate(H,'single'if self.arm=='R2'else'symmetric');prior=q.square().mean();include=self.arm!='R1';tail=(self.proto['lambda_feature']*F+self.proto['lambda_epi']*E)if include else H.sum()*0;tail=tail+self.proto['lambda_prior']*prior
  if component_gradient:
   for k,v in [('F',F),('E',E),('prior',prior)]:gr[k]=torch.autograd.grad(v,q,retain_graph=True)[0].detach().cpu().numpy()
  if gradient:tail.backward()
  totals.update(F=float(F.detach()),E=float(E.detach()),prior=float(prior.detach()));total=sum(self.rw[k]*totals[k]for k in self.rw)+totals['body']+(self.proto['lambda_feature']*totals['F']+self.proto['lambda_epi']*totals['E']if include else 0)+self.proto['lambda_prior']*totals['prior'];rec=dict(parts=totals,weights=self.rw,per_frame=per,feature=aux)
  if component_gradient:
   rec['component_gradient_normalized_pose']=gr;rec['gradient_norms']={k:float(np.linalg.norm(g))for k,g in gr.items()};rec['gradient_cosines']={a+'__'+b:float(np.dot(gr[a],gr[b])/max(np.linalg.norm(gr[a])*np.linalg.norm(gr[b]),1e-20))for a in gr for b in gr if a<b}
  return total,rec
