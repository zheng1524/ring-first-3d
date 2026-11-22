#!/usr/bin/env python3
"""Formal entry name (kept stable for the task contract); single implementation lives in
run_corrective.py, so there is exactly ONE algorithm path."""
import runpy
runpy.run_module('run_corrective', run_name='__main__')
