#!/usr/bin/env python3
"""Single public RAW → V6 → official HERO entrypoint."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from ring_first_3d.v6_raw.route import main
if __name__=='__main__':main()
