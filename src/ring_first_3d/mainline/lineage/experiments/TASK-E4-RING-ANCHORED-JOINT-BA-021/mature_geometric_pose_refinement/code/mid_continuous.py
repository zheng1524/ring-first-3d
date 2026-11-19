"""Continuous-curve audit avoids interpreting discrete sampling phase as Mid bias."""
from refine import *
from ring020 import ellipse_points
from geometry021 import cpu_curve_distance
import types,importlib

def main():
 mod=types.ModuleType('dxy_mid');mod.__path__=['/home/liu/new-polyp-dxy/src/dxy_mid'];sys.modules.setdefault('dxy_mid',mod);recover=importlib.import_module('dxy_mid._engine.ring_component').recover;v=load(M/'config/VIEWS.json')[0];cad=RenderedCAD(v['ring_path']);K=np.array(v['K']);rho=np.linalg.norm(cad.V[:,:2],axis=1);R=(rho.min()+rho.max())/2;t=np.arange(720)/720*2*np.pi;X=np.c_[R*np.cos(t),R*np.sin(t),np.zeros(720)];out=[]
 for a in load(M/'metrics/CONICS_SYNTHETIC_MID_AUDIT.json'):
  C=np.array(a['known_C']);uv=projection(X,C,K)[0];mask=np.isfinite(cast(cad.cad,K,C,360,640));lab=mask.astype(np.uint8)*2;rgb=np.full((360,640,3),120,np.uint8);rgb[mask]=15;cv2.setRNGSeed(20261112);np.random.seed(20261112);d,p=recover(lab,rgb[:,:,::-1],10.);e=d.get('centerline');err=None
  if e:
   pm=ellipse_points(e,np.arange(8192)*2*np.pi/8192);V=np.c_[pm,np.ones(len(pm))];edges=np.c_[np.arange(len(pm)),np.roll(np.arange(len(pm)),-1)];err=stats(cpu_curve_distance(uv,V,edges,np.eye(4),np.eye(3)))
  out.append(dict(depth_mm=a['depth_mm'],tilt_deg=a['tilt_deg'],Mid_valid=e is not None,Mid=e,true_circle_vs_Mid_continuous_px=err,old720point_nearest_proxy_px=a['Mid_to_true_centerline_MAE_px'],Mid_conics_camera_center_bias_mm=a['Mid_Conics_center_bias_mm'],no_real_input_or_loss_changed=True))
 save('metrics/CONICS_MID_CONTINUOUS_CURVE_CHECK.json',out);table('metrics/CONICS_MID_CONTINUOUS_CURVE_CHECK.csv',out)
if __name__=='__main__':main()
