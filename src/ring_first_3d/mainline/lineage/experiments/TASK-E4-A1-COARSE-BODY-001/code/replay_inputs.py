"""Rebuild derived caches in a fresh checkout without changing the frozen protocol.

prepare.py's initial existence assertion is a first-registration safety guard.
This replay replaces only that assertion and the protocol write with an exact
content comparison (excluding registration timestamp). Scientific preparation
statements are compiled unchanged from the frozen source, whose hash is checked.
"""
from common import *
import argparse,copy
def main(rebuild=False):
    freeze=load(R/'provenance/PREOPTIMIZATION_FREEZE.json');src=R/'code/prepare.py';record=next(x for x in freeze['files']if x['path'].endswith('/code/prepare.py'));assert sha(src)==record['sha256']
    expected=load(R/'provenance/PREPARED_INPUT_INDEX.json')
    if rebuild:
        import prepare
        original_save=prepare.save
        def replay_save(path,value):
            if path=='config/PREREGISTERED.json':
                a=copy.deepcopy(protocol());b=copy.deepcopy(value);a.pop('UTC');b.pop('UTC');assert a==b,'Frozen registration mismatch';return
            original_save(path,value)
        prepare.save=replay_save;tree=ast.parse(src.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');assert isinstance(node.body[0],ast.Assert);node.body=node.body[1:];exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),'exec'),prepare.__dict__);prepare.main()
    for x in expected:
        p=R/'inputs'/Path(x['path']).name;assert p.exists()and sha(p)==x['sha256'],str(p)
    print('INPUT_REPLAY_HASHES_PASS',len(expected))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--rebuild',action='store_true');a=ap.parse_args();main(a.rebuild)
