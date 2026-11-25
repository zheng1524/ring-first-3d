#!/usr/bin/env python3
"""Strict resume validation for M2F7; never writes or repairs traces."""
import argparse,json,hashlib,pathlib,sys

def sha(p):
 p=pathlib.Path(p);return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--state',required=True);ap.add_argument('--root',required=True);a=ap.parse_args()
 root=pathlib.Path(a.root).resolve();state=pathlib.Path(a.state).resolve()
 if not state.is_file():raise SystemExit('STATE_MISSING')
 d=json.loads(state.read_text())
 required={'run_id','route_id','code_commit','config_sha256','stages'}
 if not required.issubset(d):raise SystemExit('STATE_FIELDS_MISSING')
 if not d['run_id']:raise SystemExit('RUN_ID_EMPTY')
 seen=[];prev=None
 for st in d['stages']:
  for k in ['stage','status','input_sha256','output_sha256']:
   if k not in st:raise SystemExit('STAGE_FIELD_MISSING '+st.get('stage','?'))
  if st['stage'] in seen:raise SystemExit('DUPLICATE_STAGE '+st['stage'])
  seen.append(st['stage'])
  if st['status']!='completed':continue
  out=None
  for k,v in st.items():
   if k.endswith('_path'):
    out=pathlib.Path(v)
  if out is None:raise SystemExit('OUTPUT_PATH_MISSING '+st['stage'])
  if not out.is_absolute():out=root/out
  if not out.is_file():raise SystemExit('OUTPUT_MISSING '+st['stage'])
  if sha(out)!=st['output_sha256']:raise SystemExit('OUTPUT_SHA_MISMATCH '+st['stage'])
  if prev is not None and st['input_sha256'] not in (None,prev):raise SystemExit('INPUT_PARENT_MISMATCH '+st['stage'])
  prev=st['output_sha256']
 print('STATE_OK',d['run_id'],'stages',len(seen))
if __name__=='__main__':main()
