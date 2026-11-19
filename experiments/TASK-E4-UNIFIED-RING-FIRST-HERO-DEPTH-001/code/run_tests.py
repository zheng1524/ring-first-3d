from pathlib import Path
import io,json,sys,unittest
T=Path(__file__).resolve().parents[1];R=T.parents[1]
# Execute the exact original 247-test selection, redirecting only its outputs.
p=R/'docs/cleanup_003/code/regression.py'
text=p.read_text().replace("out=ROOT/'mainline/validation/regression'", "out=ROOT/'experiments/TASK-E4-UNIFIED-RING-FIRST-HERO-DEPTH-001/logs/regression'")
try:exec(compile(text,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
except SystemExit as e:
    r=json.loads((T/'logs/regression/RESULT.json').read_text())
    (T/'logs/REGRESSION_RESULT.json').write_text(json.dumps(r,indent=2))
    if e.code:raise
s=io.StringIO();r=unittest.TextTestRunner(stream=s,verbosity=2).run(unittest.defaultTestLoader.discover(str(T/'tests')))
(T/'logs/NEW_TESTS.txt').write_text(s.getvalue())
(T/'logs/NEW_TESTS.json').write_text(json.dumps(dict(status='PASS' if r.wasSuccessful() else 'FAIL',tests=r.testsRun,errors=len(r.errors),failures=len(r.failures)),indent=2))
print(s.getvalue());sys.exit(0 if r.wasSuccessful() else 1)
