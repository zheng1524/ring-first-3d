"""Recreate the actual official volume in memory in a fresh task-local directory."""
from hero_tsdf_adapter import *
def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--name',choices=['SINGLE','G0','G1','SINGLE_RESOLUTION_CONTROL'],required=True);parser.add_argument('--output',required=True,help='new directory under this task only');args=parser.parse_args();d=(R/args.output).resolve();assert d.is_relative_to(R)and not d.exists(),'use a NEW task-local directory';d.mkdir(parents=True)
    c=cfg();ids=c['Single']if args.name.startswith('SINGLE')else c[args.name];voxel=.05 if args.name.endswith('CONTROL')else c['voxel_length_mm'];vol=o3d.pipelines.integration.ScalableTSDFVolume(voxel*.001,c['sdf_trunc_mm']*.001,o3d.pipelines.integration.TSDFVolumeColorType.RGB8,volume_unit_resolution=c['volume_unit_resolution'],depth_sampling_stride=c['depth_sampling_stride'])
    manifest=load(R/'HERO_TSDF_INPUT_MANIFEST.json')
    for cid in ids:
        for a in next(r for r in manifest['sources']if r['source_id']==cid)['assets'].values():assert sha(a['path'])==a['sha256'],'source SHA changed'
        ad=HEROToTSDFAdapter.from_source(source(cid),c['depth_trunc_mm']);vol.integrate(ad.rgbd(),ad.intrinsic,ad.w2c_m)
    m=vol.extract_triangle_mesh();m.scale(1000,center=(0,0,0));m.compute_vertex_normals();o3d.io.write_triangle_mesh(str(d/'mesh_mm.ply'),m)
    b=vol.extract_voxel_point_cloud();np.savez_compressed(d/'tsdf_observed_band.npz',XYZ_mm=np.asarray(b.points)*1000,tsdf_normalized=np.asarray(b.colors)[:,0]*2-1)
    save(d/'REPLAY.json',dict(name=args.name,sources=ids,config=asset(R/'TSDF_CONFIG.json'),mesh=asset(d/'mesh_mm.ply'),full_volume_in_memory=True,full_volume_serialization_available=False,mesh_repaired=False))
    print('OFFICIAL_VOLUME_REPLAYED',d,flush=True)
if __name__=='__main__':main()
