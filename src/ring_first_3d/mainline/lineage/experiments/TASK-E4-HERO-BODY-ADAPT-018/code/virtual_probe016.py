"""GT-free initial image-gradient, visibility and observability control."""
from tape import *
def main():
 guard_optimizer();c=Case('virtual_Ip');ch=FreeVertices(c);ch.total_trust_D=1.;q=torch.zeros((ch.N,3),device=device,dtype=torch.float64,requires_grad=True);obj=MultiObjective(c,ch);obj.attempt=40;G,per,corr,rec=instrument(c,ch,obj,q);info,rows=observability(c,c.V,corr,obj);image=sum(G[k]for k in NAMES[:4]);gg=GeometryGuard(c,ch);d=-image;d*=ch.tau/d.norm(dim=1).max().clamp_min(1e-30);V=ch.vertices(d).detach().cpu().numpy();why,check,_=gg.inspect(V,c.V)
 rec.update(case='virtual_Ip',fit=c.fit,contour_rank_histogram={str(k):int((info['rank']==k).sum())for k in range(4)},image_shadow_reasons=why,image_shadow_check=check,depth_kind='NO_DEPTH_SUPERVISION',GT_read=False)
 save('metrics/VIRTUAL_INITIAL_PROBE.json',rec);np.savez_compressed(R/'metrics/VIRTUAL_INITIAL_PROBE.npz',V=c.V,F=c.F,F_solid=c.F_solid,image_gradient=image.cpu().numpy(),shadow_V=V,**info);save('metrics/VIRTUAL_CORRESPONDENCES.json',rows);print('VIRTUAL_INITIAL_PROBE_COMPLETE',c.fit,flush=True)
if __name__=='__main__':main()
