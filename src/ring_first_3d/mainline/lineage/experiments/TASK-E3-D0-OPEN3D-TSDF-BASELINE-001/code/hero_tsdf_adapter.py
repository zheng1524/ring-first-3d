"""HEROToTSDFAdapter v0.1: only input units/camera/pixel/mask adaptation.

Group-independent: accepts camera axial Z in mm, matching native K, c2w in mm,
RGB uint8 and categorical mask at the same resolution. No camera/depth fitting.
"""
from common import *
class HEROToTSDFAdapter:
    version='0.1'
    def __init__(self,depth_mm,rgb,labels,K_native,c2w_mm,depth_trunc_mm):
        self.K=np.array(K_native,float,copy=True);self.T=np.array(c2w_mm,float,copy=True)
        assert depth_mm.ndim==2 and rgb.shape==(*depth_mm.shape,3)and labels.shape==depth_mm.shape
        assert np.isfinite(self.K).all()and np.isfinite(self.T).all()and np.allclose(self.T[3],[0,0,0,1])
        assert np.allclose(self.T[:3,:3].T@self.T[:3,:3],np.eye(3),atol=1e-8)and np.linalg.det(self.T[:3,:3])>0
        self.valid=(labels==1)&np.isfinite(depth_mm)&(depth_mm>0)&(depth_mm<=depth_trunc_mm)
        self.depth_m=np.where(self.valid,depth_mm*.001,0).astype(np.float32)
        self.rgb=np.ascontiguousarray(rgb,dtype=np.uint8);self.depth_trunc_mm=depth_trunc_mm
        T_m=self.T.copy();T_m[:3,3]*=.001;self.w2c_m=np.linalg.inv(T_m)
        h,w=depth_mm.shape;self.intrinsic=o3d.camera.PinholeCameraIntrinsic(w,h,self.K[0,0],self.K[1,1],self.K[0,2],self.K[1,2])
    def rgbd(self):
        return o3d.geometry.RGBDImage.create_from_color_and_depth(o3d.geometry.Image(self.rgb),o3d.geometry.Image(self.depth_m),depth_scale=1.,depth_trunc=self.depth_trunc_mm*.001,convert_rgb_to_intensity=False)
    @classmethod
    def from_source(cls,s,depth_trunc_mm):
        h,w=s['depth'].shape
        labels=cv2.resize(s['labels'],(w,h),interpolation=cv2.INTER_NEAREST)
        rgb=cv2.resize(s['RGB'],(w,h),interpolation=cv2.INTER_AREA)
        return cls(s['depth'],rgb,labels,s['Kn'],s['T'],depth_trunc_mm)
def volume():
    c=cfg();return o3d.pipelines.integration.ScalableTSDFVolume(voxel_length=c['voxel_length_mm']*.001,sdf_trunc=c['sdf_trunc_mm']*.001,color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8,volume_unit_resolution=c['volume_unit_resolution'],depth_sampling_stride=c['depth_sampling_stride'])
