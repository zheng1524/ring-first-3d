import sys,json,pathlib,numpy as np
WS=pathlib.Path('/home/liu/ring_first_3d_workspace'); sys.path.insert(0,str(WS/'src'))
from ring_first_3d.mainline.native.cleaning import classify_native
out=WS/'runs/m2d_mvs_reproduction/historical_reproduction/R1/G01_004_ref03'
ring='/home/liu/ring-first-hero-core/cad/R10.npz'
rec=classify_native(out,ring); print(json.dumps(rec,indent=1)); print('historical',open('/home/liu/ring-first-hero-core/outputs/hero/CLEANING.json').read())
