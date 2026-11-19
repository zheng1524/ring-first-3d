from pathlib import Path
import unittest,io,json,sys
T=Path(__file__).resolve().parents[1];R=T.parents[1]
src=R/'docs/cleanup_003/code/regression.py';text=src.read_text().replace("out=ROOT/'mainline/validation/regression'",f"out=ROOT/'experiments/{T.name}/logs/regression'")
try:exec(compile(text,str(src),'exec'),dict(__name__='__main__',__file__=str(src)))
except SystemExit as e:
    if e.code:raise
s=io.StringIO();r=unittest.TextTestRunner(stream=s,verbosity=2).run(unittest.defaultTestLoader.discover(str(T/'tests')));(T/'logs/NEW_TESTS.txt').write_text(s.getvalue());old=json.loads((T/'logs/regression/RESULT.json').read_text());out=dict(status='PASS' if old['status']=='PASS' and r.wasSuccessful() else 'FAIL',original_tests=old['tests'],new_tests=r.testsRun,errors=len(r.errors),failures=len(r.failures));(T/'logs/TESTS.json').write_text(json.dumps(out,indent=2)+'\n');print(s.getvalue());sys.exit(0 if out['status']=='PASS' else 1)
