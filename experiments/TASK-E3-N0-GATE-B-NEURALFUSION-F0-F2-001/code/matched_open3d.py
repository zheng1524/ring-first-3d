"""Fixed same-crop, same-order, same-voxel classical comparison only."""
from common import *
from evaluate import evaluate
import argparse
def main(v,stage):
    assert not (R/f'O3D_{v}_{stage}_RUN.json').exists()
    settings=cfg()['Open3D'];scale=.001;start=time.monotonic()
    volume=o3d.pipelines.integration.ScalableTSDFVolume(voxel_length=settings['voxel_mm']*scale,
        sdf_trunc=settings['sdf_trunc_mm']*scale,color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8,
        volume_unit_resolution=16,depth_sampling_stride=1)
    for cid in cfg()['sequences'][stage]:
        c=crop(cid,v);K,T=camera(cid);Kc=c['K_crop'];E=T.copy();E[:3,3]*=scale
        rgbd=o3d.geometry.RGBDImage.create_from_color_and_depth(o3d.geometry.Image(c['RGB'].copy()),
            o3d.geometry.Image((c['depth_mm']*scale).astype(np.float32)),depth_scale=1.,depth_trunc=.1,convert_rgb_to_intensity=False)
        intrinsic=o3d.camera.PinholeCameraIntrinsic(320,240,Kc[0,0],Kc[1,1],Kc[0,2],Kc[1,2])
        volume.integrate(rgbd,intrinsic,np.linalg.inv(E))
    m=volume.extract_triangle_mesh();m.vertices=o3d.utility.Vector3dVector(np.asarray(m.vertices)/scale)
    m.compute_vertex_normals();assert len(m.triangles)>0
    path=R/'meshes'/f'O3D_{v}_{stage}_mm.ply';o3d.io.write_triangle_mesh(str(path),m)
    save(f'O3D_{v}_{stage}_RUN.json',dict(seconds=time.monotonic()-start,settings=settings,sources=cfg()['sequences'][stage],
        faces=len(m.triangles),all_faces_preserved=True,GT_read=False,GPU=0))
    evaluate('O3D',v,stage)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('version',choices=['V6','V2']);p.add_argument('stage',choices=['F0','F1','F2']);a=p.parse_args();main(a.version,a.stage)
