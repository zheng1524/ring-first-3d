from renderer019 import *

def hub(x):
 a=x.abs();return torch.where(a<1,.5*x*x,a-.5)
def skew(t):
 x,y,z=t;o=x*0;return torch.stack([torch.stack([o,-z,y]),torch.stack([z,o,-x]),torch.stack([-y,x,o])])
class FeatureLoss:
 def __init__(self,scope,ids):
  self.views={v['id']:v for v in load(R/'config/VIEWS.json')};self.epi=load(R/'features'/(scope+'_EPI.json'));self.pnp=[x for x in load(R/'features'/(scope+'_PNP.json'))if x['success']];self.ids=ids;self.epi=[x for x in self.epi if x['b']in ids];self.pnp=[x for x in self.pnp if x['target']in ids];self.data=[]
  for x in self.epi:
   a,b=self.views[x['a']],self.views[x['b']];self.data.append(dict(a=a['id'],b=b['id'],Ta=tensor(a['T'],torch.float64),Tb=tensor(b['T'],torch.float64),ia=tensor(np.linalg.inv(a['K']),torch.float64),ib=tensor(np.linalg.inv(b['K']),torch.float64),p=tensor(np.c_[x['p'],np.ones(len(x['p']))],torch.float64),q=tensor(np.c_[x['q'],np.ones(len(x['q']))],torch.float64)))
  self.proj=[dict(target=x['target'],X=tensor(x['landmark_X'],torch.float64),uv=tensor(x['uv'],torch.float64),T=tensor(self.views[x['target']]['T'],torch.float64),K=tensor(self.views[x['target']]['K'],torch.float64))for x in self.pnp]
 def __call__(self,H,details=False):
  ee={};rr={};stats_e=[];stats_r=[]
  for a in self.data:
   T=H@a['Tb'];rot=T[:3,:3].T@a['Ta'][:3,:3];t=T[:3,:3].T@(a['Ta'][:3,3]-T[:3,3]);F=a['ib'].T@skew(t)@rot@a['ia'];fp=a['p']@F.T;fq=a['q']@F;den=(fp[:,:2].square().sum(1)+fq[:,:2].square().sum(1)).clamp_min(1e-20).sqrt();e=(a['q']*fp).sum(1)/den;loss=hub(e/3).mean();ee.setdefault(a['b'],[]).append(loss)
   if details:stats_e.extend(e.detach().cpu().numpy())
  for a in self.proj:
   T=H@a['T'];P=(a['X']-T[:3,3])@T[:3,:3];Z=P[:,2];u=P@a['K'].T;uv=u[:,:2]/u[:,2:].clamp_min(1e-6);err=uv-a['uv'];loss=torch.where((Z>0)[:,None],hub(err/3),torch.full_like(err,100.)).mean();rr.setdefault(a['target'],[]).append(loss)
   if details:stats_r.extend(torch.linalg.norm(err,dim=1).detach().cpu().numpy())
  channels=[];out={}
  for key,d in [('epi',ee),('reprojection',rr)]:
   if d:val=torch.stack([torch.stack(v).mean()for v in d.values()]).mean();channels.append(val);out[key]=float(val.detach())
   else:out[key]=None
  L=torch.stack(channels).mean()if channels else H.sum()*0
  if details:out.update(epipolar_px=stats(stats_e),reprojection_px=stats(stats_r),epi_frames=len(ee),reprojection_frames=len(rr),epi_observations=sum(len(x['p'])for x in self.data),reprojection_observations=sum(len(x['X'])for x in self.proj))
  return L,out
class PoseObjective:
 def __init__(self,ids,scope='CROSS'):
  self.render=FrozenRenderer(ids);self.ids=ids;self.w=weights_for(ids,self.render.views);self.feature=FeatureLoss(scope,ids);self.scale=tensor([.6,.6,.6,*([np.deg2rad(5)]*3)],torch.float64)
 def transform(self,q,cand):return exp_se3(q*self.scale)@cand
 def score(self,H):
  p=0.;per=[]
  with torch.no_grad():
   for cid in self.ids:
    z=self.render.polyp(H,cid,True);p+=self.w[cid]*float(z);per.append(dict(view=cid,polyp_loss=float(z),weight=self.w[cid]))
   f,fs=self.feature(H,True)
  return dict(polyp=p,feature=float(f),total=p+.05*float(f),feature_details=fs,per_frame=per)
 def evaluate(self,q,cand,gradient=False):
  if gradient:q.grad=None
  P=0.;Rg=0.;per=[]
  for cid in self.ids:
   H=self.transform(q,cand);p=self.render.polyp(H,cid,False);r=self.render.ring_loss(H,cid);loss=self.w[cid]*(p+r);P+=self.w[cid]*float(p.detach());Rg+=self.w[cid]*float(r.detach());per.append(dict(view=cid,polyp=float(p.detach()),ring=float(r.detach()),weight=self.w[cid]))
   if gradient:loss.backward()
  H=self.transform(q,cand);f,fs=self.feature(H);prior=(q*q).mean();L=.05*f+.01*prior
  if gradient:L.backward()
  return P+Rg+float(L.detach()),dict(polyp=P,ring=Rg,feature=float(f.detach()),prior=float(prior.detach()),weighted_feature=.05*float(f.detach()),weighted_prior=.01*float(prior.detach()),per_frame=per,feature_details=fs)
