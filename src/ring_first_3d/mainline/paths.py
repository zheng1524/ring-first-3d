"""Explicit relocation of code only; raw observations remain manifest-bound."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
LINEAGE=Path(__file__).parent/'lineage'
def historical_path(value):
    p=Path(value);s=str(p)
    if s.startswith('/home/liu/ring_first_3d'):
        parts=p.parts
        if 'experiments'in parts:
            i=parts.index('experiments');return LINEAGE.joinpath(*parts[i:])
        return LINEAGE
    return p

def activate(name):
    """One legacy module namespace per fresh process, with explicit version."""
    import sys
    folder=LINEAGE/'experiments'/name/'code'
    if not folder.is_dir():raise FileNotFoundError(folder)
    sys.path.insert(0,str(folder));return folder
