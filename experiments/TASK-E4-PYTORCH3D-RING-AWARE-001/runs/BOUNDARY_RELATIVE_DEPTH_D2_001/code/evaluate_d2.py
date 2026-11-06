from evaluate import *
import ast

def main():
 freeze=load(R/'assets_index/PREDICTIONS_FROZEN.json');assert freeze['all_expected_finals']
 for a in freeze['files']:assert sha(a['path'])==a['sha256']
 # Preserve full inherited evaluation operators; only enumerate the fixed D2 states and per-case sample filenames.
 source=(R/'code/evaluate.py').read_text();tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='evaluate_case');s=ast.get_source_segment(source,fn);old=next(n for n in ast.walk(fn)if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='states'for t in n.targets));line=ast.get_source_segment(source,old)
 new="states=[('P0',0,R/'inputs'/name/'INITIAL.npz')]+[(arm,step,R/'local_results'/name/arm/('STEP_%04d.npz'%step))for arm in['B','E1','E2','E3']for step in[50,100,200,300]]"
 s=s.replace(line,new).replace("'audit_only/FIXED_GT_SAMPLES.npz'","'audit_only/'+name+'_FIXED_GT_SAMPLES.npz'")
 exec(compile(s,str(R/'code/evaluate.py')+':fixed_state_adapter','exec'),globals());allg=[];allp=[];posterior=[]
 for name in load(R/'config/PROTOCOL.json')['cases']:
  gt=None
  if name.startswith('virtual'):
   path=OLD/'audit_only/NATIVE_CAD_GT.npz'if name=='virtual_IIa'else R/'audit_only'/name/'GT.npz';gt=dict(np.load(path));posterior.append(asset(path))
  g,p=evaluate_case(name,gt);allg+=g;allp+=p
 table('metrics/ALL_GEOMETRY.csv',allg);save('metrics/ALL_GEOMETRY.json',allg);table('metrics/PER_VIEW_METRICS.csv',allp);save('assets_index/POSTERIOR_GT.json',dict(files=posterior,prediction_freeze_sha=sha(R/'assets_index/PREDICTIONS_FROZEN.json'),no_model_selection=True));print('EVALUATION_DONE')
if __name__=='__main__':main()
