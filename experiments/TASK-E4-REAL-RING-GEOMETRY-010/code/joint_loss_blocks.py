"""Ring blocks for B0 / C1 / C2 / C3 with the corrected geometry."""
import numpy as np
import cad_contour_geometry as G


def ring_residual(arm, base, pose, ob, K):
    b = np.asarray(base(pose, ob, 'train', K), float)
    if arm == 'B0':
        return b, dict(mode='B0', n=len(b), status=['frozen'])
    which = {'C1': 'inner', 'C2': 'outer', 'C3': 'both'}[arm]
    cb, st = G.cad_blocks(pose, K, ob, which=which)
    nq = len(ob['q_train'])
    return np.r_[cb, b[nq:]], dict(mode=arm, contour_n=len(cb), status=st)
