#!/usr/bin/env python3
"""Authorized two-video, no-GT comparison entrypoint."""
import os
from pathlib import Path
import sys
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ring_first_3d.sift_comparison.run import main
if __name__=='__main__':main()
