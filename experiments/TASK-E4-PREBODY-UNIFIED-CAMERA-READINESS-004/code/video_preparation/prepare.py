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
INIT_MODEL = '/home/liu/polyp_research/models/preserved_best_multiclass_overlapaware_20260405'
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
        _MODEL = load_pretrained_model(INIT_MODEL, torch.device('cpu'),
                                       local_files_only=True, strict=True).eval()
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
    x = cv2.resize(rgb, (256, 256), interpolation=cv2.INTER_LINEAR)
    t = torch.from_numpy(x).float().permute(2, 0, 1)[None] / 255.
    with torch.no_grad():
        o = model()(t)
    lg = o['logits'] if isinstance(o, dict) else (o[0] if isinstance(o, (tuple, list)) else o)
    p = lg.argmax(1)[0].numpy().astype(np.uint8)
    p = cv2.resize(p, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)
    p[p == 255] = 0
    return p


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
