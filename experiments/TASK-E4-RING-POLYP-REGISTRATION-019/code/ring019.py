from common import *
import types,importlib
DXY=Path('/home/liu/new-polyp-dxy/src/dxy_mid')
def dxy_module():
 pkg=types.ModuleType('dxy_mid');pkg.__path__=[str(DXY)];sys.modules.setdefault('dxy_mid',pkg);return importlib.import_module('dxy_mid._engine.ring_component')
def main():
 recover=dxy_module().recover;rows=[];rv=np.load(R/'inputs/G01/RING.npz');P=rv['V'];rho=np.linalg.norm(P[:,:2],axis=1);res=np.sqrt((rho-5.6)**2+P[:,2]**2)-.6;assert abs(res).max()<1e-4
 save('metrics/RING_CAD_AUDIT.json',dict(center_mm=P.mean(0),normal=[0,0,1],inner_radius_mm=float(rho.min()),outer_radius_mm=float(rho.max()),wire_radius_mm=float(np.ptp(P[:,2])/2),centerline_radius_mm=5.6,torus_residual_mm=stats(res),actual_CAD=asset(R/'inputs/G01/RING.npz'),normal_parity_candidates=[1,-1],right_handed=True,no_scale=True,ring_alone_yaw_observable=False))
 for v in load(R/'config/VIEWS.json'):
  a=np.load(v['cache']);cv2.setRNGSeed(20261111);np.random.seed(20261111);report,payload=recover(a['labels'],a['RGB'][:,:,::-1],10.);folder=R/'ring';folder.mkdir(exist_ok=True);np.savez_compressed(folder/(v['id']+'.npz'),inner=payload.get('inner_points',np.empty((0,2))),outer=payload.get('outer_points',np.empty((0,2))),rejected=payload.get('rejected_points',np.empty((0,2))));save('ring/'+v['id']+'.json',report);rows.append(dict(view=v['id'],video=v['video'],role=v['role'],DXY_valid=report['valid'],reason=report.get('reason'),inner_N=len(payload.get('inner_points',[])),outer_N=len(payload.get('outer_points',[])),diagnostics=report.get('diagnostics'),method='unchanged DXY visible-arc routine; no DXY diameter prediction used'))
 save('metrics/DXY_VISIBLE_RING_EVIDENCE.json',rows);table('metrics/DXY_VISIBLE_RING_EVIDENCE.csv',rows);save('provenance/DXY_READONLY_SOURCE.json',dict(files=[asset(DXY/'_engine'/n)for n in ['ring_component.py','polypseg_ring_fitting.py','ring_holes.py']],normalization='native640x360 pixels; no 2D scale formula used to calibrate 3D',outputs_only=str(R)));print('RING_EVIDENCE_COMPLETE',len(rows),sum(x['DXY_valid']for x in rows),flush=True)
if __name__=='__main__':main()
