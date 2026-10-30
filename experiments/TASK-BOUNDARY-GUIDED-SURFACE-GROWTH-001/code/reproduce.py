"""Cache-only entry point. This never calls HERO or resumes growth."""
import argparse,subprocess,sys,os
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['verify','index','figures','evaluate']);a=p.parse_args();code=Path(__file__).resolve().parent
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='2')
    def run(name,*args):subprocess.run([sys.executable,str(code/name),*args],env=env,check=True)
    if a.action=='verify':run('test_growth_results.py');run('final_verify.py')
    elif a.action=='index':run('final_report.py')
    elif a.action=='figures':run('visualize.py','positive');run('visualize.py','final')
    elif a.action=='evaluate':
        run('evaluate.py');run('surface_support_audit.py');run('audit_results.py');run('cad_audit.py');run('final_report.py');run('final_verify.py')

if __name__=='__main__':main()
