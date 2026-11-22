"""Real cross-video SIFT extraction with an explicit, auditable filter chain."""
import json
from pathlib import Path
import cv2, numpy as np

WS = Path('/home/liu/ring_first_3d_workspace')
PREP = WS/'experiments/TASK-E4-UNIFIED-RING-CONTOUR-REFINEMENT-005/runs/prepared'


def _load_views(group, video):
    p = PREP/f'{group}_{video}'/'PREPARED.json'
    return {q['view']: q for q in json.loads(Path(p).read_text())['views']}


def extract(a_id, b_id, ratio=0.75, min_matches=10, group='G03', video_a='004', video_b='005'):
    v4 = _load_views(group, video_a)[a_id]
    v5 = _load_views(group, video_b)[b_id]
    ia, ib = np.load(v4['cache']), np.load(v5['cache'])
    sift = cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.01)
    ka, da = sift.detectAndCompute(cv2.cvtColor(ia['RGB'], cv2.COLOR_RGB2GRAY), None)
    kb, db = sift.detectAndCompute(cv2.cvtColor(ib['RGB'], cv2.COLOR_RGB2GRAY), None)
    if da is None or db is None:
        return dict(a=a_id, b=b_id, n_raw=0, n_ratio=0, n_bg=0, pa=None, pb=None,
                    ids_a=None, ids_b=None)
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < ratio * n.distance]
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    fa = np.array([m.queryIdx for m in good])
    fb = np.array([m.trainIdx for m in good])
    la, lb = ia['labels'], ib['labels']
    keep = [i for i, (x, y) in enumerate(pa)
            if la[int(y), int(x)] == 0 and lb[int(pb[i][1]), int(pb[i][0])] == 0]
    return dict(a=a_id, b=b_id, n_raw=len(ka) and len(kb), n_ratio=len(good), n_bg=len(keep),
                pa=pa[keep], pb=pb[keep], ids_a=fa[keep], ids_b=fb[keep],
                frames_a=int(v4['raw_frame']), frames_b=int(v5['raw_frame']))


def collect(views_a, views_b, min_bg=10, group='G03', video_a='004', video_b='005'):
    out = []
    for a in views_a:
        for b in views_b:
            m = extract(a, b, group=group, video_a=video_a, video_b=video_b)
            if m['n_bg'] >= min_bg:
                out.append(m)
    return out
