"""Post-freeze diagnostic: execute the unchanged original nested objective."""
from common import *
def bind_objective(body,renderer):
    path=Path(__file__).with_name('fit.py');tree=ast.parse(path.read_text())
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
    objective=next(n for n in main.body if isinstance(n,ast.FunctionDef)and n.name=='evaluate')
    hub=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='huber')
    ns=dict(globals(),body=body,renderer=renderer)
    exec(compile(ast.Module(body=[hub,objective],type_ignores=[]),str(path),'exec'),ns)
    signature=hashlib.sha256(ast.dump(objective,include_attributes=False).encode()).hexdigest()
    return ns['evaluate'],dict(fit_source=asset(path),objective_AST_sha256=signature,weights_and_solver_unchanged=True)
