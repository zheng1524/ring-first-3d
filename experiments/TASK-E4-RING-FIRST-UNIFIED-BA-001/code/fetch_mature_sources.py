"""Small official reference sources only, no framework/model download."""
from ucommon import *
import urllib.request

def fetch(url):return urllib.request.urlopen(url,timeout=25).read()
def main():
 rows=[]
 for repo,ref,files in [('ceres-solver/ceres-solver','2.2.0',['examples/simple_bundle_adjuster.cc','examples/bundle_adjuster.cc','include/ceres/gradient_checker.h','LICENSE']),('colmap/colmap','main',['src/colmap/estimators/bundle_adjustment.cc','src/colmap/estimators/bundle_adjustment.h','COPYING.txt']),('cvg/pyceres','v2.6',['_pyceres/core/cost_functions.h','_pyceres/core/problem.h','examples/test_python_cost.py','LICENSE'])]:
  try:
   commit=json.loads(fetch('https://api.github.com/repos/'+repo+'/commits/'+ref))['sha']
  except Exception as e:rows.append(dict(repo=repo,ref=ref,status='MISSING_NETWORK_COMMIT',error=str(e)));continue
  for f in files:
   try:
    data=fetch('https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+f);out=N/'vendor'/repo.split('/')[-1]/Path(f);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data);rows.append(dict(repo=repo,requested_ref=ref,commit=commit,relative_source=f,source_url='https://github.com/'+repo+'/blob/'+commit+'/'+f,local=asset(out),status='READ_OFFICIAL_SOURCE'))
   except Exception as e:rows.append(dict(repo=repo,ref=ref,commit=commit,file=f,status='MISSING_NETWORK_FILE',error=str(e)))
 save('provenance/MATURE_SOURCE_READ_RECEIPT.json',rows);print('MATURE_REFERENCES',len(rows),flush=True)
if __name__=='__main__':main()
