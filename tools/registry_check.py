#!/usr/bin/env python3
"""Lightweight registry gate: status legality, manifest presence, evidence consistency."""
import sys, json
from pathlib import Path
import yaml
ROOT = Path(__file__).resolve().parents[1]
STATUS = {'exploring', 'candidate', 'confirmed', 'frozen', 'rejected', 'deprecated'}
errors = []
comps = yaml.safe_load((ROOT/'registry/components.yaml').read_text())['components']
routes = yaml.safe_load((ROOT/'registry/routes.yaml').read_text())['routes']
ids = [c['id'] for c in comps]
if len(ids) != len(set(ids)): errors.append('duplicate component ids')
by_comp = {}
for r in routes:
    by_comp.setdefault(r['component'], []).append(r)
    if r['status'] not in STATUS: errors.append(f"{r['route_id']}: bad status {r['status']}")
    m = r.get('manifest')
    if m and not (ROOT/m).exists(): errors.append(f"{r['route_id']}: manifest missing {m}")
    if m and not (ROOT/m).exists(): pass
    if r['status'] == 'confirmed':
        rep = (r.get('reproduction') or {}).get('independent_report')
        if not rep or 'PENDING' in str(rep) or not (ROOT/rep).exists():
            errors.append(f"{r['route_id']}: confirmed without independent report")
    if r['status'] == 'frozen' and not r.get('human_approval'):
        errors.append(f"{r['route_id']}: frozen without human_approval")
    if r['status'] == 'rejected' and not r.get('diagnosis'):
        errors.append(f"{r['route_id']}: rejected without diagnosis")
for c, rs in by_comp.items():
    official = [r for r in rs if r['status'] in ('confirmed', 'frozen')]
    if len(official) > 1:
        errors.append(f'{c}: multiple confirmed/frozen routes')
for c in by_comp:
    if c not in ids: errors.append(f'route references unknown component {c}')
print(json.dumps(dict(components=len(comps), routes=len(routes), errors=errors), indent=1))
sys.exit(1 if errors else 0)
