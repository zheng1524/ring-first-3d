"""Thin transport check on actual HIST snapshots, including Target/Support identities."""
import numpy as np
from common import *
from ring_first_3d.contracts.coordinates import resize_intrinsics,unproject,project,validate_c2w
from ring_first_3d.sim.geometry import se3,transform
rows=[]
for v in ['004','005']:
 folder=T/'inputs'/('V6_HIST_'+v);a=np.load(folder/'local005_camera_0.npz');h=np.load(folder/'005_supported_ref00000.npz');surface=np.load(folder/'005_supported_ref00000_surface.npz');ledger=read(folder/'ledger005.json');C=a['c2w'];K=a['K'];ref=int(h['reference']);sources=h['sources'];assert len(sources)==3 and ref not in sources;np.testing.assert_allclose(h['K_index_native'],resize_intrinsics(K,[640,360],[640,352]));np.testing.assert_array_equal(C,h['c2w']);np.testing.assert_array_equal(surface['pose'],C[ref]);np.testing.assert_array_equal(surface['source_frames'],sources)
 z=h['depth_mm'];y,x=np.mgrid[0:352:8,0:640:8];uv=np.c_[x.ravel(),y.ravel()];z=z[y,x].ravel();good=np.isfinite(z)&(z>0);uv,z=uv[good],z[good];P=unproject(uv,z,h['K_index_native'],C[ref]);q,d=project(P,h['K_index_native'],C[ref]);H=se3([.1,-.2,.3,1,2,3]);out=H@C;newq,newz=project(transform(P,H),h['K_index_native'],out[ref]);maxpx=float(np.max(abs(newq-q)));assert maxpx<1e-8;assert np.max(abs(newz-z))<1e-8
 for cc in out:validate_c2w(cc)
 L=a['points'];front=((L-C[ref,:3,3])@C[ref,:3,:3])[:,2]>0;L=L[front];lp,_=project(L,K,C[ref]);lq,_=project(transform(L,H),K,out[ref]);landmark_px=float(np.max(abs(lp-lq)));relative_delta=float(np.max(abs(np.linalg.inv(C[ref])@C-np.linalg.inv(out[ref])@out)));assert landmark_px<1e-7 and relative_delta<1e-8
 rows.append(dict(video=v,native_K=h['K_index_native'],network_WH=[640,352],packaged_WH=[640,360],stored_depth_unit='mm',c2w_unit='mm',target_raw=ledger[ref]['raw_frame'],support_raw=[ledger[int(i)]['raw_frame']for i in sources],native_roundtrip_max_px=float(np.max(abs(q-uv))),transport_max_px=maxpx,camera_transport_projection_checked=True,landmark_projection_invariance_max_px=landmark_px,landmark_projection_checked_N=int(front.sum()),landmark_nonpositive_N=int((~front).sum()),relative_camera_matrix_max_delta=relative_delta,landmark_count=len(transform(a['points'],H)),reference_frame_matches=True,NOTE='One example per video read in full; all39 native/surface files hashed in V6_INTERFACE. No real registration success claimed.'))
save(T/'evidence/V6_TRANSPORT_TEST.json',rows)
