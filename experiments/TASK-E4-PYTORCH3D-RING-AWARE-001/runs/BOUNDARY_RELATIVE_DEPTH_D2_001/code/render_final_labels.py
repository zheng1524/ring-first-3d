"""Redraw A/D only after label/legend QA; no prediction or metric changes."""
from figures_d2 import *
source=(R/'code/figures_d2.py').read_text();fn=next(x for x in ast.parse(source).body if isinstance(x,ast.FunctionDef)and x.name=='main');nodes=fn.body[:11]+fn.body[24:32];exec(compile(ast.Module(body=nodes,type_ignores=[]),str(R/'code/figures_d2.py')+':A_D_labels','exec'),globals());print('A_D_LABELS_DONE')
