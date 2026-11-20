"""Stage 1 (now unblocked): raw video frame -> frozen INIT mask -> cache npz.

Inputs are read-only. No model training, no threshold changes.
"""
import json, hashlib, sys
from pathlib import Path
import numpy as np, cv2, torch
from PIL import Image
sys.path.insert(0, '/home/liu/polyp_research/src')
from polypseg.common import load_pretrained_model

WS = Path('/home/liu/ring_first_3d_workspace')
ARCH_DIR = '/home/liu/polyp_research/models/preserved_best_multiclass_overlapaware_20260405'
# DXY frozen INIT checkpoint (verified sha256 981aa596...), loaded into the same architecture.
INIT_WEIGHTS = '/home/liu/polyp_research/experiments/dxy_remeasurement_20260917/02_segmentation/model/model.safetensors'
INIT_WEIGHT_SHA256 = '981aa596e8906edc4457219581c606d4a5a22bfc6f7e4924d3d9a4b9aff64464'
VIDEO_DIR = WS / 'smart_endoscope_20260805 (1)/raw'
K = np.array([[490., 0, 319.5], [0, 490., 179.5], [0, 0, 1]])


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


_MODEL = None


def model():
    global _MODEL
    if _MODEL is None:
        from safetensors.torch import load_file
        _MODEL = load_pretrained_model(ARCH_DIR, torch.device('cpu'),
                                       local_files_only=True, strict=True).eval()
        _MODEL.load_state_dict(load_file(INIT_WEIGHTS), strict=True)
    return _MODEL


def decode(video, frame_index, size=(640, 360)):
    c = cv2.VideoCapture(str(video))
    c.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
    ok, f = c.read(); c.release()
    if not ok:
        raise RuntimeError(f'cannot read {video} #{frame_index}')
    rgb = cv2.cvtColor(f, cv2.COLOR_BGR2RGB)
    if rgb.shape[1::-1] != size:
        rgb = cv2.resize(rgb, size, interpolation=cv2.INTER_AREA)
    return rgb


def segment(rgb):
    """DXY frozen inference math: PIL bilinear 256 / 255, bilinear logit upsampling, then argmax."""
    import torch.nn.functional as F
    h, w = rgb.shape[:2]
    im = Image.fromarray(rgb)
    a = np.asarray(im.resize((256, 256), Image.Resampling.BILINEAR), dtype=np.float32) / 255.
    t = torch.from_numpy(a).permute(2, 0, 1)[None]
    with torch.no_grad():
        o = model()(t)
    lg = o['logits'] if isinstance(o, dict) else (o[0] if isinstance(o, (tuple, list)) else o)
    lg = F.interpolate(lg, size=(h, w), mode='bilinear', align_corners=False)
    return torch.argmax(lg, dim=1).squeeze(0).numpy().astype(np.uint8)


def prepare_view(video, frame_index, out):
    rgb = decode(video, frame_index)
    labels = segment(rgb)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, RGB=rgb, labels=labels, K=K)
    return dict(cache=str(out), rgb_sha256=hashlib.sha256(rgb.tobytes()).hexdigest(),
                label_counts={int(k): int(v) for k, v in zip(*np.unique(labels, return_counts=True))})


if __name__ == '__main__':
    vm = json.loads((WS / 'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004/metrics/VIDEO_FRAME_MAP.json').read_text() if False else '{}')
    g, v = sys.argv[1], sys.argv[2]
    import pandas as pd
    mp = pd.read_csv(WS / 'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004/metrics/VIDEO_FRAME_MAP.csv')
    row = mp[(mp.group == g) & (mp.video.astype(str).str.zfill(3) == v.zfill(3))].iloc[0]
    video = Path(row.video_path)
    ALL = json.loads(Path('/home/liu/polyp_research/ring-first-3d/experiments/TASK-E4-PYTORCH3D-014/config/ALL_VIEWS.json').read_text())
    views = [x for x in ALL if x['case'] == g and x['video'] == v and isinstance(x.get('raw_frame'), int)][:8]
    outdir = WS / 'experiments/TASK-E4-PREBODY-UNIFIED-CAMERA-READINESS-004/runs/prepared' / f'{g}_{v}'
    recs = []
    for x in views:
        r = prepare_view(video, int(x['raw_frame']), outdir / (x['id'] + '.npz'))
        recs.append(dict(view=x['id'], raw_frame=int(x['raw_frame']), **r))
        print('prepared', x['id'], r['label_counts'], flush=True)
    (outdir / 'PREPARED.json').write_text(json.dumps(dict(video=str(video), video_sha256=sha(video),
                                                          init_model=INIT_MODEL, views=recs), indent=1))
    print('done', len(recs))
