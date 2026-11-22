#!/usr/bin/env python3
"""Repo-root convenience entry -> the single formal implementation."""
import runpy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent/'core'))
runpy.run_module('run_corrective', run_name='__main__')
