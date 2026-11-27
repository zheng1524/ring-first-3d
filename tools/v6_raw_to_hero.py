#!/usr/bin/env python3
"""Single public RAW → V6 → official HERO entrypoint."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ring_first_3d.v6_raw.full_run import main
if __name__=='__main__':
 if len(sys.argv)==1:sys.argv.append('run')
 main()
