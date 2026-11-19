"""Collaborator CLI with explicit inputs and outputs, no legacy workspace paths."""
import argparse
from pathlib import Path
import json
import os
import sys
import time
import numpy as np
from PIL import Image
from .io import read_json, save_json, check_assets

def frames_from(data):
    data=Path(data);manifest=read_json(data/'DATA_MANIFEST.json');check_assets(data,manifest)
    if manifest.get('unit')!='mm' or manifest.get('work_hw')!=[360,640]:
        raise ValueError('Frozen input contract requires millimetres and 640x360 work images')
    from .geometry import validate_camera
    frames=[]
    for row in manifest['frames']:
        validate_camera(row['c2w_mm'],row['K'])
        frames.append(dict(row,RGB=np.asarray(Image.open(data/row['rgb']).convert('RGB')),labels=np.asarray(Image.open(data/row['labels'])),K=np.asarray(row['K']),c2w_mm=np.asarray(row['c2w_mm'])))
    return manifest,frames

def main(argv=None):
    sys.dont_write_bytecode=True
    p=argparse.ArgumentParser(description='Ring-First metric cameras and official HERO native surfaces')
    sub=p.add_subparsers(dest='command',required=True)
    c=sub.add_parser('camera_demo',help='Actual Ring5DoF + real-map SIFT/PnP + yaw recovery')
    c.add_argument('--data',type=Path,required=True);c.add_argument('--out',type=Path,required=True)
    c.add_argument('--ring-only',action='store_true',help='Report unresolved yaw; do not pretend 6DoF certification')
    h=sub.add_parser('hero_demo',help='New official HERO inference with fixed cameras')
    h.add_argument('--data',type=Path,required=True);h.add_argument('--out',type=Path,required=True)
    h.add_argument('--mvs-root',type=Path);h.add_argument('--dino-root',type=Path);h.add_argument('--checkpoint',type=Path)
    h.add_argument('--runtime-config',type=Path,help='Optional machine-local paths, excluded from Git')
    h.add_argument('--source-manifest',type=Path,default=Path(__file__).with_name('upstream_source_lock.json'))
    h.add_argument('--clean',action='store_true');h.add_argument('--compare-history',action='store_true')
    h.add_argument('--visualize',action='store_true')
    v=sub.add_parser('visualize',help='Render actual saved native outputs; no inference')
    v.add_argument('--data',type=Path,required=True);v.add_argument('--output',type=Path,required=True);v.add_argument('--gallery',type=Path,required=True)
    args=p.parse_args(argv)
    if args.command=='camera_demo':
        from .camera import recover,observe
        from .rgb import pnp
        from .geometry import project
        import cv2
        cv2.setNumThreads(1)
        manifest,frames=frames_from(args.data);v=frames[0];start=time.time()
        rr=None if args.ring_only else pnp(v['RGB'],v['labels'],v['K'],dict(np.load(args.data/'REFERENCE_RGB_MAP.npz')))
        result=recover(v['labels'],v['K'],rr)
        result.update(seconds=time.time()-start,source_view=v['id'],historical_fallback=0,GT_used=False)
        args.out.mkdir(parents=True,exist_ok=True);save_json(args.out/'CAMERA_RESULT.json',result)
        if rr is not None:save_json(args.out/'RGB_GEOMETRY.json',rr)
        if not args.ring_only:
            ref=read_json(args.data/'historical/CAMERA_INITIAL.json')
            comparison=dict(c2w_max_abs=float(abs(np.asarray(result['c2w_mm'])-np.asarray(ref['C'])).max()),candidate_source_equal=result['candidate_source']==ref['candidate_source'],FIT_objective_abs=abs(result['FIT_objective']-ref['FIT_objective']),not_independent_pose_GT=True)
            save_json(args.out/'HISTORICAL_CAMERA_COMPARISON.json',comparison)
        print(json.dumps(dict(status=result['status'],source=result['candidate_source'],seconds=result['seconds'])))
    elif args.command=='hero_demo':
        rt=read_json(args.runtime_config) if args.runtime_config else {}
        sys.path[:0]=[str(Path(p).resolve()) for p in rt.get('readonly_dependency_paths',[])]
        for key in ['mvs_root','dino_root','checkpoint']:
            if getattr(args,key) is None:
                if key not in rt:p.error('Provide --'+key.replace('_','-')+' or --runtime-config')
                setattr(args,key,Path(rt[key]))
        # Runtime directories are caller output, never the dependency source tree.
        runtime=args.out.resolve()/'runtime';runtime.mkdir(parents=True,exist_ok=True)
        for key,tail in [('HF_HOME','hf'),('HF_MODULES_CACHE','hf_modules'),('TORCH_HOME','torch'),('MPLCONFIGDIR','mpl'),('XDG_CACHE_HOME','cache')]:os.environ[key]=str(runtime/tail)
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        import torch
        from .hero import load_official,infer
        if not torch.cuda.is_available():raise RuntimeError('Official frozen HERO path requires CUDA; no synthetic/cached fallback')
        torch.set_num_threads(4);torch.manual_seed(20261115)
        manifest,frames=frames_from(args.data)
        model,receipt=load_official(args.mvs_root,args.checkpoint,args.dino_root,read_json(args.source_manifest))
        rec=infer(model,frames,args.out);save_json(args.out/'MODEL_RECEIPT.json',receipt)
        if args.clean:
            from .cleaning import classify_native
            classify_native(args.out,args.data/'RING_CAD.npz')
        if args.compare_history:
            from .validation import compare_history
            compare_history(args.data,args.out)
        if args.visualize:
            from .visualization import generate
            generate(args.data,args.out,Path('visualization'))
        print(json.dumps(rec))
    else:
        from .visualization import generate
        generate(args.data,args.output,args.gallery)

if __name__=='__main__':main()
