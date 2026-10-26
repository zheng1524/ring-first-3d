"""Independent L1-L4 replay: only saved XYZ/RGB/cameras + CAD + config.

No original RGB, Mask, depth image, video, upstream model or GT is opened.
"""
import argparse,json,sys,os
from pathlib import Path
os.environ.setdefault('PYTHONDONTWRITEBYTECODE','1')
REPO=Path(__file__).resolve().parents[3];sys.path.insert(0,str(REPO))
import numpy as np,trimesh
from visualization import real_p0_renderer as base
from visualization import pointcloud_audit_renderer as diag
from visualization.same_camera_scene import SameCameraScene
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--layers',required=True,type=Path);parser.add_argument('--ring',required=True,type=Path);parser.add_argument('--config',required=True,type=Path);parser.add_argument('--output-root',required=True,type=Path);args=parser.parse_args()
    if args.output_root.exists()and any(args.output_root.iterdir()):parser.error('Choose a new empty output directory')
    args.output_root.mkdir(parents=True,exist_ok=True);os.environ.setdefault('MPLCONFIGDIR',str(args.output_root/'mpl'))
    def forbid_source_images(event,values):
        if event!='open'or not isinstance(values[0],(str,bytes)):return
        path=Path(os.fsdecode(values[0])).resolve();mode=values[1]if len(values)>1 and isinstance(values[1],str)else'';flags=values[2]if len(values)>2 and isinstance(values[2],int)else 0
        write=any(c in mode for c in 'wax+')or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        if not write and(path.suffix.lower()in {'.png','.jpg','.jpeg','.mp4','.blend'}or(path.suffix.lower()=='.npz'and path!=args.layers.resolve())):raise PermissionError('XYZ-only replay forbids source image/depth/video input: '+str(path))
    sys.addaudithook(forbid_source_images)
    a=dict(np.load(args.layers));cfg=json.loads(args.config.read_text());mesh=trimesh.load(args.ring,process=False);size=tuple(a['source_image_size']);scene=SameCameraScene(mesh,a['source_K'],a['source_c2w'],size,cfg['open3d_vendor'])
    poses=[dict(name=n,c2w=a[key])for n,key in [('source_reference','source_c2w'),('diagnostic_left','diagnostic_left_c2w'),('diagnostic_right','diagnostic_right_c2w')]]
    figures,metadata=diag.figures(a['P0_XYZ_mm'],a['P0_RGB'],a['background_XYZ_mm'],a['background_RGB'],mesh,scene,a['source_K'],a['source_c2w'],poses,size,cfg,str(a['scene_id']),str(a['morphology']),str(a['ring']),str(a['condition']))
    plt=base.configure()
    for name,fig in figures.items():fig.savefig(args.output_root/name,dpi=cfg['PNG_DPI'],facecolor='white');plt.close(fig)
    print('XYZ_ONLY_REPLAY_COMPLETE',args.output_root,'; no RGB/Mask/depth image or video inputs')
if __name__=='__main__':main()
