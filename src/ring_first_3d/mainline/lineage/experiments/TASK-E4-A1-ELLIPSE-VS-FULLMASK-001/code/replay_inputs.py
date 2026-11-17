"""Replay exact frozen input preparation; never replace the protocol."""
from common import *
import argparse
def main(rebuild=False):
    reference=load(R/'provenance/PREPARED_INPUT_INDEX.json');freeze=load(R/'provenance/PREOPTIMIZATION_CORRECTION_v0.2.json');src=R/'code/prepare.py';expected=next(x['sha256']for x in freeze['files']if x['path'].endswith('/code/prepare.py'));assert sha(src)==expected
    if rebuild:
        import prepare
        original=prepare.save
        def checked_save(name,value):
            if name=='config/PROTOCOL.json':assert clean(value)==protocol(),'Frozen protocol differs';return
            original(name,value)
        prepare.save=checked_save;tree=ast.parse(src.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');assert isinstance(node.body[0],ast.Assert);node.body=node.body[1:];exec(compile(ast.Module(body=[node],type_ignores=[]),str(src),'exec'),prepare.__dict__);prepare.main()
    for x in reference:
        path=R/'inputs'/Path(x['path']).name;assert path.exists()and sha(path)==x['sha256'],str(path)
    print('INPUT_REPLAY_13_SHA_PASS')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--rebuild',action='store_true');args=ap.parse_args();main(args.rebuild)
