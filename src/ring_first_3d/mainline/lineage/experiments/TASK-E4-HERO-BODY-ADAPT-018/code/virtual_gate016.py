"""Explicit native Blender/OpenCV/PyTorch3D projection gate, before virtual fitting."""
from p3d import *

def main():
 root=Path(__file__).resolve().parents[1];native=load(root/'metrics/VIRTUAL_NATIVE_PROJECTION_GATE.json');assert native['all_pass'];c=Case('virtual_Ip');gp=Path(native['GT_source']['path']);g=np.load(gp);gm=mesh((g['V']-c.center)/c.scale,g['F']);rows=[]
 for cid,d in c.views.items():
  with torch.no_grad():fr=c.hard(gm,cameras=d['cam']);bz=fr.zbuf[0,...,0];pred=(fr.pix_to_face[0,...,0]>=0)&(bz<d['cad_z']);target=d['target']>0;iou=float((pred&target).sum()/((pred|target).sum().clamp_min(1)))
  # Corresponding fixed points: image boundary coordinates minus half-pixel.
  V=g['V'][::max(1,len(g['V'])//100)];X=(V-d['T'][:3,3])@d['T'][:3,:3];h=X@d['K'].T;uv=h[:,:2]/h[:,2,None];small=(uv+.5)*.5-.5
  with torch.no_grad():p=d['cam'].transform_points_screen(tensor(((V-c.center)/c.scale)[None]),image_size=[c.size])[0,:,:2].cpu().numpy()-.5
  error=float(np.linalg.norm(p-small,axis=1).max());rows.append(dict(view=cid,P3D_GT_small_Mask_IoU=iou,projection_max_px=error,pass_gate=iou>=.97 and error<=.02))
 out=dict(rows=rows,all_pass=all(x['pass_gate']for x in rows),GT_only_projection_audit=True,GT_source=asset(gp),Ring_CAD_fixed=True);save('metrics/VIRTUAL_P3D_PROJECTION_GATE.json',out);assert out['all_pass'],out;print('VIRTUAL_P3D_GATE',rows,flush=True)
if __name__=='__main__':main()
