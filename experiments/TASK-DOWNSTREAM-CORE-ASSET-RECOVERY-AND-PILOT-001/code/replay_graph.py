"""Explicit historical STEP024 replay: zero optimizer steps."""
import json,numpy as np,torch
from pilot import TASK,REPO,sha
from ring_first_3d.mainline.paths import activate
activate('TASK-E4-STRUCTURED-BODY-UPDATE-002')
from deformation_graph import DeformationGraph
from smooth_arap import SmoothARAP
rows=[]
for r in json.loads((TASK/'evidence/HISTORY_PROTECTION.json').read_text()):
 assert sha(REPO/r['retained'])==r['sha256']
for case in ['G01','G03']:
 root=TASK/'fixtures/history'/case;initial=dict(np.load(root/'INITIAL.npz'));state=np.load(root/'STEP_024/GRAPH.npz');expected=np.load(root/'STEP_024/BODY.npz');graph=DeformationGraph(initial['V'],initial['F_solid']);actual=graph.mesh(torch.tensor(state['rotation']),torch.tensor(state['translation']));error=float(np.linalg.norm(actual.numpy()-expected['V'],axis=1).max());arap=SmoothARAP(initial['V'],initial['F_solid']);energies=arap.energies(actual,arap.rotations(actual));assert error<1e-9
 rows.append(dict(case=case,optimizer_steps=0,max_vertex_error_mm=error,ARAP=float(energies[0]),smooth=float(energies[1]),SARAP=float(energies[2]),meaning='historical parameter replay; not new training',growth_history='G01 ACCEPTED; fixed-frame GT worsened' if case=='G01' else 'G03 PER_VIEW_PROTECTION rejected; formal length NaN'))
(TASK/'evidence/HISTORICAL_REPLAY.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
