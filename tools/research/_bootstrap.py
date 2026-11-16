"""Run scripts without editable install or writes to shared environments."""
import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))


def args(description):
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--fixture", type=Path, default=ROOT / "tools/research/frozen_fixture.json")
    p.add_argument("--output", type=Path)
    p.add_argument("--dxy-root", type=Path, default=Path(os.environ.get("DXY_ROOT", "/home/liu/new-polyp-dxy")))
    return p.parse_args()


def emit(value, output=None):
    from ring_first_3d.evaluation.validation import clean
    s = json.dumps(clean(value), indent=2, allow_nan=False) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(s)
    print(s, end="")
