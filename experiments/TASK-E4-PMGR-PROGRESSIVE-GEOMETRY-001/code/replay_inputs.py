"""Rebuild deterministic task inputs while preserving preregistered records."""
from inputs import *
import argparse
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--rebuild',action='store_true');args=ap.parse_args();frozen=load(R/'metrics/INPUT_FREEZE.json')
    if args.rebuild:
        import prepare
        original_save=prepare.save
        def frozen_save(name,value):
            if name=='config/LOCKED_PROTOCOL.json':assert clean(value)==protocol(),'protocol differs';return
            if name=='metrics/INPUT_FREEZE.json':return
            if(R/name).exists():return
            original_save(name,value)
        prepare.save=frozen_save;tree=ast.parse((R/'code/prepare.py').read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='main');assert isinstance(node.body[0],ast.Assert);node.body=node.body[1:];exec(compile(ast.Module(body=[node],type_ignores=[]),str(R/'code/prepare.py'),'exec'),prepare.__dict__);prepare.main()
    for x in frozen['inputs']:
        p=R/'inputs'/Path(x['path']).name;assert p.exists()and sha(p)==x['sha256'],str(p)
    assert sha(R/'config/LOCKED_PROTOCOL.json')==frozen['protocol']['sha256']
    print('FROZEN_INPUT_SHA_PASS',len(frozen['inputs']))
if __name__=='__main__':main()
